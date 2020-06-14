# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Installation tests."""
import contextlib
import os
import shutil
import subprocess
import tarfile
import tempfile

from ci import config
from ci import nox


@contextlib.contextmanager
def temp_chdir(session: nox.Session, target: str):
    cwd = os.path.abspath(os.getcwd())
    print("Changing directory from", cwd, "to", target)
    session.chdir(target)
    yield cwd
    print("Changing directory from", target, "to", cwd)
    session.chdir(cwd)


def predicate():
    commit_ref = os.getenv("CI_COMMIT_REF_NAME")
    return commit_ref in (config.PROD_BRANCH, config.PREPROD_BRANCH) and "CI" in os.environ


@nox.session(reuse_venv=False, only_if=predicate)
def pip(session: nox.Session):
    """Run through sandboxed install of PyPI package."""
    if "--showtime" in session.posargs:
        print("Testing we can install packaged pypi object")
        session.install(config.MAIN_PACKAGE)
        session.run("python", "-m", config.MAIN_PACKAGE)
        # Prevent nox caching old versions and using those when tests run.
        session.run("pip", "uninstall", "-vvv", "-y", config.MAIN_PACKAGE)

    else:
        try:
            print("Testing published ref can be installed as a package.")
            url = session.env.get("CI_PROJECT_URL")
            sha1 = session.env.get("CI_COMMIT_SHA", "master")
            slug = f"git+{url}.git@{sha1}"
            session.install(slug)
            session.run("python", "-m", config.MAIN_PACKAGE)
            # Prevent nox caching old versions and using those when tests run.
            session.run("pip", "uninstall", "-vvv", "-y", config.MAIN_PACKAGE)
        except Exception:
            print("Failed to install from GitLab.")
            raise KeyError from None


@nox.session(reuse_venv=False)
def pip_git(session: nox.Session):
    """Test installing repository from Git repository directly via pip."""
    print("Testing installing from git repository only")

    try:
        branch = os.environ["CI_COMMIT_SHA"]
    except KeyError:
        branch = subprocess.check_output(["git", "symbolic-ref", "--short", "HEAD"]).decode("utf8")[0:-1]

    print("Testing for branch", branch)

    with tempfile.TemporaryDirectory() as temp_dir:
        with temp_chdir(session, temp_dir) as project_dir:
            session.install(f"git+file://{project_dir}")
            session.install(config.MAIN_PACKAGE)
            session.run("python", "-m", config.MAIN_PACKAGE)

    print("Installed as git dir in temporary environment successfully!")


@nox.session(reuse_venv=False)
def pip_sdist(session: nox.Session):
    """Test installing as an sdist package."""
    session.install("wheel")
    session.run("python", "setup.py", "build", "sdist")

    print("Testing installing from wheel")
    with tempfile.TemporaryDirectory() as temp_dir:
        with temp_chdir(session, temp_dir) as project_dir:
            dist = os.path.join(project_dir, "dist")
            wheels = [os.path.join(dist, wheel) for wheel in os.listdir(dist) if wheel.endswith(".tar.gz")]
            wheels.sort(key=lambda wheel: os.stat(wheel).st_ctime)
            newest_tarball = wheels.pop()
            newest_tarball_name = os.path.basename(newest_tarball)

            if newest_tarball_name.lower().endswith(".tar.gz"):
                newest_tarball_dir = newest_tarball_name[: -len(".tar.gz")]
            else:
                newest_tarball_dir = newest_tarball_name[: -len(".tgz")]

            print(f"copying newest tarball found at {newest_tarball} and installing it in temp dir")
            shutil.copyfile(newest_tarball, newest_tarball_name)

            print("extracting tarball")
            with tarfile.open(newest_tarball_name) as tar:
                tar.extractall()

            print("installing sdist")
            with temp_chdir(session, newest_tarball_dir):
                session.run("python", "setup.py", "install")
                session.run("python", "-m", config.MAIN_PACKAGE)

    print("Installed as wheel in temporary environment successfully!")


@nox.session(reuse_venv=False)
def pip_bdist_wheel(session: nox.Session):
    """Test installing as a platform independent bdist_wheel package."""
    session.install("wheel")
    session.run("python", "setup.py", "build", "bdist_wheel")

    print("Testing installing from wheel")
    with tempfile.TemporaryDirectory() as temp_dir:
        with temp_chdir(session, temp_dir) as project_dir:
            dist = os.path.join(project_dir, "dist")
            wheels = [os.path.join(dist, wheel) for wheel in os.listdir(dist) if wheel.endswith(".whl")]
            wheels.sort(key=lambda wheel: os.stat(wheel).st_ctime)
            newest_wheel = wheels.pop()
            newest_wheel_name = os.path.basename(newest_wheel)
            print(f"copying newest wheel found at {newest_wheel} and installing it in temp dir")
            shutil.copyfile(newest_wheel, newest_wheel_name)
            session.run("pip", "install", newest_wheel_name)
            session.run("python", "-m", config.MAIN_PACKAGE)

    print("Installed as wheel in temporary environment successfully!")

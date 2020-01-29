#!/usr/bin/env python3
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
import contextlib
import os
import shutil
import subprocess
import tarfile
import tempfile

import nox.sessions


def pathify(arg, *args, root=False):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)) if not root else "/", arg, *args))


# Configuration stuff we probably might move around eventually.
MAIN_PACKAGE = "hikari"
OWNER = "nekokatt"
TECHNICAL_DIR = "technical"
TEST_PATH = "tests/hikari"
PYLINT_VERSION = "2.4.4"
PYLINT_THRESHOLD = 8
COVERAGE_RC = ".coveragerc"
ARTIFACT_DIR = "public"
DOCUMENTATION_DIR = "docs"
CI_SCRIPT_DIR = "tasks"
SPHINX_OPTS = "-WTvvn"
BLACK_PACKAGES = [MAIN_PACKAGE, TEST_PATH]
BLACK_PATHS = [m.replace(".", "/") for m in BLACK_PACKAGES] + [__file__, pathify(DOCUMENTATION_DIR, "conf.py")]
BLACK_SHIM_PATH = pathify(CI_SCRIPT_DIR, "black.py")
GENDOC_PATH = pathify(CI_SCRIPT_DIR, "gendoc.py")
MAIN_PACKAGE_PATH = MAIN_PACKAGE.replace(".", "/")
REPOSITORY = f"https://gitlab.com/{OWNER}/{MAIN_PACKAGE}"
PYTEST_ARGS = [
    "--cov",
    MAIN_PACKAGE,
    "--cov-config",
    COVERAGE_RC,
    "--cov-report",
    "term",
    "--cov-report",
    f"html:{ARTIFACT_DIR}/coverage/html",
    "--cov-branch",
    f"--junitxml={ARTIFACT_DIR}/tests.xml",
    "--showlocals",
    "--testdox",
    "--force-testdox",
]


@nox.session()
def test(session) -> None:
    """Run unit tests in Pytest."""
    session.run("pip", "install", "-Ur", "requirements.txt")
    session.run("pip", "install", "-Ur", "dev-requirements.txt")
    session.run("python", "-m", "pytest", *PYTEST_ARGS, *session.posargs, TEST_PATH)


@nox.session()
def documentation(session) -> None:
    """Generate documentation using Sphinx for the current branch."""
    session.run("pip", "install", "-Ur", "requirements.txt")
    session.run("pip", "install", "-Ur", "dev-requirements.txt")
    session.run("pip", "install", "-Ur", "doc-requirements.txt")
    session.env["SPHINXOPTS"] = SPHINX_OPTS
    tech_dir = pathify(DOCUMENTATION_DIR, TECHNICAL_DIR)
    shutil.rmtree(tech_dir, ignore_errors=True, onerror=lambda *_: None)
    os.mkdir(tech_dir)
    session.run(
        "python",
        GENDOC_PATH,
        ".",
        MAIN_PACKAGE,
        pathify(DOCUMENTATION_DIR, "_templates", "gendoc"),
        pathify(DOCUMENTATION_DIR, "index.rst"),
        pathify(DOCUMENTATION_DIR, TECHNICAL_DIR),
    )
    session.run("python", "-m", "sphinx.cmd.build", DOCUMENTATION_DIR, ARTIFACT_DIR, "-b", "html")


@nox.session()
def sast(session) -> None:
    """Run static application security testing with Bandit."""
    session.run("pip", "install", "bandit")
    pkg = MAIN_PACKAGE.split(".")[0]
    session.run("bandit", pkg, "-r")


@nox.session()
def safety(session) -> None:
    """Run safety checks against a vulnerability database using Safety."""
    session.run("pip", "install", "-Ur", "requirements.txt")
    session.run("pip", "install", "safety")
    session.run("safety", "check")


@nox.session()
def format(session) -> None:
    """Reformat code with Black. Pass the '--check' flag to check formatting only."""
    session.run("pip", "install", "black")
    session.run("python", BLACK_SHIM_PATH, *BLACK_PATHS, *session.posargs)


@nox.session()
def lint(session) -> None:
    """Check formating with pylint"""
    session.run("pip", "install", "-Ur", "requirements.txt")
    session.run("pip", "install", "-Ur", "dev-requirements.txt")
    session.run("pip", "install", "-Ur", "doc-requirements.txt")
    session.run("pip", "install", "pylint-junit==0.2.0")
    # TODO: Change code under this comment to the commented code when we update to pylint 2.5
    # session.run("pip", "install", f"pylint=={PYLINT_VERSION}" if PYLINT_VERSION else "pylint")
    session.run(
        "pip", "install", "git+https://github.com/davfsa/pylint"
    )  # Freezed version of pylint 2.5 pre-release to make sure that nothing will break
    pkg = MAIN_PACKAGE.split(".")[0]

    try:
        session.run("pylint", pkg, "--rcfile=pylintrc", f"--fail-under={PYLINT_THRESHOLD}")
    finally:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)

        with open(os.path.join(ARTIFACT_DIR, "pylint.xml"), "w") as fp:
            session.run(
                "pylint",
                pkg,
                "--rcfile=pylintrc",
                f"--fail-under={PYLINT_THRESHOLD}",
                "--output-format=pylint_junit.JUnitReporter",
                stdout=fp,
            )


if os.getenv("CI"):

    @nox.session()
    def pip(session: nox.sessions.Session):
        """Run through sandboxed install of PyPI package (if running on CI)"""
        if "--showtime" not in session.posargs:
            pip_showtime(session)
        else:
            try:
                pip_from_ref(session)
            except Exception:
                print("Failed to install from GitLab.")
                raise KeyError from None


@nox.session(reuse_venv=False)
def pip_bdist_wheel(session: nox.sessions.Session):
    """
    Test installing a bdist_wheel package.
    """
    session.run("pip", "install", "wheel")
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
            session.run("python", "-m", MAIN_PACKAGE, "-V")

    print("Installed as wheel in temporary environment successfully!")


@nox.session(reuse_venv=False)
def pip_sdist(session: nox.sessions.Session):
    """
    Test installing an sdist package.
    """
    session.run("pip", "install", "wheel")
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
                session.run("python", "-m", MAIN_PACKAGE, "-V")

    print("Installed as wheel in temporary environment successfully!")


@nox.session(reuse_venv=False)
def pip_git(session: nox.sessions.Session):
    """
    Test installing repository from Git.
    """
    print("Testing installing from git repository only")

    try:
        branch = os.environ["CI_COMMIT_SHA"]
    except KeyError:
        branch = subprocess.check_output(["git", "symbolic-ref", "--short", "HEAD"]).decode("utf8")[0:-1]

    print("Testing for branch", branch)

    with tempfile.TemporaryDirectory() as temp_dir:
        with temp_chdir(session, temp_dir) as project_dir:
            session.run("pip", "install", f"git+file://{project_dir}")
            session.run("pip", "install", MAIN_PACKAGE)
            session.run("python", "-m", MAIN_PACKAGE, "-V")

    print("Installed as git dir in temporary environment successfully!")


def pip_showtime(session):
    print("Testing we can install packaged pypi object")
    session.run("pip", "install", MAIN_PACKAGE)
    session.run("python", "-c", f"import {MAIN_PACKAGE}; print({MAIN_PACKAGE}.__version__)")
    # Prevent nox caching old versions and using those when tests run.
    session.run("pip", "uninstall", "-vvv", "-y", MAIN_PACKAGE)


def pip_from_ref(session):
    print("Testing published ref can be installed as a package.")
    url = session.env.get("CI_PROJECT_URL", REPOSITORY)
    sha1 = session.env.get("CI_COMMIT_SHA", "master")
    slug = f"git+{url}.git@{sha1}"
    session.run("pip", "install", slug)
    session.run("python", "-c", f"import {MAIN_PACKAGE}; print({MAIN_PACKAGE}.__version__)")
    # Prevent nox caching old versions and using those when tests run.
    session.run("pip", "uninstall", "-vvv", "-y", MAIN_PACKAGE)


@contextlib.contextmanager
def temp_chdir(session, target):
    cwd = os.path.abspath(os.getcwd())
    print("Changing directory from", cwd, "to", target)
    session.chdir(target)
    yield cwd
    print("Changing directory from", target, "to", cwd)
    session.chdir(cwd)

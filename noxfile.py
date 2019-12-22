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
import fnmatch
import os
import shutil
import traceback

import nox.sessions


def pathify(arg, *args, root=False):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)) if not root else "/", arg, *args))


# Configuration stuff we probably might move around eventually.
MAIN_PACKAGE = "hikari"
OWNER = "nekokatt"
TECHNICAL_DIR = "technical"
TEST_PATH = "tests/hikari"
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
    "--showlocals",
    "--testdox",
    "--force-testdox",
]

if os.getenv("CI"):
    PYTEST_ARGS.append("-rA")


# Guard against connection resets by retring installs several times before actually giving up.
def failsafe_install(session, *args):
    ex = None
    for i in range(10):
        try:
            session.install(*args)
            ex = None
            break
        except Exception as ex:
            traceback.print_exc()
            print("trying again...")

    if ex is not None:
        raise ex


@nox.session(python=False)
def test(session) -> None:
    """Run unit tests in Pytest."""
    session.run("python", "-m", "pytest", *PYTEST_ARGS, *session.posargs, TEST_PATH)


@nox.session(python=False)
def documentation(session) -> None:
    """Generate documentation using Sphinx for the current branch."""
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
    failsafe_install(session, "bandit")
    pkg = MAIN_PACKAGE.split(".")[0]
    session.run("bandit", pkg, "-r")


@nox.session()
def safety(session) -> None:
    """Run safety checks against a vulnerability database using Safety."""
    session.run("poetry", "update", "--no-dev", external=True)
    failsafe_install(session, "safety")
    session.run("safety", "check")


@nox.session()
def format(session) -> None:
    """Reformat code with Black. Pass the '--check' flag to check formatting only."""
    failsafe_install(session, "black")
    session.run("python", BLACK_SHIM_PATH, *BLACK_PATHS, *session.posargs)


@nox.session()
def pip(session: nox.sessions.Session):
    """Run through sandboxed install of PyPI package (if running on CI) or of installing package locally."""
    try:
        if os.environ["CI"]:
            if "--showtime" in session.posargs:
                session.log("Testing we can install packaged pypi object")
                session.run("pip", "install", MAIN_PACKAGE)
            else:
                try:
                    session.log("Testing published ref can be installed as a package.")
                    url = session.env.get("CI_PROJECT_URL", REPOSITORY)
                    sha1 = session.env.get("CI_COMMIT_SHA", "master")
                    slug = f"git+{url}.git@{sha1}"
                    session.run("pip", "install", slug)
                except Exception:
                    session.log("Failed to install from GitLab. Resorting to local install.")
                    raise KeyError from None
        else:
            raise KeyError
    except KeyError:
        session.log("Testing local repository can be installed as a package.")
        session.run("pip", "install", "--isolated", ".")

    session.run("python", "-c", f"import {MAIN_PACKAGE}; print({MAIN_PACKAGE}.__version__)")

    # Prevent nox caching old versions and using those when tests run.
    session.run("pip", "uninstall", "-vvv", "-y", MAIN_PACKAGE)

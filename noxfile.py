#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import time

import nox.sessions


print("Before you go any further, please read https://gitlab.com/nekokatt/hikari/wikis/Contributing")
time.sleep(2)


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
    "-ra",
    "--showlocals",
    "--testdox",
    "--force-testdox",
]


def line_count(directories, file_include_globs=("*.py",), dir_exclude_globs=("__pycache__",)):
    def match_globs(names, globs):
        results = set()
        for glob in globs:
            results |= set(fnmatch.filter(names, glob))
        return results

    def get_files_matching():
        for root, dirs, files in os.walk(directory, topdown=True):
            for exclude in match_globs(dirs, dir_exclude_globs):
                dirs.remove(exclude)

            for file in match_globs(files, file_include_globs):
                yield os.path.join(root, file)

    def print_line_count(count, file):
        print(f"{count: >10.0f}", file)

    total_lines = 0
    for directory in directories:
        total_sub_lines = 0
        print()
        print("Line count in", directory)
        for file in sorted(get_files_matching()):
            with open(file) as fp:
                file_lines = fp.read().count("\n")
                print_line_count(file_lines, file)
                total_sub_lines += file_lines
                total_lines += file_lines

        print_line_count(total_sub_lines, "TOTAL in " + directory)

    print()
    print_line_count(total_lines, "TOTAL")


@nox.session(python=False)
def stats(_) -> None:
    """Count lines of code."""
    line_count([TEST_PATH, MAIN_PACKAGE_PATH])


@nox.session(python=False)
def pytest(session) -> None:
    """Run pytest"""
    session.run(
        "python", "-W", "ignore::DeprecationWarning", "-m", "pytest", *PYTEST_ARGS, *session.posargs, TEST_PATH,
    )


@nox.session(python=False)
def sphinx(session) -> None:
    """Generate documentation."""
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


@nox.session(python=False)
def bandit(session) -> None:
    """Run static application security analysis."""
    pkg = MAIN_PACKAGE.split(".")[0]
    session.run("bandit", pkg, "-r")


@nox.session(python=False)
def black(session) -> None:
    """Check formatting."""
    session.run("python", BLACK_SHIM_PATH, *BLACK_PATHS, *session.posargs)


@nox.session()
def install(session: nox.sessions.Session):
    """Test installing PyPI package or zipped code bundle if running locally."""
    if os.getenv("CI", False):
        if "--showtime" in session.posargs:
            session.log("Testing we can install packaged pypi object")
            session.run("pip", "install", MAIN_PACKAGE)
        else:
            session.log("Testing published ref can be installed as a package.")
            url = session.env.get("CI_PROJECT_URL", REPOSITORY)
            ref = session.env.get("CI_COMMIT_REF_NAME", "master")
            slug = f"git+{url}.git@{ref}"
            session.run("pip", "install", slug)
    else:
        session.log("Testing local repository can be installed as a package.")
        session.run("pip", "install", "--isolated", ".")

    session.run("python", "-c", f"import {MAIN_PACKAGE}; print({MAIN_PACKAGE}.__version__)")

    # Prevent nox caching old versions and using those when tests run.
    session.run("pip", "uninstall", "-vvv", "-y", MAIN_PACKAGE)

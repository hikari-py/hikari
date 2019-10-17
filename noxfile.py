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
import functools
import fnmatch
import os
import shutil
import traceback
import typing

from nox import session as nox_session
from nox import sessions


def pathify(arg, *args, root=False):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)) if not root else "/", arg, *args))


# Configuration stuff we probably might move around eventually.
MAIN_PACKAGE = "hikari.core"
OWNER = "nekokatt"
TECHNICAL_DIR = "technical"
TEST_PATH = "tests/hikari/core"
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


class PoetryNoxSession(sessions.Session):
    # noinspection PyMissingConstructor
    def __init__(self, session: sessions.Session) -> None:
        self.__session = session

    def __getattr__(self, item) -> typing.Any:
        return getattr(self.__session, item)

    def poetry(self, command, *args, **kwargs) -> None:
        self.__session.run("poetry", command, *args, **kwargs)

    def run(self, *args, **kwargs) -> None:
        self.poetry("run", *args, **kwargs)


def using_poetry(session_logic):
    """Ensure that the decorated function always initializes itself using poetry first."""

    @functools.wraps(session_logic)
    def wrapper(session: sessions.Session, *args, **kwargs):
        session.install("poetry")
        session = PoetryNoxSession(session)
        return session_logic(session, *args, **kwargs)

    return wrapper


@nox_session()
@using_poetry
def pytest(session: PoetryNoxSession) -> None:
    try:
        line_count([TEST_PATH, MAIN_PACKAGE_PATH])
    except:
        traceback.print_exc()

    session.poetry("update")
    session.run(
        "python",
        "-W",
        "ignore::DeprecationWarning",
        "-m",
        "pytest",
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
        *session.posargs,
        TEST_PATH,
    )


@nox_session()
@using_poetry
def sphinx(session: PoetryNoxSession) -> None:
    session.poetry("update")
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
        pathify(DOCUMENTATION_DIR, TECHNICAL_DIR, "index.rst"),
        pathify(DOCUMENTATION_DIR, TECHNICAL_DIR),
    )
    session.run("python", "-m", "sphinx.cmd.build", DOCUMENTATION_DIR, ARTIFACT_DIR, "-b", "html")


@nox_session()
@using_poetry
def bandit(session: PoetryNoxSession) -> None:
    session.install("bandit")
    pkg = MAIN_PACKAGE.split(".")[0]
    session.run("bandit", pkg, "-r")


def _black(session, *args, **kwargs):
    session.install("black")
    session.run("python", BLACK_SHIM_PATH, *BLACK_PATHS, *args, **kwargs)


@nox_session()
def format_fix(session: PoetryNoxSession) -> None:
    _black(session)


@nox_session()
def format_check(session: PoetryNoxSession) -> None:
    _black(session, "--check")


@nox_session()
def pypitest(session: sessions.Session):
    if os.getenv("CI", False):
        print("Testing published ref can be installed as a package.")
        url = os.getenv("CI_PROJECT_URL", REPOSITORY)
        ref = os.getenv("CI_COMMIT_REF_NAME", "master")
        slug = f"git+{url}.git@{ref}"
        session.install("-vvv", slug)
    else:
        print("Testing local repository can be installed as a package.")
        session.install("-vvv", "--isolated", ".")

    session.run("python", "-c", f"import {MAIN_PACKAGE}; print({MAIN_PACKAGE}.__version__)")

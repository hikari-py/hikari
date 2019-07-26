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
import os
import shutil
import typing

from nox import session as nox_session
from nox import sessions


def pathify(arg, *args, root=False):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)) if not root else "/", arg, *args))


# Configuration stuff we probably might move around eventually.
MAIN_PACKAGE = "hikari"
TEST_PACKAGE = "hikari_tests"
COVERAGE_RC = ".coveragerc"
ARTIFACT_DIR = "public"
DOCUMENTATION_DIR = "docs"
CI_SCRIPT_DIR = "tasks"
SPHINX_OPTS = "-WTvvn"
ISORT_ARGS = ["--jobs", "8", "--trailing-comma", "--case-sensitive", "--verbose"]
BLACK_PATHS = [MAIN_PACKAGE, TEST_PACKAGE, pathify(DOCUMENTATION_DIR, "conf.py"), __file__]
BLACK_SHIM_PATH = pathify(CI_SCRIPT_DIR, "black.py")
GENDOC_PATH = pathify(CI_SCRIPT_DIR, "gendoc.py")
PYLINTRC = ".pylintrc"
PYTHON_TARGETS = ["python3.7", "python3.8", "python3.9"]
OFFLINE_FLAG = "NOX_OFFLINE"

existing_python_installs = [target for target in PYTHON_TARGETS if shutil.which(target)]
has_dumped_venv_info = False

if not existing_python_installs:
    raise OSError(f"Cannot find a valid Python interpreter from the list of {PYTHON_TARGETS} to run.")


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

    def run_if_online(self, *args, **kwargs) -> None:
        if not os.getenv(OFFLINE_FLAG, False):
            self.run(*args, **kwargs)

    def install(self, *args, **kwargs):
        self.run("pip", "install", *args, **kwargs)

    def install_requirements(self, *requirements_file_path_parts) -> None:
        requirements_file = pathify(*requirements_file_path_parts)
        with open(requirements_file, encoding="utf-8") as fp:
            for line in fp.read().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    self.install(line)


def using_poetry(session_logic):
    """Ensure that the decorated function always initializes itself using poetry first."""

    @functools.wraps(session_logic)
    def wrapper(session: sessions.Session, *args, **kwargs):
        session.install("poetry")
        session = PoetryNoxSession(session)
        session.poetry("config", "settings.virtualenvs.create", "false", silent=False)
        if not os.getenv(OFFLINE_FLAG, False) and not has_dumped_venv_info:
            session.poetry("update", "-v", silent=True)
            session.poetry("show", "-v")
        return session_logic(session, *args, **kwargs)

    return wrapper


@nox_session(python=existing_python_installs, reuse_venv=True)
@using_poetry
def pytest(session: PoetryNoxSession) -> None:
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
        f"annotate:{pathify(ARTIFACT_DIR, session.python)}-coverage-annotated",
        "--cov-report",
        f"html:{pathify(ARTIFACT_DIR, session.python)}-coverage-html",
        "--cov-branch",
        "-ra",
        "--showlocals",
        "--testdox",
        *session.posargs,
        TEST_PACKAGE,
    )


@nox_session(reuse_venv=True)
@using_poetry
def pylint(session: PoetryNoxSession):
    session.run("pylint", MAIN_PACKAGE, f"--rcfile={PYLINTRC}")


@nox_session(reuse_venv=True)
@using_poetry
def sphinx(session: PoetryNoxSession) -> None:
    session.install_requirements(DOCUMENTATION_DIR, "requirements.txt")
    session.env["SPHINXOPTS"] = SPHINX_OPTS
    session.run(
        "python",
        GENDOC_PATH,
        MAIN_PACKAGE,
        pathify(DOCUMENTATION_DIR, "_templates", "gendoc"),
        pathify(DOCUMENTATION_DIR, "index.rst"),
        pathify(DOCUMENTATION_DIR),
    )
    session.run("sphinx-build", DOCUMENTATION_DIR, ARTIFACT_DIR, "-b", "html")


@nox_session(reuse_venv=True)
@using_poetry
def bandit(session: PoetryNoxSession) -> None:
    session.install("bandit")
    session.run("bandit", MAIN_PACKAGE, "-r")
    session.run("bandit", MAIN_PACKAGE, "-r", "-f", "html", "-o", pathify(ARTIFACT_DIR, "bandit.html"))


def _black(session, *args, **kwargs):
    session.install("black")
    session.run("python", BLACK_SHIM_PATH, *BLACK_PATHS, *args, **kwargs)


def _isort(session, *args, **kwargs):
    session.install("isort")
    session.run("python", "-m", "isort", *args, **kwargs)


@nox_session(reuse_venv=True)
@using_poetry
def format_fix(session: PoetryNoxSession) -> None:
    _isort(session, *ISORT_ARGS, "--apply", "--atomic")
    _black(session)


@nox_session(reuse_venv=True)
@using_poetry
def format_check(session: PoetryNoxSession) -> None:
    _isort(session, *ISORT_ARGS, "--check")
    _black(session, "--check")

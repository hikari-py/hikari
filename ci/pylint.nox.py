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
"""Pylint support."""
import os
import traceback
from ci import config
from ci import nox

FLAGS = ["pylint", config.MAIN_PACKAGE, "--rcfile", config.PYLINT_INI]
PYLINT_VER = "pylint==2.5.2"
PYLINT_JUNIT_VER = "pylint-junit==0.2.0"
SUCCESS_CODES = list(range(0, 256))


@nox.session(default=True, reuse_venv=True)
def pylint(session: nox.Session) -> None:
    """Run pylint against the code base and report any code smells or issues."""

    session.install("-r", config.REQUIREMENTS, "-r", config.DEV_REQUIREMENTS, PYLINT_VER)

    try:
        print("generating plaintext report")
        session.run(*FLAGS, *session.posargs, success_codes=SUCCESS_CODES)
    except Exception:
        traceback.print_exc()


@nox.session(default=False, reuse_venv=True)
def pylint_junit(session: nox.Session) -> None:
    """Runs `pylint', but produces JUnit reports instead of textual ones."""

    session.install(
        "-r", config.REQUIREMENTS, "-r", config.DEV_REQUIREMENTS, PYLINT_VER, PYLINT_JUNIT_VER,
    )

    try:
        print("generating plaintext report")
        if not os.path.exists(config.ARTIFACT_DIRECTORY):
            os.mkdir(config.ARTIFACT_DIRECTORY)

        with open(config.PYLINT_JUNIT_OUTPUT_PATH, "w+") as fp:
            session.run(
                *FLAGS,
                "--output-format=pylint_junit.JUnitReporter",
                *session.posargs,
                success_codes=SUCCESS_CODES,
                stdout=fp,
            )
    except Exception:
        traceback.print_exc()

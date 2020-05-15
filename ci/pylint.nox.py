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
from concurrent import futures

from ci import config
from ci import nox

FLAGS = [
    "pylint",
    config.MAIN_PACKAGE,
    "--rcfile",
    config.PYLINT_INI
]

SUCCESS_CODES = list(range(0, 256))

JUNIT_FLAG = "--and-junit-report"
HTML_FLAG = "--and-html-report"
NON_PYLINT_FLAGS = [JUNIT_FLAG, HTML_FLAG]


@nox.session(default=True, reuse_venv=True)
def pylint(session: nox.Session) -> None:
    """Run pylint against the code base and report any code smells or issues."""

    tasks = [pylint_text]
    cpus_per_task = max(1, (os.cpu_count() or 1) // len(tasks))

    if JUNIT_FLAG in session.posargs:
        tasks.append(pylint_junit)

    if HTML_FLAG in session.posargs:
        tasks.append(pylint_html)

    session.install(
        "-r", config.REQUIREMENTS, "-r", config.DEV_REQUIREMENTS,
    )

    if "--jobs" not in session.posargs:
        print("Using", cpus_per_task, "workers per task")
        extra_flags = ["--jobs", str(cpus_per_task)]
    else:
        extra_flags = []

    # Mapping concurrently halves the execution time (unless you have less than
    # two CPU cores, but who cares).
    with futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        pool.map(lambda f: f(session, *extra_flags), tasks)


def pylint_text(session: nox.Session, *extra_flags) -> None:
    try:
        print("generating plaintext report")
        args = [arg for arg in session.posargs if arg not in NON_PYLINT_FLAGS]
        session.run(*FLAGS, *args, *extra_flags, success_codes=SUCCESS_CODES)
    except Exception:
        traceback.print_exc()


def pylint_junit(session: nox.Session, *extra_flags) -> None:
    try:
        print("generating junit report")
        if not os.path.exists(config.ARTIFACT_DIRECTORY):
            os.mkdir(config.ARTIFACT_DIRECTORY)
        args = [arg for arg in session.posargs if arg not in NON_PYLINT_FLAGS]
        with open(config.PYLINT_JUNIT_OUTPUT_PATH, "w") as fp:
            session.run(
                *FLAGS,
                "--output-format",
                "pylint_junit.JUnitReporter",
                *args,
                *extra_flags,
                stdout=fp,
                success_codes=SUCCESS_CODES
            )
    except Exception:
        traceback.print_exc()


def pylint_html(session: nox.Session, *extra_flags) -> None:
    try:
        print("generating json report")
        args = [arg for arg in session.posargs if arg not in NON_PYLINT_FLAGS]
        if not os.path.exists(config.ARTIFACT_DIRECTORY):
            os.mkdir(config.ARTIFACT_DIRECTORY)
        with open(config.PYLINT_JSON_OUTPUT_PATH, "w") as fp:
            session.run(*FLAGS, "--output-format", "json", *args, *extra_flags, stdout=fp, success_codes=SUCCESS_CODES)
        print("producing html report in", config.PYTEST_HTML_OUTPUT_PATH)
        session.run("pylint-json2html", "-o", config.PYLINT_HTML_OUTPUT_PATH, config.PYLINT_JSON_OUTPUT_PATH)
        print("artifacts:")
        print(os.listdir(config.ARTIFACT_DIRECTORY))
    except Exception:
        traceback.print_exc()

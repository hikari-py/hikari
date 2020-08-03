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
"""Py.test integration."""
import os
import shutil

from ci import config
from ci import nox

FLAGS = [
    "-c",
    config.PYTEST_INI,
    "-r",
    "a",
    "--full-trace",
    "--cov",
    config.MAIN_PACKAGE,
    "--cov-config",
    config.COVERAGE_INI,
    "--cov-report",
    "term",
    "--cov-report",
    f"html:{config.COVERAGE_HTML_PATH}",
    "--cov-branch",
    "--junitxml",
    config.COVERAGE_JUNIT_PATH,
    "--force-testdox",
    "--showlocals",
    config.TEST_PACKAGE,
]


@nox.session(reuse_venv=True)
def pytest(session: nox.Session) -> None:
    """Run unit tests and measure code coverage."""
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    shutil.rmtree(".coverage", ignore_errors=True)
    session.run("python", "-m", "pytest", *FLAGS, *session.posargs)


@nox.session(reuse_venv=True)
def pytest_profile(session: nox.Session) -> None:
    """Run pytest with a profiler enabled to debug test times."""
    session.posargs.append("--profile")
    session.posargs.append("--durations=0")
    pytest(session)
    print("Generating profiling reports in `prof' directory.")

    import pstats

    with open("prof/results-by-tottime.txt", "w") as fp:
        stats = pstats.Stats("prof/combined.prof", stream=fp)
        stats.sort_stats("tottime")
        stats.print_stats()

    with open("prof/results-by-ncalls.txt", "w") as fp:
        stats = pstats.Stats("prof/combined.prof", stream=fp)
        stats.sort_stats("calls")
        stats.print_stats()


@nox.session(reuse_venv=True)
def mutpy(session: nox.Session) -> None:
    """Run mutation tests on a given module and test suite.

    This randomly mutates the module undergoing testing to make it invalid
    by altering parts of the code. It will then attempt to run the tests to
    verify that they now fail.
    """
    if len(session.posargs) < 2:
        print("Please provide two arguments:")
        print("  1. the module to mutate")
        print("  2. the test suite for this module")
        print()
        print("e.g.     nox -s mutpy -- foo test_foo")
        exit(1)

    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    session.run(
        "mut.py",
        "--target",
        session.posargs[0],
        "--unit-test",
        session.posargs[1],
        "--runner",
        "pytest",
        "-c",
        "--disable-operator",
        "SCI",  # SCI is buggy for some reason.
        *session.posargs[2:],
    )


@nox.session(reuse_venv=True)
def coalesce_coverage(session: nox.Session) -> None:
    """Combine coverage stats from several CI jobs."""
    session.install("coverage")

    coverage_files = []
    for file in os.listdir(config.ARTIFACT_DIRECTORY):
        if file.endswith(".coverage"):
            coverage_files.append(os.path.join(config.ARTIFACT_DIRECTORY, file))
    print("files for coverage:", coverage_files)

    session.run("coverage", "combine", f"--rcfile={config.COVERAGE_INI}", *coverage_files)
    session.run("coverage", "report", "-i", "-m", f"--rcfile={config.COVERAGE_INI}")

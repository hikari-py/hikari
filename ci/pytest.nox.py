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


@nox.session(default=True, reuse_venv=True)
def pytest(session: nox.Session) -> None:
    """Run unit tests and measure code coverage."""
    session.install(
        "-r", config.REQUIREMENTS, "-r", config.DEV_REQUIREMENTS,
    )
    shutil.rmtree(".coverage", ignore_errors=True)
    session.run("python", "-m", "pytest", *FLAGS)


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

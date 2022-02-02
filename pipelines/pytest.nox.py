# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Pytest integration."""
import os

from pipelines import config
from pipelines import nox

RUN_FLAGS = [
    "-c",
    config.PYPROJECT_TOML,
    "--showlocals",
]
COVERAGE_FLAGS = [
    "--cov",
    config.MAIN_PACKAGE,
    "--cov-config",
    config.PYPROJECT_TOML,
    "--cov-report",
    "term",
    "--cov-report",
    f"html:{config.COVERAGE_HTML_PATH}",
    "--cov-report",
    "xml",
    "--cov-branch",
]


@nox.session(reuse_venv=True)
def pytest(session: nox.Session) -> None:
    """Run unit tests and measure code coverage.

    Coverage can be disabled with the `--skip-coverage` flag.
    """
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    _pytest(session)


@nox.session(reuse_venv=True)
def pytest_all_features(session: nox.Session) -> None:
    """Run unit tests and measure code coverage, using speedup modules.

    Coverage can be disabled with the `--skip-coverage` flag.
    """
    session.install(
        "-r",
        "requirements.txt",
        "-r",
        "server-requirements.txt",
        "-r",
        "speedup-requirements.txt",
        "-r",
        "dev-requirements.txt",
    )
    _pytest(session, "-OO")


def _pytest(session: nox.Session, *py_flags: str) -> None:
    if "--skip-coverage" in session.posargs:
        session.posargs.remove("--skip-coverage")
        flags = RUN_FLAGS
    else:
        try:
            os.remove(".coverage")
        except:
            # Ignore errors
            pass

        flags = [*RUN_FLAGS, *COVERAGE_FLAGS]

    session.run("python", *py_flags, "-m", "pytest", *flags, *session.posargs, config.TEST_PACKAGE)

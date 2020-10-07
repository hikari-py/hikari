# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import shutil

from pipelines import config
from pipelines import nox

FLAGS = [
    "-c",
    config.PYTEST_INI,
    "--cov",
    config.MAIN_PACKAGE,
    "--cov-config",
    config.COVERAGE_INI,
    "--cov-report",
    "term",
    "--cov-report",
    f"html:{config.COVERAGE_HTML_PATH}",
    "--cov-report",
    "xml",
    "--cov-branch",
    "--showlocals",
]


@nox.session(reuse_venv=True)
def pytest(session: nox.Session) -> None:
    """Run unit tests and measure code coverage."""
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    _pytest(session)


@nox.session(reuse_venv=True)
def pytest_speedups(session: nox.Session) -> None:
    """Run unit tests and measure code coverage, using speedup modules."""
    session.install("-r", "requirements.txt", "-r", "speedup-requirements.txt", "-r", "dev-requirements.txt")
    _pytest(session, "-OO")


def _pytest(session: nox.Session, *py_flags: str) -> None:
    shutil.rmtree(".coverage", ignore_errors=True)
    session.run("python", *py_flags, "-m", "pytest", *FLAGS, *session.posargs, config.TEST_PACKAGE)


@nox.inherit_environment_vars
@nox.session(reuse_venv=False)
def coveralls(session: nox.Session) -> None:
    """Run coveralls. This has little effect outside TravisCI."""
    session.install("-U", "python-coveralls")
    session.run("coveralls")

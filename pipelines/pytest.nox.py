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

from __future__ import annotations

import typing

from pipelines import config
from pipelines import nox

RUN_FLAGS = ["-c", config.PYPROJECT_TOML, "--showlocals"]
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
]


@nox.session()
def pytest(session: nox.Session) -> None:
    """Run unit tests and measure code coverage.

    Coverage can be disabled with the `--skip-coverage` flag.
    """
    _pytest(session)


@nox.session()
def pytest_all_features(session: nox.Session) -> None:
    """Run unit tests and measure code coverage, using speedup modules.

    Coverage can be disabled with the `--skip-coverage` flag.
    """
    _pytest(session, extras_install=["speedups", "server"], python_flags=("-OO",))


def _pytest(
    session: nox.Session, *, extras_install: typing.Sequence[str] = (), python_flags: typing.Sequence[str] = ()
) -> None:
    nox.sync(session, self=True, extras=extras_install, groups=["pytest"])

    flags = RUN_FLAGS

    if "--coverage" in session.posargs:
        session.posargs.remove("--coverage")
        flags.extend(COVERAGE_FLAGS)

    session.run("python", *python_flags, "-m", "pytest", *flags, *session.posargs, config.TEST_PACKAGE)

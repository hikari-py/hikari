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
import typing

from pipelines import config
from pipelines import nox


@nox.session()
def flake8(session: nox.Session) -> None:
    """Run code linting, SAST, and analysis."""
    _flake8(session)


@nox.session()
def flake8_html(session: nox.Session) -> None:
    """Run code linting, SAST, and analysis and generate an HTML report."""
    _flake8(session, ("--format=html", f"--htmldir={config.FLAKE8_REPORT}"))


def _flake8(session: nox.Session, extra_args: typing.Sequence[str] = ()) -> None:
    session.install("-r", "requirements.txt", *nox.dev_requirements("flake8"), *nox.dev_requirements("formatting"))
    session.run(
        "flake8",
        "--statistics",
        "--show-source",
        "--benchmark",
        "--tee",
        *extra_args,
        config.MAIN_PACKAGE,
        config.TEST_PACKAGE,
        config.EXAMPLE_SCRIPTS,
    )

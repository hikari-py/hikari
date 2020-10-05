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

from pipelines import config
from pipelines import nox

STUBGEN_GENERATE = ["hikari/__init__.py", "hikari/events/__init__.py"]


@nox.session(reuse_venv=True)
def mypy(session: nox.Session) -> None:
    """Perform static type analysis on Python source code."""
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")

    _generate_stubs(session)

    session.run("mypy", "-p", config.MAIN_PACKAGE, "--config", config.MYPY_INI)
    session.run("mypy", "-p", config.EXAMPLE_SCRIPTS, "--config", config.MYPY_INI)


@nox.session(reuse_venv=True)
def generate_stubs(session: nox.Session) -> None:
    """Generate the stubs for the package."""
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    _generate_stubs(session)


def _generate_stubs(session: nox.Session) -> None:
    session.run("stubgen", *STUBGEN_GENERATE, "-o", ".", "--include-private", "--no-import")

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
"""Pyright integrations."""

from pipelines import config
from pipelines import nox


@nox.session()
def pyright(session: nox.Session) -> None:
    """Perform static type analysis on Python source code using pyright.

    At the time of writing this, this pipeline will not run successfully,
    as hikari does not have 100% compatibility with pyright just yet. This
    exists to make it easier to test and eventually reach that 100% compatibility.
    """
    session.install(
        "-r",
        "requirements.txt",
        "-r",
        "speedup-requirements.txt",
        "-r",
        "server-requirements.txt",
        *nox.dev_requirements("pyright"),
    )
    session.run("pyright")


@nox.session()
def verify_types(session: nox.Session) -> None:
    """Verify the "type completeness" of types exported by the library using Pyright."""
    session.install(".", *nox.dev_requirements("pyright"))
    session.run("pyright", "--verifytypes", config.MAIN_PACKAGE, "--ignoreexternal")

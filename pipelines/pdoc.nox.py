# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Website pages generation."""
import os
import shutil
import typing

from pipelines import config
from pipelines import nox


@nox.session(reuse_venv=True)
def pdoc(session: nox.Session) -> None:
    """Generate documentation using pdoc."""
    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    path = os.path.join(config.ARTIFACT_DIRECTORY, "docs")
    _pdoc(session, ("-o", path))

    # Replace index.html with hikari.html
    os.replace(os.path.join(path, "hikari.html"), os.path.join(path, "index.html"))


@nox.session(reuse_venv=True)
def pdoc_int(session: nox.Session) -> None:
    """Run pdoc in interactive mode."""
    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    _pdoc(session, ("-n",))


def _pdoc(session: nox.Session, extra_arguments: typing.Sequence[str] = ()):
    # We need to install everything so that typehints link correctly
    session.install(
        "-r",
        "requirements.txt",
        "-r",
        "dev-requirements.txt",
        "-r",
        "server-requirements.txt",
        "-r",
        "speedup-requirements.txt",
    )

    session.run(
        "python",
        "docs/patched_pdoc.py",
        "--docformat",
        "numpy",
        "-t",
        "./docs",
        "./hikari",
        *extra_arguments,
        *session.posargs,
    )

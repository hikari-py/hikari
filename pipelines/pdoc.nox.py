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


def copy_from_in(src: str, dest: str) -> None:
    for parent, _, files in os.walk(src):
        sub_parent = os.path.relpath(parent, src)

        for file in files:
            sub_src = os.path.join(parent, file)
            sub_dest = os.path.normpath(os.path.join(dest, sub_parent, file))
            print(sub_src, "->", sub_dest)
            shutil.copy(sub_src, sub_dest)


def _pdoc(session: nox.Session, extra_arguments: typing.Sequence[str] = ()):
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")

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


@nox.session(reuse_venv=True)
def pdoc(session: nox.Session) -> None:
    """Generate documentation using pdoc."""
    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    _pdoc(session, ("-o", os.path.join(config.ARTIFACT_DIRECTORY, "docs")))


@nox.session(reuse_venv=True)
def pdoc_int(session: nox.Session) -> None:
    """Run pdoc in interactive mode."""
    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    _pdoc(session, ("-n",))

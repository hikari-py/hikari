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
"""Additional utilities for Nox."""
import os
import shutil

from pipelines import nox

DIRECTORIES_TO_DELETE = [
    ".nox",
    "build",
    "dist",
    "hikari.egg-info",
    "public",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
]

FILES_TO_DELETE = [".coverage", "package-lock.json"]

TO_DELETE = [(shutil.rmtree, DIRECTORIES_TO_DELETE), (os.remove, FILES_TO_DELETE)]


@nox.session(venv_backend="none")
def purge(session: nox.Session) -> None:
    """Delete any nox-generated files."""
    for func, trash_list in TO_DELETE:
        for trash in trash_list:
            try:
                func(trash)
            except Exception as exc:
                session.warn(f"[ FAIL ] Failed to remove {trash!r}: {exc!s}")
            else:
                session.log(f"[  OK  ] Removed {trash!r}")

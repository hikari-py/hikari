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
"""Additional utilities for Nox."""
import os
import shutil

from pipelines import nox

TRASH = [
    ".nox",
    "build",
    "dist",
    "hikari.egg-info",
    "public",
    ".coverage",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "package-lock.json",
]


@nox.session(reuse_venv=False)
def purge(_: nox.Session) -> None:
    """Delete any nox-generated files."""
    for trash in TRASH:
        print("Removing", trash)
        try:
            os.remove(trash)
        except:
            # Ignore errors
            pass

        shutil.rmtree(trash, ignore_errors=True)

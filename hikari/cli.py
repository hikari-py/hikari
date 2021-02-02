# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Provides the `python -m hikari` and `hikari` commands to the shell."""
from __future__ import annotations

import inspect
import os
import platform
import sys

try:
    import git  # type: ignore[import]
except ImportError:
    # No git module = git not installed
    git = None

from hikari import _about


def main() -> None:
    """Print package info and exit."""
    sourcefile = inspect.getsourcefile(_about)
    assert isinstance(sourcefile, str)

    path = os.path.abspath(os.path.dirname(sourcefile))
    sha1 = _about.__git_sha1__[:8]
    version = _about.__version__
    py_impl = platform.python_implementation()
    py_ver = platform.python_version()
    py_compiler = platform.python_compiler()

    # Provide a more helpful commit information if available
    if sha1.casefold() == "head" and git:
        try:
            repo = git.Repo()
            sha1 = str(repo.head.commit)[:8]
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            # Repo not available
            pass

    sys.stderr.write(f"hikari ({version}) [{sha1}]\n")
    sys.stderr.write(f"located at {path}\n")
    sys.stderr.write(f"{py_impl} {py_ver} {py_compiler}\n")
    sys.stderr.write(" ".join(frag.strip() for frag in platform.uname() if frag and frag.strip()) + "\n")

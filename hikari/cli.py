# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Provides the `python -m hikari` and `hikari` commands to the shell."""
from __future__ import annotations

import importlib.metadata
import pathlib
import platform
import sys
import typing

from hikari import _about


def _get_entry_points(group: str) -> typing.Optional[typing.Sequence[importlib.metadata.EntryPoint]]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)

    return importlib.metadata.entry_points().get(group)


def main() -> None:
    """Print package info and exit."""
    path = pathlib.Path(_about.__file__).parent
    sha1 = _about.__git_sha1__[:8]
    version = _about.__version__
    py_impl = platform.python_implementation()
    py_ver = platform.python_version()
    py_compiler = platform.python_compiler()

    sys.stderr.write(f"hikari ({version}) [{sha1}]\n")
    sys.stderr.write(f"located at {path}\n")
    sys.stderr.write(f"{py_impl} {py_ver} {py_compiler}\n")
    sys.stderr.write(" ".join(frag.strip() for frag in platform.uname() if frag and frag.strip()) + "\n")

    if extensions := _get_entry_points("hikari"):
        sys.stderr.write("\nInstalled extensions:\n")

        for extension in extensions:
            name = extension.name
            version = importlib.metadata.version(name)
            module = extension.load()
            module_path = pathlib.Path(module.__file__).parent

            sys.stderr.write(f"  {name} ({version}) [{module_path}]\n")

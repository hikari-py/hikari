# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Provides the `python -m hikari` and `hikari` commands to the shell."""
from __future__ import annotations

import inspect
import os
import platform
import sys
import typing

from hikari import _about


def main() -> None:
    """Print package info and exit."""
    # noinspection PyTypeChecker
    sourcefile = typing.cast(str, inspect.getsourcefile(_about))
    path: typing.Final[str] = os.path.abspath(os.path.dirname(sourcefile))
    version: typing.Final[str] = _about.__version__
    py_impl: typing.Final[str] = platform.python_implementation()
    py_ver: typing.Final[str] = platform.python_version()
    py_compiler: typing.Final[str] = platform.python_compiler()
    sys.stderr.write(f"hikari v{version} (installed in {path}) ({py_impl} {py_ver} {py_compiler})\n")

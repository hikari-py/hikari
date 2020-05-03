#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Provides a command-line entry point that shows the library version and then exits."""

from __future__ import annotations

import inspect
import os
import platform
import click

from hikari import _about


@click.command()
def main():
    """Show the application version, then exit."""
    version = _about.__version__
    path = os.path.abspath(os.path.dirname(inspect.getsourcefile(_about)))
    py_impl = platform.python_implementation()
    py_ver = platform.python_version()
    py_compiler = platform.python_compiler()
    print(f"hikari v{version} (installed in {path}) ({py_impl} {py_ver} {py_compiler})")


main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
"""
Utilities for discovering the user agent and library information.
"""
import platform


def library_version() -> str:
    """
    Creates a string that is representative of the version of this library.

    Example:
        hikari.core 2019.12.12.1399
    """
    from hikari.core import __version__

    return f"hikari.core {__version__}"


def python_version() -> str:
    """
    Creates a comprehensive string representative of this version of Python, along with the compiler used, if present.

    Examples:
        CPython3.7:
            CPython 3.7.3 GCC 8.2.1 20181127
        PyPy3.6:
            PyPy 3.6.1 release-pypy3.6-v7.1.1
    """
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_branch(),
        platform.python_compiler(),
    ]
    return " ".join(a for a in attrs if a.strip())


def system_type() -> str:
    """
    Get a string representing the system type.
    """
    # Might change this eventually to be more detailed, who knows.
    return platform.system()


def user_agent() -> str:
    """
    Creates a User-Agent header string acceptable by the API.

    Examples:
        CPython3.7:
            DiscordBot (https://gitlab.com/nekokatt/hikari.core, 0.0.1a) CPython 3.7.3 GCC 8.2.1 20181127 Linux
        PyPy3.6:
            DiscordBot (https://gitlab.com/nekokatt/hikari.core, 0.0.1a) PyPy 3.6.1 release-pypy3.6-v7.1.1 Linux
    """
    from hikari.core import __version__, __url__

    system = system_type()
    python = python_version()
    return f"DiscordBot ({__url__}, {__version__}) {python} {system}"


__all__ = ("library_version", "python_version", "system_type", "user_agent")

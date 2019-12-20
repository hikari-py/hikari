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
"""
User agent information that is calculated on startup and stored for the lifetime of the application.
"""
import platform

from hikari.internal_utilities import cache


@cache.cached_function()
def library_version() -> str:
    from hikari import __version__

    return f"hikari {__version__}"


@cache.cached_function()
def python_version() -> str:
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_branch(),
        platform.python_compiler(),
    ]
    return " ".join(a for a in attrs if a.strip())


@cache.cached_function()
def system_type() -> str:
    # Might change this eventually to be more detailed, who knows.
    return platform.system()


@cache.cached_function()
def user_agent() -> str:
    from hikari import __version__, __url__

    system = system_type()
    python = python_version()
    return f"DiscordBot ({__url__}, {__version__}) {python} {system}"


__all__ = ("library_version", "python_version", "system_type", "user_agent")

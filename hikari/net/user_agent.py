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
"""Anonymous system information that we have to provide to Discord when using their API.

This information contains details such as the version of Python you are using, and
the version of this library, the OS you are making requests from, etc.

This information is provided to enable Discord to detect that you are using a
valid bot and not attempting to abuse the API.
"""
__all__ = ["library_version", "python_version", "system_type", "user_agent"]

import platform

from hikari.internal_utilities import cache


@cache.cached_function()
def library_version() -> str:
    """The version of the library being used.

    Returns
    -------
    :obj:`str`
        A string representing the version of this library.

    Example
    -------
    .. code-block:: python
    
        >>> from hikari.net import user_agent
        >>> print(user_agent.library_version())
        hikari 0.0.71
    """
    from hikari._about import __version__

    return f"hikari {__version__}"


@cache.cached_function()
def python_version() -> str:
    """The python version being used.

    Returns
    -------
    :obj:`str`
        A string representing the version of this release of Python.

    Example
    -------
    .. code-block:: python

        >>> from hikari.net import user_agent
        >>> print(user_agent.python_version())
        CPython 3.8.1 GCC 9.2.0
    """
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_branch(),
        platform.python_compiler(),
    ]
    return " ".join(a.strip() for a in attrs if a.strip())


@cache.cached_function()
def system_type() -> str:
    """The operating system being used.

    Returns
    -------
    :obj:`str`
        A string representing the system being used.

    Example
    -------
    .. code-block:: python

        >>> from hikari.net import user_agent
        >>> print(user_agent.system_type())
        Linux-5.4.15-2-MANJARO-x86_64-with-glibc2.2.5
    """
    # Might change this eventually to be more detailed, who knows.
    return platform.platform()


@cache.cached_function()
def user_agent() -> str:
    """The user agent of the bot

    Returns
    -------
    :obj:`str`
        The string to use for the library ``User-Agent`` HTTP header that is required
        to be sent with every HTTP request.

    Example
    -------
    .. code-block:: python

        >>> from hikari.net import user_agent
        >>> print(user_agent.user_agent())
        DiscordBot (https://gitlab.com/nekokatt/hikari, 0.0.71) CPython 3.8.1 GCC 9.2.0 Linux
    """
    from hikari._about import __version__, __url__

    system = system_type()
    python = python_version()
    return f"DiscordBot ({__url__}, {__version__}) {python} {system}"

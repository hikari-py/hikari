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

from __future__ import annotations

__all__: typing.List[str] = ["UserAgent"]

import aiohttp
import typing

from hikari.utilities import klass


class UserAgent(klass.Singleton):
    """Platform version info.

    !!! note
        This is a singleton.
    """

    library_version: typing.Final[str]
    """The version of the library.

    Examples
    --------
    `"hikari 1.0.1"`
    """

    platform_version: typing.Final[str]
    """The platform version.

    Examples
    --------
    `"CPython 3.8.2 GCC 9.2.0"`
    """

    system_type: typing.Final[str]
    """The operating system type.

    Examples
    --------
    `"Linux 64bit"`
    """

    user_agent: typing.Final[str]
    """The Hikari-specific user-agent to use in HTTP connections to Discord.

    Examples
    --------
    `"DiscordBot (https://gitlab.com/nekokatt/hikari; 1.0.1) Nekokatt Aiohttp/3.6.2 CPython/3.8.2 Linux 64bit"`
    """

    def __init__(self) -> None:
        from hikari._about import __author__, __url__, __version__
        from platform import python_implementation, python_version, python_branch, python_compiler, architecture, system

        self.library_version = f"hikari {__version__}"
        self.platform_version = self._join_strip(
            python_implementation(), python_version(), python_branch(), python_compiler()
        )
        self.system_type = " ".join((system(), architecture()[0]))
        self.user_agent = (
            f"DiscordBot ({__url__}; {__version__}) {__author__} "
            f"Aiohttp/{aiohttp.__version__} "
            f"{python_implementation()}/{python_version()} "
            f"{self.system_type}"
        )

        logger = klass.get_logger(self)
        logger.debug("Using User-Agent %r", self.user_agent)

    @staticmethod
    def _join_strip(*args: str) -> str:
        return " ".join((arg.strip() for arg in args if arg.strip()))

    @property
    def websocket_triplet(self) -> typing.Dict[str, str]:
        """Generate a dict representing device and library info.

        This is the object to send to Discord representing device info when
        IDENTIFYing with the gateway in the format `typing.Dict[str, str]`
        """
        return {
            "$os": self.system_type,
            "$browser": self.library_version,
            "$device": self.platform_version,
        }

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
__all__ = ["UserAgent"]

import typing

from hikari.internal import meta


class UserAgent(metaclass=meta.SingletonMeta):
    """Platform version info.

    Notes
    -----
    This is a singleton.
    """

    #: The version of the library.
    #:
    #: Example
    #: -------
    #: ``"hikari 1.0.1"``
    #:
    #: :type: :obj:`typing.Final` [ :obj:`str` ]
    library_version: typing.Final[str]

    #: The platform version.
    #:
    #: Example
    #: -------
    #: ``"CPython 3.8.2 GCC 9.2.0"``
    #:
    #: :type: :obj:`typing.Final` [ :obj:`str` ]
    platform_version: typing.Final[str]

    #: The operating system type.
    #:
    #: Example
    #: -------
    #: ``"Linux-5.4.15-2-MANJARO-x86_64-with-glibc2.2.5"``
    #:
    #: :type: :obj:`typing.Final` [ :obj:`str` ]
    system_type: typing.Final[str]

    #: The Hikari-specific user-agent to use in HTTP connections to Discord.
    #:
    #: Example
    #: -------
    #: ``"DiscordBot (https://gitlab.com/nekokatt/hikari; 1.0.1; Nekokatt) CPython 3.8.2 GCC 9.2.0 Linux"``
    #:
    #: :type: :obj:`typing.Final` [ :obj:`str` ]
    user_agent: typing.Final[str]

    def __init__(self):
        from hikari._about import __author__, __url__, __version__
        from platform import python_implementation, python_version, python_branch, python_compiler, platform

        self.library_version = f"hikari {__version__}"
        self.platform_version = self._join_strip(
            python_implementation(), python_version(), python_branch(), python_compiler()
        )
        self.system_type = platform()
        self.user_agent = f"DiscordBot ({__url__}; {__version__}; {__author__}) {python_version()} {self.system_type}"

        def __attr__(_):
            raise TypeError("cannot change attributes once set")

        self.__delattr__ = __attr__
        self.__setattr__ = __attr__

    @staticmethod
    def _join_strip(*args):
        return " ".join((arg.strip() for arg in args if arg.strip()))

    # Ignore docstring not starting in an imperative mood
    @property
    def websocket_triplet(self) -> typing.Dict[str, str]:  # noqa: D401
        """A dict representing device and library info.

        Returns
        -------
        :obj:`typing.Dict` [ :obj:`str`, :obj:`str` ]
            The object to send to Discord representing device info when
            IDENTIFYing with the gateway.
        """
        return {
            "$os": self.system_type,
            "$browser": self.library_version,
            "$device": self.platform_version,
        }

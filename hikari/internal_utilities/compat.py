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
Functions and classes aimed to maintain compatibility between supported Python versions.

These are mostly delegates and crude backports to enable code elsewhere to be platform
and interpreter agnostic (for the most part).

These members are subject to change at any time without prior warning.
"""
import asyncio as _asyncio
import sys as _sys
import typing as _typing


class _FakeModule:
    def __init__(self, cascade_to):
        self.__cascade_to = cascade_to

    def __getattr__(self, item):
        return getattr(self.__cascade_to, item)

    def __setattr__(self, key, value):
        self.__dict__[key] = value


asyncio = _FakeModule(_asyncio)
typing = _FakeModule(_typing)

################################################################################
# asyncio.create_task                                                          #
#     introduced in Python 3.7.0, but only allows a string as the name of the  #
#     task from Python 3.8.0. Before 3.8.0, tasks were not able to have names. #
################################################################################
if _sys.version_info >= (3, 8):
    asyncio.create_task = _asyncio.create_task
else:
    asyncio.create_task = lambda coro, *, name=None: _asyncio.create_task(coro)


##################################
# typing.Protocol                #
#     introduced in Python 3.8.0 #
##################################
if _sys.version_info >= (3, 8):
    typing.Protocol = _typing.Protocol
else:
    typing._ProtocolT = _typing.TypeVar("_ProtocolT")

    class Protocol(_typing.Generic[typing._ProtocolT]):
        pass

    typing.Protocol = Protocol
    del Protocol

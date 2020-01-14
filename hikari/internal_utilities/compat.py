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
import signal as _signal
import sys as _sys
import types as _types
import typing as _typing


class asyncio:
    ################################################################################
    # asyncio.create_task                                                          #
    #     introduced in Python 3.7.0, but only allows a string as the name of the  #
    #     task from Python 3.8.0. Before 3.8.0, tasks were not able to have names. #
    ################################################################################
    #: Prevents erroring on Python 3.7 if we specify a task name. This is just ignored if
    #: unsupported.
    if _sys.version_info < (3, 8):

        @staticmethod
        def create_task(coro, *, name=None):
            return _asyncio.create_task(coro)

    else:

        @staticmethod
        def create_task(coro, *, name=None):
            return _asyncio.create_task(coro, name=name)


class signal:
    ##################################
    # signal.strsignal               #
    #     introduced in Python 3.8.0 #
    ##################################
    #: Python3.8 introduced strsignal to get a signal name. This just works around Python3.7 lacking
    #: this feature.
    if _sys.version_info < (3, 8):

        @staticmethod
        def strsignal(signalnum):
            try:
                return _signal.Signals(  # ("signals.Signals" is only in Python3.7) pylint: disable=no-member
                    signalnum
                ).name
            except ValueError:
                return None

    else:

        @staticmethod
        def strsignal(signalnum):
            return _signal.strsignal(signalnum)


class typing:
    ##################################
    # typing.Protocol                #
    #     introduced in Python 3.8.0 #
    ##################################
    #: typing.Protocol is new to Python 3.8. On Python3.7, a cheap generic with a typevar
    #: is made to copy the syntax. This may or may not screw up static type checkers, so
    #: be wary!
    if _sys.version_info < (3, 8):
        _ProtocolT = _typing.TypeVar("_ProtocolT")
        Protocol = _types.new_class("Protocol", (_typing.Generic[_ProtocolT],))
    else:
        Protocol = _typing.Protocol

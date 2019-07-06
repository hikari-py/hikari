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
Contextlib compatibility methods.

This namespace contains the entirety of the :mod:`contextlib` module. Any members documented below are assumed to
*override* the original implementation if it exists for your target platform implementation and Python version.
"""
import abc

# noinspection PyUnresolvedReferences
from contextlib import *


# Not implemented in Python3.6, this one will provide aenter and aexit by default if unspecified.
class AbstractAsyncContextManager(abc.ABC):
    """An abstract base class for asynchronous context managers."""
    __slots__ = ()

    async def __aenter__(self):
        return self

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        ...

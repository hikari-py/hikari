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
Asyncio compatibility methods.

This namespace contains the entirety of the :mod:`asyncio` module. Any members documented below are assumed to
*override* the original implementation if it exists for your target platform implementation and Python version.
"""
import asyncio as _asyncio

# noinspection PyUnresolvedReferences
from asyncio import *

#: Not supported before Python3.8, so just no-op if not available.
set_task_name = getattr(_asyncio.tasks, "_set_task_name", lambda task, name: None)

#: Not in the same namespace in Python3.7.
current_task = getattr(_asyncio, "current_task", _asyncio.tasks.Task.current_task)

#: Not implemented in spec for Python3.6, so we assume it doesn't exist and fall back to
#: :func:`asyncio.get_event_loop` if required.
get_running_loop = getattr(_asyncio, "get_running_loop", _asyncio.get_event_loop)

#: Not implemented in Python3.6. Does not support names in 3.7, so use :attr:`set_task_name` instead to set that.
create_task = getattr(_asyncio, "create_task", lambda coro: get_running_loop().create_task(coro))

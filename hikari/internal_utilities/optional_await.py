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
Optional await decorator for async functions so that they can be called without await
"""
import functools
import asyncio

from hikari.internal_utilities import compat


def optional_await(description: str = None, shield: bool = False):
    def decorator(coro_fn):
        @functools.wraps(coro_fn)
        def wrapper(*args, **kwargs):
            coro = asyncio.shield(coro_fn(*args, **kwargs)) if shield else coro_fn(*args, **kwargs)
            return compat.asyncio.create_task(coro, name=description)

        return wrapper

    return decorator

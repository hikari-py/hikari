#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
import asyncio

import pytest

from hikari.internal import more_typing


# noinspection PyProtocol
@pytest.mark.asyncio
class TestFuture:
    async def test_is_instance(self, event_loop):
        assert isinstance(event_loop.create_future(), more_typing.Future)

        async def nil():
            pass

        assert isinstance(asyncio.create_task(nil()), more_typing.Future)


# noinspection PyProtocol
@pytest.mark.asyncio
class TestTask:
    async def test_is_instance(self, event_loop):
        async def nil():
            pass

        assert isinstance(asyncio.create_task(nil()), more_typing.Task)

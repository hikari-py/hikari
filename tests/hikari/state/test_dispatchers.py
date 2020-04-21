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
import mock
import pytest

from hikari import events
from hikari.state import dispatchers


class PartialDispatcherImpl(dispatchers.EventDispatcher):
    close = NotImplemented
    add_listener = mock.MagicMock(wraps=lambda _, f, **__: f)
    remove_listener = NotImplemented
    wait_for = NotImplemented
    dispatch_event = NotImplemented


class SomeEvent(events.HikariEvent):
    ...


@pytest.fixture
def dispatcher():
    return PartialDispatcherImpl()


class TestEventDispatcher:
    def test_on_with_explicit_type_returns_decorated_function(self, dispatcher):
        async def handler(event):
            ...

        assert dispatcher.on(SomeEvent)(handler) is handler

    def test_on_with_type_hint_returns_decorated_function(self, dispatcher):
        async def handler(event: SomeEvent):
            ...

        assert dispatcher.on()(handler) is handler

    def test_on_with_explicit_type_registers_decorated_function(self, dispatcher):
        async def handler(event):
            ...

        dispatcher.on(SomeEvent)(handler)

        dispatcher.add_listener.assert_called_once_with(SomeEvent, handler, _stack_level=3)

    def test_on_with_explicit_type_registers_decorated_function(self, dispatcher):
        async def handler(event):
            ...

        dispatcher.on(SomeEvent)(handler)

        dispatcher.add_listener.assert_called_once_with(SomeEvent, handler, _stack_level=3)

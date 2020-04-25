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
from tests.hikari import _helpers


class SomeEvent(events.HikariEvent):
    ...


@pytest.fixture
def dispatcher():
    class PartialDispatcherImpl(dispatchers.EventDispatcher):
        close = NotImplemented
        add_listener = mock.MagicMock(wraps=lambda _, f, **__: f)
        remove_listener = NotImplemented
        wait_for = NotImplemented
        dispatch_event = NotImplemented

    return PartialDispatcherImpl()


class TestEventDispatcher:
    def test_on_for_function_with_explicit_type_returns_decorated_function(self, dispatcher):
        async def handler(event):
            ...

        assert dispatcher.on(SomeEvent)(handler) is handler

    def test_on_for_function_with_type_hint_returns_decorated_function(self, dispatcher):
        async def handler(event: SomeEvent):
            ...

        assert dispatcher.on()(handler) is handler

    def test_on_for_function_with_explicit_type_registers_decorated_function(self, dispatcher):
        async def handler(event):
            ...

        dispatcher.on(SomeEvent)(handler)

        dispatcher.add_listener.assert_called_once_with(SomeEvent, handler, _stack_level=3)

    def test_on_for_function_with_type_hint_registers_decorated_function(self, dispatcher):
        async def handler(event: SomeEvent):
            ...

        dispatcher.on()(handler)

        dispatcher.add_listener.assert_called_once_with(SomeEvent, handler, _stack_level=3)

    @_helpers.assert_raises(type_=AttributeError)
    def test_on_for_function_without_type_hint_and_without_explicit_type_raises_AttributeError(self, dispatcher):
        async def handler(event):
            ...

        dispatcher.on()(handler)

    @_helpers.assert_raises(type_=TypeError)
    def test_on_for_function_with_no_args_raises_TypeError(self, dispatcher):
        async def handler():
            ...

        dispatcher.on()(handler)

    @_helpers.assert_raises(type_=TypeError)
    def test_on_for_function_with_too_many_args_raises_TypeError(self, dispatcher):
        async def handler(foo: SomeEvent, bar):
            ...

        dispatcher.on()(handler)

    def test_on_for_method_with_explicit_type_returns_decorated_method(self, dispatcher):
        class Class:
            async def handler(self, event):
                ...

        inst = Class()

        handler = inst.handler
        assert dispatcher.on(SomeEvent)(handler) is handler

    def test_on_for_method_with_type_hint_returns_decorated_method(self, dispatcher):
        class Class:
            async def handler(self, event: SomeEvent):
                ...

        inst = Class()
        handler = inst.handler

        assert dispatcher.on()(handler) is handler

    def test_on_for_method_with_explicit_type_registers_decorated_method(self, dispatcher):
        class Class:
            async def handler(self, event):
                ...

        inst = Class()

        dispatcher.on(SomeEvent)(inst.handler)

        dispatcher.add_listener.assert_called_once_with(SomeEvent, inst.handler, _stack_level=3)

    def test_on_for_method_with_type_hint_registers_decorated_method(self, dispatcher):
        class Class:
            async def handler(self, event: SomeEvent):
                ...

        inst = Class()

        dispatcher.on()(inst.handler)

        dispatcher.add_listener.assert_called_once_with(SomeEvent, inst.handler, _stack_level=3)

    @_helpers.assert_raises(type_=AttributeError)
    def test_on_for_method_without_type_hint_and_without_explicit_type_raises_AttributeError(self, dispatcher):
        class Class:
            async def handler(self, event):
                ...

        inst = Class()

        dispatcher.on()(inst.handler)

    @_helpers.assert_raises(type_=TypeError)
    def test_on_for_method_with_no_args_raises_TypeError(self, dispatcher):
        class Class:
            async def handler(self):
                ...

        inst = Class()

        dispatcher.on()(inst.handler)

    @_helpers.assert_raises(type_=TypeError)
    def test_on_for_method_with_too_many_args_raises_TypeError(self, dispatcher):
        class Class:
            async def handler(self, event: SomeEvent, foo: int):
                ...

        inst = Class()

        dispatcher.on()(inst.handler)

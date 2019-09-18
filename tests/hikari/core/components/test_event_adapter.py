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

import asynctest
import pytest

from hikari.core.components import event_adapter


class Impl(event_adapter.EventAdapter):
    async def handle_something(self, gateway, payload):
        pass


@pytest.fixture
def event_adapter_impl():
    return Impl()


@pytest.fixture
def gateway():
    return asynctest.MagicMock()


@pytest.fixture()
def payload():
    return {}


@pytest.mark.asyncio
async def test_that_consume_raw_event_consumes_a_named_coroutine_if_it_exists(event_adapter_impl, gateway, payload):
    event_adapter_impl.handle_something = asynctest.CoroutineMock(wraps=event_adapter_impl.handle_something)
    await event_adapter_impl.consume_raw_event(gateway, "SOMETHING", payload)
    event_adapter_impl.handle_something.assert_called_with(gateway, payload)


@pytest.mark.asyncio
async def test_that_consume_raw_event_calls_handle_unrecognised_event_hook_on_invalid_event(event_adapter_impl, gateway, payload):
    event_adapter_impl.handle_unrecognised_event = asynctest.CoroutineMock(wraps=event_adapter_impl.handle_unrecognised_event)
    await event_adapter_impl.consume_raw_event(gateway, "SOMETHING_ELSE", payload)
    event_adapter_impl.handle_unrecognised_event.assert_called_with(gateway, "SOMETHING_ELSE", payload)


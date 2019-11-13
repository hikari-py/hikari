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
import logging
from unittest import mock

import asynctest
import pytest

from hikari import state_registry
from hikari.core import event_adapter_impl
from hikari.net import gateway as _gateway
from tests.hikari import _helpers


@pytest.fixture()
def logger_impl():
    return mock.MagicMock(spec_set=logging.Logger)


@pytest.fixture()
def state_registry_impl():
    return asynctest.MagicMock(spec_set=state_registry.StateRegistry)


@pytest.fixture()
def dispatch_impl():
    return mock.MagicMock(spec_set=lambda name, *args: None)


@pytest.fixture()
def gateway_impl():
    return mock.MagicMock(spec_set=_gateway.GatewayClient)


@pytest.fixture()
def adapter_impl(state_registry_impl, dispatch_impl, logger_impl):
    instance = _helpers.unslot_class(event_adapter_impl.EventAdapterImpl)(state_registry_impl, dispatch_impl)
    instance.logger = logger_impl
    return instance


# noinspection PyProtectedMember
@pytest.mark.state
class TestStateRegistryImpl:
    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_first_time_adds_to_ignored_events_set(
        self, adapter_impl, gateway_impl
    ):
        adapter_impl._ignored_events.clear()
        assert not adapter_impl._ignored_events, "ignored events were not empty at the start!"

        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        assert "try_to_do_something" in adapter_impl._ignored_events

    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_first_time_logs_warning(
        self, adapter_impl, gateway_impl
    ):
        adapter_impl._ignored_events.clear()
        assert not adapter_impl._ignored_events, "ignored events were not empty at the start!"

        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        adapter_impl.logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_second_time_does_not_log_anything(
        self, adapter_impl, gateway_impl
    ):
        adapter_impl._ignored_events = {"try_to_do_something"}

        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        assert "try_to_do_something" in adapter_impl._ignored_events
        adapter_impl.logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_invokes_raw_dispatch(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        dispatch_impl.assert_called_with("raw_try_to_do_something", ...)

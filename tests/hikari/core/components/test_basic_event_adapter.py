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
from unittest import mock

import asynctest
import pytest

from hikari.core.components import basic_event_adapter
from hikari.core.net import gateway as _gateway


@pytest.mark.asyncio
async def test_unrecognised_events_only_get_warned_once(event_adapter, dispatch, gateway):
    adapter = basic_event_adapter.BasicEventAdapter(asynctest.MagicMock(), asynctest.MagicMock())
    adapter.logger.warning = mock.MagicMock()

    await adapter.handle_unrecognised_event(asynctest.MagicMock(), "no_idea", {})
    assert adapter.logger.warning.call_args[0][1] == "no_idea"

    adapter.logger.warning.reset_mock()

    await adapter.handle_unrecognised_event(asynctest.MagicMock(), "no_idea", {})
    assert adapter.logger.warning.call_count == 0


@pytest.fixture
def gateway():
    return mock.MagicMock(spec_set=_gateway.GatewayClient)


@pytest.fixture
def state_registry():
    return mock.MagicMock()


@pytest.fixture
def dispatch():
    return mock.MagicMock()


@pytest.fixture
def event_adapter(state_registry, dispatch):
    return basic_event_adapter.BasicEventAdapter(state_registry, dispatch)


@pytest.mark.asyncio
async def test_handle_disconnect(event_adapter, dispatch, gateway):
    await event_adapter.handle_disconnect(gateway, {"code": 123, "reason": "server on fire"})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.DISCONNECT, gateway, 123, "server on fire")


@pytest.mark.asyncio
async def test_handle_hello(event_adapter, dispatch, gateway):
    await event_adapter.handle_hello(gateway, {})

    dispatch.assert_called_with(basic_event_adapter.BasicEvent.CONNECT, gateway)


@pytest.mark.asyncio
async def test_handle_invalid_session(event_adapter, dispatch, gateway):
    await event_adapter.handle_invalid_session(gateway, False)

    dispatch.assert_called_with(basic_event_adapter.BasicEvent.INVALID_SESSION, gateway, False)


@pytest.mark.asyncio
async def test_handle_request_to_reconnect(event_adapter, dispatch, gateway):
    await event_adapter.handle_request_to_reconnect(gateway, {})

    dispatch.assert_called_with(basic_event_adapter.BasicEvent.REQUEST_TO_RECONNECT, gateway)


@pytest.mark.asyncio
async def test_handle_resumed(event_adapter, dispatch, gateway):
    await event_adapter.handle_resumed(gateway, {})

    dispatch.assert_called_with(basic_event_adapter.BasicEvent.RESUME, gateway)


@pytest.mark.asyncio
async def test_handle_channel_create_when_dm(event_adapter, dispatch, gateway, state_registry):
    channel = mock.MagicMock()
    state_registry.parse_channel = mock.MagicMock(return_value=channel)
    channel.is_dm = True
    await event_adapter.handle_channel_create(gateway, {})
    state_registry.parse_channel.assert_called_with({})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.DM_CHANNEL_CREATE, channel)


@pytest.mark.asyncio
async def test_handle_channel_create_when_valid_guild(event_adapter, dispatch, gateway, state_registry):
    channel = mock.MagicMock()
    state_registry.parse_channel = mock.MagicMock(return_value=channel)
    channel.is_dm = False
    channel.guild = mock.MagicMock()
    await event_adapter.handle_channel_create(gateway, {})
    state_registry.parse_channel.assert_called_with({})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_CHANNEL_CREATE, channel)


@pytest.mark.asyncio
async def test_handle_channel_create_when_invalid_guild(event_adapter, dispatch, gateway, state_registry):
    channel = mock.MagicMock()
    state_registry.parse_channel = mock.MagicMock(return_value=channel)
    channel.is_dm = False
    channel.guild = None
    await event_adapter.handle_channel_create(gateway, {})
    dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_channel_update_when_existing_guild_channel(event_adapter, dispatch, gateway, state_registry):
    payload = {"id": "1234"}
    old_channel = mock.MagicMock()
    new_channel = mock.MagicMock()
    new_channel.is_dm = False
    state_registry.get_guild_channel_by_id = mock.MagicMock(return_value=old_channel)
    state_registry.get_dm_channel_by_id = mock.MagicMock(return_value=None)
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)

    await event_adapter.handle_channel_update(gateway, payload)
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_CHANNEL_UPDATE, old_channel, new_channel)


@pytest.mark.asyncio
async def test_handle_channel_update_when_existing_dm_channel(event_adapter, dispatch, gateway, state_registry):
    payload = {"id": "1234"}
    old_channel = mock.MagicMock()
    new_channel = mock.MagicMock()
    new_channel.is_dm = True
    state_registry.get_guild_channel_by_id = mock.MagicMock(return_value=None)
    state_registry.get_dm_channel_by_id = mock.MagicMock(return_value=old_channel)
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)

    await event_adapter.handle_channel_update(gateway, payload)
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.DM_CHANNEL_UPDATE, old_channel, new_channel)


@pytest.mark.asyncio
async def test_handle_channel_update_when_no_channel_cached(event_adapter, dispatch, gateway, state_registry):
    payload = {"id": "1234"}
    no_channel = None
    new_channel = mock.MagicMock()
    new_channel.is_dm = True
    state_registry.get_guild_channel_by_id = mock.MagicMock(return_value=no_channel)
    state_registry.get_dm_channel_by_id = mock.MagicMock(return_value=no_channel)
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)

    await event_adapter.handle_channel_update(gateway, payload)
    dispatch.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_delete_when_dm_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_delete_when_guild_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_delete_when_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_pins_update_in_dm_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_pins_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_pins_update_in_guild_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_pins_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_pins_update_in_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_pins_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_channel_pins_when_channel_not_cached(event_adapter, dispatch, gateway):
    await event_adapter.handle_channel_pins_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_create_when_guild_was_unavailable_and_now_is_unavailable(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_create_when_guild_was_unavailable_and_is_now_available(event_adapter, dispatch, gateway):
    # GUILD AVAILABLE
    await event_adapter.handle_guild_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_create_when_guild_was_not_cached_and_is_now_available(event_adapter, dispatch, gateway):
    # GUILD JOIN
    await event_adapter.handle_guild_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_update_when_guild_changes(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_update_when_available_guild_becomes_unavailable(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_update_when_guild_was_not_previously_cached(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_delete_when_unavailable_unspecified(event_adapter, dispatch, gateway, state_registry):
    # guild leave
    await event_adapter.handle_guild_delete(gateway, {})
    dispatch.assert_called_with()
    state_registry.delete_guild.assert_called_with()


# TODO: continue writing test names, then writing tests, then continue implementing the code being tested.


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_delete_when_unavailable_specified(event_adapter, dispatch, gateway):
    # guild unavailable
    await event_adapter.handle_guild_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_ban_add_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_ban_add(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_ban_add_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_ban_add(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_ban_remove(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_ban_remove(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_emojis_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_emojis_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_integrations_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_integrations_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_add(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_add(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_remove(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_remove(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_members_chunk(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_members_chunk(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_create(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_create(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_delete(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_delete(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_create(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_create(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete_bulk(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete_bulk(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_reaction_add(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_reaction_add(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_reaction_remove(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_reaction_remove(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_reaction_remove_all(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_reaction_remove_all(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_presence_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_presence_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_typing_start(event_adapter, dispatch, gateway):
    await event_adapter.handle_typing_start(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_user_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_user_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_voice_state_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_voice_state_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_voice_server_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_voice_server_update(gateway, {})

    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_webhooks_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_webhooks_update(gateway, {})

    dispatch.assert_called_with()

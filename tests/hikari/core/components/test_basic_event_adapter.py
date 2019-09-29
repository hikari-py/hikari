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
import datetime
from unittest import mock

import asynctest
import pytest

from hikari.core.components import basic_event_adapter
from hikari.core.components import basic_state_registry
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
    return mock.MagicMock(spec_set=basic_state_registry.BasicStateRegistry)


@pytest.fixture
def dispatch():
    return mock.MagicMock(spec_set=lambda *args: None)


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
    state_registry.get_channel_by_id = mock.MagicMock(return_value=old_channel)
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)

    await event_adapter.handle_channel_update(gateway, payload)
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_CHANNEL_UPDATE, old_channel, new_channel)


@pytest.mark.asyncio
async def test_handle_channel_update_when_existing_dm_channel(event_adapter, dispatch, gateway, state_registry):
    payload = {"id": "1234"}
    old_channel = mock.MagicMock()
    new_channel = mock.MagicMock()
    new_channel.is_dm = True
    state_registry.get_channel_by_id = mock.MagicMock(return_value=old_channel)
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)

    await event_adapter.handle_channel_update(gateway, payload)
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.DM_CHANNEL_UPDATE, old_channel, new_channel)


@pytest.mark.asyncio
async def test_handle_channel_update_when_no_channel_cached(event_adapter, dispatch, gateway, state_registry):
    payload = {"id": "1234"}
    no_channel = None
    new_channel = mock.MagicMock()
    new_channel.is_dm = True
    state_registry.get_channel_by_id = mock.MagicMock(return_value=no_channel)
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)

    await event_adapter.handle_channel_update(gateway, payload)
    state_registry.parse_channel.assert_not_called()
    dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_channel_delete_when_dm_channel(event_adapter, dispatch, gateway, state_registry):
    existing_channel = mock.MagicMock()
    new_channel = mock.MagicMock()
    new_channel.id = 1234
    new_channel.is_dm = True
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)
    state_registry.delete_channel = mock.MagicMock(return_value=new_channel)
    state_registry.get_channel_by_id = mock.MagicMock(return_value=existing_channel)
    await event_adapter.handle_channel_delete(gateway, {"id": "1234"})
    state_registry.get_channel_by_id.assert_called_with(1234)
    state_registry.parse_channel.assert_called_with({"id": "1234"})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.DM_CHANNEL_DELETE, new_channel)
    state_registry.delete_channel.assert_called_with(1234)


@pytest.mark.asyncio
async def test_handle_channel_delete_when_guild_channel(event_adapter, dispatch, gateway, state_registry):
    existing_channel = mock.MagicMock()
    new_channel = mock.MagicMock()
    new_channel.id = 1234
    new_channel.is_dm = False
    new_channel.guild = mock.MagicMock()
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)
    state_registry.delete_channel = mock.MagicMock(return_value=new_channel)
    state_registry.get_channel_by_id = mock.MagicMock(return_value=existing_channel)
    await event_adapter.handle_channel_delete(gateway, {"id": "1234", "guild_id": "5432"})
    state_registry.get_channel_by_id.assert_called_with(1234)
    state_registry.parse_channel.assert_called_with({"id": "1234", "guild_id": "5432"})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_CHANNEL_DELETE, new_channel)
    state_registry.delete_channel.assert_called_with(1234)


@pytest.mark.asyncio
async def test_handle_channel_delete_when_invalid_guild(event_adapter, dispatch, gateway, state_registry):
    new_channel = mock.MagicMock()
    new_channel.id = 1234
    new_channel.is_dm = False
    new_channel.guild = None
    state_registry.parse_channel = mock.MagicMock(return_value=new_channel)
    state_registry.delete_channel = mock.MagicMock(return_value=KeyError)
    state_registry.get_channel_by_id = mock.MagicMock(return_value=None)
    await event_adapter.handle_channel_delete(gateway, {"id": "1234", "guild": "6969"})
    state_registry.parse_channel.assert_not_called()
    dispatch.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("is_dm", [True, False])
@pytest.mark.parametrize(
    ["last_pin_timestamp", "expected_args"],
    [
        (
            "2019-10-10T05:22:33.023456+00:00",
            (datetime.datetime(2019, 10, 10, 5, 22, 33, 23456, tzinfo=datetime.timezone.utc),),
        ),
        (None, ()),
    ],
)
async def test_handle_guild_pins_update_when_valid_channel(
    event_adapter, dispatch, gateway, state_registry, is_dm, last_pin_timestamp, expected_args
):
    payload = {"channel_id": "12345", "guild_id": None if is_dm else "54321", "last_pin_timestamp": last_pin_timestamp}

    existing_channel = mock.MagicMock()
    existing_channel.is_dm = is_dm

    if is_dm:
        if last_pin_timestamp is not None:
            event = basic_event_adapter.BasicEvent.DM_CHANNEL_PIN_ADDED
        else:
            event = basic_event_adapter.BasicEvent.DM_CHANNEL_PIN_REMOVED
    else:
        if last_pin_timestamp is not None:
            event = basic_event_adapter.BasicEvent.GUILD_CHANNEL_PIN_ADDED
        else:
            event = basic_event_adapter.BasicEvent.GUILD_CHANNEL_PIN_REMOVED

    state_registry.get_channel_by_id = mock.MagicMock(return_value=existing_channel)
    await event_adapter.handle_channel_pins_update(gateway, payload)
    state_registry.get_channel_by_id.assert_called_with(12345)
    dispatch.assert_called_with(event, *expected_args)


@pytest.mark.asyncio
async def test_handle_guild_pins_update_when_invalid_channel(event_adapter, dispatch, gateway, state_registry):
    payload = {"channel_id": "12345", "guild_id": "54321", "last_pin_timestamp": None}

    state_registry.get_channel_by_id = mock.MagicMock(return_value=None)
    await event_adapter.handle_channel_pins_update(gateway, payload)
    state_registry.get_channel_by_id.assert_called_with(12345)
    dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_guild_create_unavailable_when_not_cached(event_adapter, dispatch, gateway, state_registry):
    state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
    guild = mock.MagicMock()
    state_registry.parse_guild = mock.MagicMock(return_value=guild)
    await event_adapter.handle_guild_create(gateway, {"id": "1234", "unavailable": True})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_CREATE, guild)


@pytest.mark.asyncio
async def test_handle_guild_create_available(event_adapter, dispatch, gateway, state_registry):
    old_guild = mock.MagicMock()
    old_guild.unavailable = True
    state_registry.get_guild_by_id = mock.MagicMock(return_value=old_guild)
    new_guild = mock.MagicMock()
    state_registry.parse_guild = mock.MagicMock(return_value=new_guild)
    await event_adapter.handle_guild_create(gateway, {"id": "1234", "unavailable": False})
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_AVAILABLE, new_guild)


@pytest.mark.asyncio
async def test_handle_guild_update(event_adapter, dispatch, gateway, state_registry):
    new_guild = mock.MagicMock()
    old_guild = mock.MagicMock()
    old_guild.clone = mock.MagicMock(return_value=new_guild)
    state_registry.get_guild_by_id = mock.MagicMock(return_value=old_guild)
    state_registry.parse_guild = mock.MagicMock(return_value=old_guild)

    await event_adapter.handle_guild_update(
        gateway,
        {
            "id": "1234",
            "unavailable": False,
            # ...
        },
    )
    # This might seem counter intuitive, but our copy of the original guild gets discarded later and we just update
    # the existing copy.
    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_UPDATE, new_guild, old_guild)


@pytest.mark.asyncio
async def test_handle_guild_update_when_inconsistent_state(event_adapter, dispatch, gateway, state_registry):
    payload = {
        "id": "1234",
        "unavailable": False,
        # ...
    }
    state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
    new_guild = mock.MagicMock()
    state_registry.parse_guild = mock.MagicMock(return_value=new_guild)
    event_adapter.handle_guild_create = asynctest.CoroutineMock()
    await event_adapter.handle_guild_update(gateway, payload)
    event_adapter.handle_guild_create.assert_awaited_once_with(gateway, payload)


@pytest.mark.asyncio
async def test_handle_guild_delete_when_unavailable_and_guild_was_cached(
    event_adapter, dispatch, gateway, state_registry
):
    existing_guild = mock.MagicMock()
    existing_guild.unavailable = False
    state_registry.get_guild_by_id = mock.MagicMock(return_value=existing_guild)

    await event_adapter.handle_guild_delete(gateway, {"unavailable": True, "id": "123456"})

    state_registry.get_guild_by_id.assert_called_with(123456)

    # We just update the existing guild
    assert existing_guild.unavailable is True

    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_UNAVAILABLE, existing_guild)


@pytest.mark.asyncio
async def test_handle_guild_delete_when_unavailable_and_guild_was_not_cached(
    event_adapter, dispatch, gateway, state_registry
):
    state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
    event_adapter.handle_guild_create = asynctest.CoroutineMock()
    payload = {"unavailable": True, "id": "123456"}

    await event_adapter.handle_guild_delete(gateway, payload)

    state_registry.get_guild_by_id.assert_called_with(123456)
    event_adapter.handle_guild_create.assert_awaited_once_with(gateway, payload)


@pytest.mark.asyncio
async def test_handle_guild_delete_when_not_unavailable(event_adapter, dispatch, gateway, state_registry):
    new_guild = mock.MagicMock()
    new_guild.unavailable = False
    state_registry.parse_guild = mock.MagicMock(return_value=new_guild)

    await event_adapter.handle_guild_delete(gateway, {"id": "123456"})

    state_registry.parse_guild.assert_called_with({"id": "123456"})

    dispatch.assert_called_with(basic_event_adapter.BasicEvent.GUILD_LEAVE, new_guild)


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
async def test_handle_guild_ban_remove_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_ban_remove(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_ban_remove_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_ban_remove(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_emojis_update_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_emojis_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_emojis_update_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_emojis_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_integrations_update_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_integrations_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_integrations_update_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_integrations_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_add_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_add(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_add_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_add(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_update_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_update_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_update_on_uncached_member(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_remove_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_remove(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_remove_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_remove(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_member_remove_on_uncached_member(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_member_remove(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_members_chunk(event_adapter, dispatch, gateway):
    # TODO: implement this.
    raise NotImplementedError


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_create_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_create_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_update_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_update_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_update_on_unknown_role(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_delete_on_valid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_delete_on_invalid_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_guild_role_delete_on_unknown_role(event_adapter, dispatch, gateway):
    await event_adapter.handle_guild_role_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_create_in_known_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_create_in_unknown_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_create(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_update_on_cached_message(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_update_on_uncached_message(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_update_in_invalid_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete_on_cached_message(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete_on_uncached_message(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete_in_invalid_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete_bulk_in_valid_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete_bulk(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_delete_bulk_in_invalid_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_delete_bulk(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_message_reaction_add(event_adapter, dispatch, gateway):
    await event_adapter.handle_message_reaction_add(gateway, {})
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
async def test_handle_presence_update_on_known_member_in_known_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_presence_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_presence_update_on_unknown_member_in_known_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_presence_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_presence_update_on_known_member_in_unknown_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_presence_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_presence_update_on_unknown_member_in_unknown_guild(event_adapter, dispatch, gateway):
    await event_adapter.handle_presence_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_typing_start_on_valid_channel(event_adapter, dispatch, gateway):
    await event_adapter.handle_typing_start(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_typing_start_on_invalid_channel(event_adapter, dispatch, gateway):
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
    # TODO: implement
    await event_adapter.handle_voice_state_update(gateway, {})
    dispatch.assert_called_with()


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_voice_server_update(event_adapter, dispatch, gateway):
    # TODO: implement
    raise NotImplementedError


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_handle_webhooks_update(event_adapter, dispatch, gateway):
    await event_adapter.handle_webhooks_update(gateway, {})
    dispatch.assert_called_with()

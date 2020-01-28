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
import contextlib
import datetime
import inspect
import logging
from unittest import mock

import pytest

from hikari.net import gateway as _gateway
from hikari.orm import fabric
from hikari.orm.gateway import base_chunker as _chunker
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.gateway import event_types
from hikari.orm.models import channels
from hikari.orm.models import emojis
from hikari.orm.models import guilds
from hikari.orm.models import members
from hikari.orm.models import messages
from hikari.orm.models import reactions
from hikari.orm.models import roles
from hikari.orm.models import users
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture()
def logger_impl():
    return mock.MagicMock(spec_set=logging.Logger)


@pytest.fixture()
def state_registry_impl():
    return mock.MagicMock(spec_set=base_registry.BaseRegistry)


@pytest.fixture()
def dispatch_impl():
    return mock.MagicMock(spec_set=lambda name, *args: None)


@pytest.fixture()
def gateway_impl():
    # noinspection PyTypeChecker
    gw: _gateway.GatewayClient = mock.MagicMock(spec_set=_gateway.GatewayClient)
    gw.shard_id = 123
    gw.shard_count = 456
    return gw


@pytest.fixture()
def chunker_impl():
    return mock.MagicMock(spec_set=_chunker.BaseChunker)


@pytest.fixture()
def fabric_impl(state_registry_impl, gateway_impl, chunker_impl):
    return fabric.Fabric(state_registry=state_registry_impl, gateways={None: gateway_impl}, chunker=chunker_impl)


@pytest.fixture()
def adapter_impl(fabric_impl, dispatch_impl, logger_impl):
    instance = _helpers.unslot_class(dispatching_event_adapter_impl.DispatchingEventAdapterImpl)(
        fabric_impl, dispatch_impl,
    )
    instance.logger = logger_impl
    instance._request_chunks_mode = dispatching_event_adapter_impl.AutoRequestChunksMode.NEVER
    return instance


@pytest.fixture()
def discord_ready_payload():
    return {
        # https://discordapp.com/developers/docs/topics/gateway#ready-ready-event-fields
        "v": 69,
        "_trace": ["potato.com", "tomato.net"],
        "session_id": "69420lmaolmao",
        "guilds": [{"id": "9182736455463", "unavailable": True}, {"id": "72819099110270", "unavailable": True}],
        "private_channels": [],  # always empty /shrug
        "user": {
            "id": "81624",
            "username": "Ben_Dover",
            "discriminator": 9921,
            "avatar": "a_d41d8cd98f00b204e9800998ecf8427e",
            "bot": bool("of course i am"),
            "mfa_enabled": True,
            "locale": "en_gb",
            "verified": False,
            "email": "chestylaroo@boing.biz",
            "flags": 69,
            "premimum_type": 0,
        },
    }


# noinspection PyProtectedMember
@pytest.mark.orm
class TestDispatchingEventAdapterImpl:
    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_first_time_does_nothing(self, adapter_impl, gateway_impl):
        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

    @pytest.mark.asyncio
    async def test_handle_disconnect_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        payload = {"code": 123, "reason": "test"}
        await adapter_impl.handle_disconnect(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.DISCONNECT, gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_connect_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_connect(gateway_impl, {})
        dispatch_impl.assert_called_with(event_types.EventType.CONNECT, gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_ready_dispatches_event(
        self, discord_ready_payload, adapter_impl, gateway_impl, dispatch_impl
    ):
        await adapter_impl.handle_ready(gateway_impl, discord_ready_payload)
        dispatch_impl.assert_called_with(event_types.EventType.READY, gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_ready_doesnt_chunk_when_no_guilds_in_payload(
        self, discord_ready_payload, adapter_impl, gateway_impl, chunker_impl, state_registry_impl,
    ):
        discord_ready_payload["guilds"] = []
        adapter_impl._request_chunks_mode = dispatching_event_adapter_impl.AutoRequestChunksMode.MEMBERS_AND_PRESENCES
        await adapter_impl.handle_ready(gateway_impl, discord_ready_payload)
        chunker_impl.load_members_for.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_ready_adds_application_user(
        self, discord_ready_payload, fabric_impl, adapter_impl, gateway_impl
    ):
        await adapter_impl.handle_ready(gateway_impl, discord_ready_payload)

        fabric_impl.state_registry.parse_application_user.assert_called_with(discord_ready_payload["user"])

    @pytest.mark.asyncio
    async def test_handle_invalid_session_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_invalid_session(gateway_impl, {})

        dispatch_impl.assert_called_with(event_types.EventType.INVALID_SESSION, gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_reconnect_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_reconnect(gateway_impl, ...)

        dispatch_impl.assert_called_with(event_types.EventType.RECONNECT, gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_resume_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_resumed(gateway_impl, ...)

        dispatch_impl.assert_called_with(event_types.EventType.RESUME, gateway_impl)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["handler_name", "raw_event_expected"],
        [
            ("handle_channel_create", event_types.EventType.RAW_CHANNEL_CREATE),
            ("handle_channel_update", event_types.EventType.RAW_CHANNEL_UPDATE),
            ("handle_channel_delete", event_types.EventType.RAW_CHANNEL_DELETE),
            ("handle_channel_pins_update", event_types.EventType.RAW_CHANNEL_PINS_UPDATE),
            ("handle_guild_create", event_types.EventType.RAW_GUILD_CREATE),
            ("handle_guild_update", event_types.EventType.RAW_GUILD_UPDATE),
            ("handle_guild_delete", event_types.EventType.RAW_GUILD_DELETE),
            ("handle_guild_ban_add", event_types.EventType.RAW_GUILD_BAN_ADD),
            ("handle_guild_ban_remove", event_types.EventType.RAW_GUILD_BAN_REMOVE),
            ("handle_guild_emojis_update", event_types.EventType.RAW_GUILD_EMOJIS_UPDATE),
            ("handle_guild_integrations_update", event_types.EventType.RAW_GUILD_INTEGRATIONS_UPDATE),
            ("handle_guild_member_add", event_types.EventType.RAW_GUILD_MEMBER_ADD),
            ("handle_guild_member_update", event_types.EventType.RAW_GUILD_MEMBER_UPDATE),
            ("handle_guild_member_remove", event_types.EventType.RAW_GUILD_MEMBER_REMOVE),
            ("handle_guild_members_chunk", event_types.EventType.RAW_GUILD_MEMBERS_CHUNK),
            ("handle_guild_role_create", event_types.EventType.RAW_GUILD_ROLE_CREATE),
            ("handle_guild_role_update", event_types.EventType.RAW_GUILD_ROLE_UPDATE),
            ("handle_guild_role_delete", event_types.EventType.RAW_GUILD_ROLE_DELETE),
            ("handle_message_create", event_types.EventType.RAW_MESSAGE_CREATE),
            ("handle_message_update", event_types.EventType.RAW_MESSAGE_UPDATE),
            ("handle_message_delete", event_types.EventType.RAW_MESSAGE_DELETE),
            ("handle_message_delete_bulk", event_types.EventType.RAW_MESSAGE_DELETE_BULK),
            ("handle_message_reaction_add", event_types.EventType.RAW_MESSAGE_REACTION_ADD),
            ("handle_message_reaction_remove", event_types.EventType.RAW_MESSAGE_REACTION_REMOVE),
            ("handle_message_reaction_remove_all", event_types.EventType.RAW_MESSAGE_REACTION_REMOVE_ALL),
            ("handle_presence_update", event_types.EventType.RAW_PRESENCE_UPDATE),
            ("handle_typing_start", event_types.EventType.RAW_TYPING_START),
            ("handle_user_update", event_types.EventType.RAW_USER_UPDATE),
            ("handle_message_reaction_remove", event_types.EventType.RAW_MESSAGE_REACTION_REMOVE),
            ("handle_voice_state_update", event_types.EventType.RAW_VOICE_STATE_UPDATE),
            ("handle_voice_server_update", event_types.EventType.RAW_VOICE_SERVER_UPDATE),
            ("handle_webhooks_update", event_types.EventType.RAW_WEBHOOKS_UPDATE),
        ],
    )
    async def test_raw_event_handler(self, gateway_impl, dispatch_impl, adapter_impl, handler_name, raw_event_expected):
        handler = getattr(adapter_impl, handler_name)
        assert inspect.ismethod(handler)

        payload = mock.MagicMock()

        # Being lazy, I just brute force this as it is the first thing that happens ever in any event, so meh.
        # Any exception raised afterwards can be ignored unless the assertion fails.
        with contextlib.suppress(Exception):
            await handler(gateway_impl, payload)

        assert len(dispatch_impl.call_args_list) > 0, f"dispatch did not get invoked for {handler_name}"
        args, kwargs = dispatch_impl.call_args_list[0]
        assert args == (
            raw_event_expected,
            payload,
        ), f"dispatch was not invoked with {raw_event_expected} first from {handler_name}"

    @pytest.mark.asyncio
    async def test_handle_channel_create_for_valid_guild_channel_dispatches_GUILD_CHANNEL_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": str(guild_obj.id)}

        await adapter_impl.handle_channel_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_CHANNEL_CREATE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_create_for_guild_channel_in_unknown_guild_does_not_dispatch(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123"}

        await adapter_impl.handle_channel_create(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_CHANNEL_CREATE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_create_for_dm_channel_dispatches_DM_CHANNEL_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, is_dm=True)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": None}

        await adapter_impl.handle_channel_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.DM_CHANNEL_CREATE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_create_parses_channel(self, adapter_impl, gateway_impl, fabric_impl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": str(guild_obj.id)}

        await adapter_impl.handle_channel_create(gateway_impl, payload)

        fabric_impl.state_registry.parse_channel.assert_called_with(payload, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_update_for_invalid_update_event_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.update_channel = mock.MagicMock(return_value=None)
        payload = {"id": "123"}
        await adapter_impl.handle_channel_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_CHANNEL_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_update_for_valid_dm_channel_update_dispatches_DM_CHANNEL_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj_before = _helpers.mock_model(channels.GroupDMChannel, id=123, is_dm=True, name="original")
        channel_obj_after = _helpers.mock_model(channels.GroupDMChannel, id=123, is_dm=True, name="updated")
        fabric_impl.state_registry.update_channel = mock.MagicMock(return_value=(channel_obj_before, channel_obj_after))
        payload = {"id": str(channel_obj_after.id), "type": channel_obj_after.is_dm}
        await adapter_impl.handle_channel_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.DM_CHANNEL_UPDATE, channel_obj_before, channel_obj_after)

    @pytest.mark.asyncio
    async def test_handle_channel_update_for_valid_guild_channel_update_dispatches_GUILD_CHANNEL_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj_before = _helpers.mock_model(channels.GuildTextChannel, id=123, is_dm=False, name="original")
        channel_obj_after = _helpers.mock_model(channels.GuildTextChannel, id=123, is_dm=False, name="updated")
        fabric_impl.state_registry.update_channel = mock.MagicMock(return_value=(channel_obj_before, channel_obj_after))
        payload = {"id": str(channel_obj_after.id), "type": channel_obj_after.is_dm}

        await adapter_impl.handle_channel_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(
            event_types.EventType.GUILD_CHANNEL_UPDATE, channel_obj_before, channel_obj_after
        )

    @pytest.mark.asyncio
    async def test_handle_channel_update_invokes_update_channel(self, adapter_impl, gateway_impl, fabric_impl):
        payload = {"id": "123", "type": True}

        await adapter_impl.handle_channel_update(gateway_impl, payload)

        fabric_impl.state_registry.update_channel.assert_called_with(payload)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_for_invalid_update_event_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123"}

        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_CHANNEL_DELETE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_parses_channel(self, adapter_impl, gateway_impl, fabric_impl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": str(guild_obj.id)}

        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        fabric_impl.state_registry.parse_channel.assert_called_with(payload, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_for_dm_channel_dispatches_DM_CHANNEL_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, id=123, is_dm=True)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": None}

        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.DM_CHANNEL_DELETE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_for_guild_channel_dispatches_GUILD_CHANNEL_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, id=123, is_dm=False)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": str(guild_obj.id)}

        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_CHANNEL_DELETE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_unknown_channel_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=None)
        payload = {"channel_id": "123", "type": False, "last_pin_timestamp": None}

        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_CHANNEL_PINS_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_known_channel_invokes_set_last_pinned_timestamp_on_state(
        self, adapter_impl, gateway_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, id=123, is_dm=False)
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {"channel_id": "123", "type": False, "last_pin_timestamp": timestamp.isoformat()}

        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        fabric_impl.state_registry.set_last_pinned_timestamp.assert_called_with(channel_obj, timestamp)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_adding_pin_to_guild_channel_invokes_GUILD_CHANNEL_PIN_ADDED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, id=123, is_dm=False)
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {
            "channel_id": str(channel_obj.id),
            "type": channel_obj.is_dm,
            "last_pin_timestamp": timestamp.isoformat(),
        }

        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_CHANNEL_PIN_ADDED, timestamp)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_adding_pin_to_dm_channel_invokes_DM_CHANNEL_PIN_ADDED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, id=123, is_dm=True)
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {
            "channel_id": str(channel_obj.id),
            "type": channel_obj.is_dm,
            "last_pin_timestamp": timestamp.isoformat(),
        }

        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.DM_CHANNEL_PIN_ADDED, timestamp)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_removing_pin_from_guild_channel_invokes_GUILD_CHANNEL_PIN_REMOVED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, id=123, is_dm=False)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {"channel_id": str(channel_obj.id), "type": channel_obj.is_dm, "last_pin_timestamp": None}

        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_CHANNEL_PIN_REMOVED)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_removing_pin_from_dm_channel_invokes_DM_CHANNEL_PIN_REMOVED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, id=123, is_dm=True)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {"channel_id": str(channel_obj.id), "type": channel_obj.is_dm, "last_pin_timestamp": None}

        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.DM_CHANNEL_PIN_REMOVED)

    @pytest.mark.asyncio
    async def test_handle_guild_create_parses_guild(self, adapter_impl, gateway_impl, fabric_impl):
        payload = {"id": "123", "unavailable": False}

        await adapter_impl.handle_guild_create(gateway_impl, payload)

        fabric_impl.state_registry.parse_guild.assert_called_with(payload)

    @pytest.mark.asyncio
    async def test_handle_guild_create_when_already_known_and_now_available_dispatches_GUILD_AVAILABLE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        fabric_impl.state_registry.parse_guild = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"id": str(guild_obj.id), "unavailable": False}

        await adapter_impl.handle_guild_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_AVAILABLE, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_create_when_not_already_known_dispatches_GUILD_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        fabric_impl.state_registry.parse_guild = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"id": str(guild_obj.id), "unavailable": True}

        await adapter_impl.handle_guild_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_CREATE, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_update_when_valid_dispatches_GUILD_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj_before = _helpers.mock_model(guilds.Guild, id=123, name="original")
        guild_obj_after = _helpers.mock_model(guilds.Guild, id=123, name="updated")
        fabric_impl.state_registry.update_guild = mock.MagicMock(return_value=(guild_obj_before, guild_obj_after))
        payload = {"id": str(guild_obj_after.id)}

        await adapter_impl.handle_guild_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_UPDATE, guild_obj_before, guild_obj_after)

    @pytest.mark.asyncio
    async def test_handle_guild_update_when_invalid_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.update_guild = mock.MagicMock(return_value=None)
        payload = {"id": "123"}

        await adapter_impl.handle_guild_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_delete_when_unavailable_invokes__handle_guild_unavailable(
        self, adapter_impl, gateway_impl
    ):
        adapter_impl._handle_guild_unavailable = mock.AsyncMock()
        payload = {"id": "123", "unavailable": True}

        await adapter_impl.handle_guild_delete(gateway_impl, payload)

        adapter_impl._handle_guild_unavailable.assert_called_with(gateway_impl, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_delete_when_available_invokes__handle_guild_leave(self, adapter_impl, gateway_impl):
        adapter_impl._handle_guild_leave = mock.AsyncMock()
        payload = {"id": "123", "unavailable": False}

        await adapter_impl.handle_guild_delete(gateway_impl, payload)

        adapter_impl._handle_guild_leave.assert_called_with(gateway_impl, payload)

    @pytest.mark.asyncio
    async def test__handle_guild_unavailable_when_not_cached_parses_guild(
        self, adapter_impl, fabric_impl, gateway_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"id": "123", "unavailable": False}

        await adapter_impl._handle_guild_unavailable(gateway_impl, payload)

        fabric_impl.state_registry.parse_guild.assert_called_with(payload)

    @pytest.mark.asyncio
    async def test__handle_guild_unavailable_when_not_cached_does_not_dispatch_anything(
        self, adapter_impl, dispatch_impl, fabric_impl, gateway_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"id": "123", "unavailable": True}

        await adapter_impl._handle_guild_unavailable(gateway_impl, payload)

        dispatch_impl.assert_not_called()

    @pytest.mark.asyncio
    async def test__handle_guild_unavailable_when_cached_dispatches_GUILD_UNAVAILABLE(
        self, adapter_impl, dispatch_impl, fabric_impl, gateway_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, is_unavailable=True)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"id": str(guild_obj.id), "unavailable": guild_obj.is_unavailable}

        await adapter_impl._handle_guild_unavailable(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_UNAVAILABLE, guild_obj)

    @pytest.mark.asyncio
    async def test__handle_guild_unavailable_when_cached_sets_guild_unavailablility(
        self, adapter_impl, fabric_impl, gateway_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, is_unavailable=True)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"id": str(guild_obj.id), "unavailable": guild_obj.is_unavailable}

        await adapter_impl._handle_guild_unavailable(gateway_impl, payload)

        fabric_impl.state_registry.set_guild_unavailability.assert_called_with(guild_obj, True)

    @pytest.mark.asyncio
    async def test__handle_guild_leave_parses_guild(self, adapter_impl, fabric_impl, gateway_impl):
        payload = {"id": "123", "unavailable": False}

        await adapter_impl._handle_guild_leave(gateway_impl, payload)

        fabric_impl.state_registry.parse_guild.assert_called_with(payload)

    @pytest.mark.asyncio
    async def test__handle_guild_leave_deletes_guild(self, adapter_impl, fabric_impl, gateway_impl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, is_unavailable=False)
        fabric_impl.state_registry.parse_guild = mock.MagicMock(return_value=guild_obj)
        payload = {"id": str(guild_obj.id), "unavailable": guild_obj.is_unavailable}

        await adapter_impl._handle_guild_leave(gateway_impl, payload)

        fabric_impl.state_registry.delete_guild.assert_called_with(guild_obj)

    @pytest.mark.asyncio
    async def test__handle_guild_leave_dispatches_GUILD_LEAVE(
        self, adapter_impl, dispatch_impl, fabric_impl, gateway_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, is_unavailable=False)
        fabric_impl.state_registry.parse_guild = mock.MagicMock(return_value=guild_obj)
        payload = {"id": guild_obj.id, "unavailable": guild_obj.is_unavailable}

        await adapter_impl._handle_guild_leave(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_LEAVE, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_ban_add_parses_user(self, adapter_impl, gateway_impl, fabric_impl):
        payload = {"guild_id": "123", "user": {"id": "456"}}

        await adapter_impl.handle_guild_ban_add(gateway_impl, payload)

        fabric_impl.state_registry.parse_user.assert_called_with(payload["user"])

    @pytest.mark.asyncio
    async def test_handle_guild_ban_add_resolves_member_if_available_and_guild_is_cached(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={})
        user_obj = _helpers.mock_model(users.User, id=456)
        member_obj = _helpers.mock_model(members.Member, id=456)
        guild_obj.members = {member_obj.id: member_obj}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_user = mock.MagicMock(return_value=user_obj)
        payload = {"guild_id": str(guild_obj.id), "user": {"id": str(user_obj.id)}}

        await adapter_impl.handle_guild_ban_add(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_BAN_ADD, guild_obj, member_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_ban_add_uses_user_if_member_is_not_cached_but_guild_is_cached(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={})
        user_obj = _helpers.mock_model(users.User, id=456)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_user = mock.MagicMock(return_value=user_obj)
        payload = {"guild_id": str(guild_obj.id), "user": {"id": str(user_obj.id)}}

        await adapter_impl.handle_guild_ban_add(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_BAN_ADD, guild_obj, user_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_ban_add_when_guild_is_cached_dispatches_GUILD_BAN_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={})
        user_obj = _helpers.mock_model(users.User, id=456)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_user = mock.MagicMock(return_value=user_obj)
        payload = {"guild_id": str(guild_obj.id), "user": {"id": str(user_obj.id)}}

        await adapter_impl.handle_guild_ban_add(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_BAN_ADD, guild_obj, user_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_ban_add_when_guild_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "user": {"id": "456"}}

        await adapter_impl.handle_guild_ban_add(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_BAN_ADD, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_ban_remove_parses_user(self, adapter_impl, gateway_impl, fabric_impl):
        payload = {"guild_id": "123", "user": {"id": "456"}}

        await adapter_impl.handle_guild_ban_remove(gateway_impl, payload)

        fabric_impl.state_registry.parse_user.assert_called_with(payload["user"])

    @pytest.mark.asyncio
    async def test_handle_guild_ban_remove_when_guild_cached_dispatches_GUILD_BAN_REMOVE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={})
        user_obj = _helpers.mock_model(users.User, id=456)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_user = mock.MagicMock(return_value=user_obj)
        payload = {"guild_id": str(guild_obj.id), "user": {"id": str(user_obj.id)}}

        await adapter_impl.handle_guild_ban_remove(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_BAN_REMOVE, guild_obj, user_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_ban_remove_when_guild_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "user": {"id": "456"}}

        await adapter_impl.handle_guild_ban_remove(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_BAN_REMOVE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_emojis_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {
            "guild_id": "123",
            "emojis": [{"id": "1234", "name": "bowsettebaka"}, {"id": "1235", "name": "bowsettel00d"}],
        }

        await adapter_impl.handle_guild_emojis_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_EMOJIS_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_emojis_update_when_guild_is_cached_dispatches_GUILD_EMOJIS_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        existing_emoji_1 = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="bowsettebaka", is_animated=False)
        existing_emoji_2 = _helpers.mock_model(emojis.GuildEmoji, id=1235, name="bowsettel00d", is_animated=False)
        existing_emoji_3 = _helpers.mock_model(emojis.GuildEmoji, id=1236, name="bowsetteowo", is_animated=True)

        initial_emoji_map = {
            existing_emoji_1.id: existing_emoji_1,
            existing_emoji_2.id: existing_emoji_2,
            existing_emoji_3.id: existing_emoji_3,
        }
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, emojis=dict(initial_emoji_map))
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.update_guild_emojis = mock.MagicMock(
            return_value=(set(initial_emoji_map.values()), {existing_emoji_1})
        )
        payload = {
            "guild_id": str(guild_obj.id),
            "emojis": [{"id": "1234", "name": "bowsettebaka"}, {"id": "1235", "name": "bowsettel00d"}],
        }

        await adapter_impl.handle_guild_emojis_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(
            event_types.EventType.GUILD_EMOJIS_UPDATE, guild_obj, set(initial_emoji_map.values()), {existing_emoji_1}
        )

    @pytest.mark.asyncio
    async def test_handle_guild_integrations_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123"}

        await adapter_impl.handle_guild_integrations_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_INTEGRATIONS_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_integrations_update_when_guild_is_cached_dispatches_GUILD_INTEGRATIONS_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"guild_id": str(guild_obj.id)}

        await adapter_impl.handle_guild_integrations_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_INTEGRATIONS_UPDATE, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_member_add_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123"}

        await adapter_impl.handle_guild_member_add(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_MEMBER_ADD, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_member_add_when_guild_is_cached_dispatches_GUILD_MEMBER_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        member_obj = _helpers.mock_model(members.Member, id=123)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_member = mock.MagicMock(return_value=member_obj)
        payload = {"guild_id": guild_obj.id}

        await adapter_impl.handle_guild_member_add(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_MEMBER_ADD, member_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_member_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "user": {"id": "123"}, "roles": [], "nick": None}

        await adapter_impl.handle_guild_member_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_MEMBER_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_member_update_when_member_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"guild_id": str(guild_obj.id), "user": {"id": "123"}, "roles": [], "nick": None}

        await adapter_impl.handle_guild_member_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_MEMBER_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_member_update_when_role_is_not_cached_does_not_pass_update_member_that_role(
        self, adapter_impl, gateway_impl, fabric_impl
    ):
        role_obj = _helpers.mock_model(roles.Role, id=1)
        member_obj = _helpers.mock_model(members.Member, id=123, nick=None)
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={}, roles={})
        guild_obj.members = {member_obj.id: member_obj}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_role_by_id = mock.MagicMock(return_value=None)
        payload = {
            "guild_id": str(guild_obj.id),
            "user": {"id": str(member_obj.id)},
            "nick": "potatoboi",
            "roles": [role_obj.id],
        }

        await adapter_impl.handle_guild_member_update(gateway_impl, payload)

        fabric_impl.state_registry.update_member.assert_called_with(member_obj, [], payload)

    @pytest.mark.asyncio
    async def test_handle_guild_member_update_calls_update_member_with_roles_and_nick(
        self, adapter_impl, gateway_impl, fabric_impl
    ):
        role_obj = _helpers.mock_model(roles.Role, id=1)
        member_obj = _helpers.mock_model(members.Member, id=123, nick=None)
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={}, roles={})
        guild_obj.members = {member_obj.id: member_obj}
        guild_obj.roles = {role_obj.id: role_obj}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_role_by_id = mock.MagicMock(return_value=role_obj)
        payload = {
            "guild_id": str(guild_obj.id),
            "user": {"id": str(member_obj.id)},
            "nick": "potatoboi",
            "roles": [role_obj.id],
        }

        await adapter_impl.handle_guild_member_update(gateway_impl, payload)

        fabric_impl.state_registry.update_member.assert_called_with(member_obj, [role_obj], payload)

    @pytest.mark.asyncio
    async def test_handle_guild_member_update_when_member_is_cached_dispatches_GUILD_MEMBER_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        member_obj = _helpers.mock_model(members.Member, id=123, nick=None)
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, members={}, roles={})
        guild_obj.members = {member_obj.id: member_obj}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"guild_id": str(guild_obj.id), "user": {"id": str(member_obj.id)}, "nick": None, "roles": []}

        await adapter_impl.handle_guild_member_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_MEMBER_UPDATE)

    @pytest.mark.asyncio
    async def test_handle_guild_member_remove_when_member_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "user": {"id": "123"}}

        await adapter_impl.handle_guild_member_remove(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_MEMBER_REMOVE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_member_remove_when_member_is_cached_deletes_member(
        self, adapter_impl, gateway_impl, fabric_impl
    ):
        member_obj = _helpers.mock_model(members.Member, id=123)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        payload = {"guild_id": "123", "user": {"id": str(member_obj.id)}}

        await adapter_impl.handle_guild_member_remove(gateway_impl, payload)

        fabric_impl.state_registry.delete_member.assert_called_with(member_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_member_remove_when_member_is_cached_dispatches_GUILD_MEMBER_REMOVE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        member_obj = _helpers.mock_model(members.Member, id=123)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        payload = {"guild_id": "123", "user": {"id": str(member_obj.id)}}

        await adapter_impl.handle_guild_member_remove(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_MEMBER_REMOVE, member_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_members_chunk_calls_chunker(self, adapter_impl, fabric_impl, gateway_impl):
        fabric_impl.chunker = mock.MagicMock(spec_set=_chunker.BaseChunker)
        fabric_impl.chunker.handle_next_chunk = mock.AsyncMock()

        payload = {...}

        await adapter_impl.handle_guild_members_chunk(gateway_impl, payload)

        fabric_impl.chunker.handle_next_chunk.assert_called_once_with(payload, gateway_impl.shard_id)

    @pytest.mark.asyncio
    async def test_handle_guild_role_create_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "role": {"id": "123"}}

        await adapter_impl.handle_guild_role_create(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_ROLE_CREATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_role_create_when_guild_is_cached_dispatches_GUILD_ROLE_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        role_obj = _helpers.mock_model(roles.Role, id=1)
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, roles={})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_role = mock.MagicMock(return_value=role_obj)
        payload = {"guild_id": str(guild_obj.id), "role": {"id": str(role_obj.id)}}

        await adapter_impl.handle_guild_role_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_ROLE_CREATE, role_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_role_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "role": {"id": "12"}}
        await adapter_impl.handle_guild_role_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_ROLE_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_role_update_when_guild_is_cached_but_role_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id="123", roles={})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.update_role = mock.MagicMock(return_value=None)
        payload = {"guild_id": str(guild_obj.id), "role": {"id": "12"}}

        await adapter_impl.handle_guild_role_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_ROLE_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_role_update_when_diff_is_valid_dispatches_GUILD_ROLE_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        role_obj_before = _helpers.mock_model(roles.Role, id=12, name="original")
        role_obj_after = _helpers.mock_model(roles.Role, id=12, name="updated")
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, roles={role_obj_before.id: role_obj_before})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.update_role = mock.MagicMock(return_value=(role_obj_before, role_obj_after))
        payload = {"guild_id": str(guild_obj.id), "role": {"id": str(role_obj_after.id)}}

        await adapter_impl.handle_guild_role_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_ROLE_UPDATE, role_obj_before, role_obj_after)

    @pytest.mark.asyncio
    async def test_handle_guild_role_delete_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "role_id": "12"}

        await adapter_impl.handle_guild_role_delete(gateway_impl, payload)

        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_ROLE_DELETE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_role_delete_when_role_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, roles={})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"guild_id": str(guild_obj.id), "role_id": "123"}

        await adapter_impl.handle_guild_role_delete(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_GUILD_ROLE_DELETE, payload)

    @pytest.mark.asyncio
    async def test_handle_guild_role_delete_when_role_is_cached_deletes_the_role(
        self, adapter_impl, gateway_impl, fabric_impl
    ):
        role_obj = _helpers.mock_model(roles.Role, id=12)
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, roles={role_obj.id: role_obj})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"guild_id": str(guild_obj.id), "role_id": str(role_obj.id)}

        await adapter_impl.handle_guild_role_delete(gateway_impl, payload)

        fabric_impl.state_registry.delete_role.assert_called_with(role_obj)

    @pytest.mark.asyncio
    async def test_handle_guild_role_delete_when_role_is_cached_dispatches_GUILD_ROLE_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        role_obj = _helpers.mock_model(roles.Role, id=12)
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, roles={role_obj.id: role_obj})
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        payload = {"guild_id": str(guild_obj.id), "role_id": str(role_obj.id)}

        await adapter_impl.handle_guild_role_delete(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.GUILD_ROLE_DELETE, role_obj)

    @pytest.mark.asyncio
    async def test_handle_message_create_when_channel_does_not_exist_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.parse_message = mock.MagicMock(return_value=None)
        payload = {"id": "123", "channel_id": "456", "content": "potatoboi test message"}

        await adapter_impl.handle_message_create(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_CREATE, payload)

    @pytest.mark.asyncio
    async def test_handle_message_create_when_channel_exists_dispatches_MESSAGE_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=123, content="potatoboi test message")
        channel_obj = _helpers.mock_model(channels.Channel, id=456)
        fabric_impl.state_registry.parse_message = mock.MagicMock(return_value=message_obj)
        payload = {"id": str(message_obj.id), "channel_id": str(channel_obj.id), "content": message_obj.content}

        await adapter_impl.handle_message_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_CREATE, message_obj)

    @pytest.mark.asyncio
    async def test_handle_message_update_when_message_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.update_message = mock.MagicMock(return_value=None)
        payload = {"id": "123", "channel_id": "456", "content": "potatoboi test message"}

        await adapter_impl.handle_message_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_message_update_when_message_is_cached_dispatches_MESSAGE_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj_before = _helpers.mock_model(messages.Message, id=123, content="original")
        message_obj_after = _helpers.mock_model(messages.Message, id=123, content="updated")
        fabric_impl.state_registry.update_message = mock.MagicMock(return_value=(message_obj_before, message_obj_after))
        payload = {"id": str(message_obj_after.id), "channel_id": "456", "content": message_obj_after.content}

        await adapter_impl.handle_message_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_UPDATE, message_obj_before, message_obj_after)

    @pytest.mark.asyncio
    async def test_handle_message_delete_when_message_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=None)
        payload = {"id": "123", "channel_id": "456"}

        await adapter_impl.handle_message_delete(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_DELETE, payload)

    @pytest.mark.asyncio
    async def test_handle_message_delete_when_message_is_cached_deletes_message(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=123, channel_id=456)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        payload = {"id": str(message_obj.id), "channel_id": str(message_obj.channel_id)}

        await adapter_impl.handle_message_delete(gateway_impl, payload)

        fabric_impl.state_registry.delete_message.assert_called_with(message_obj)

    @pytest.mark.asyncio
    async def test_handle_message_delete_when_message_is_cached_dispatches_MESSAGE_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=123, channel_id=456)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        payload = {"id": str(message_obj.id), "channel_id": str(message_obj.channel_id)}

        await adapter_impl.handle_message_delete(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_DELETE, message_obj)

    @pytest.mark.asyncio
    async def test_handle_message_delete_bulk_dispatches_correctly_for_cached_messages(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj1 = _helpers.mock_model(messages.Message, id=1234)
        message_obj2 = _helpers.mock_model(messages.Message, id=1235)

        channel_obj = _helpers.mock_model(channels.Channel, id=456)
        fabric_impl.state_registry.delete_message = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(side_effect=[message_obj1, message_obj2])
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)

        payload = {"ids": [str(message_obj1.id), str(message_obj2.id)], "channel_id": str(channel_obj.id)}

        await adapter_impl.handle_message_delete_bulk(gateway_impl, payload)

        dispatch_impl.assert_called_with(
            event_types.EventType.MESSAGE_DELETE_BULK,
            channel_obj,
            {message_obj1.id: message_obj1, message_obj2.id: message_obj2},
        )

    @pytest.mark.asyncio
    async def test_handle_message_delete_bulk_dispatches_correctly_for_uncached_messages(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj1 = _helpers.mock_model(messages.Message, id=1234)
        message_obj2 = _helpers.mock_model(messages.Message, id=1235)
        message_obj3 = _helpers.mock_model(messages.Message, id=1236)

        channel_obj = _helpers.mock_model(channels.Channel, id=456)
        fabric_impl.state_registry.delete_message = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)

        payload = {
            "ids": [str(message_obj1.id), str(message_obj2.id), str(message_obj3.id)],
            "channel_id": str(channel_obj.id),
        }

        await adapter_impl.handle_message_delete_bulk(gateway_impl, payload)

        dispatch_impl.assert_called_with(
            event_types.EventType.MESSAGE_DELETE_BULK,
            channel_obj,
            {message_obj1.id: None, message_obj2.id: None, message_obj3.id: None},
        )

    @pytest.mark.asyncio
    async def test_handle_message_delete_bulk_when_channel_does_not_exist_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj1 = _helpers.mock_model(messages.Message, id=1234)
        message_obj2 = _helpers.mock_model(messages.Message, id=1235)
        message_obj3 = _helpers.mock_model(messages.Message, id=1236)

        fabric_impl.state_registry.delete_message = mock.MagicMock(side_effect=[message_obj1, message_obj2, None])
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=None)

        payload = {"ids": [str(message_obj1.id), str(message_obj2.id), str(message_obj3.id)], "channel_id": "456"}

        await adapter_impl.handle_message_delete_bulk(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_DELETE_BULK, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_message_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=None)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": "789",
            "emoji": {"id": "1234", "name": "potatobiofire"},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_ADD, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_parses_emoji(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": "1234", "name": "potatobiofire"},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        fabric_impl.state_registry.parse_emoji.asset_called_with(payload["emoji"], None)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_increments_reaction_count(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        fabric_impl.state_registry.increment_reaction_count.asset_called_with(message_obj, emoji_obj)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_in_guild_attempts_to_resolve_member_who_added_reaction(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        guild_obj = _helpers.mock_model(guilds.Guild, id=345)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "guild_id": str(guild_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        fabric_impl.state_registry.get_member_by_id.assert_called_with(123, guild_obj.id)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_not_in_guild_uses_user(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        fabric_impl.state_registry.get_user_by_id.assert_called_with(123)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_cannot_resolve_user_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_ADD, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_cannot_resolve_member_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        guild_obj = _helpers.mock_model(guilds.Guild, id=345)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "guild_id": str(guild_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_ADD, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_resolved_member_dispatches_MESSAGE_REACTION_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        member_obj = _helpers.mock_model(members.Member, id=123)
        message_obj = _helpers.mock_model(messages.Message, id=789)
        guild_obj = _helpers.mock_model(guilds.Guild, id=345)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        reaction_obj = _helpers.mock_model(reactions.Reaction, count=1, emoji=emoji_obj, message=message_obj)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        fabric_impl.state_registry.increment_reaction_count = mock.MagicMock(return_value=reaction_obj)
        payload = {
            "user_id": str(member_obj.id),
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "guild_id": str(guild_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_REACTION_ADD, reaction_obj, member_obj)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_add_when_resolved_user_dispatches_MESSAGE_REACTION_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        user_obj = _helpers.mock_model(users.User, id=123)
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        reaction_obj = _helpers.mock_model(reactions.Reaction, count=1, emoji=emoji_obj, message=message_obj)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        fabric_impl.state_registry.increment_reaction_count = mock.MagicMock(return_value=reaction_obj)
        payload = {
            "user_id": str(user_obj.id),
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_add(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_REACTION_ADD, reaction_obj, user_obj)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_when_message_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=None)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": "789",
            "emoji": {"id": "1234", "name": "potatobiofire"},
        }

        await adapter_impl.handle_message_reaction_remove(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_REMOVE, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_when_in_guild_attempts_to_resolve_member_who_added_reaction(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        guild_obj = _helpers.mock_model(guilds.Guild, id=345)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "guild_id": str(guild_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_remove(gateway_impl, payload)

        fabric_impl.state_registry.get_member_by_id.assert_called_with(123, guild_obj.id)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_when_not_in_guild_uses_user(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_remove(gateway_impl, payload)

        fabric_impl.state_registry.get_user_by_id.assert_called_with(123)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_when_reaction_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        fabric_impl.state_registry.decrement_reaction_count = mock.MagicMock(return_value=None)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_remove(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_REMOVE, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_when_reaction_by_that_user_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        reaction_obj = _helpers.mock_model(reactions.Reaction, count=0, emoji=emoji_obj, message=message_obj)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        fabric_impl.state_registry.decrement_reaction_count = mock.MagicMock(return_value=reaction_obj)
        payload = {
            "user_id": "123",
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_remove(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_REMOVE, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_dispatches_MESSAGE_REACTION_REMOVE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        user_obj = _helpers.mock_model(users.User, id=123)
        message_obj = _helpers.mock_model(messages.Message, id=789)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="potatobiofire", is_animated=False)
        reaction_obj = _helpers.mock_model(reactions.Reaction, count=0, emoji=emoji_obj, message=message_obj)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.parse_emoji = mock.MagicMock(return_value=emoji_obj)
        fabric_impl.state_registry.decrement_reaction_count = mock.MagicMock(return_value=reaction_obj)
        payload = {
            "user_id": str(user_obj.id),
            "channel_id": "456",
            "message_id": str(message_obj.id),
            "emoji": {"id": str(emoji_obj.id), "name": emoji_obj.name},
        }

        await adapter_impl.handle_message_reaction_remove(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_REACTION_REMOVE, reaction_obj, user_obj)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_all_when_uncached_message_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=None)
        payload = {"channel_id": "123", "message_id": "456"}

        await adapter_impl.handle_message_reaction_remove_all(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_MESSAGE_REACTION_REMOVE_ALL, payload)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_all_deletes_all_reactions(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=456)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        payload = {"channel_id": "123", "message_id": str(message_obj.id)}

        await adapter_impl.handle_message_reaction_remove_all(gateway_impl, payload)

        fabric_impl.state_registry.delete_all_reactions(message_obj)

    @pytest.mark.asyncio
    async def test_handle_message_reaction_remove_all_dispatches_MESSAGE_REACTION_REMOVE_ALL(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=456)
        fabric_impl.state_registry.get_message_by_id = mock.MagicMock(return_value=message_obj)
        payload = {"channel_id": "123", "message_id": str(message_obj.id)}

        await adapter_impl.handle_message_reaction_remove_all(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.MESSAGE_REACTION_REMOVE_ALL, message_obj)

    @pytest.mark.asyncio
    async def test_handle_presence_update_when_guild_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        payload = {
            "user": {"id": "123"},
            "roles": ["456", "654", "4"],
            "game": None,
            "guild_id": "789",
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }

        await adapter_impl.handle_presence_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_PRESENCE_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_presence_update_when_user_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=789)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=None)
        payload = {
            "user": {"id": "123"},
            "roles": ["456", "654", "4"],
            "game": None,
            "guild_id": str(guild_obj.id),
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }
        await adapter_impl.handle_presence_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_PRESENCE_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_presence_update_when_member_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=789)
        user_obj = _helpers.mock_model(users.User, id=123)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=None)
        payload = {
            "user": {"id": str(user_obj.id)},
            "roles": ["456", "654", "4"],
            "game": None,
            "guild_id": str(guild_obj.id),
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }
        await adapter_impl.handle_presence_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_PRESENCE_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_presence_update_when_cached_member_invokes_update_member_presence(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=789)
        user_obj = _helpers.mock_model(users.User, id=123)
        member_obj = _helpers.mock_model(members.Member, id=123)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        payload = {
            "user": {"id": str(user_obj.id)},
            "roles": ["456", "654", "4"],
            "game": None,
            "guild_id": str(guild_obj.id),
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }
        await adapter_impl.handle_presence_update(gateway_impl, payload)

        fabric_impl.state_registry.update_member_presence.assert_called_with(member_obj, payload)

    @pytest.mark.asyncio
    async def test_handle_presence_update_ignores_unknown_roles(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=789)
        user_obj = _helpers.mock_model(users.User, id=123)
        member_obj = _helpers.mock_model(members.Member, id=123)
        role_obj1 = _helpers.mock_model(roles.Role, id=456)
        role_obj2 = _helpers.mock_model(roles.Role, id=654)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        fabric_impl.state_registry.get_role_by_id = mock.MagicMock(side_effect=[role_obj1, role_obj2, None])
        payload = {
            "user": {"id": str(user_obj.id)},
            "roles": [str(role_obj1.id), str(role_obj2.id), "4"],
            "game": None,
            "guild_id": str(guild_obj.id),
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }
        await adapter_impl.handle_presence_update(gateway_impl, payload)

        fabric_impl.state_registry.set_roles_for_member.assert_called_with([role_obj1, role_obj2], member_obj)

    @pytest.mark.asyncio
    async def test_handle_presence_update_sets_roles_for_member(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=789)
        user_obj = _helpers.mock_model(users.User, id=123)
        member_obj = _helpers.mock_model(members.Member, id=123)
        role_obj1 = _helpers.mock_model(roles.Role, id=456)
        role_obj2 = _helpers.mock_model(roles.Role, id=654)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        fabric_impl.state_registry.get_role_by_id = mock.MagicMock(side_effect=[role_obj1, role_obj2, None])
        payload = {
            "user": {"id": str(user_obj.id)},
            "roles": [str(role_obj1.id), str(role_obj2.id), "4"],
            "game": None,
            "guild_id": str(guild_obj.id),
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }
        await adapter_impl.handle_presence_update(gateway_impl, payload)

        fabric_impl.state_registry.set_roles_for_member.assert_called_with([role_obj1, role_obj2], member_obj)

    @pytest.mark.asyncio
    async def test_handle_presence_update_dispatches_PRESENCE_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=789)
        user_obj = _helpers.mock_model(users.User, id=123)
        member_obj = _helpers.mock_model(members.Member, id=123)
        role_obj1 = _helpers.mock_model(roles.Role, id=456)
        role_obj2 = _helpers.mock_model(roles.Role, id=654)
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        fabric_impl.state_registry.get_member_by_id = mock.MagicMock(return_value=member_obj)
        fabric_impl.state_registry.get_role_by_id = mock.MagicMock(side_effect=[role_obj1, role_obj2, None])
        payload = {
            "user": {"id": str(user_obj.id)},
            "roles": [str(role_obj1.id), str(role_obj2.id), "4"],
            "game": None,
            "guild_id": str(guild_obj.id),
            "status": "idle",
            "activities": [],
            "client_status": {"desktop": "online"},
        }
        await adapter_impl.handle_presence_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.PRESENCE_UPDATE)

    @pytest.mark.asyncio
    async def test_handle_typing_start_in_uncached_channel_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=None)
        payload = {"channel_id": "123", "user_id": "456", "timestamp": timestamp.isoformat()}

        await adapter_impl.handle_typing_start(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_TYPING_START, payload)

    @pytest.mark.asyncio
    async def test_handle_typing_start_by_unknown_user_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        channel_obj = _helpers.mock_model(channels.DMChannel, id=123, is_dm=True)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=None)
        payload = {"channel_id": str(channel_obj.id), "user_id": "456", "timestamp": timestamp.isoformat()}

        await adapter_impl.handle_typing_start(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_TYPING_START, payload)

    @pytest.mark.asyncio
    async def test_handle_typing_start_in_guild_resolves_member(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        channel_obj = _helpers.mock_model(channels.GuildChannel, id=123, is_dm=False)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {"channel_id": str(channel_obj.id), "user_id": "456", "timestamp": timestamp.isoformat()}

        await adapter_impl.handle_typing_start(gateway_impl, payload)

        channel_obj.guild.members.get.assert_called_with(456)

    @pytest.mark.asyncio
    async def test_handle_typing_start_in_non_guild_resolves_user(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        channel_obj = _helpers.mock_model(channels.DMChannel, id=123, is_dm=True)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=None)
        payload = {"channel_id": str(channel_obj.id), "user_id": "456", "timestamp": timestamp.isoformat()}

        await adapter_impl.handle_typing_start(gateway_impl, payload)

        fabric_impl.state_registry.get_user_by_id.assert_called_with(456)

    @pytest.mark.asyncio
    async def test_handle_typing_start_dispatches_TYPING_START(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        channel_obj = _helpers.mock_model(channels.DMChannel, id=123, is_dm=True)
        user_obj = _helpers.mock_model(users.User, id=456)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        fabric_impl.state_registry.get_user_by_id = mock.MagicMock(return_value=user_obj)
        payload = {"channel_id": str(channel_obj.id), "user_id": str(user_obj.id), "timestamp": timestamp.isoformat()}

        await adapter_impl.handle_typing_start(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.TYPING_START, user_obj, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_user_update_dispatches_USER_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        user_obj = _helpers.mock_model(users.User, id=123)
        fabric_impl.state_registry.parse_user = mock.MagicMock(return_value=user_obj)
        payload = {"id": str(user_obj.id)}

        await adapter_impl.handle_user_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.USER_UPDATE, user_obj)

    @pytest.mark.asyncio
    async def test_handle_webhooks_update_when_channel_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=None)
        payload = {"guild_id": "123", "channel_id": "456"}

        await adapter_impl.handle_webhooks_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(event_types.EventType.RAW_WEBHOOKS_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_webhooks_update_when_channel_cached_dispatches_WEBHOOKS_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, id=456)
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        payload = {"guild_id": "123", "channel_id": str(channel_obj.id)}

        await adapter_impl.handle_webhooks_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(event_types.EventType.WEBHOOKS_UPDATE, channel_obj)

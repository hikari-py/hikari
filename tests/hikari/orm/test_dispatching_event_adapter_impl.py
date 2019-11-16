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
import inspect
import logging
import traceback
import datetime
from unittest import mock

import asynctest
import pytest

from hikari.net import gateway as _gateway
from hikari.orm import dispatching_event_adapter_impl
from hikari.orm import events
from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import channels
from hikari.orm.models import guilds
from tests.hikari import _helpers


@pytest.fixture()
def logger_impl():
    return mock.MagicMock(spec_set=logging.Logger)


@pytest.fixture()
def state_registry_impl():
    return asynctest.MagicMock(spec_set=state_registry.IStateRegistry)


@pytest.fixture()
def dispatch_impl():
    return mock.MagicMock(spec_set=lambda name, *args: None)


@pytest.fixture()
def gateway_impl():
    return mock.MagicMock(spec_set=_gateway.GatewayClientV7)


@pytest.fixture()
def fabric_impl(state_registry_impl, gateway_impl):
    return fabric.Fabric(state_registry=state_registry_impl, gateways={None: gateway_impl})


@pytest.fixture()
def adapter_impl(fabric_impl, dispatch_impl, logger_impl):
    instance = _helpers.unslot_class(dispatching_event_adapter_impl.DispatchingEventAdapterImpl)(
        fabric_impl, dispatch_impl
    )
    instance.logger = logger_impl
    return instance


# noinspection PyProtectedMember
@pytest.mark.state
class TestStateRegistryImpl:
    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_first_time_adds_to_ignored_events_set(self, adapter_impl, gateway_impl):
        adapter_impl._ignored_events.clear()
        assert not adapter_impl._ignored_events, "ignored events were not empty at the start!"

        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        assert "try_to_do_something" in adapter_impl._ignored_events

    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_first_time_logs_warning(self, adapter_impl, gateway_impl):
        adapter_impl._ignored_events.clear()
        assert not adapter_impl._ignored_events, "ignored events were not empty at the start!"

        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        adapter_impl.logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_second_time_does_not_log_anything(self, adapter_impl, gateway_impl):
        adapter_impl._ignored_events = {"try_to_do_something"}

        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        assert "try_to_do_something" in adapter_impl._ignored_events
        adapter_impl.logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_drain_unrecognised_event_invokes_raw_dispatch(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.drain_unrecognised_event(gateway_impl, "try_to_do_something", ...)

        dispatch_impl.assert_called_with("raw_try_to_do_something", ...)

    @pytest.mark.asyncio
    async def test_handle_disconnect_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        payload = {"code": 123, "reason": "test"}
        await adapter_impl.handle_disconnect(gateway_impl, payload)

        dispatch_impl.assert_called_with("disconnect", gateway_impl, payload.get("code"), payload.get("reason"))

    @pytest.mark.asyncio
    async def test_handle_connect_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_connect(gateway_impl, ...)

        dispatch_impl.assert_called_with("connect", gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_invalid_session_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_invalid_session(gateway_impl, False)

        dispatch_impl.assert_called_with("invalid_session", gateway_impl, False)

    @pytest.mark.asyncio
    async def test_handle_reconnect_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_reconnect(gateway_impl, ...)

        dispatch_impl.assert_called_with("reconnect", gateway_impl)

    @pytest.mark.asyncio
    async def test_handle_resumed_dispatches_event(self, adapter_impl, gateway_impl, dispatch_impl):
        await adapter_impl.handle_resumed(gateway_impl, ...)

        dispatch_impl.assert_called_with("resumed", gateway_impl)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["handler_name", "raw_event_expected"],
        [
            ("handle_channel_create", events.RAW_CHANNEL_CREATE),
            ("handle_channel_update", events.RAW_CHANNEL_UPDATE),
            ("handle_channel_delete", events.RAW_CHANNEL_DELETE),
            ("handle_channel_pins_update", events.RAW_CHANNEL_PINS_UPDATE),
            ("handle_guild_create", events.RAW_GUILD_CREATE),
            ("handle_guild_update", events.RAW_GUILD_UPDATE),
            ("handle_guild_delete", events.RAW_GUILD_DELETE),
            ("handle_guild_ban_add", events.RAW_GUILD_BAN_ADD),
            ("handle_guild_ban_remove", events.RAW_GUILD_BAN_REMOVE),
            ("handle_guild_emojis_update", events.RAW_GUILD_EMOJIS_UPDATE),
            ("handle_guild_integrations_update", events.RAW_GUILD_INTEGRATIONS_UPDATE),
            ("handle_guild_member_add", events.RAW_GUILD_MEMBER_ADD),
            ("handle_guild_member_update", events.RAW_GUILD_MEMBER_UPDATE),
            ("handle_guild_member_remove", events.RAW_GUILD_MEMBER_REMOVE),
            ("handle_guild_members_chunk", events.RAW_GUILD_MEMBERS_CHUNK),
            ("handle_guild_role_create", events.RAW_GUILD_ROLE_CREATE),
            ("handle_guild_role_update", events.RAW_GUILD_ROLE_UPDATE),
            ("handle_guild_role_delete", events.RAW_GUILD_ROLE_DELETE),
            ("handle_message_create", events.RAW_MESSAGE_CREATE),
            ("handle_message_update", events.RAW_MESSAGE_UPDATE),
            ("handle_message_delete", events.RAW_MESSAGE_DELETE),
            ("handle_message_delete_bulk", events.RAW_MESSAGE_DELETE_BULK),
            ("handle_message_reaction_add", events.RAW_MESSAGE_REACTION_ADD),
            ("handle_message_reaction_remove", events.RAW_MESSAGE_REACTION_REMOVE),
            ("handle_message_reaction_remove_all", events.RAW_MESSAGE_REACTION_REMOVE_ALL),
            ("handle_presence_update", events.RAW_PRESENCE_UPDATE),
            ("handle_typing_start", events.RAW_TYPING_START),
            ("handle_user_update", events.RAW_USER_UPDATE),
            ("handle_message_reaction_remove", events.RAW_MESSAGE_REACTION_REMOVE),
            ("handle_voice_state_update", events.RAW_VOICE_STATE_UPDATE),
            ("handle_voice_server_update", events.RAW_VOICE_SERVER_UPDATE),
            ("handle_webhooks_update", events.RAW_WEBHOOKS_UPDATE),
        ],
    )
    async def test_raw_event_handler(self, gateway_impl, dispatch_impl, adapter_impl, handler_name, raw_event_expected):
        handler = getattr(adapter_impl, handler_name)
        assert inspect.ismethod(handler)

        payload = mock.MagicMock()

        # Being lazy, I just brute force this as it is the first thing that happens ever in any event, so meh.
        # Any exception raised afterwards can be ignored unless the assertion fails.
        try:
            await handler(gateway_impl, payload)
        except Exception:
            traceback.print_exc()

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
        payload = {"guild_id": guild_obj.id}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.GUILD_CHANNEL_CREATE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_create_for_guild_channel_in_unknown_guild_does_not_dispatch(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        payload = {"guild_id": 123}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        await adapter_impl.handle_channel_create(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(events.RAW_CHANNEL_CREATE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_create_for_dm_channel_dispatches_DM_CHANNEL_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, is_dm=True)
        payload = {"guild_id": None}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=None)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_create(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.DM_CHANNEL_CREATE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_create_parses_channel(self, adapter_impl, gateway_impl, fabric_impl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        payload = {"guild_id": guild_obj.id}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_create(gateway_impl, payload)

        fabric_impl.state_registry.parse_channel.assert_called_with(payload, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_update_for_invalid_update_event_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        payload = {"id": 123}
        fabric_impl.state_registry.update_channel = mock.MagicMock(return_value=None)
        await adapter_impl.handle_channel_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(events.RAW_CHANNEL_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_update_for_valid_dm_channel_update_dispatches_DM_CHANNEL_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj_before = _helpers.mock_model(channels.GroupDMChannel, is_dm=True, name="original")
        channel_obj_after = _helpers.mock_model(channels.GroupDMChannel, is_dm=True, name="updated")
        payload = {"id": channel_obj_after.id, "type": channel_obj_after.is_dm}
        fabric_impl.state_registry.update_channel = mock.MagicMock(
            return_value=(channel_obj_before, channel_obj_after)
        )
        await adapter_impl.handle_channel_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.DM_CHANNEL_UPDATE, channel_obj_before, channel_obj_after)

    @pytest.mark.asyncio
    async def test_handle_channel_update_for_valid_guild_channel_update_dispatches_GUILD_CHANNEL_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj_before = _helpers.mock_model(channels.GuildTextChannel, is_dm=False, name="original")
        channel_obj_after = _helpers.mock_model(channels.GuildTextChannel, is_dm=False, name="updated")
        payload = {"id": channel_obj_after.id, "type": channel_obj_after.is_dm}
        fabric_impl.state_registry.update_channel = mock.MagicMock(
            return_value=(channel_obj_before, channel_obj_after)
        )
        fabric_impl.state_registry.update_channel = mock.MagicMock(
            return_value=(channel_obj_before, channel_obj_after)
        )
        await adapter_impl.handle_channel_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.GUILD_CHANNEL_UPDATE, channel_obj_before, channel_obj_after)

    @pytest.mark.asyncio
    async def test_handle_channel_update_invokes_update_channel(self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl):
        payload = {"id": 123, "type": True}
        await adapter_impl.handle_channel_update(gateway_impl, payload)

        fabric_impl.state_registry.update_channel.assert_called_with(payload)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_for_invalid_update_event_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        payload = {"guild_id": 123}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(
            return_value=None)
        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(events.RAW_CHANNEL_DELETE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_parses_channel(self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        payload = {"guild_id": guild_obj.id}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(
            return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(
            return_value=channel_obj)
        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        fabric_impl.state_registry.parse_channel.assert_called_with(
            payload, guild_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_for_dm_channel_dispatches_DM_CHANNEL_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, is_dm=True)
        payload = {"guild_id": None}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(
            return_value=None)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(
            return_value=channel_obj)
        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.DM_CHANNEL_DELETE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_delete_for_guild_channel_dispatches_GUILD_CHANNEL_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        payload = {"guild_id": guild_obj.id}
        fabric_impl.state_registry.get_guild_by_id = mock.MagicMock(
            return_value=guild_obj)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(
            return_value=channel_obj)
        await adapter_impl.handle_channel_delete(gateway_impl, payload)

        dispatch_impl.assert_called_with(
            events.GUILD_CHANNEL_DELETE, channel_obj)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_unknown_channel_dispatches_nothing(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        payload = {"channel_id": 123, "type": False, "last_pin_timestamp": None}
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=None)
        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        # Not called other than the raw from earlier.
        dispatch_impl.assert_called_once()
        dispatch_impl.assert_called_with(events.RAW_CHANNEL_PINS_UPDATE, payload)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_known_channel_invokes_set_last_pinned_timestamp_on_state(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        payload = {"channel_id": 123, "type": False, "last_pin_timestamp": timestamp.isoformat()}
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        fabric_impl.state_registry.set_last_pinned_timestamp.assert_called_with(
            channel_obj, timestamp)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_adding_pin_to_guild_channel_invokes_GUILD_CHANNEL_PIN_ADDED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        payload = {"channel_id": channel_obj.id, "type": channel_obj.is_dm,
                   "last_pin_timestamp": timestamp.isoformat()}
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.GUILD_CHANNEL_PIN_ADDED, timestamp)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_adding_pin_to_dm_channel_invokes_DM_CHANNEL_PIN_ADDED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, is_dm=True)
        timestamp = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        payload = {"channel_id": channel_obj.id, "type": channel_obj.is_dm,
                   "last_pin_timestamp": timestamp.isoformat()}
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.DM_CHANNEL_PIN_ADDED, timestamp)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_removing_pin_from_guild_channel_invokes_GUILD_CHANNEL_PIN_REMOVED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.GuildChannel, is_dm=False)
        payload = {"channel_id": channel_obj.id, "type": channel_obj.is_dm,
                   "last_pin_timestamp": None}
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.GUILD_CHANNEL_PIN_REMOVED)

    @pytest.mark.asyncio
    async def test_handle_channel_pins_update_for_removing_pin_from_dm_channel_invokes_DM_CHANNEL_PIN_REMOVED(
        self, adapter_impl, gateway_impl, dispatch_impl, fabric_impl
    ):
        channel_obj = _helpers.mock_model(channels.DMChannel, is_dm=True)
        payload = {"channel_id": channel_obj.id, "type": channel_obj.is_dm,
                   "last_pin_timestamp": None}
        fabric_impl.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        await adapter_impl.handle_channel_pins_update(gateway_impl, payload)

        dispatch_impl.assert_called_with(events.DM_CHANNEL_PIN_REMOVED)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_create_parses_guild(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_create_when_already_known_and_now_available_dispatches_GUILD_AVAILABLE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_create_when_not_already_known_dispatches_GUILD_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_update_when_valid_dispatches_GUILD_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_update_when_invalid_dispatches_nothing(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_delete_when_unavailable_invokes__handle_guild_unavailable(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_delete_when_available_invokes__handle_guild_leave(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_unavailable_when_not_cached_parses_guild(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_unavailable_when_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_unavailable_when_cached_dispatches_GUILD_UNAVAILABLE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_unavailable_when_cached_sets_guild_unavailablility(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_leave_parses_guild(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_leave_deletes_guild(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test__handle_guild_leave_dispatches_GUILD_LEAVE(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_add_parses_user(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_add_resolves_member_if_available_and_guild_is_cached(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_add_uses_user_if_member_is_not_cached_but_guild_is_cached(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_add_when_guild_is_cached_dispatches_GUILD_BAN_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_add_when_guild_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_remove_parses_user(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_remove_when_guild_cached_dispatches_GUILD_BAN_REMOVE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_ban_remove_when_guild_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_emojis_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_emojis_update_when_guild_is_cached_dispatches_GUILD_EMOJIS_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_integrations_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_integrations_update_when_guild_is_cached_dispatches_GUILD_INTEGRATIONS_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_add_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_add_when_guild_is_cached_dispatches_GUILD_MEMBER_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_update_when_member_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_update_when_role_is_not_cached_does_not_pass_update_member_that_role(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_update_calls_update_member_with_roles_and_nick(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_update_when_member_is_cached_dispatches_GUILD_MEMBER_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_remove_when_member_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_remove_when_member_is_cached_deletes_member(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_member_remove_when_member_is_cached_dispatches_GUILD_MEMBER_REMOVE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_create_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_create_when_guild_is_cached_dispatches_GUILD_ROLE_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_update_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_update_when_guild_is_cached_but_role_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_update_when_diff_is_valid_dispatches_GUILD_ROLE_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_delete_when_guild_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_delete_when_role_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_delete_when_role_is_cached_deletes_the_role(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_guild_role_delete_when_role_is_cached_dispatches_GUILD_ROLE_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_create_when_channel_does_not_exist_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_create_when_channel_exists_dispatches_MESSAGE_CREATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_update_when_message_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_update_when_message_is_cached_dispatches_MESSAGE_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_delete_when_message_is_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_delete_when_message_is_cached_deletes_message(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_delete_when_message_is_cached_dispatches_MESSAGE_DELETE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_delete_bulk_dispatches_with_any_cached_messages(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_delete_bulk_does_not_dispatch_with_uncached_messages(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_delete_bulk_when_channel_does_not_exist_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_message_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_parses_emoji(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_increments_reaction_count(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_in_guild_attempts_to_resolve_member_who_added_reaction(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_not_in_guild_uses_user(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_cannot_resolve_user_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_cannot_resolve_member_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_resolved_member_dispatches_MESSAGE_REACTION_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_add_when_resolved_user_dispatches_MESSAGE_REACTION_ADD(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_when_message_not_cached_does_not_resolve_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_when_in_guild_attempts_to_resolve_member_who_added_reaction(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_when_not_in_guild_uses_user(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_when_reaction_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_when_reaction_by_that_user_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_dispatches_MESSAGE_REACTION_REMOVE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_all_when_uncached_message_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_all_deletes_all_reactions(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_message_reaction_remove_all_dispatches_MESSAGE_REACTION_REMOVE_ALL(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_when_guild_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_when_user_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_when_member_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_when_cached_member_invokes_update_member_presence(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_ignores_unknown_roles(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_sets_roles_for_member(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_presence_update_dispatches_PRESENCE_UPDATE(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_typing_start_in_uncached_channel_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_typing_start_by_unknown_user_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_typing_start_in_guild_resolves_member(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_typing_start_in_non_guild_resolves_user(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_typing_start_dispatches_TYPING_START(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_user_update_dispatches_USER_UPDATE(self, adapter_impl, gateway_impl, dispatch_impl):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_webhooks_update_when_channel_not_cached_does_not_dispatch_anything(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Not implemented")
    async def test_handle_webhooks_update_when_channel_cached_dispatches_WEBHOOKS_UPDATE(
        self, adapter_impl, gateway_impl, dispatch_impl
    ):
        ...

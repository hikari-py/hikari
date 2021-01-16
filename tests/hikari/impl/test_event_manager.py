# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import asyncio

import mock
import pytest

from hikari import channels
from hikari import intents
from hikari import presences
from hikari.impl import event_manager
from tests.hikari import hikari_test_helpers


class TestEventManagerImpl:
    @pytest.fixture()
    def app(self):
        return mock.Mock(intents=intents.Intents.ALL)

    @pytest.fixture()
    def shard(self):
        return mock.Mock(id=987)

    @pytest.fixture()
    def event_manager(self, app):
        obj = hikari_test_helpers.mock_class_namespace(event_manager.EventManagerImpl, slots_=False)(
            app, cache=mock.Mock()
        )

        obj.dispatch = mock.AsyncMock()
        return obj

    @pytest.fixture()
    def stateless_event_manager(self, app):
        obj = hikari_test_helpers.mock_class_namespace(event_manager.EventManagerImpl, slots_=False)(app, cache=None)

        obj.dispatch = mock.AsyncMock()
        return obj

    @pytest.mark.asyncio
    async def test_on_ready_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(my_user=mock.Mock())

        event_manager._app.event_factory.deserialize_ready_event.return_value = event

        await event_manager.on_ready(shard, payload)

        event_manager._cache.update_me.assert_called_once_with(event.my_user)
        event_manager._app.event_factory.deserialize_ready_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_ready_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_ready(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_ready_event.assert_called_once_with(shard, payload)
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_ready_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_resumed(self, event_manager, shard, app):
        payload = {}

        await event_manager.on_resumed(shard, payload)

        event_manager._app.event_factory.deserialize_resumed_event.assert_called_once_with(shard)
        event_manager.dispatch.assert_awaited_once_with(
            event_manager._app.event_factory.deserialize_resumed_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_create_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(channel=mock.Mock(channels.GuildChannel))

        event_manager._app.event_factory.deserialize_channel_create_event.return_value = event

        await event_manager.on_channel_create(shard, payload)

        event_manager._cache.set_guild_channel.assert_called_once_with(event.channel)
        event_manager._app.event_factory.deserialize_channel_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_create_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_channel_create(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_channel_create_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_channel_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_update_stateful(self, event_manager, shard, app):
        payload = {"id": 123}
        old_channel = object()
        event = mock.Mock(channel=mock.Mock(channels.GuildChannel))

        event_manager._app.event_factory.deserialize_channel_update_event.return_value = event
        event_manager._cache.get_guild_channel.return_value = old_channel

        await event_manager.on_channel_update(shard, payload)

        event_manager._cache.get_guild_channel.assert_called_once_with(123)
        event_manager._cache.update_guild_channel.assert_called_once_with(event.channel)
        event_manager._app.event_factory.deserialize_channel_update_event.assert_called_once_with(
            shard, payload, old_channel=old_channel
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"id": 123}

        await stateless_event_manager.on_channel_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_channel_update_event.assert_called_once_with(
            shard, payload, old_channel=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_channel_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_delete_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(channel=mock.Mock(id=123))

        event_manager._app.event_factory.deserialize_channel_delete_event.return_value = event

        await event_manager.on_channel_delete(shard, payload)

        event_manager._cache.delete_guild_channel.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_channel_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_delete_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_channel_delete(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_channel_delete_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_channel_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_pins_update(self, stateless_event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        stateless_event_manager._app.event_factory.deserialize_channel_pins_update_event.return_value = event

        await stateless_event_manager.on_channel_pins_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_channel_pins_update_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_create_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(
            guild=mock.Mock(id=123, is_large=False),
            channels={"TestChannel": 456},
            emojis={"TestEmoji": 789},
            roles={"TestRole": 1234},
            members={"TestMember": 5678},
            presences={"TestPresence": 9012},
            voice_states={"TestState": 345},
            chunk_nonce=None,
        )

        event_manager._app.event_factory.deserialize_guild_create_event.return_value = event
        shard.request_guild_members = mock.AsyncMock()

        await event_manager.on_guild_create(shard, payload)

        assert event.chunk_nonce is None
        shard.request_guild_members.assert_not_called()

        event_manager._cache.update_guild.assert_called_once_with(event.guild)

        event_manager._cache.clear_guild_channels_for_guild.assert_called_once_with(123)
        event_manager._cache.set_guild_channel.assert_called_once_with(456)

        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.set_emoji.assert_called_once_with(789)

        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._cache.set_role.assert_called_once_with(1234)

        event_manager._cache.clear_members_for_guild.assert_called_once_with(123)
        event_manager._cache.set_member.assert_called_once_with(5678)

        event_manager._cache.clear_presences_for_guild.assert_called_once_with(123)
        event_manager._cache.set_presence.assert_called_once_with(9012)

        event_manager._cache.clear_voice_states_for_guild.assert_called_once_with(123)
        event_manager._cache.set_voice_state.assert_called_once_with(345)

        event_manager._app.event_factory.deserialize_guild_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_create_when_request_chunks(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(
            guild=mock.Mock(id=123, is_large=True),
            channels={"TestChannel": 456},
            emojis={"TestEmoji": 789},
            roles={"TestRole": 1234},
            members={"TestMember": 5678},
            presences={"TestPresence": 9012},
            voice_states={"TestState": 345},
            chunk_nonce=None,
        )

        event_manager._app.event_factory.deserialize_guild_create_event.return_value = event
        shard.request_guild_members = mock.Mock()

        with mock.patch.object(asyncio, "create_task") as create_task:
            with mock.patch("hikari.impl.event_manager._fixed_size_nonce", return_value="uuid") as uuid:
                await event_manager.on_guild_create(shard, payload)

        uuid.assert_called_once_with()
        nonce = "987.uuid"
        assert event.chunk_nonce == nonce
        shard.request_guild_members.assert_called_once_with(event.guild, include_presences=True, nonce=nonce)
        create_task.assert_called_once_with(shard.request_guild_members(), name="987:123 guild create members request")

        event_manager._cache.update_guild.assert_called_once_with(event.guild)

        event_manager._cache.clear_guild_channels_for_guild.assert_called_once_with(123)
        event_manager._cache.set_guild_channel.assert_called_once_with(456)

        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.set_emoji.assert_called_once_with(789)

        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._cache.set_role.assert_called_once_with(1234)

        event_manager._cache.clear_members_for_guild.assert_called_once_with(123)
        event_manager._cache.set_member.assert_called_once_with(5678)

        event_manager._cache.clear_presences_for_guild.assert_called_once_with(123)
        event_manager._cache.set_presence.assert_called_once_with(9012)

        event_manager._cache.clear_voice_states_for_guild.assert_called_once_with(123)
        event_manager._cache.set_voice_state.assert_called_once_with(345)

        event_manager._app.event_factory.deserialize_guild_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_create_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        shard.request_guild_members = mock.AsyncMock()

        await stateless_event_manager.on_guild_create(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_create_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_update_stateful(self, event_manager, shard, app):
        payload = {"id": 123}
        old_guild = object()
        mock_role = object()
        mock_emoji = object()
        event = mock.Mock(roles={555: mock_role}, emojis={333: mock_emoji}, guild=mock.Mock(id=123))

        event_manager._app.event_factory.deserialize_guild_update_event.return_value = event
        event_manager._cache.get_guild.return_value = old_guild

        await event_manager.on_guild_update(shard, payload)

        event_manager._cache.get_guild.assert_called_once_with(123)
        event_manager._cache.update_guild.assert_called_once_with(event.guild)
        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._cache.set_role.assert_called_once_with(mock_role)
        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.set_emoji.assert_called_once_with(mock_emoji)
        event_manager._app.event_factory.deserialize_guild_update_event.assert_called_once_with(
            shard, payload, old_guild=old_guild
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"id": 123}

        await stateless_event_manager.on_guild_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_update_event.assert_called_once_with(
            shard, payload, old_guild=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateful_when_available(self, event_manager, shard, app):
        payload = {"unavailable": False}
        event = mock.Mock(guild_id=123)

        event_manager._app.event_factory.deserialize_guild_leave_event.return_value = event

        await event_manager.on_guild_delete(shard, payload)

        event_manager._cache.delete_guild.assert_called_once_with(123)
        event_manager._cache.clear_voice_states_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_invites_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_members_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_presences_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_guild_channels_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_guild_leave_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateful_when_unavailable(self, event_manager, shard, app):
        payload = {"unavailable": True}
        event = mock.Mock(guild_id=123)

        event_manager._app.event_factory.deserialize_guild_unavailable_event.return_value = event

        await event_manager.on_guild_delete(shard, payload)

        event_manager._cache.set_guild_availability.assert_called_once_with(event.guild_id, False)
        event_manager._app.event_factory.deserialize_guild_unavailable_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateless_when_available(self, stateless_event_manager, shard, app):
        payload = {"unavailable": False}

        await stateless_event_manager.on_guild_delete(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_leave_event.assert_called_once_with(shard, payload)
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_leave_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateless_when_unavailable(self, stateless_event_manager, shard, app):
        payload = {"unavailable": True}

        await stateless_event_manager.on_guild_delete(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_unavailable_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_unavailable_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_ban_add(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_guild_ban_add_event.return_value = event

        await event_manager.on_guild_ban_add(shard, payload)

        event_manager._app.event_factory.deserialize_guild_ban_add_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_ban_remove(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_guild_ban_remove_event.return_value = event

        await event_manager.on_guild_ban_remove(shard, payload)

        event_manager._app.event_factory.deserialize_guild_ban_remove_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_emojis_update_stateful(self, event_manager, shard, app):
        payload = {"guild_id": 123}
        old_emojis = {"Test": 123}
        mock_emoji = object()
        event = mock.Mock(emojis=[mock_emoji], guild_id=123)

        event_manager._app.event_factory.deserialize_guild_emojis_update_event.return_value = event
        event_manager._cache.clear_emojis_for_guild.return_value = old_emojis

        await event_manager.on_guild_emojis_update(shard, payload)

        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.set_emoji.assert_called_once_with(mock_emoji)
        event_manager._app.event_factory.deserialize_guild_emojis_update_event.assert_called_once_with(
            shard, payload, old_emojis=[123]
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_emojis_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"guild_id": 123}

        await stateless_event_manager.on_guild_emojis_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_emojis_update_event.assert_called_once_with(
            shard, payload, old_emojis=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_emojis_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_integrations_update(self, event_manager, shard):
        assert await event_manager.on_guild_integrations_update(shard, {}) is None

        event_manager.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_integration_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_integration_create_event.return_value = event

        await event_manager.on_integration_create(shard, payload)

        event_manager._app.event_factory.deserialize_integration_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_delete(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_integration_delete_event.return_value = event

        await event_manager.on_integration_delete(shard, payload)

        event_manager._app.event_factory.deserialize_integration_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_integration_update_event.return_value = event

        await event_manager.on_integration_update(shard, payload)

        event_manager._app.event_factory.deserialize_integration_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_add_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(user=object(), member=object())

        event_manager._app.event_factory.deserialize_guild_member_add_event.return_value = event

        await event_manager.on_guild_member_add(shard, payload)

        event_manager._cache.update_member.assert_called_once_with(event.member)
        event_manager._app.event_factory.deserialize_guild_member_add_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_add_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_guild_member_add(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_member_add_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_member_add_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_member_remove_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(user=mock.Mock(id=123), guild_id=456)

        event_manager._app.event_factory.deserialize_guild_member_remove_event.return_value = event

        await event_manager.on_guild_member_remove(shard, payload)

        event_manager._cache.delete_member.assert_called_once_with(456, 123)
        event_manager._app.event_factory.deserialize_guild_member_remove_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_remove_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_guild_member_remove(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_member_remove_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_member_remove_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_member_update_stateful(self, event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_member = object()
        event = mock.Mock(member=mock.Mock())

        event_manager._app.event_factory.deserialize_guild_member_update_event.return_value = event
        event_manager._cache.get_member.return_value = old_member

        await event_manager.on_guild_member_update(shard, payload)

        event_manager._cache.get_member.assert_called_once_with(456, 123)
        event_manager._cache.update_member.assert_called_once_with(event.member)
        event_manager._app.event_factory.deserialize_guild_member_update_event.assert_called_once_with(
            shard, payload, old_member=old_member
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}

        await stateless_event_manager.on_guild_member_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_member_update_event.assert_called_once_with(
            shard, payload, old_member=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_member_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_members_chunk_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(members={"TestMember": 123}, presences={"TestPresences": 456})
        event_manager._app.event_factory.deserialize_guild_member_chunk_event.return_value = event

        await event_manager.on_guild_members_chunk(shard, payload)

        event_manager._cache.set_member.assert_called_once_with(123)
        event_manager._cache.set_presence.assert_called_once_with(456)
        event_manager._app.event_factory.deserialize_guild_member_chunk_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_members_chunk_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_guild_members_chunk(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_member_chunk_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_member_chunk_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_create_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(role=object())

        event_manager._app.event_factory.deserialize_guild_role_create_event.return_value = event

        await event_manager.on_guild_role_create(shard, payload)

        event_manager._cache.set_role.assert_called_once_with(event.role)
        event_manager._app.event_factory.deserialize_guild_role_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_create_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_guild_role_create(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_role_create_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_role_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_update_stateful(self, event_manager, shard, app):
        payload = {"role": {"id": 123}}
        old_role = object()
        event = mock.Mock(role=mock.Mock())

        event_manager._app.event_factory.deserialize_guild_role_update_event.return_value = event
        event_manager._cache.get_role.return_value = old_role

        await event_manager.on_guild_role_update(shard, payload)

        event_manager._cache.get_role.assert_called_once_with(123)
        event_manager._cache.update_role.assert_called_once_with(event.role)
        event_manager._app.event_factory.deserialize_guild_role_update_event.assert_called_once_with(
            shard, payload, old_role=old_role
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"role": {"id": 123}}

        await stateless_event_manager.on_guild_role_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_role_update_event.assert_called_once_with(
            shard, payload, old_role=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_role_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_delete_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(role_id=123)

        event_manager._app.event_factory.deserialize_guild_role_delete_event.return_value = event

        await event_manager.on_guild_role_delete(shard, payload)

        event_manager._cache.delete_role.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_guild_role_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_delete_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_guild_role_delete(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_guild_role_delete_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_guild_role_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_invite_create_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(invite="qwerty")

        event_manager._app.event_factory.deserialize_invite_create_event.return_value = event

        await event_manager.on_invite_create(shard, payload)

        event_manager._cache.set_invite.assert_called_once_with("qwerty")
        event_manager._app.event_factory.deserialize_invite_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_invite_create_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_invite_create(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_invite_create_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_invite_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_invite_delete_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(code="qwerty")

        event_manager._app.event_factory.deserialize_invite_delete_event.return_value = event

        await event_manager.on_invite_delete(shard, payload)

        event_manager._cache.delete_invite.assert_called_once_with("qwerty")
        event_manager._app.event_factory.deserialize_invite_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_invite_delete_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_invite_delete(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_invite_delete_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_invite_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_create_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(message=object())

        event_manager._app.event_factory.deserialize_message_create_event.return_value = event

        await event_manager.on_message_create(shard, payload)

        event_manager._cache.set_message.assert_called_once_with(event.message)
        event_manager._app.event_factory.deserialize_message_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_create_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_message_create(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_message_create_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_message_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_update_stateful(self, event_manager, shard, app):
        payload = {"id": 123}
        old_message = object()
        event = mock.Mock(message=mock.Mock())

        event_manager._app.event_factory.deserialize_message_update_event.return_value = event
        event_manager._cache.get_message.return_value = old_message

        await event_manager.on_message_update(shard, payload)

        event_manager._cache.get_message.assert_called_once_with(123)
        event_manager._cache.update_message.assert_called_once_with(event.message)
        event_manager._app.event_factory.deserialize_message_update_event.assert_called_once_with(
            shard, payload, old_message=old_message
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"id": 123}

        await stateless_event_manager.on_message_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_message_update_event.assert_called_once_with(
            shard, payload, old_message=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_message_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_delete_stateless(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(message_id=123)

        event_manager._app.event_factory.deserialize_message_delete_event.return_value = event

        await event_manager.on_message_delete(shard, payload)

        event_manager._cache.delete_message.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_message_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_delete_stateful(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_message_delete(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_message_delete_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_message_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_delete_bulk_stateful(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(message_ids=[123, 456, 789])

        event_manager._app.event_factory.deserialize_message_delete_bulk_event.return_value = event

        await event_manager.on_message_delete_bulk(shard, payload)

        event_manager._cache.delete_message.assert_has_calls([mock.call(123), mock.call(456), mock.call(789)])
        event_manager._app.event_factory.deserialize_message_delete_bulk_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_delete_bulk_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_message_delete_bulk(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_message_delete_bulk_event.assert_called_once_with(
            shard, payload
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_message_delete_bulk_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_reaction_add(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_add_event.return_value = event

        await event_manager.on_message_reaction_add(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_add_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_remove_event.return_value = event

        await event_manager.on_message_reaction_remove(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_remove_event.assert_called_once_with(
            shard, payload
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_all(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_remove_all_event.return_value = event

        await event_manager.on_message_reaction_remove_all(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_remove_all_event.assert_called_once_with(
            shard, payload
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_emoji(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_remove_emoji_event.return_value = event

        await event_manager.on_message_reaction_remove_emoji(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_remove_emoji_event.assert_called_once_with(
            shard, payload
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update_stateful_update(self, event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_presence = object()
        event = mock.Mock(presence=mock.Mock(visible_status=presences.Status.ONLINE))

        event_manager._app.event_factory.deserialize_presence_update_event.return_value = event
        event_manager._cache.get_presence.return_value = old_presence

        await event_manager.on_presence_update(shard, payload)

        event_manager._cache.get_presence.assert_called_once_with(456, 123)
        event_manager._cache.update_presence.assert_called_once_with(event.presence)
        event_manager._app.event_factory.deserialize_presence_update_event.assert_called_once_with(
            shard, payload, old_presence=old_presence
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update_stateful_delete(self, event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_presence = object()
        event = mock.Mock(presence=mock.Mock(visible_status=presences.Status.OFFLINE))

        event_manager._app.event_factory.deserialize_presence_update_event.return_value = event
        event_manager._cache.get_presence.return_value = old_presence

        await event_manager.on_presence_update(shard, payload)

        event_manager._cache.get_presence.assert_called_once_with(456, 123)
        event_manager._cache.delete_presence.assert_called_once_with(event.presence.guild_id, event.presence.user_id)
        event_manager._app.event_factory.deserialize_presence_update_event.assert_called_once_with(
            shard, payload, old_presence=old_presence
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}

        await stateless_event_manager.on_presence_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_presence_update_event.assert_called_once_with(
            shard, payload, old_presence=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_presence_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_typing_start(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_typing_start_event.return_value = event

        await event_manager.on_typing_start(shard, payload)

        event_manager._app.event_factory.deserialize_typing_start_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_user_update_stateful(self, event_manager, shard, app):
        payload = {}
        old_user = object()
        event = mock.Mock(user=mock.Mock())

        event_manager._app.event_factory.deserialize_own_user_update_event.return_value = event
        event_manager._cache.get_me.return_value = old_user

        await event_manager.on_user_update(shard, payload)

        event_manager._cache.update_me.assert_called_once_with(event.user)
        event_manager._app.event_factory.deserialize_own_user_update_event.assert_called_once_with(
            shard, payload, old_user=old_user
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_user_update_stateless(self, stateless_event_manager, shard, app):
        payload = {}

        await stateless_event_manager.on_user_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_own_user_update_event.assert_called_once_with(
            shard, payload, old_user=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_own_user_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_voice_state_update_stateful_update(self, event_manager, shard, app):
        payload = {"user_id": 123, "guild_id": 456}
        old_state = object()
        event = mock.Mock(state=mock.Mock(channel_id=123))

        event_manager._app.event_factory.deserialize_voice_state_update_event.return_value = event
        event_manager._cache.get_voice_state.return_value = old_state

        await event_manager.on_voice_state_update(shard, payload)

        event_manager._cache.get_voice_state.assert_called_once_with(456, 123)
        event_manager._cache.update_voice_state.assert_called_once_with(event.state)
        event_manager._app.event_factory.deserialize_voice_state_update_event.assert_called_once_with(
            shard, payload, old_state=old_state
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_voice_state_update_stateful_delete(self, event_manager, shard, app):
        payload = {"user_id": 123, "guild_id": 456}
        old_state = object()
        event = mock.Mock(state=mock.Mock(channel_id=None))

        event_manager._app.event_factory.deserialize_voice_state_update_event.return_value = event
        event_manager._cache.get_voice_state.return_value = old_state

        await event_manager.on_voice_state_update(shard, payload)

        event_manager._cache.get_voice_state.assert_called_once_with(456, 123)
        event_manager._cache.delete_voice_state.assert_called_once_with(event.state.guild_id, event.state.user_id)
        event_manager._app.event_factory.deserialize_voice_state_update_event.assert_called_once_with(
            shard, payload, old_state=old_state
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_voice_state_update_stateless(self, stateless_event_manager, shard, app):
        payload = {"user_id": 123, "guild_id": 456}

        await stateless_event_manager.on_voice_state_update(shard, payload)

        stateless_event_manager._app.event_factory.deserialize_voice_state_update_event.assert_called_once_with(
            shard, payload, old_state=None
        )
        stateless_event_manager.dispatch.assert_awaited_once_with(
            stateless_event_manager._app.event_factory.deserialize_voice_state_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_voice_server_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_voice_server_update_event.return_value = event

        await event_manager.on_voice_server_update(shard, payload)

        event_manager._app.event_factory.deserialize_voice_server_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_webhooks_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_webhook_update_event.return_value = event

        await event_manager.on_webhooks_update(shard, payload)

        event_manager._app.event_factory.deserialize_webhook_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

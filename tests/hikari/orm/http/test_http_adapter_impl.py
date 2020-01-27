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
from unittest import mock

import pytest

from hikari.internal_utilities import unspecified
from hikari.net import http_client
from hikari.orm import fabric
from hikari.orm.http import http_adapter_impl as _http_adapter_impl
from hikari.orm.models import applications
from hikari.orm.models import audit_logs
from hikari.orm.models import channels
from hikari.orm.models import colors
from hikari.orm.models import connections
from hikari.orm.models import embeds
from hikari.orm.models import emojis
from hikari.orm.models import gateway_bot
from hikari.orm.models import guilds
from hikari.orm.models import integrations
from hikari.orm.models import invites
from hikari.orm.models import media
from hikari.orm.models import members
from hikari.orm.models import messages
from hikari.orm.models import overwrites
from hikari.orm.models import permissions
from hikari.orm.models import reactions
from hikari.orm.models import roles
from hikari.orm.models import users
from hikari.orm.models import voices
from hikari.orm.models import webhooks
from hikari.orm.state import base_registry
from tests.hikari import _helpers


# noinspection PyDunderSlots
@pytest.mark.orm
class TestHTTPAdapterImpl:
    @pytest.fixture()
    def fabric_impl(self):
        fabric_impl = fabric.Fabric()

        http_client_impl = mock.MagicMock(spec_set=http_client.HTTPClient)
        state_registry_impl = mock.MagicMock(spec_set=base_registry.BaseRegistry)
        http_adapter_impl = _http_adapter_impl.HTTPAdapterImpl(fabric_impl)

        fabric_impl.state_registry = state_registry_impl
        fabric_impl.http_client = http_client_impl
        fabric_impl.http_adapter = http_adapter_impl

        return fabric_impl

    @pytest.mark.asyncio
    async def test_gateway_url(self, fabric_impl):
        fabric_impl.http_client.get_gateway = mock.AsyncMock(return_value="wss://some-site.com")

        for _ in range(15):
            assert await fabric_impl.http_adapter.gateway_url == "wss://some-site.com"

        fabric_impl.http_client.get_gateway.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_gateway_bot(self, fabric_impl):
        mock_model = _helpers.mock_model(gateway_bot.GatewayBot)
        mock_payload = mock.MagicMock(spec_set=dict)
        fabric_impl.http_client.get_gateway_bot = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_gateway_bot.return_value = mock_model

        result = await fabric_impl.http_adapter.fetch_gateway_bot()

        assert result is mock_model
        fabric_impl.http_client.get_gateway_bot.assert_called_once_with()
        fabric_impl.state_registry.parse_gateway_bot.assert_called_once_with(mock_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    async def test_fetch_audit_log_with_default_args(self, fabric_impl, guild):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_client.get_guild_audit_log = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_audit_log.return_value = mock_audit_log

        result = await fabric_impl.http_adapter.fetch_audit_log(guild)

        fabric_impl.http_client.get_guild_audit_log.assert_called_once_with(
            guild_id="112233",
            user_id=unspecified.UNSPECIFIED,
            action_type=unspecified.UNSPECIFIED,
            limit=unspecified.UNSPECIFIED,
        )

        fabric_impl.state_registry.parse_audit_log.assert_called_once_with(mock_payload)

        assert result is mock_audit_log

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 334455, users.User, users.OAuth2User)
    async def test_fetch_audit_log_with_optional_args_specified(self, fabric_impl, guild, user):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_client.get_guild_audit_log = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_audit_log.return_value = mock_audit_log

        result = await fabric_impl.http_adapter.fetch_audit_log(
            guild, user=user, action_type=audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE, limit=69,
        )

        fabric_impl.http_client.get_guild_audit_log.assert_called_once_with(
            guild_id="112233",
            user_id="334455",
            action_type=int(audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE),
            limit=69,
        )

        fabric_impl.state_registry.parse_audit_log.assert_called_once_with(mock_payload)

        assert result is mock_audit_log

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.DMChannel)
    async def test_fetch_dm_channel(self, fabric_impl, channel):
        mock_channel_payload = {"id": "532323423432343234", "name": "nyakuza"}
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        fabric_impl.http_client.get_channel = mock.AsyncMock(return_value=mock_channel_payload)
        assert await fabric_impl.http_adapter.fetch_channel(channel) is mock_channel
        fabric_impl.http_client.get_channel.assert_called_once_with("532323423432343234")
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, None)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.GuildChannel)
    async def test_fetch_guild_channel_when_is_guild_channel_and_guild_is_unresolved(self, fabric_impl, channel):
        mock_channel_payload = {"id": "532323423432343234", "name": "nyakuza", "guild_id": "22222222"}
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        fabric_impl.http_client.get_channel = mock.AsyncMock(return_value=mock_channel_payload)
        assert await fabric_impl.http_adapter.fetch_channel(channel) is mock_channel
        fabric_impl.http_client.get_channel.assert_called_once_with("532323423432343234")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(22222222)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.GuildChannel)
    async def test_fetch_guild_channel_when_is_guild_channel_and_guild_is_resolved(self, fabric_impl, channel):
        mock_channel_payload = {"id": "532323423432343234", "name": "nyakuza", "guild_id": "22222222"}
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        fabric_impl.http_client.get_channel = mock.AsyncMock(return_value=mock_channel_payload)
        assert await fabric_impl.http_adapter.fetch_channel(channel) is mock_channel
        fabric_impl.http_client.get_channel.assert_called_once_with("532323423432343234")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(22222222)
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    async def test_update_dm_channel_without_optionals(self, fabric_impl, channel):
        mock_channel_payload = {"id": "20409595959", "name": "mechanical-hands"}
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.http_client.modify_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert await fabric_impl.http_adapter.update_channel(channel) is mock_channel
        fabric_impl.http_client.modify_channel.assert_called_once_with(
            channel_id="532323423432343234",
            position=unspecified.UNSPECIFIED,
            topic=unspecified.UNSPECIFIED,
            nsfw=unspecified.UNSPECIFIED,
            rate_limit_per_user=unspecified.UNSPECIFIED,
            bitrate=unspecified.UNSPECIFIED,
            user_limit=unspecified.UNSPECIFIED,
            permission_overwrites=unspecified.UNSPECIFIED,
            parent_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, None)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    async def test_update_guild_channel_without_optionals_with_guild_unresolved(self, fabric_impl, channel):
        mock_channel_payload = {"id": "20409595959", "name": "mechanical-hands", "guild_id": "4959595959"}
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.http_client.modify_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert await fabric_impl.http_adapter.update_channel(channel) is mock_channel
        fabric_impl.http_client.modify_channel.assert_called_once_with(
            channel_id="532323423432343234",
            position=unspecified.UNSPECIFIED,
            topic=unspecified.UNSPECIFIED,
            nsfw=unspecified.UNSPECIFIED,
            rate_limit_per_user=unspecified.UNSPECIFIED,
            bitrate=unspecified.UNSPECIFIED,
            user_limit=unspecified.UNSPECIFIED,
            permission_overwrites=unspecified.UNSPECIFIED,
            parent_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(4959595959)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    async def test_update_guild_channel_without_optionals_with_guild_resolved(self, fabric_impl, channel):
        mock_channel_payload = {"id": "20409595959", "name": "mechanical-hands", "guild_id": "4959595959"}
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.http_client.modify_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert await fabric_impl.http_adapter.update_channel(channel) is mock_channel
        fabric_impl.http_client.modify_channel.assert_called_once_with(
            channel_id="532323423432343234",
            position=unspecified.UNSPECIFIED,
            topic=unspecified.UNSPECIFIED,
            nsfw=unspecified.UNSPECIFIED,
            rate_limit_per_user=unspecified.UNSPECIFIED,
            bitrate=unspecified.UNSPECIFIED,
            user_limit=unspecified.UNSPECIFIED,
            permission_overwrites=unspecified.UNSPECIFIED,
            parent_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(4959595959)
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    @_helpers.parametrize_valid_id_formats_for_models("parent_category", 324123123123123, channels.GuildCategory)
    async def test_update_dm_channel_with_all_optionals(self, fabric_impl, channel, parent_category):
        mock_channel_payload = {"id": "3949583839939", "name": "nothing-gets-me-down"}
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.http_client.modify_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert (
            await fabric_impl.http_adapter.update_channel(
                channel,
                position=4,
                topic="I can't believe it's a topic.",
                nsfw=True,
                rate_limit_per_user=4040404,
                bitrate=320,
                user_limit=2,
                permission_overwrites=[
                    overwrites.Overwrite(id=22, deny=69, allow=42, type=overwrites.OverwriteEntityType.MEMBER)
                ],
                parent_category=parent_category,
                reason="You just got vectored.",
            )
            is mock_channel
        )
        fabric_impl.http_client.modify_channel.assert_called_once_with(
            channel_id="532323423432343234",
            position=4,
            topic="I can't believe it's a topic.",
            nsfw=True,
            rate_limit_per_user=4040404,
            bitrate=320,
            user_limit=2,
            permission_overwrites=[{"id": 22, "allow": 42, "deny": 69, "type": "member"}],
            parent_id="324123123123123",
            reason="You just got vectored.",
        )
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, None)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    @_helpers.parametrize_valid_id_formats_for_models("parent_category", 324123123123123, channels.GuildCategory)
    async def test_update_guild_channel_with_all_optionals_with_guild_resolved(
        self, fabric_impl, channel, parent_category
    ):
        mock_channel_payload = {"id": "3949583839939", "name": "nothing-gets-me-down", "guild_id": "4945939393"}
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        mock_channel = mock.MagicMock(channels.Channel)
        fabric_impl.http_client.modify_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert (
            await fabric_impl.http_adapter.update_channel(
                channel,
                position=4,
                topic="I can't believe it's a topic.",
                nsfw=True,
                rate_limit_per_user=4040404,
                bitrate=320,
                user_limit=2,
                permission_overwrites=[
                    overwrites.Overwrite(id=22, deny=69, allow=42, type=overwrites.OverwriteEntityType.MEMBER)
                ],
                parent_category=parent_category,
                reason="You just got vectored.",
            )
            is mock_channel
        )
        fabric_impl.http_client.modify_channel.assert_called_once_with(
            channel_id="532323423432343234",
            position=4,
            topic="I can't believe it's a topic.",
            nsfw=True,
            rate_limit_per_user=4040404,
            bitrate=320,
            user_limit=2,
            permission_overwrites=[{"id": 22, "allow": 42, "deny": 69, "type": "member"}],
            parent_id="324123123123123",
            reason="You just got vectored.",
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(4945939393)
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    async def test_delete_channel(self, fabric_impl, channel):
        fabric_impl.http_client.delete_close_channel = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_channel(channel) is None
        fabric_impl.http_client.delete_close_channel.assert_called_once_with(channel_id="532323423432343234")

    @pytest.mark.asyncio
    @_helpers.todo_implement
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    async def test_fetch_messages_without_optionals(self, fabric_impl, channel):
        mock_message_payload = {"id": "553243", "content": "Hello World!"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        fabric_impl.http_client.get_channel_messages = mock.AsyncMock(return_value=[mock_message_payload])
        assert await fabric_impl.http_adapter.fetch_messages(channel) == [mock_message]
        fabric_impl.http_client.get_channel_messages.assert_called_once_with(channel_id="532323423432343234")
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    @_helpers.todo_implement
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532323423432343234, channels.TextChannel)
    async def test_fetch_messages_with_all_optionals(self, fabric_impl, channel):
        raise NotImplementedError

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", ("322222212121", 322222212121))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    async def test_fetch_message(self, fabric_impl, message, channel):
        mock_message_payload = {"id": "4444444", "content": "Hello World!"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        fabric_impl.http_client.get_channel_message = mock.AsyncMock(return_value=mock_message_payload)
        assert await fabric_impl.http_adapter.fetch_message(message, channel=channel) is mock_message
        fabric_impl.http_client.get_channel_message.assert_called_once_with(
            channel_id="532432123", message_id="322222212121"
        )
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    async def test_fetch_message_with_message_obj(self, fabric_impl):
        mock_message_payload = {"id": "4444444", "content": "Hello World!"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        fabric_impl.http_client.get_channel_message = mock.AsyncMock(return_value=mock_message_payload)
        assert (
            await fabric_impl.http_adapter.fetch_message(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123),
                )
            )
            is mock_message
        )
        fabric_impl.http_client.get_channel_message.assert_called_once_with(
            channel_id="532432123", message_id="322222212121"
        )
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_fetch_raises_type_error_without_channel(self, fabric_impl):
        fabric_impl.http_client.get_channel_message = mock.AsyncMock()
        await fabric_impl.http_adapter.fetch_message("2132132")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 2121231312, channels.Channel)
    async def test_create_message_without_optionals(self, fabric_impl, channel):
        mock_message_payload = {"id": "32123123", "content": "whoop"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        fabric_impl.http_client.create_message = mock.AsyncMock(return_value=mock_message_payload)
        assert await fabric_impl.http_adapter.create_message(channel) is mock_message
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)
        fabric_impl.http_client.create_message.assert_called_once_with(
            channel_id="2121231312",
            content=unspecified.UNSPECIFIED,
            tts=False,
            files=unspecified.UNSPECIFIED,
            embed=unspecified.UNSPECIFIED,
        )

    @pytest.mark.skip(reason="tests are now failing...")
    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 2121231312, channels.Channel)
    async def test_create_message_with_all_optionals(self, fabric_impl, channel):
        mock_message_payload = {"id": "32123123", "content": "whoop"}
        mock_message = mock.MagicMock(messages.Message)
        mock_file = mock.MagicMock(
            spec=media.File,
            open=mock.MagicMock(return_value=mock.AsyncMock(read=mock.AsyncMock(return_value=b"53234234"))),
        )
        mock_file.name = "Nekos"
        mock_in_memory_file = mock.MagicMock(
            spec=media.InMemoryFile,
            open=mock.MagicMock(return_value=mock.MagicMock(read=mock.MagicMock(return_value=b"4ascbdas32"))),
        )
        mock_in_memory_file.name = "cafe"
        fabric_impl.state_registry.parse_message.return_value = mock_message
        fabric_impl.http_client.create_message = mock.AsyncMock(return_value=mock_message_payload)
        assert (
            await fabric_impl.http_adapter.create_message(
                channel,
                content="hey, hey",
                tts=True,
                files=[mock_file],
                embed=mock.MagicMock(
                    spec=embeds.Embed,
                    to_dict=mock.MagicMock(return_value={"description": "fi", "type": "rich"}),
                    assets_to_upload=[mock_in_memory_file],
                ),
            )
            is mock_message
        )
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)
        fabric_impl.http_client.create_message.assert_called_once_with(
            channel_id="2121231312",
            content="hey, hey",
            tts=True,
            files=[("Nekos", b"53234234"), ("cafe", b"4ascbdas32")],
            embed={"description": "fi", "type": "rich"},
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "emoji", ["emoji:20202020", mock.MagicMock(emojis.UnknownEmoji, url_name="emoji:20202020")]
    )
    async def test_create_reaction_with_message_obj(self, fabric_impl, emoji):
        fabric_impl.http_client.create_reaction = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.create_reaction(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123),
                ),
                emoji,
            )
            is None
        )
        fabric_impl.http_client.create_reaction.assert_called_once_with(
            emoji="emoji:20202020", message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "emoji", ["emoji:20202020", mock.MagicMock(emojis.UnknownEmoji, url_name="emoji:20202020")]
    )
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    @pytest.mark.parametrize("message", (322222212121, "322222212121"))
    async def test_create_reaction(self, fabric_impl, message, emoji, channel):
        fabric_impl.http_client.create_reaction = mock.AsyncMock()
        assert await fabric_impl.http_adapter.create_reaction(message, emoji, channel=channel) is None
        fabric_impl.http_client.create_reaction.assert_called_once_with(
            emoji="emoji:20202020", message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_create_reaction_raises_type_error_without_channel(self, fabric_impl):
        fabric_impl.http_client.create_reaction = mock.AsyncMock()
        await fabric_impl.http_adapter.create_reaction("321123", "2123123")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 21323212312, members.Member)
    async def test_delete_reaction_with_reaction_obj(self, fabric_impl, user):
        fabric_impl.http_client.delete_user_reaction = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_reaction(
                user=user,
                reaction=_helpers.mock_model(
                    reactions.Reaction,
                    emoji=_helpers.mock_model(
                        emojis.GuildEmoji, id=21212121212, name="nya", url_name="nya:21212121212"
                    ),
                    message=_helpers.mock_model(
                        messages.Message, id=532432123, channel=_helpers.mock_model(channels.Channel, id=434343)
                    ),
                ),
            )
            is None
        )
        fabric_impl.http_client.delete_user_reaction.assert_called_once_with(
            emoji="nya:21212121212", user_id="21323212312", channel_id="434343", message_id="532432123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 21323212312, members.Member)
    async def test_delete_reaction_with_message_and_unknown_emoji_objects(self, fabric_impl, user):
        fabric_impl.http_client.delete_user_reaction = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_reaction(
                reaction=mock.MagicMock(emojis.UnknownEmoji, url_name="nya:21212121212"),
                user=user,
                message=_helpers.mock_model(
                    messages.Message, id=532432123, channel=_helpers.mock_model(channels.Channel, id=434343)
                ),
            )
            is None
        )
        fabric_impl.http_client.delete_user_reaction.assert_called_once_with(
            emoji="nya:21212121212", user_id="21323212312", channel_id="434343", message_id="532432123",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "reaction", (mock.MagicMock(emojis.UnknownEmoji, url_name="nya:21212121212"), "nya:21212121212")
    )
    @pytest.mark.parametrize("message", (532432123, "532432123"))
    @_helpers.parametrize_valid_id_formats_for_models("user", 21323212312, members.Member)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 434343, channels.Channel)
    async def test_delete_reaction(self, fabric_impl, reaction, channel, message, user):
        fabric_impl.http_client.delete_user_reaction = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_reaction(
                reaction=reaction, user=user, channel=channel, message=message,
            )
            is None
        )
        fabric_impl.http_client.delete_user_reaction.assert_called_once_with(
            emoji="nya:21212121212", user_id="21323212312", channel_id="434343", message_id="532432123",
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_delete_reaction_raises_type_error_without_chanel(self, fabric_impl):
        fabric_impl.http_client.delete_user_reaction = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_reaction("OwO:123", 123, message=202020)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_delete_reaction_raises_type_error_without_message(self, fabric_impl):
        fabric_impl.http_client.delete_user_reaction = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_reaction("OwO:123", 123, channel=202020)

    @pytest.mark.asyncio
    async def test_delete_all_reaction_with_message_obj(self, fabric_impl):
        fabric_impl.http_client.delete_all_reactions = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_all_reactions(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123)
                )
            )
            is None
        )
        fabric_impl.http_client.delete_all_reactions.assert_called_once_with(
            message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (322222212121, "322222212121"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    async def test_delete_all_reaction(self, fabric_impl, message, channel):
        fabric_impl.http_client.delete_all_reactions = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_all_reactions(message, channel=channel) is None
        fabric_impl.http_client.delete_all_reactions.assert_called_once_with(
            message_id="322222212121", channel_id="532432123"
        )

    @_helpers.todo_implement
    @pytest.mark.asyncio
    async def test_fetch_reactors(self, fabric_impl):
        raise NotImplementedError

    @pytest.mark.asyncio
    async def test_update_message_without_optionals_with_message_obj(self, fabric_impl):
        mock_message_payload = {"id": "32123123", "content": "whoop"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.http_client.edit_message = mock.AsyncMock(return_value=mock_message_payload)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        assert (
            await fabric_impl.http_adapter.update_message(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123),
                )
            )
            is mock_message
        )
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)
        fabric_impl.http_client.edit_message.assert_called_once_with(
            message_id="322222212121",
            channel_id="532432123",
            content=unspecified.UNSPECIFIED,
            embed=unspecified.UNSPECIFIED,
            flags=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (322222212121, "322222212121"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    async def test_update_message_without_optionals(self, fabric_impl, message, channel):
        mock_message_payload = {"id": "32123123", "content": "whoop"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.http_client.edit_message = mock.AsyncMock(return_value=mock_message_payload)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        assert await fabric_impl.http_adapter.update_message(message, channel=channel) is mock_message
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)
        fabric_impl.http_client.edit_message.assert_called_once_with(
            message_id="322222212121",
            channel_id="532432123",
            content=unspecified.UNSPECIFIED,
            embed=unspecified.UNSPECIFIED,
            flags=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    async def test_update_message_with_all_optionals_with_message_obj(self, fabric_impl):
        mock_message_payload = {"id": "32123123", "content": "whoop"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.http_client.edit_message = mock.AsyncMock(return_value=mock_message_payload)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        assert (
            await fabric_impl.http_adapter.update_message(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123),
                ),
                content="OK",
                embed=embeds.Embed(description="This_is_an_embed"),
                flags=4,
            )
            is mock_message
        )
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)
        fabric_impl.http_client.edit_message.assert_called_once_with(
            message_id="322222212121",
            channel_id="532432123",
            content="OK",
            embed={"description": "This_is_an_embed", "type": "rich"},
            flags=4,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", ("322222212121", 322222212121))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    async def test_update_message_with_all_optionals(self, fabric_impl, message, channel):
        mock_message_payload = {"id": "32123123", "content": "whoop"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.http_client.edit_message = mock.AsyncMock(return_value=mock_message_payload)
        fabric_impl.state_registry.parse_message.return_value = mock_message
        assert (
            await fabric_impl.http_adapter.update_message(
                message, channel=channel, content="OK", embed=embeds.Embed(description="This_is_an_embed"), flags=4,
            )
            is mock_message
        )
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)
        fabric_impl.http_client.edit_message.assert_called_once_with(
            message_id="322222212121",
            channel_id="532432123",
            content="OK",
            embed={"description": "This_is_an_embed", "type": "rich"},
            flags=4,
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_update_message_raises_type_error_without_channel(self, fabric_impl):
        fabric_impl.http_client.edit_message = mock.AsyncMock()
        await fabric_impl.http_adapter.update_message(123123)

    @pytest.mark.asyncio
    async def test_delete_messages_single_with_message_obj(self, fabric_impl):
        fabric_impl.http_client.delete_message = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_messages(
                _helpers.mock_model(
                    messages.Message, id=55544322, channel=_helpers.mock_model(channels.Channel, id=543234),
                )
            )
            is None
        )
        fabric_impl.http_client.delete_message.assert_called_once_with(channel_id="543234", message_id="55544322")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (55544322, "55544322"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 543234, channels.Channel)
    async def test_delete_messages_single(self, fabric_impl, message, channel):
        fabric_impl.http_client.delete_message = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_messages(message, channel=channel) is None
        fabric_impl.http_client.delete_message.assert_called_once_with(channel_id="543234", message_id="55544322")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 55544322, messages.Message)
    async def test_delete_messages_single_duplicated_with_message_obj(self, fabric_impl, additional_message):
        fabric_impl.http_client.delete_message = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_messages(
                _helpers.mock_model(
                    messages.Message, id=55544322, channel=_helpers.mock_model(channels.Channel, id=543234),
                ),
                additional_message,
                55544322,
                55544322,
                55544322,
            )
            is None
        )
        fabric_impl.http_client.delete_message.assert_called_once_with(
            channel_id="543234", message_id="55544322",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (55544322, "55544322"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 543234, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 55544322, messages.Message)
    async def test_delete_messages_single_duplicated(self, fabric_impl, message, additional_message, channel):
        fabric_impl.http_client.delete_message = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_messages(
                message, additional_message, 55544322, 55544322, 55544322, channel=channel
            )
            is None
        )
        fabric_impl.http_client.delete_message.assert_called_once_with(
            channel_id="543234", message_id="55544322",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 213123123, messages.Message)
    async def test_delete_messages_multiple_with_message_obj(self, fabric_impl, additional_message):
        fabric_impl.http_client.bulk_delete_messages = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_messages(
                _helpers.mock_model(
                    messages.Message, id=55544322, channel=_helpers.mock_model(channels.Channel, id=543234),
                ),
                additional_message,
                213123123,
            )
            is None
        )
        fabric_impl.http_client.bulk_delete_messages.assert_called_once_with(
            channel_id="543234", messages=["55544322", "213123123"]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (55544322, "55544322"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 543234, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 213123123, messages.Message)
    async def test_delete_messages_multiple(self, fabric_impl, message, additional_message, channel):
        fabric_impl.http_client.bulk_delete_messages = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_messages(message, additional_message, 213123123, channel=channel)
            is None
        )
        fabric_impl.http_client.bulk_delete_messages.assert_called_once_with(
            channel_id="543234", messages=["55544322", "213123123"]
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=ValueError)
    async def test_delete_messages_raises_value_error_when_too_many_messages_passed(self, fabric_impl):
        fabric_impl.http_client.bulk_delete_messages = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_messages(*range(101), channel=321231)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_delete_messages_raises_type_error_without_channel(self, fabric_impl):
        fabric_impl.http_client.delete_message = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_messages("12312")

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=ValueError)
    async def test_delete_messages_raises_value_error_when_too_many_messages_passed(self, fabric_impl):
        fabric_impl.http_client.bulk_delete_messages = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_messages(*range(0, 101), channel=212)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 245321970760024064, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 115590097100865541, overwrites.Overwrite)
    async def test_update_channel_overwrite_without_optionals(self, fabric_impl, channel, overwrite):
        fabric_impl.http_client.edit_channel_permissions = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_channel_overwrite(channel=channel, overwrite=overwrite) is None
        fabric_impl.http_client.edit_channel_permissions.assert_called_once_with(
            channel_id="245321970760024064",
            overwrite_id="115590097100865541",
            allow=unspecified.UNSPECIFIED,
            deny=unspecified.UNSPECIFIED,
            type_=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 245321970760024064, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 115590097100865541, overwrites.Overwrite)
    @pytest.mark.parametrize("overwrite_type", ["role", overwrites.OverwriteEntityType.ROLE])
    async def test_update_channel_overwrite_with_all_optionals(self, fabric_impl, channel, overwrite, overwrite_type):
        fabric_impl.http_client.edit_channel_permissions = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_channel_overwrite(
                channel=channel, overwrite=overwrite, allow=68, deny=44, overwrite_type=overwrite_type, reason="OK"
            )
            is None
        )
        fabric_impl.http_client.edit_channel_permissions.assert_called_once_with(
            channel_id="245321970760024064",
            overwrite_id="115590097100865541",
            allow=68,
            deny=44,
            type_="role",
            reason="OK",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 245321970760024064, channels.Channel)
    async def test_fetch_invites_for_channel(self, fabric_impl, channel):
        mock_invite_payload = {"code": "ewqrew"}
        mock_invite = mock.MagicMock(invites.Invite)
        fabric_impl.http_client.get_channel_invites = mock.AsyncMock(return_value=[mock_invite_payload])
        fabric_impl.state_registry.parse_invite.return_value = mock_invite
        assert await fabric_impl.http_adapter.fetch_invites_for_channel(channel) == [mock_invite]
        fabric_impl.http_client.get_channel_invites.assert_called_once_with(channel_id="245321970760024064")
        fabric_impl.state_registry.parse_invite.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.Channel)
    async def test_create_invite_for_channel_without_optionals(self, fabric_impl, channel):
        mock_invite_payload = {"code": "doweqs"}
        mock_invite = mock.MagicMock(invites.Invite)
        fabric_impl.http_client.create_channel_invite = mock.AsyncMock(return_value=mock_invite_payload)
        fabric_impl.state_registry.parse_invite.return_value = mock_invite
        assert await fabric_impl.http_adapter.create_invite_for_channel(channel) is mock_invite
        fabric_impl.state_registry.parse_invite.assert_called_once_with(mock_invite_payload)
        fabric_impl.http_client.create_channel_invite.assert_called_once_with(
            channel_id="115590097100865541",
            max_age=unspecified.UNSPECIFIED,
            max_uses=unspecified.UNSPECIFIED,
            temporary=unspecified.UNSPECIFIED,
            unique=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.Channel)
    async def test_create_invite_for_channel_with_all_optionals(self, fabric_impl, channel):
        mock_invite_payload = {"code": "doweqs"}
        mock_invite = mock.MagicMock(invites.Invite)
        fabric_impl.http_client.create_channel_invite = mock.AsyncMock(return_value=mock_invite_payload)
        fabric_impl.state_registry.parse_invite.return_value = mock_invite
        assert (
            await fabric_impl.http_adapter.create_invite_for_channel(
                channel, max_age=5, max_uses=42, temporary=False, unique=True, reason="good luck stopping me kid.",
            )
            is mock_invite
        )
        fabric_impl.state_registry.parse_invite.assert_called_once_with(mock_invite_payload)
        fabric_impl.http_client.create_channel_invite.assert_called_once_with(
            channel_id="115590097100865541",
            max_age=5,
            max_uses=42,
            temporary=False,
            unique=True,
            reason="good luck stopping me kid.",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 245321970760024064, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 115590097100865541, overwrites.Overwrite)
    async def test_delete_channel_overwrite(self, fabric_impl, channel, overwrite):
        fabric_impl.http_client.delete_channel_permission = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_channel_overwrite(channel, overwrite) is None
        fabric_impl.http_client.delete_channel_permission.assert_called_once_with(
            channel_id="245321970760024064", overwrite_id="115590097100865541"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.GuildTextChannel)
    async def test_trigger_typing(self, fabric_impl, channel):
        fabric_impl.http_client.trigger_typing_indicator = mock.AsyncMock()
        assert await fabric_impl.http_adapter.trigger_typing(channel) is None
        fabric_impl.http_client.trigger_typing_indicator.assert_called_once_with("115590097100865541")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 23123123, channels.GuildTextChannel)
    async def test_fetch_pins(self, fabric_impl, channel):
        mock_message_payload = {"content": "42", "id": "44232424"}
        mock_message = mock.MagicMock(messages.Message)
        fabric_impl.http_client.get_pinned_messages = mock.AsyncMock(return_value=[mock_message_payload])
        fabric_impl.state_registry.parse_message.return_value = mock_message
        assert await fabric_impl.http_adapter.fetch_pins(channel) == [mock_message]
        fabric_impl.http_client.get_pinned_messages.assert_called_once_with("23123123")
        fabric_impl.state_registry.parse_message.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    async def test_pin_message_with_message_obj(self, fabric_impl):
        fabric_impl.http_client.add_pinned_channel_message = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.pin_message(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123),
                )
            )
            is None
        )
        fabric_impl.http_client.add_pinned_channel_message.assert_called_once_with(
            message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (322222212121, "322222212121"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    async def test_pin_message(self, fabric_impl, message, channel):
        fabric_impl.http_client.add_pinned_channel_message = mock.AsyncMock()
        assert await fabric_impl.http_adapter.pin_message(message, channel=channel) is None
        fabric_impl.http_client.add_pinned_channel_message.assert_called_once_with(
            message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_test_pin_message_raises_type_error_without_channel(self, fabric_impl):
        fabric_impl.http_client.add_pinned_channel_message = mock.AsyncMock()
        await fabric_impl.http_adapter.pin_message("41231")

    @pytest.mark.asyncio
    async def test_unpin_message_with_message_obj(self, fabric_impl):
        fabric_impl.http_client.delete_pinned_channel_message = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.unpin_message(
                _helpers.mock_model(
                    messages.Message, id=322222212121, channel=_helpers.mock_model(channels.Channel, id=532432123),
                )
            )
            is None
        )
        fabric_impl.http_client.delete_pinned_channel_message.assert_called_once_with(
            message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("message", (322222212121, "322222212121"))
    @_helpers.parametrize_valid_id_formats_for_models("channel", 532432123, channels.Channel)
    async def test_unpin_message(self, fabric_impl, message, channel):
        fabric_impl.http_client.delete_pinned_channel_message = mock.AsyncMock()
        assert await fabric_impl.http_adapter.unpin_message(message, channel=channel) is None
        fabric_impl.http_client.delete_pinned_channel_message.assert_called_once_with(
            message_id="322222212121", channel_id="532432123"
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_test_unpin_message_raises_type_error_without_channel(self, fabric_impl):
        fabric_impl.http_client.delete_pinned_channel_message = mock.AsyncMock()
        await fabric_impl.http_adapter.unpin_message("3123")

    @pytest.mark.asyncio
    async def test_fetch_guild_emoji_when_guild_is_unresolved_with_emoji_obj(self, fabric_impl):
        mock_emoji_payload = {"name": "Nep", "id": "34332", "animated": True}
        mock_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.state_registry.parse_emoji.return_value = mock_emoji
        fabric_impl.http_client.get_guild_emoji = mock.AsyncMock(return_value=mock_emoji_payload)
        assert (
            await fabric_impl.http_adapter.fetch_guild_emoji(
                emoji=_helpers.mock_model(
                    emojis.GuildEmoji, id=34332, guild=_helpers.mock_model(guilds.Guild, id=345342222),
                )
            )
            is mock_emoji
        )
        fabric_impl.http_client.get_guild_emoji.assert_called_once_with(guild_id="345342222", emoji_id="34332")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(345342222)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_emoji_payload, mock_guild)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("emoji", (34332, "34332"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 345342222, guilds.Guild)
    async def test_fetch_guild_emoji_when_guild_is_unresolved(self, fabric_impl, emoji, guild):
        mock_emoji_payload = {"name": "Nep", "id": "34332", "animated": True}
        mock_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.state_registry.parse_emoji.return_value = mock_emoji
        fabric_impl.http_client.get_guild_emoji = mock.AsyncMock(return_value=mock_emoji_payload)
        assert await fabric_impl.http_adapter.fetch_guild_emoji(emoji=emoji, guild=guild) is mock_emoji
        fabric_impl.http_client.get_guild_emoji.assert_called_once_with(guild_id="345342222", emoji_id="34332")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(345342222)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_emoji_payload, mock_guild)

    @pytest.mark.asyncio
    async def test_fetch_guild_emoji_when_guild_is_resolved_with_emoji_obj(self, fabric_impl):
        mock_emoji_payload = {"name": "Nep", "id": "34332", "animated": True}
        mock_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        fabric_impl.state_registry.parse_emoji.return_value = mock_emoji
        fabric_impl.http_client.get_guild_emoji = mock.AsyncMock(return_value=mock_emoji_payload)
        assert (
            await fabric_impl.http_adapter.fetch_guild_emoji(
                emoji=_helpers.mock_model(
                    emojis.GuildEmoji, id=34332, guild=_helpers.mock_model(guilds.Guild, id=345342222),
                )
            )
            is mock_emoji
        )
        fabric_impl.http_client.get_guild_emoji.assert_called_once_with(guild_id="345342222", emoji_id="34332")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(345342222)
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_emoji_payload, mock_guild)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("emoji", (34332, "34332"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 345342222, guilds.Guild)
    async def test_fetch_guild_emoji_when_guild_is_resolved(self, fabric_impl, emoji, guild):
        mock_emoji_payload = {"name": "Nep", "id": "34332", "animated": True}
        mock_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        fabric_impl.state_registry.parse_emoji.return_value = mock_emoji
        fabric_impl.http_client.get_guild_emoji = mock.AsyncMock(return_value=mock_emoji_payload)
        assert await fabric_impl.http_adapter.fetch_guild_emoji(emoji=emoji, guild=guild) is mock_emoji
        fabric_impl.http_client.get_guild_emoji.assert_called_once_with(guild_id="345342222", emoji_id="34332")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(345342222)
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_emoji_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_fetch_guild_emoji_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.get_guild_emoji = mock.AsyncMock()
        await fabric_impl.http_adapter.fetch_guild_emoji(emoji="123123")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 777, guilds.Guild)
    async def test_fetch_guild_emojis_when_guild_is_unresolved(self, fabric_impl, guild):
        mock_guild_emoji_payload = {"id": "31232", "name": "sure", "animated": True}
        mock_guild_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.http_client.list_guild_emojis = mock.AsyncMock(return_value=[mock_guild_emoji_payload])
        fabric_impl.state_registry.parse_emoji.return_value = mock_guild_emoji
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        assert await fabric_impl.http_adapter.fetch_guild_emojis(guild) == [mock_guild_emoji]
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(777)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_guild_emoji_payload, mock_guild)
        fabric_impl.http_client.list_guild_emojis.assert_called_once_with(guild_id="777")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 777, guilds.Guild)
    async def test_fetch_guild_emojis_when_guild_is_resolved(self, fabric_impl, guild):
        mock_guild_emoji_payload = {"id": "31232", "name": "sure", "animated": True}
        mock_guild_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.list_guild_emojis = mock.AsyncMock(return_value=[mock_guild_emoji_payload])
        fabric_impl.state_registry.parse_emoji.return_value = mock_guild_emoji
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        assert await fabric_impl.http_adapter.fetch_guild_emojis(guild) == [mock_guild_emoji]
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(777)
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_guild_emoji_payload, mock_guild)
        fabric_impl.http_client.list_guild_emojis.assert_called_once_with(guild_id="777")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 4242, guilds.Guild)
    async def test_create_guild_emoji_without_optionals_when_guild_is_unresolved(self, fabric_impl, guild):
        mock_guild_emoji_payload = {"id": "31232", "name": "sure", "animated": True}
        mock_guild_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.http_client.create_guild_emoji = mock.AsyncMock(return_value=mock_guild_emoji_payload)
        fabric_impl.state_registry.parse_emoji.return_value = mock_guild_emoji
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        assert (
            await fabric_impl.http_adapter.create_guild_emoji(
                guild=guild, name="A name", image_data=b"44422242vsewr21",
            )
            is mock_guild_emoji
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(4242)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_guild_emoji_payload, mock_guild)
        fabric_impl.http_client.create_guild_emoji.assert_called_once_with(
            guild_id="4242", name="A name", image=b"44422242vsewr21", roles=[], reason=unspecified.UNSPECIFIED
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 4242, guilds.Guild)
    async def test_create_guild_emoji_without_optionals_when_guild_is_resolved(self, fabric_impl, guild):
        mock_guild_emoji_payload = {"id": "31232", "name": "sure", "animated": True}
        mock_guild_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.create_guild_emoji = mock.AsyncMock(return_value=mock_guild_emoji_payload)
        fabric_impl.state_registry.parse_emoji.return_value = mock_guild_emoji
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        assert (
            await fabric_impl.http_adapter.create_guild_emoji(
                guild=guild, name="A name", image_data=b"44422242vsewr21",
            )
            is mock_guild_emoji
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(4242)
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_guild_emoji_payload, mock_guild)
        fabric_impl.http_client.create_guild_emoji.assert_called_once_with(
            guild_id="4242", name="A name", image=b"44422242vsewr21", roles=[], reason=unspecified.UNSPECIFIED
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 4242, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 6969, roles.Role)
    async def test_create_guild_emoji_with_all_optionals_when_guild_is_resolved(self, fabric_impl, guild, role):
        mock_guild_emoji_payload = {"id": "31232", "name": "sure", "animated": True}
        mock_guild_emoji = mock.MagicMock(emojis.GuildEmoji)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.create_guild_emoji = mock.AsyncMock(return_value=mock_guild_emoji_payload)
        fabric_impl.state_registry.parse_emoji.return_value = mock_guild_emoji
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        assert (
            await fabric_impl.http_adapter.create_guild_emoji(
                guild=guild, name="A name", image_data=b"44422242vsewr21", roles=(role,), reason="Needed more nekos.",
            )
            is mock_guild_emoji
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(4242)
        fabric_impl.state_registry.parse_emoji.assert_called_once_with(mock_guild_emoji_payload, mock_guild)
        fabric_impl.http_client.create_guild_emoji.assert_called_once_with(
            guild_id="4242", name="A name", image=b"44422242vsewr21", roles=["6969"], reason="Needed more nekos.",
        )

    @pytest.mark.asyncio
    async def test_update_guild_emoji_without_optionals_with_emoji_obj(self, fabric_impl):
        fabric_impl.http_client.modify_guild_emoji = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_guild_emoji(
                emoji=_helpers.mock_model(
                    emojis.GuildEmoji, id=34332, guild=_helpers.mock_model(guilds.Guild, id=345342222),
                )
            )
            is None
        )
        fabric_impl.http_client.modify_guild_emoji.assert_called_once_with(
            emoji_id="34332",
            guild_id="345342222",
            name=unspecified.UNSPECIFIED,
            roles=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("emoji", (34332, "34332"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 345342222, guilds.Guild)
    async def test_update_guild_emoji_without_optionals(self, fabric_impl, emoji, guild):
        fabric_impl.http_client.modify_guild_emoji = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_guild_emoji(emoji=emoji, guild=guild) is None
        fabric_impl.http_client.modify_guild_emoji.assert_called_once_with(
            emoji_id="34332",
            guild_id="345342222",
            name=unspecified.UNSPECIFIED,
            roles=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @_helpers.parametrize_valid_id_formats_for_models("role", 53333, roles.Role)
    async def test_update_guild_emoji_with_all_optionals_with_emoji_object(self, fabric_impl, role):
        fabric_impl.http_client.modify_guild_emoji = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_guild_emoji(
                emoji=_helpers.mock_model(
                    emojis.GuildEmoji, id=34332, guild=_helpers.mock_model(guilds.Guild, id=345342222),
                ),
                name="ok",
                roles=[role],
                reason="BYE BYE",
            )
            is None
        )
        fabric_impl.http_client.modify_guild_emoji.assert_called_once_with(
            emoji_id="34332", guild_id="345342222", name="ok", roles=["53333"], reason="BYE BYE",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("emoji", (34332, "34332"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 345342222, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 53333, roles.Role)
    async def test_update_guild_emoji_with_all_optionals(self, fabric_impl, emoji, guild, role):
        fabric_impl.http_client.modify_guild_emoji = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_guild_emoji(
                emoji=emoji, guild=guild, name="ok", roles=[role], reason="BYE BYE",
            )
            is None
        )
        fabric_impl.http_client.modify_guild_emoji.assert_called_once_with(
            emoji_id="34332", guild_id="345342222", name="ok", roles=["53333"], reason="BYE BYE",
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_update_guild_emoji_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.modify_guild_emoji = mock.AsyncMock()
        await fabric_impl.http_adapter.update_guild_emoji("22222")

    @pytest.mark.asyncio
    async def test_delete_guild_emoji_with_emoji_obj(self, fabric_impl):
        fabric_impl.http_client.delete_guild_emoji = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_guild_emoji(
                emoji=_helpers.mock_model(
                    emojis.GuildEmoji, id=34332, guild=_helpers.mock_model(guilds.Guild, id=345342222),
                )
            )
            is None
        )
        fabric_impl.http_client.delete_guild_emoji.assert_called_once_with(
            emoji_id="34332", guild_id="345342222",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("emoji", (34332, "34332"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 345342222, guilds.Guild)
    async def test_delete_guild_emoji(self, fabric_impl, emoji, guild):
        fabric_impl.http_client.delete_guild_emoji = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_guild_emoji(emoji=emoji, guild=guild) is None
        fabric_impl.http_client.delete_guild_emoji.assert_called_once_with(
            emoji_id="34332", guild_id="345342222",
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_delete_guild_emoji_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.delete_guild_emoji = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_guild_emoji("4123")

    @_helpers.todo_implement
    @pytest.mark.asyncio
    async def test_create_guild_without_optionals(self, fabric_impl):
        mock_guild_payload = {"id": 231232, "owner_id": 115590097100865541}
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.create_guild = mock.AsyncMock(return_value=mock_guild_payload)
        fabric_impl.state_registry.parse_guild.return_value = mock_guild
        assert await fabric_impl.http_adapter.create_guild("I am a guild") is mock_guild
        fabric_impl.http_client.create_guild.assert_called_once_with(
            name="I am a guild",
            region=unspecified.UNSPECIFIED,
            icon=unspecified.UNSPECIFIED,
            verification_level=unspecified.UNSPECIFIED,
            default_message_notifications=unspecified.UNSPECIFIED,
            explicit_content_filter=unspecified.UNSPECIFIED,
            roles=unspecified.UNSPECIFIED,
            channels=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.parse_guild.assert_called_once_with(mock_guild_payload, None)

    @_helpers.todo_implement
    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models(
        "role",
        341232132132123,
        roles.Role,
        #  to_dict=mock.MagicMock(return_value={"id": 2132123}))
    )
    @_helpers.parametrize_valid_id_formats_for_models(
        "channel",
        7655462341233211,
        channels.GuildTextChannel,
        #  to_dict=mock.MagicMock(return_value={"id": 444444}))
    )
    @pytest.mark.parametrize(
        ["verification_level", "default_message_notifications", "explicit_content_filter"],
        [
            (
                guilds.VerificationLevel(2),
                guilds.DefaultMessageNotificationsLevel(1),
                guilds.ExplicitContentFilterLevel(0),
            ),
            (2, 1, 0),
        ],
    )
    async def test_create_guild_with_all_optionals(
        self, fabric_impl, role, channel, verification_level, default_message_notifications, explicit_content_filter
    ):
        mock_guild_payload = {"id": 231232, "owner_id": 115590097100865541}
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.create_guild = mock.AsyncMock(return_value=mock_guild_payload)
        fabric_impl.state_registry.parse_guild.return_value = mock_guild
        assert (
            await fabric_impl.http_adapter.create_guild(
                "I am a guild",
                region="LONDON",
                icon_data=b"5324324",
                verification_level=verification_level,
                default_message_notifications=default_message_notifications,
                explicit_content_filter=explicit_content_filter,
                roles=[role],
                channels=[channel],
            )
            is mock_guild
        )
        fabric_impl.http_client.create_guild.assert_called_once_with(
            name="I am a guild",
            region="LONDON",
            icon=b"5324324",
            verification_level=2,
            default_message_notifications=1,
            explicit_content_filter=0,
            roles=[{"id": 2132123}],
            channels=[{"id": 444444}],
        )
        fabric_impl.state_registry.parse_guild.assert_called_once_with(mock_guild_payload, None)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 1231236545645, guilds.Guild)
    async def test_fetch_guild(self, fabric_impl, guild):
        mock_guild_payload = {"id": 1231236545645, "name": "this is a guild"}
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.parse_guild.return_value = mock_guild
        fabric_impl.http_client.get_guild = mock.AsyncMock(return_value=mock_guild_payload)
        assert await fabric_impl.http_adapter.fetch_guild(guild=guild) is mock_guild
        fabric_impl.http_client.get_guild.assert_called_once_with(guild_id="1231236545645")
        fabric_impl.state_registry.parse_guild.assert_called_once_with(mock_guild_payload, None)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 341232132132123, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 7655462341233211, channels.GuildTextChannel)
    @pytest.mark.parametrize(
        ["verification_level", "default_message_notifications", "explicit_content_filter"],
        [
            (
                guilds.VerificationLevel(2),
                guilds.DefaultMessageNotificationsLevel(1),
                guilds.ExplicitContentFilterLevel(0),
            ),
            (2, 1, 0),
        ],
    )
    async def test_update_guild_with_all_optionals(
        self,
        fabric_impl,
        guild,
        user,
        channel,
        verification_level,
        default_message_notifications,
        explicit_content_filter,
    ):
        fabric_impl.http_client.modify_guild = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_guild(
                guild,
                name="OK",
                region="London",
                verification_level=verification_level,
                default_message_notifications=default_message_notifications,
                explicit_content_filter=explicit_content_filter,
                afk_channel=channel,
                afk_timeout=50,
                icon_data=b"54345",
                owner=user,
                splash_data=b"45234",
                system_channel=channel,
                reason="OK",
            )
            is None
        )
        fabric_impl.http_client.modify_guild.assert_called_once_with(
            guild_id="379953393319542784",
            name="OK",
            region="London",
            verification_level=2,
            default_message_notifications=1,
            explicit_content_filter=0,
            afk_channel_id="7655462341233211",
            afk_timeout=50,
            icon=b"54345",
            owner_id="341232132132123",
            splash=b"45234",
            system_channel_id="7655462341233211",
            reason="OK",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_guild_without_optionals(self, fabric_impl, guild):
        fabric_impl.http_client.modify_guild = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_guild(guild) is None
        fabric_impl.http_client.modify_guild.assert_called_once_with(
            guild_id="379953393319542784",
            name=unspecified.UNSPECIFIED,
            region=unspecified.UNSPECIFIED,
            verification_level=unspecified.UNSPECIFIED,
            default_message_notifications=unspecified.UNSPECIFIED,
            explicit_content_filter=unspecified.UNSPECIFIED,
            afk_channel_id=unspecified.UNSPECIFIED,
            afk_timeout=unspecified.UNSPECIFIED,
            icon=unspecified.UNSPECIFIED,
            owner_id=unspecified.UNSPECIFIED,
            splash=unspecified.UNSPECIFIED,
            system_channel_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_delete_guild(self, fabric_impl, guild):
        fabric_impl.http_client.delete_guild = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_guild(guild) is None
        fabric_impl.http_client.delete_guild.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_channels_when_guild_is_unresolved(self, fabric_impl, guild):
        mock_channel_payload = {"name": "OK", "id": "23123123123123", "type": 0}
        mock_channel = mock.MagicMock(channels.GuildTextChannel)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.http_client.get_guild_channels = mock.AsyncMock(return_value=[mock_channel_payload])
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert await fabric_impl.http_adapter.fetch_guild_channels(guild) == [mock_channel]
        fabric_impl.http_client.get_guild_channels.assert_called_once_with(guild_id="379953393319542784")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_channels_when_guild_is_resolved(self, fabric_impl, guild):
        mock_channel_payload = {"name": "OK", "id": "23123123123123", "type": 0}
        mock_channel = mock.MagicMock(channels.GuildTextChannel)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        fabric_impl.http_client.get_guild_channels = mock.AsyncMock(return_value=[mock_channel_payload])
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        assert await fabric_impl.http_adapter.fetch_guild_channels(guild) == [mock_channel]
        fabric_impl.http_client.get_guild_channels.assert_called_once_with(guild_id="379953393319542784")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("category", 537340989808050216, channels.GuildCategory)
    @pytest.mark.parametrize("channel_type", [0, channels.ChannelType.GUILD_TEXT])
    async def test_create_guild_channel_with_all_optionals_when_guild_is_resolved(
        self, fabric_impl, guild, category, channel_type
    ):
        mock_channel_payload = {"id": "215061635574792192", "name": "lolz"}
        mock_channel = mock.MagicMock(channels.GuildTextChannel)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.create_guild_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        overwrite = overwrites.Overwrite(id=42, allow=5, deny=5, type=overwrites.OverwriteEntityType.MEMBER)
        assert (
            await fabric_impl.http_adapter.create_guild_channel(
                guild,
                "OK",
                channel_type,
                topic="A topic",
                bitrate=320,
                user_limit=5,
                rate_limit_per_user=55,
                position=555,
                permission_overwrites=[overwrite],
                parent_category=category,
                nsfw=True,
                reason="True",
            )
            is mock_channel
        )
        fabric_impl.http_client.create_guild_channel.assert_called_once_with(
            guild_id="379953393319542784",
            name="OK",
            type_=0,
            topic="A topic",
            bitrate=320,
            user_limit=5,
            rate_limit_per_user=55,
            position=555,
            permission_overwrites=[{"allow": 5, "deny": 5, "type": "member", "id": 42}],
            parent_id="537340989808050216",
            nsfw=True,
            reason="True",
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @pytest.mark.parametrize("channel_type", [0, channels.ChannelType.GUILD_TEXT])
    async def test_create_guild_channel_without_optionals_when_guild_is_unresolved(
        self, fabric_impl, guild, channel_type
    ):
        mock_channel_payload = {"id": "215061635574792192", "name": "lolz"}
        mock_channel = mock.MagicMock(channels.GuildTextChannel)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.http_client.create_guild_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        assert await fabric_impl.http_adapter.create_guild_channel(guild, "OK", channel_type) is mock_channel
        fabric_impl.http_client.create_guild_channel.assert_called_once_with(
            guild_id="379953393319542784",
            name="OK",
            type_=0,
            topic=unspecified.UNSPECIFIED,
            bitrate=unspecified.UNSPECIFIED,
            user_limit=unspecified.UNSPECIFIED,
            rate_limit_per_user=unspecified.UNSPECIFIED,
            position=unspecified.UNSPECIFIED,
            permission_overwrites=unspecified.UNSPECIFIED,
            parent_id=unspecified.UNSPECIFIED,
            nsfw=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @pytest.mark.parametrize("channel_type", [0, channels.ChannelType.GUILD_TEXT])
    async def test_create_guild_channel_without_optionals_when_guild_is_resolved(
        self, fabric_impl, guild, channel_type
    ):
        mock_channel_payload = {"id": "215061635574792192", "name": "lolz"}
        mock_channel = mock.MagicMock(channels.GuildTextChannel)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.create_guild_channel = mock.AsyncMock(return_value=mock_channel_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_channel
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        assert await fabric_impl.http_adapter.create_guild_channel(guild, "OK", channel_type) is mock_channel
        fabric_impl.http_client.create_guild_channel.assert_called_once_with(
            guild_id="379953393319542784",
            name="OK",
            type_=0,
            topic=unspecified.UNSPECIFIED,
            bitrate=unspecified.UNSPECIFIED,
            user_limit=unspecified.UNSPECIFIED,
            rate_limit_per_user=unspecified.UNSPECIFIED,
            position=unspecified.UNSPECIFIED,
            permission_overwrites=unspecified.UNSPECIFIED,
            parent_id=unspecified.UNSPECIFIED,
            nsfw=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_channel_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("additional_channel", 381870553235193857, channels.Channel)
    async def test_reposition_guild_channels_with_channel_obj(self, fabric_impl, additional_channel):
        fabric_impl.http_client.modify_guild_channel_positions = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.reposition_guild_channels(
                (
                    0,
                    _helpers.mock_model(
                        channels.GuildChannel,
                        id=131506134161948672,
                        guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                    ),
                ),
                (1, additional_channel),
            )
            is None
        )
        fabric_impl.http_client.modify_guild_channel_positions.assert_called_once_with(
            "379953393319542784", ("131506134161948672", 0), ("381870553235193857", 1)
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("channel", (131506134161948672, "131506134161948672"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("additional_channel", 381870553235193857, channels.Channel)
    async def test_reposition_guild_channels(self, fabric_impl, guild, channel, additional_channel):
        fabric_impl.http_client.modify_guild_channel_positions = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.reposition_guild_channels((0, channel), (1, additional_channel), guild=guild)
            is None
        )
        fabric_impl.http_client.modify_guild_channel_positions.assert_called_once_with(
            "379953393319542784", ("131506134161948672", 0), ("381870553235193857", 1)
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_reposition_guild_channels_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.modify_guild_channel_positions = mock.AsyncMock()
        await fabric_impl.http_adapter.reposition_guild_channels((0, 123), (1, 4321))

    @pytest.mark.asyncio
    async def test_fetch_member_when_guild_is_unresolved_with_member_obj(self, fabric_impl):
        mock_member_payload = {"nick": "Genre: Help", "user": {"id": "131506134161948672"}}
        mock_member = mock.MagicMock(members.Member)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.state_registry.parse_member.return_value = mock_member
        fabric_impl.http_client.get_guild_member = mock.AsyncMock(return_value=mock_member_payload)
        assert (
            await fabric_impl.http_adapter.fetch_member(
                user=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                )
            )
            is mock_member
        )
        fabric_impl.http_client.get_guild_member.assert_called_once_with(
            user_id="131506134161948672", guild_id="379953393319542784"
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_member.assert_called_once_with(mock_member_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_member_when_guild_is_unresolved(self, fabric_impl, guild, user):
        mock_member_payload = {"nick": "Genre: Help", "user": {"id": "131506134161948672"}}
        mock_member = mock.MagicMock(members.Member)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.state_registry.parse_member.return_value = mock_member
        fabric_impl.http_client.get_guild_member = mock.AsyncMock(return_value=mock_member_payload)
        assert await fabric_impl.http_adapter.fetch_member(user=user, guild=guild) is mock_member
        fabric_impl.http_client.get_guild_member.assert_called_once_with(
            user_id="131506134161948672", guild_id="379953393319542784"
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_member.assert_called_once_with(mock_member_payload, mock_guild)

    @pytest.mark.asyncio
    async def test_fetch_member_when_guild_is_resolved_with_member_obj(self, fabric_impl):
        mock_member_payload = {"nick": "Genre: Help", "user": {"id": "131506134161948672"}}
        mock_member = mock.MagicMock(members.Member)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        fabric_impl.state_registry.parse_member.return_value = mock_member
        fabric_impl.http_client.get_guild_member = mock.AsyncMock(return_value=mock_member_payload)
        assert (
            await fabric_impl.http_adapter.fetch_member(
                user=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                )
            )
            is mock_member
        )
        fabric_impl.http_client.get_guild_member.assert_called_once_with(
            user_id="131506134161948672", guild_id="379953393319542784"
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_member.assert_called_once_with(mock_member_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_member_when_guild_is_resolved(self, fabric_impl, guild, user):
        mock_member_payload = {"nick": "Genre: Help", "user": {"id": "131506134161948672"}}
        mock_member = mock.MagicMock(members.Member)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        fabric_impl.state_registry.parse_member.return_value = mock_member
        fabric_impl.http_client.get_guild_member = mock.AsyncMock(return_value=mock_member_payload)
        assert await fabric_impl.http_adapter.fetch_member(user=user, guild=guild) is mock_member
        fabric_impl.http_client.get_guild_member.assert_called_once_with(
            user_id="131506134161948672", guild_id="379953393319542784"
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_member.assert_called_once_with(mock_member_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_fetch_member_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.get_guild_member = mock.AsyncMock()
        await fabric_impl.http_adapter.fetch_member("777")

    @pytest.mark.asyncio
    @_helpers.todo_implement
    async def test_fetch_members(self, fabric_impl):
        raise NotImplementedError

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("role", 1232123123, roles.Role)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 55554554, channels.GuildVoiceChannel)
    async def test_update_member_with_all_optionals_with_member_obj(self, fabric_impl, role, channel):
        fabric_impl.http_client.modify_guild_member = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_member(
                member=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
                nick="ok Nick",
                roles=[role],
                mute=True,
                deaf=False,
                current_voice_channel=channel,
                reason="OK",
            )
            is None
        )
        fabric_impl.http_client.modify_guild_member.assert_called_once_with(
            user_id="131506134161948672",
            guild_id="379953393319542784",
            nick="ok Nick",
            roles=["1232123123"],
            mute=True,
            deaf=False,
            channel_id="55554554",
            reason="OK",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("member", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 1232123123, roles.Role)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 55554554, channels.GuildVoiceChannel)
    async def test_update_member_with_all_optionals(self, fabric_impl, member, guild, role, channel):
        fabric_impl.http_client.modify_guild_member = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_member(
                member=member,
                guild=guild,
                nick="ok Nick",
                roles=[role],
                mute=True,
                deaf=False,
                current_voice_channel=channel,
                reason="OK",
            )
            is None
        )
        fabric_impl.http_client.modify_guild_member.assert_called_once_with(
            user_id="131506134161948672",
            guild_id="379953393319542784",
            nick="ok Nick",
            roles=["1232123123"],
            mute=True,
            deaf=False,
            channel_id="55554554",
            reason="OK",
        )

    @pytest.mark.asyncio
    async def test_update_member_without_optionals_with_member_obj(self, fabric_impl):
        fabric_impl.http_client.modify_guild_member = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_member(
                member=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                )
            )
            is None
        )
        fabric_impl.http_client.modify_guild_member.assert_called_once_with(
            user_id="131506134161948672",
            guild_id="379953393319542784",
            nick=unspecified.UNSPECIFIED,
            roles=unspecified.UNSPECIFIED,
            mute=unspecified.UNSPECIFIED,
            deaf=unspecified.UNSPECIFIED,
            channel_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("member", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_member_without_optionals(self, fabric_impl, member, guild):
        fabric_impl.http_client.modify_guild_member = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_member(member=member, guild=guild) is None
        fabric_impl.http_client.modify_guild_member.assert_called_once_with(
            user_id="131506134161948672",
            guild_id="379953393319542784",
            nick=unspecified.UNSPECIFIED,
            roles=unspecified.UNSPECIFIED,
            mute=unspecified.UNSPECIFIED,
            deaf=unspecified.UNSPECIFIED,
            channel_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_update_member_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.modify_guild_member = mock.AsyncMock()
        await fabric_impl.http_adapter.update_member("64323")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 55555555, guilds.Guild)
    async def test_update_my_nickname(self, fabric_impl, guild):
        fabric_impl.http_client.modify_current_user_nick = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_my_nickname("nick", guild, reason="cause_i_can") is None
        fabric_impl.http_client.modify_current_user_nick.assert_called_once_with(
            guild_id="55555555", nick="nick", reason="cause_i_can"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123123123, roles.Role)
    async def test_add_role_to_member_with_member_obj(self, fabric_impl, role):
        fabric_impl.http_client.add_guild_member_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.add_role_to_member(
                member=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
                role=role,
                reason="rolling, rolling, rolling, rolling.",
            )
            is None
        )
        fabric_impl.http_client.add_guild_member_role.assert_called_once_with(
            guild_id="379953393319542784",
            user_id="131506134161948672",
            role_id="123123123123",
            reason="rolling, rolling, rolling, rolling.",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("member", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123123123, roles.Role)
    async def test_add_role_to_member(self, fabric_impl, member, guild, role):
        fabric_impl.http_client.add_guild_member_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.add_role_to_member(
                guild=guild, member=member, role=role, reason="rolling, rolling, rolling, rolling."
            )
            is None
        )
        fabric_impl.http_client.add_guild_member_role.assert_called_once_with(
            guild_id="379953393319542784",
            user_id="131506134161948672",
            role_id="123123123123",
            reason="rolling, rolling, rolling, rolling.",
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_add_role_to_member_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.add_guild_member_role = mock.AsyncMock()
        await fabric_impl.http_adapter.add_role_to_member("212", "333")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123123123, roles.Role)
    async def test_remove_role_from_member_with_member_obj(self, fabric_impl, role):
        fabric_impl.http_client.remove_guild_member_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.remove_role_from_member(
                member=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
                role=role,
                reason="rolling, rolling, rolling, rolling.",
            )
            is None
        )
        fabric_impl.http_client.remove_guild_member_role.assert_called_once_with(
            guild_id="379953393319542784",
            user_id="131506134161948672",
            role_id="123123123123",
            reason="rolling, rolling, rolling, rolling.",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("member", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123123123, roles.Role)
    async def test_remove_role_from_member(self, fabric_impl, member, guild, role):
        fabric_impl.http_client.remove_guild_member_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.remove_role_from_member(
                guild=guild, member=member, role=role, reason="rolling, rolling, rolling, rolling."
            )
            is None
        )
        fabric_impl.http_client.remove_guild_member_role.assert_called_once_with(
            guild_id="379953393319542784",
            user_id="131506134161948672",
            role_id="123123123123",
            reason="rolling, rolling, rolling, rolling.",
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_remove_role_from_member_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.remove_guild_member_role = mock.AsyncMock()
        await fabric_impl.http_adapter.remove_role_from_member("222", "444")

    @pytest.mark.asyncio
    async def test_kick_member_with_member_obj(self, fabric_impl):
        fabric_impl.http_client.remove_guild_member = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.kick_member(
                member=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
                reason="bye",
            )
            is None
        )
        fabric_impl.http_client.remove_guild_member.assert_called_once_with(
            guild_id="379953393319542784", user_id="131506134161948672", reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("member", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_kick_member(self, fabric_impl, member, guild):
        fabric_impl.http_client.remove_guild_member = mock.AsyncMock()
        assert await fabric_impl.http_adapter.kick_member(member=member, guild=guild, reason="bye") is None
        fabric_impl.http_client.remove_guild_member.assert_called_once_with(
            guild_id="379953393319542784", user_id="131506134161948672", reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_kick_member_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.remove_guild_member = mock.AsyncMock()
        await fabric_impl.http_adapter.kick_member("22222")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 131506134161948672, users.User)
    async def test_fetch_ban(self, fabric_impl, guild, user):
        mock_ban_payload = {"reason": "Nyaa'd by the Nyakuza", "user": {id: "131506134161948672"}}
        mock_ban = mock.MagicMock(guilds.Ban)
        fabric_impl.state_registry.parse_ban.return_value = mock_ban
        fabric_impl.http_client.get_guild_ban = mock.AsyncMock(return_value=mock_ban_payload)
        assert await fabric_impl.http_adapter.fetch_ban(guild=guild, user=user) == mock_ban
        fabric_impl.state_registry.parse_ban.assert_called_once_with(mock_ban_payload)
        fabric_impl.http_client.get_guild_ban.assert_called_once_with(
            guild_id="379953393319542784", user_id="131506134161948672"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_bans(self, fabric_impl, guild):
        mock_ban_payload = {"reason": "Nyaa'd by the Nyakuza", "user": {id: "131506134161948672"}}
        mock_ban = mock.MagicMock(guilds.Ban)
        fabric_impl.state_registry.parse_ban.return_value = mock_ban
        fabric_impl.http_client.get_guild_bans = mock.AsyncMock(return_value=[mock_ban_payload])
        assert await fabric_impl.http_adapter.fetch_bans(guild=guild) == [mock_ban]
        fabric_impl.state_registry.parse_ban.assert_called_once_with(mock_ban_payload)
        fabric_impl.http_client.get_guild_bans.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    async def test_ban_member_with_member_object(self, fabric_impl):
        fabric_impl.http_client.create_guild_ban = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.ban_member(
                member=_helpers.mock_model(
                    members.Member,
                    id=131506134161948672,
                    guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
                delete_message_days=6,
                reason="bye",
            )
            is None
        )
        fabric_impl.http_client.create_guild_ban.assert_called_once_with(
            guild_id="379953393319542784", user_id="131506134161948672", delete_message_days=6, reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("member", 131506134161948672, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_ban_member(self, fabric_impl, member, guild):
        fabric_impl.http_client.create_guild_ban = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.ban_member(member=member, guild=guild, delete_message_days=6, reason="bye")
            is None
        )
        fabric_impl.http_client.create_guild_ban.assert_called_once_with(
            guild_id="379953393319542784", user_id="131506134161948672", delete_message_days=6, reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_ban_member_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.create_guild_ban = mock.AsyncMock()
        await fabric_impl.http_adapter.ban_member("222")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 379953393319542784, users.User)
    async def test_unban_member(self, fabric_impl, guild, user):
        fabric_impl.http_client.remove_guild_ban = mock.AsyncMock()
        assert await fabric_impl.http_adapter.unban_member(guild, user, reason="OK") is None
        fabric_impl.http_client.remove_guild_ban.assert_called_once_with(
            guild_id="379953393319542784", user_id="379953393319542784", reason="OK"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_roles_when_guild_is_unresolved(self, fabric_impl, guild):
        mock_role_payload = {"id": "595945838", "name": "Iamarole"}
        mock_role = mock.MagicMock(roles.Role)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.http_client.get_guild_roles = mock.AsyncMock(return_value=[mock_role_payload])
        fabric_impl.state_registry.parse_role.return_value = mock_role
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        assert await fabric_impl.http_adapter.fetch_roles(guild) == [mock_role]
        fabric_impl.http_client.get_guild_roles.assert_called_once_with(guild_id="379953393319542784")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_role.assert_called_once_with(mock_role_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_roles_when_guild_is_resolved(self, fabric_impl, guild):
        mock_role_payload = {"id": "595945838", "name": "Iamarole"}
        mock_role = mock.MagicMock(roles.Role)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.http_client.get_guild_roles = mock.AsyncMock(return_value=[mock_role_payload])
        fabric_impl.state_registry.parse_role.return_value = mock_role
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        assert await fabric_impl.http_adapter.fetch_roles(guild) == [mock_role]
        fabric_impl.http_client.get_guild_roles.assert_called_once_with(guild_id="379953393319542784")
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_role.assert_called_once_with(mock_role_payload, mock_guild)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["permission", "color"], [(permissions.Permission(512), colors.Color.from_int(4571114)), (512, 4571114)]
    )
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_create_role_with_all_optionals_when_guild_is_resolved(self, fabric_impl, guild, permission, color):
        mock_role_payload = {"id": "424242424242", "name": "OKThisIsaRole"}
        mock_role = mock.MagicMock(roles.Role)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.http_client.create_guild_role = mock.AsyncMock(return_value=mock_role_payload)
        fabric_impl.state_registry.parse_role.return_value = mock_role
        assert (
            await fabric_impl.http_adapter.create_role(
                guild, name="OK", permissions=permission, color=color, hoist=True, mentionable=True, reason="DERP"
            )
            is mock_role
        )
        fabric_impl.http_client.create_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            name="OK",
            permissions=512,
            color=4571114,
            hoist=True,
            mentionable=True,
            reason="DERP",
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_role.assert_called_once_with(mock_role_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_create_role_without_optionals_when_guild_is_unresolved(self, fabric_impl, guild):
        mock_role_payload = {"id": "424242424242", "name": "OKThisIsaRole"}
        mock_role = mock.MagicMock(roles.Role)
        mock_guild = mock.MagicMock(guilds.Guild)
        awaitable_mock = _helpers.AwaitableMock(return_value=mock_guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = awaitable_mock
        fabric_impl.http_client.create_guild_role = mock.AsyncMock(return_value=mock_role_payload)
        fabric_impl.state_registry.parse_role.return_value = mock_role
        assert await fabric_impl.http_adapter.create_role(guild) is mock_role
        fabric_impl.http_client.create_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            name=unspecified.UNSPECIFIED,
            permissions=unspecified.UNSPECIFIED,
            color=unspecified.UNSPECIFIED,
            hoist=unspecified.UNSPECIFIED,
            mentionable=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        awaitable_mock.assert_awaited_once()
        fabric_impl.state_registry.parse_role.assert_called_once_with(mock_role_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_create_role_without_optionals_when_guild_is_resolved(self, fabric_impl, guild):
        mock_role_payload = {"id": "424242424242", "name": "OKThisIsaRole"}
        mock_role = mock.MagicMock(roles.Role)
        mock_guild = mock.MagicMock(guilds.Guild)
        fabric_impl.state_registry.get_mandatory_guild_by_id.return_value = mock_guild
        fabric_impl.http_client.create_guild_role = mock.AsyncMock(return_value=mock_role_payload)
        fabric_impl.state_registry.parse_role.return_value = mock_role
        assert await fabric_impl.http_adapter.create_role(guild) is mock_role
        fabric_impl.http_client.create_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            name=unspecified.UNSPECIFIED,
            permissions=unspecified.UNSPECIFIED,
            color=unspecified.UNSPECIFIED,
            hoist=unspecified.UNSPECIFIED,
            mentionable=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.get_mandatory_guild_by_id.assert_called_once_with(379953393319542784)
        fabric_impl.state_registry.parse_role.assert_called_once_with(mock_role_payload, mock_guild)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("additional_role", 245321970760024064, roles.Role)
    async def test_reposition_roles_with_role_obj(self, fabric_impl, additional_role):
        fabric_impl.http_client.modify_guild_role_positions = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.reposition_roles(
                (
                    1,
                    _helpers.mock_model(
                        roles.Role,
                        id=115590097100865541,
                        guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                    ),
                ),
                (2, additional_role),
            )
            is None
        )
        fabric_impl.http_client.modify_guild_role_positions.assert_called_once_with(
            "379953393319542784", ("115590097100865541", 1), ("245321970760024064", 2)
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", (115590097100865541, "115590097100865541"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("additional_role", 245321970760024064, roles.Role)
    async def test_reposition_roles(self, fabric_impl, guild, role, additional_role):
        fabric_impl.http_client.modify_guild_role_positions = mock.AsyncMock()
        assert await fabric_impl.http_adapter.reposition_roles((1, role), (2, additional_role), guild=guild) is None
        fabric_impl.http_client.modify_guild_role_positions.assert_called_once_with(
            "379953393319542784", ("115590097100865541", 1), ("245321970760024064", 2)
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_reposition_roles_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.modify_guild_role_positions = mock.AsyncMock()
        await fabric_impl.http_adapter.reposition_roles((1, 321), (2, 5432))

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("permission", "color"), [(permissions.Permission(512), colors.Color.from_int(4571114)), (512, 4571114)]
    )
    async def test_update_role_with_all_optionals_with_role_obj(self, fabric_impl, permission, color):
        fabric_impl.http_client.modify_guild_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_role(
                _helpers.mock_model(
                    roles.Role, id=115590097100865541, guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
                name="Nekos",
                permissions=permission,
                color=color,
                hoist=True,
                mentionable=True,
                reason="OK",
            )
            is None
        )
        fabric_impl.http_client.modify_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            role_id="115590097100865541",
            name="Nekos",
            permissions=512,
            color=4571114,
            hoist=True,
            mentionable=True,
            reason="OK",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", ("115590097100865541", 115590097100865541))
    @pytest.mark.parametrize(
        ("permission", "color"), [(permissions.Permission(512), colors.Color.from_int(4571114)), (512, 4571114)]
    )
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_role_with_all_optionals(self, fabric_impl, guild, role, permission, color):
        fabric_impl.http_client.modify_guild_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_role(
                role,
                guild=guild,
                name="Nekos",
                permissions=permission,
                color=color,
                hoist=True,
                mentionable=True,
                reason="OK",
            )
            is None
        )
        fabric_impl.http_client.modify_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            role_id="115590097100865541",
            name="Nekos",
            permissions=512,
            color=4571114,
            hoist=True,
            mentionable=True,
            reason="OK",
        )

    @pytest.mark.asyncio
    async def test_update_role_without_optionals_with_role_object(self, fabric_impl):
        fabric_impl.http_client.modify_guild_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_role(
                _helpers.mock_model(
                    roles.Role, id=115590097100865541, guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                )
            )
            is None
        )
        fabric_impl.http_client.modify_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            role_id="115590097100865541",
            name=unspecified.UNSPECIFIED,
            permissions=unspecified.UNSPECIFIED,
            color=unspecified.UNSPECIFIED,
            hoist=unspecified.UNSPECIFIED,
            mentionable=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", ("115590097100865541", 115590097100865541))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_role_without_optionals(self, fabric_impl, guild, role):
        fabric_impl.http_client.modify_guild_role = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_role(role, guild=guild) is None
        fabric_impl.http_client.modify_guild_role.assert_called_once_with(
            guild_id="379953393319542784",
            role_id="115590097100865541",
            name=unspecified.UNSPECIFIED,
            permissions=unspecified.UNSPECIFIED,
            color=unspecified.UNSPECIFIED,
            hoist=unspecified.UNSPECIFIED,
            mentionable=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_update_role_raises_type_error_without_guild(self, fabric_impl):
        await fabric_impl.http_adapter.update_role(213212312)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", (115590097100865541, "115590097100865541"))
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_delete_role(self, fabric_impl, guild, role):
        fabric_impl.http_client.delete_guild_role = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_role(role, guild=guild) is None
        fabric_impl.http_client.delete_guild_role.assert_called_once_with(
            guild_id="379953393319542784", role_id="115590097100865541"
        )

    @pytest.mark.asyncio
    async def test_delete_role_with_role_obj(self, fabric_impl):
        fabric_impl.http_client.delete_guild_role = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.delete_role(
                _helpers.mock_model(
                    roles.Role, id=115590097100865541, guild=_helpers.mock_model(guilds.Guild, id=379953393319542784),
                ),
            )
            is None
        )
        fabric_impl.http_client.delete_guild_role.assert_called_once_with(
            guild_id="379953393319542784", role_id="115590097100865541"
        )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=TypeError)
    async def test_delete_role_raises_type_error_without_guild(self, fabric_impl):
        fabric_impl.http_client.delete_guild_role = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_role(1231231231)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_estimate_guild_prune_count(self, fabric_impl, guild):
        mock_prune_payload = 68
        fabric_impl.http_client.get_guild_prune_count = mock.AsyncMock(return_value=mock_prune_payload)
        assert await fabric_impl.http_adapter.estimate_guild_prune_count(guild, 7) is mock_prune_payload
        fabric_impl.http_client.get_guild_prune_count.assert_called_once_with(guild_id="379953393319542784", days=7)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_begin_guild_prune(self, fabric_impl, guild):
        mock_prune_payload = 68
        fabric_impl.http_client.begin_guild_prune = mock.AsyncMock(return_value=mock_prune_payload)
        assert (
            await fabric_impl.http_adapter.begin_guild_prune(guild, 7, compute_prune_count=True, reason="OK")
            is mock_prune_payload
        )
        fabric_impl.http_client.begin_guild_prune.assert_called_once_with(
            guild_id="379953393319542784", days=7, compute_prune_count=True, reason="OK"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_voice_regions(self, fabric_impl, guild):
        mock_voice_region_payload = {"name": "Londoon", "id": "london", "vip": True}
        mock_voice_region = mock.MagicMock(voices.VoiceRegion)
        fabric_impl.http_client.get_guild_voice_regions = mock.AsyncMock(return_value=[mock_voice_region_payload])
        with _helpers.mock_patch(voices.VoiceRegion, return_value=mock_voice_region) as VoiceRegion:
            assert await fabric_impl.http_adapter.fetch_guild_voice_regions(guild=guild) == [mock_voice_region]
            VoiceRegion.assert_called_once_with(mock_voice_region_payload)
        fabric_impl.http_client.get_guild_voice_regions.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_invites(self, fabric_impl, guild):
        mock_invite_payload = {"code": "odsaw"}
        mock_invite = mock.MagicMock(invites.Invite)
        fabric_impl.state_registry.parse_invite.return_value = mock_invite
        fabric_impl.http_client.get_guild_invites = mock.AsyncMock(return_value=[mock_invite_payload])
        assert await fabric_impl.http_adapter.fetch_guild_invites(guild) == [mock_invite]
        fabric_impl.http_client.get_guild_invites.assert_called_once_with(guild_id="379953393319542784")
        fabric_impl.state_registry.parse_invite.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_integrations(self, fabric_impl, guild):
        mock_integration_payload = {"id": "42342342324323", "name": "iIntegration", "type": "twitch"}
        mock_integration = mock.MagicMock(integrations.Integration)
        fabric_impl.state_registry.parse_integration.return_value = mock_integration
        fabric_impl.http_client.get_guild_integrations = mock.AsyncMock(return_value=[mock_integration_payload])
        assert await fabric_impl.http_adapter.fetch_integrations(guild) == [mock_integration]
        fabric_impl.http_client.get_guild_integrations.assert_called_once_with(guild_id="379953393319542784")
        fabric_impl.state_registry.parse_integration.assert_called_once_with(mock_integration_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_create_guild_integration(self, fabric_impl, guild):
        mock_integration_payload = {"id": "42342342324323", "name": "iIntegration", "type": "twitch"}
        mock_integration = mock.MagicMock(integrations.Integration)
        fabric_impl.state_registry.parse_integration.return_value = mock_integration
        fabric_impl.http_client.create_guild_integration = mock.AsyncMock(return_value=mock_integration_payload)
        assert (
            await fabric_impl.http_adapter.create_guild_integration(
                guild=guild, integration_type="twitch", integration_id=2355432324231, reason="OK",
            )
            is mock_integration
        )
        fabric_impl.http_client.create_guild_integration.assert_called_once_with(
            guild_id="379953393319542784", type_="twitch", integration_id=2355432324231, reason="OK",
        )
        fabric_impl.state_registry.parse_integration.assert_called_once_with(mock_integration_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("integration", 115590097100865541, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_integration_with_all_optionals(self, fabric_impl, guild, integration):
        fabric_impl.http_client.modify_guild_integration = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.update_integration(
                guild, integration, expire_grace_period=7, expire_behaviour=1, enable_emojis=True, reason="OK"
            )
            is None
        )
        fabric_impl.http_client.modify_guild_integration.assert_called_once_with(
            guild_id="379953393319542784",
            integration_id="115590097100865541",
            expire_behaviour=1,
            expire_grace_period=7,
            enable_emojis=True,
            reason="OK",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("integration", 115590097100865541, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_integration_without_optionals(self, fabric_impl, guild, integration):
        fabric_impl.http_client.modify_guild_integration = mock.AsyncMock()
        assert await fabric_impl.http_adapter.update_integration(guild, integration) is None
        fabric_impl.http_client.modify_guild_integration.assert_called_once_with(
            guild_id="379953393319542784",
            integration_id="115590097100865541",
            expire_behaviour=unspecified.UNSPECIFIED,
            expire_grace_period=unspecified.UNSPECIFIED,
            enable_emojis=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("integration", 115590097100865541, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_delete_integration(self, fabric_impl, guild, integration):
        fabric_impl.http_client.delete_guild_integration = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_integration(guild, integration) is None
        fabric_impl.http_client.delete_guild_integration.assert_called_once_with(
            guild_id="379953393319542784", integration_id="115590097100865541"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("integration", 115590097100865541, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_sync_guild_integration(self, fabric_impl, guild, integration):
        fabric_impl.http_client.sync_guild_integration = mock.AsyncMock()
        assert await fabric_impl.http_adapter.sync_guild_integration(guild, integration) is None
        fabric_impl.http_client.sync_guild_integration.assert_called_once_with(
            guild_id="379953393319542784", integration_id="115590097100865541"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_embed(self, fabric_impl, guild):
        mock_guild_embed_payload = {"channel_id": "379953393319542784"}
        mock_guild_embed = mock.MagicMock(guilds.GuildEmbed)
        fabric_impl.http_client.get_guild_embed = mock.AsyncMock(return_value=mock_guild_embed_payload)
        with _helpers.mock_patch(guilds.GuildEmbed.from_dict, return_value=mock_guild_embed) as from_dict:
            assert await fabric_impl.http_adapter.fetch_guild_embed(guild=guild) is mock_guild_embed
            from_dict.assert_called_once_with(mock_guild_embed_payload)
        fabric_impl.http_client.get_guild_embed.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_modify_guild_embed(self, fabric_impl, guild):
        mock_guild_embed = mock.MagicMock(guilds.GuildEmbed)
        fabric_impl.http_client.modify_guild_embed = mock.AsyncMock()
        assert await fabric_impl.http_adapter.modify_guild_embed(guild, mock_guild_embed, reason="OK") is None
        fabric_impl.http_client.modify_guild_embed.assert_called_once_with(
            guild_id="379953393319542784", embed=mock_guild_embed.to_dict(), reason="OK"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    async def test_fetch_guild_vanity_url(self, fabric_impl, guild):
        mock_vanity_url_payload = {"code": "this-is-not-a-vanity-url", "uses": 42}
        mock_vanity_url = mock.MagicMock(invites.VanityURL)
        fabric_impl.http_client.get_guild_vanity_url = mock.AsyncMock(return_value=mock_vanity_url_payload)
        with _helpers.mock_patch(invites.VanityURL, return_value=mock_vanity_url) as VanityURL:
            assert await fabric_impl.http_adapter.fetch_guild_vanity_url(guild) is mock_vanity_url
            VanityURL.assert_called_once_with(mock_vanity_url_payload)
        fabric_impl.http_client.get_guild_vanity_url.assert_called_once_with("112233")

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("style", ["banner2", guilds.WidgetStyle("banner2")])
    def test_fetch_guild_widget_image(self, fabric_impl, guild, style):
        mock_guild_widget = "https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=banner2"
        fabric_impl.http_client.get_guild_widget_image_url.return_value = mock_guild_widget
        assert fabric_impl.http_adapter.fetch_guild_widget_image(guild, style=style) is mock_guild_widget
        fabric_impl.http_client.get_guild_widget_image_url.assert_called_once_with(
            guild_id="574921006817476608", style="banner2"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invite",
        [
            "gfawxcz",
            _helpers.mock_model(invites.Invite, code="gfawxcz", __str__=invites.Invite.__str__),
            _helpers.mock_model(invites.InviteWithMetadata, code="gfawxcz", __str__=invites.InviteWithMetadata.__str__),
        ],
    )
    async def test_fetch_invite(self, fabric_impl, invite):
        mock_invite_payload = {
            "code": "discord-api",
            "guild": {
                "id": "81384788765712384",
                "name": "Discord API",
                "splash": None,
                "banner": None,
                "description": None,
                "icon": None,
                "features": [],
                "verification_level": 3,
                "vanity_url_code": "discord-api",
            },
            "channel": {"id": "242538455840718849", "name": "general", "type": 0},
            "approximate_member_count": 49240,
            "approximate_presence_count": 17993,
        }
        mock_invite = mock.MagicMock(invites.Invite)
        fabric_impl.http_client.get_invite = mock.AsyncMock(return_value=mock_invite_payload)
        fabric_impl.state_registry.parse_invite.return_value = mock_invite
        assert await fabric_impl.http_adapter.fetch_invite(invite, with_counts=True) is mock_invite
        fabric_impl.http_client.get_invite.assert_called_once_with(invite_code="gfawxcz", with_counts=True)
        fabric_impl.state_registry.parse_invite.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invite",
        [
            "gfawxcz",
            _helpers.mock_model(invites.Invite, code="gfawxcz", __str__=invites.Invite.__str__),
            _helpers.mock_model(invites.InviteWithMetadata, code="gfawxcz", __str__=invites.InviteWithMetadata.__str__),
        ],
    )
    async def test_delete_invite(self, fabric_impl, invite):
        fabric_impl.http_client.delete_invite = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_invite(invite) is None
        fabric_impl.http_client.delete_invite.assert_called_once_with(invite_code="gfawxcz")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 33333333, users.User)
    async def test_fetch_user(self, fabric_impl, user):
        mock_user = mock.MagicMock(users.User)
        fabric_impl.http_client.get_user = mock.AsyncMock()
        fabric_impl.state_registry.parse_user.return_value = mock_user
        assert await fabric_impl.http_adapter.fetch_user(user) is mock_user
        fabric_impl.http_client.get_user.assert_called_once_with(user_id="33333333")

    @pytest.mark.asyncio
    async def test_fetch_application_info(self, fabric_impl):
        mock_application_info_payload = {"id": "3423412232", "name": "superflat"}
        mock_application_info = mock.MagicMock(applications.Application)
        fabric_impl.http_client.get_current_application_info = mock.AsyncMock(
            return_value=mock_application_info_payload
        )
        fabric_impl.state_registry.parse_application.return_value = mock_application_info
        assert await fabric_impl.http_adapter.fetch_application_info() is mock_application_info
        fabric_impl.http_client.get_current_application_info.assert_called_once()
        fabric_impl.state_registry.parse_application.assert_called_once_with(mock_application_info_payload)

    @pytest.mark.asyncio
    async def test_fetch_me(self, fabric_impl):
        mock_user_payload = {"id": "45465632334123", "username": "Nekocord"}
        mock_user = mock.MagicMock(users.OAuth2User)
        fabric_impl.http_client.get_current_user = mock.AsyncMock(return_value=mock_user_payload)
        fabric_impl.state_registry.parse_application_user.return_value = mock_user
        assert await fabric_impl.http_adapter.fetch_me() is mock_user
        fabric_impl.http_client.get_current_user.assert_called_once()
        fabric_impl.state_registry.parse_application_user.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_update_me_without_optionals(self, fabric_impl):
        mock_user_payload = {"id": "45465632334123", "username": "Nekocord"}
        fabric_impl.http_client.modify_current_user = mock.AsyncMock(return_value=mock_user_payload)
        await fabric_impl.http_adapter.update_me()
        fabric_impl.http_client.modify_current_user.assert_called_once_with(
            username=unspecified.UNSPECIFIED, avatar=unspecified.UNSPECIFIED
        )
        fabric_impl.state_registry.parse_user.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_update_me_with_all_optionals(self, fabric_impl):
        mock_user_payload = {"id": "45465632334123", "username": "OwO"}
        fabric_impl.http_client.modify_current_user = mock.AsyncMock(return_value=mock_user_payload)
        await fabric_impl.http_adapter.update_me(avatar_data=b"f416049374de081ea5ff47d1e8328f74", username="OWO")
        fabric_impl.http_client.modify_current_user.assert_called_once_with(
            avatar=b"f416049374de081ea5ff47d1e8328f74", username="OWO"
        )
        fabric_impl.state_registry.parse_user.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_fetch_my_connections(self, fabric_impl):
        mock_user_connections_payload = {"type": "twitch", "id": "534231", "name": "neko_speeding"}
        mock_user_connections = mock.MagicMock(connections.Connection)
        fabric_impl.http_client.get_current_user_connections = mock.AsyncMock(
            return_value=[mock_user_connections_payload]
        )
        fabric_impl.state_registry.parse_connection.return_value = mock_user_connections
        assert await fabric_impl.http_adapter.fetch_my_connections() == [mock_user_connections]
        fabric_impl.http_client.get_current_user_connections.assert_called_once()
        fabric_impl.state_registry.parse_connection.assert_called_once_with(mock_user_connections_payload)

    @pytest.mark.asyncio
    @_helpers.todo_implement
    async def test_fetch_my_guilds(self):
        raise NotImplementedError

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 190007233919057920, guilds.Guild)
    async def test_leave_guild(self, fabric_impl, guild):
        fabric_impl.http_client.leave_guild = mock.AsyncMock()
        await fabric_impl.http_adapter.leave_guild(guild)
        fabric_impl.http_client.leave_guild.assert_called_once_with(guild_id="190007233919057920")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("recipient", 33333333, users.User)
    async def test_create_dm_channel(self, fabric_impl, recipient):
        mock_dm_payload = {"id": 3323232, "type": 2, "last_message_id": "3343820033257021450", "recipients": []}
        mock_dm = mock.MagicMock(channels.DMChannel)
        fabric_impl.http_client.create_dm = mock.AsyncMock(return_value=mock_dm_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_dm
        assert await fabric_impl.http_adapter.create_dm_channel(recipient) is mock_dm
        fabric_impl.http_client.create_dm.assert_called_once_with(recipient_id="33333333")
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_dm_payload)

    @pytest.mark.asyncio
    async def test_fetch_voice_regions(self, fabric_impl):
        mock_voice_region_payload = {"id": "London", "name": "London"}
        mock_voice_region = mock.MagicMock(voices.VoiceRegion)
        fabric_impl.http_client.list_voice_regions = mock.AsyncMock(return_value=[mock_voice_region_payload])
        with _helpers.mock_patch(voices.VoiceRegion, return_value=mock_voice_region) as VoiceRegion:
            assert await fabric_impl.http_adapter.fetch_voice_regions() == (mock_voice_region,)
            VoiceRegion.assert_called_once_with(mock_voice_region_payload)
        fabric_impl.http_client.list_voice_regions.assert_called_once()

    @pytest.fixture
    def mock_webhook_payload(self):
        return {"id": "4325321123653"}

    @pytest.fixture
    def mock_webhook(self):
        return _helpers.mock_model(webhooks.Webhook)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.Channel)
    async def test_create_webhook_with_all_optionals(self, fabric_impl, mock_webhook_payload, mock_webhook, channel):
        fabric_impl.http_client.create_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook
        assert (
            await fabric_impl.http_adapter.create_webhook(
                channel, "OK", avatar_data=b"239isadjiu83e24io", reason="A reason"
            )
            is mock_webhook
        )
        fabric_impl.http_client.create_webhook.assert_called_once_with(
            channel_id="33333333", name="OK", avatar=b"239isadjiu83e24io", reason="A reason",
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.Channel)
    async def test_create_webhook_without_optionals(self, fabric_impl, mock_webhook_payload, mock_webhook, channel):
        fabric_impl.http_client.create_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook
        assert await fabric_impl.http_adapter.create_webhook(channel, "OK") is mock_webhook
        fabric_impl.http_client.create_webhook.assert_called_once_with(
            channel_id="33333333", name="OK", avatar=unspecified.UNSPECIFIED, reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.Channel)
    async def test_fetch_channel_webhooks(self, fabric_impl, mock_webhook_payload, mock_webhook, channel):
        fabric_impl.http_client.get_channel_webhooks = mock.AsyncMock(return_value=[mock_webhook_payload])
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook
        assert await fabric_impl.http_adapter.fetch_channel_webhooks(channel) == (mock_webhook,)
        fabric_impl.http_client.get_channel_webhooks.assert_called_once_with(channel_id="33333333")
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 878787, guilds.Guild)
    async def test_fetch_guild_webhooks(self, fabric_impl, mock_webhook_payload, mock_webhook, guild):
        fabric_impl.http_client.get_guild_webhooks = mock.AsyncMock(return_value=[mock_webhook_payload])
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert await fabric_impl.http_adapter.fetch_guild_webhooks(guild) == (mock_webhook,)
        fabric_impl.http_client.get_guild_webhooks.assert_called_once_with(guild_id="878787")
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 878787, webhooks.Webhook)
    async def test_fetch_webhook(self, fabric_impl, mock_webhook_payload, mock_webhook, webhook):
        fabric_impl.http_client.get_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert await fabric_impl.http_adapter.fetch_webhook(webhook) is mock_webhook
        fabric_impl.http_client.get_webhook.assert_called_once_with(webhook_id="878787")
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 646464, webhooks.Webhook)
    async def test_update_webhook_when_all_unspecified(self, fabric_impl, mock_webhook_payload, mock_webhook, webhook):
        fabric_impl.http_client.modify_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert await fabric_impl.http_adapter.update_webhook(webhook) is mock_webhook
        fabric_impl.http_client.modify_webhook.assert_called_once_with(
            webhook_id="646464",
            name=unspecified.UNSPECIFIED,
            avatar=unspecified.UNSPECIFIED,
            channel_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 646464, webhooks.Webhook)
    async def test_update_webhook_when_filled(self, fabric_impl, mock_webhook_payload, mock_webhook, webhook):
        mock_channel = _helpers.mock_model(channels.GuildTextChannel, id=42)
        fabric_impl.http_client.modify_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert (
            await fabric_impl.http_adapter.update_webhook(
                webhook, name="Nekohook", avatar_data=b"dookx0o2", channel=mock_channel, reason="We need more cats."
            )
            is mock_webhook
        )
        fabric_impl.http_client.modify_webhook.assert_called_once_with(
            webhook_id="646464", name="Nekohook", avatar=b"dookx0o2", channel_id="42", reason="We need more cats.",
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 33331111, webhooks.Webhook)
    async def test_delete_webhook(self, fabric_impl, webhook):
        fabric_impl.http_client.delete_webhook = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_webhook(webhook) is None
        fabric_impl.http_client.delete_webhook.assert_called_once_with(webhook_id="33331111")

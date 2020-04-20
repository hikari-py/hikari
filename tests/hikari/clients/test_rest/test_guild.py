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
import io

import mock
import pytest

from hikari import audit_logs
from hikari import channels
from hikari import colors
from hikari import emojis
from hikari import files
from hikari import guilds
from hikari import invites
from hikari import permissions
from hikari import users
from hikari import voices
from hikari import webhooks
from hikari.clients.rest import guild as _guild
from hikari.internal import helpers
from hikari.net import rest
from tests.hikari import _helpers


def test__get_member_id():
    member = mock.MagicMock(
        guilds.GuildMember, user=mock.MagicMock(users.User, id=123123123, __int__=users.User.__int__)
    )
    assert _guild._get_member_id(member) == "123123123"


class TestRESTGuildLogic:
    @pytest.fixture()
    def rest_guild_logic_impl(self):
        mock_low_level_restful_client = mock.MagicMock(rest.REST)

        class RESTGuildLogicImpl(_guild.RESTGuildComponent):
            def __init__(self):
                super().__init__(mock_low_level_restful_client)

        return RESTGuildLogicImpl()

    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 22222222, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("before", 123123123123, audit_logs.AuditLogEntry)
    def test_fetch_audit_log_entries_before_with_optionals(self, rest_guild_logic_impl, guild, before, user):
        mock_audit_log_iterator = mock.MagicMock(audit_logs.AuditLogIterator)
        with mock.patch.object(audit_logs, "AuditLogIterator", return_value=mock_audit_log_iterator):
            result = rest_guild_logic_impl.fetch_audit_log_entries_before(
                guild, before=before, user=user, action_type=audit_logs.AuditLogEventType.MEMBER_MOVE, limit=42,
            )
            assert result is mock_audit_log_iterator
            audit_logs.AuditLogIterator.assert_called_once_with(
                guild_id="379953393319542784",
                request=rest_guild_logic_impl._session.get_guild_audit_log,
                before="123123123123",
                user_id="22222222",
                action_type=26,
                limit=42,
            )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    def test_fetch_audit_log_entries_before_without_optionals(self, rest_guild_logic_impl, guild):
        mock_audit_log_iterator = mock.MagicMock(audit_logs.AuditLogIterator)
        with mock.patch.object(audit_logs, "AuditLogIterator", return_value=mock_audit_log_iterator):
            assert rest_guild_logic_impl.fetch_audit_log_entries_before(guild) is mock_audit_log_iterator
            audit_logs.AuditLogIterator.assert_called_once_with(
                guild_id="379953393319542784",
                request=rest_guild_logic_impl._session.get_guild_audit_log,
                before=None,
                user_id=...,
                action_type=...,
                limit=None,
            )

    def test_fetch_audit_log_entries_before_with_datetime_object(self, rest_guild_logic_impl):
        mock_audit_log_iterator = mock.MagicMock(audit_logs.AuditLogIterator)
        with mock.patch.object(audit_logs, "AuditLogIterator", return_value=mock_audit_log_iterator):
            date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
            result = rest_guild_logic_impl.fetch_audit_log_entries_before(123123123, before=date)
            assert result is mock_audit_log_iterator
            audit_logs.AuditLogIterator.assert_called_once_with(
                guild_id="123123123",
                request=rest_guild_logic_impl._session.get_guild_audit_log,
                before="537340988620800000",
                user_id=...,
                action_type=...,
                limit=None,
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 115590097100865541, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("before", 1231231123, audit_logs.AuditLogEntry)
    async def test_fetch_audit_log_with_optionals(self, rest_guild_logic_impl, guild, user, before):
        mock_audit_log_payload = {"entries": [], "integrations": [], "webhooks": [], "users": []}
        mock_audit_log_obj = mock.MagicMock(audit_logs.AuditLog)
        rest_guild_logic_impl._session.get_guild_audit_log.return_value = mock_audit_log_payload
        with mock.patch.object(audit_logs.AuditLog, "deserialize", return_value=mock_audit_log_obj):
            result = await rest_guild_logic_impl.fetch_audit_log(
                guild, user=user, action_type=audit_logs.AuditLogEventType.MEMBER_MOVE, limit=100, before=before,
            )
            assert result is mock_audit_log_obj
            rest_guild_logic_impl._session.get_guild_audit_log.assert_called_once_with(
                guild_id="379953393319542784",
                user_id="115590097100865541",
                action_type=26,
                limit=100,
                before="1231231123",
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_audit_log_without_optionals(self, rest_guild_logic_impl, guild):
        mock_audit_log_payload = {"entries": [], "integrations": [], "webhooks": [], "users": []}
        mock_audit_log_obj = mock.MagicMock(audit_logs.AuditLog)
        rest_guild_logic_impl._session.get_guild_audit_log.return_value = mock_audit_log_payload
        with mock.patch.object(audit_logs.AuditLog, "deserialize", return_value=mock_audit_log_obj):
            assert await rest_guild_logic_impl.fetch_audit_log(guild) is mock_audit_log_obj
            rest_guild_logic_impl._session.get_guild_audit_log.assert_called_once_with(
                guild_id="379953393319542784", user_id=..., action_type=..., limit=..., before=...
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_audit_log_handles_datetime_object(self, rest_guild_logic_impl, guild):
        mock_audit_log_payload = {"entries": [], "integrations": [], "webhooks": [], "users": []}
        mock_audit_log_obj = mock.MagicMock(audit_logs.AuditLog)
        rest_guild_logic_impl._session.get_guild_audit_log.return_value = mock_audit_log_payload
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        with mock.patch.object(audit_logs.AuditLog, "deserialize", return_value=mock_audit_log_obj):
            assert await rest_guild_logic_impl.fetch_audit_log(guild, before=date) is mock_audit_log_obj
            rest_guild_logic_impl._session.get_guild_audit_log.assert_called_once_with(
                guild_id="379953393319542784", user_id=..., action_type=..., limit=..., before="537340988620800000"
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 40404040404, emojis.GuildEmoji)
    async def test_fetch_guild_emoji(self, rest_guild_logic_impl, guild, emoji):
        mock_emoji_payload = {"id": "92929", "name": "nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_guild_logic_impl._session.get_guild_emoji.return_value = mock_emoji_payload
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            assert await rest_guild_logic_impl.fetch_guild_emoji(guild=guild, emoji=emoji) is mock_emoji_obj
            rest_guild_logic_impl._session.get_guild_emoji.assert_called_once_with(
                guild_id="93443949", emoji_id="40404040404",
            )
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    async def test_fetch_guild_emojis(self, rest_guild_logic_impl, guild):
        mock_emoji_payload = {"id": "92929", "name": "nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_guild_logic_impl._session.list_guild_emojis.return_value = [mock_emoji_payload]
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            assert await rest_guild_logic_impl.fetch_guild_emojis(guild=guild) == [mock_emoji_obj]
            rest_guild_logic_impl._session.list_guild_emojis.assert_called_once_with(guild_id="93443949",)
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 537340989808050216, guilds.GuildRole)
    async def test_create_guild_emoji_with_optionals(self, rest_guild_logic_impl, guild, role):
        mock_emoji_payload = {"id": "229292929", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_guild_logic_impl._session.create_guild_emoji.return_value = mock_emoji_payload
        mock_image_data = mock.MagicMock(bytes)
        mock_image_obj = mock.MagicMock(files.File)
        mock_image_obj.read_all = mock.AsyncMock(return_value=mock_image_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj))
        with stack:
            result = await rest_guild_logic_impl.create_guild_emoji(
                guild=guild, name="fairEmoji", image=mock_image_obj, roles=[role], reason="hello",
            )
            assert result is mock_emoji_obj
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)
            mock_image_obj.read_all.assert_awaited_once()
        rest_guild_logic_impl._session.create_guild_emoji.assert_called_once_with(
            guild_id="93443949", name="fairEmoji", image=mock_image_data, roles=["537340989808050216"], reason="hello",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    async def test_create_guild_emoji_without_optionals(self, rest_guild_logic_impl, guild):
        mock_emoji_payload = {"id": "229292929", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_guild_logic_impl._session.create_guild_emoji.return_value = mock_emoji_payload
        mock_image_obj = mock.MagicMock(files.File)
        mock_image_data = mock.MagicMock(bytes)
        mock_image_obj = mock.MagicMock(files.File)
        mock_image_obj.read_all = mock.AsyncMock(return_value=mock_image_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj))
        with stack:
            result = await rest_guild_logic_impl.create_guild_emoji(
                guild=guild, name="fairEmoji", image=mock_image_obj,
            )
            assert result is mock_emoji_obj
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)
            mock_image_obj.read_all.assert_awaited_once()
        rest_guild_logic_impl._session.create_guild_emoji.assert_called_once_with(
            guild_id="93443949", name="fairEmoji", image=mock_image_data, roles=..., reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 4123321, emojis.GuildEmoji)
    async def test_update_guild_emoji_without_optionals(self, rest_guild_logic_impl, guild, emoji):
        mock_emoji_payload = {"id": "202020", "name": "Nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_guild_logic_impl._session.modify_guild_emoji.return_value = mock_emoji_payload
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            assert await rest_guild_logic_impl.update_guild_emoji(guild, emoji) is mock_emoji_obj
            rest_guild_logic_impl._session.modify_guild_emoji.assert_called_once_with(
                guild_id="93443949", emoji_id="4123321", name=..., roles=..., reason=...,
            )
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 4123321, emojis.GuildEmoji)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123123, guilds.GuildRole)
    async def test_update_guild_emoji_with_optionals(self, rest_guild_logic_impl, guild, emoji, role):
        mock_emoji_payload = {"id": "202020", "name": "Nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_guild_logic_impl._session.modify_guild_emoji.return_value = mock_emoji_payload
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            result = await rest_guild_logic_impl.update_guild_emoji(
                guild, emoji, name="Nyaa", roles=[role], reason="Agent 42"
            )
            assert result is mock_emoji_obj
            rest_guild_logic_impl._session.modify_guild_emoji.assert_called_once_with(
                guild_id="93443949", emoji_id="4123321", name="Nyaa", roles=["123123123"], reason="Agent 42",
            )
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 4123321, emojis.GuildEmoji)
    async def test_delete_guild_emoji(self, rest_guild_logic_impl, guild, emoji):
        rest_guild_logic_impl._session.delete_guild_emoji.return_value = ...
        assert await rest_guild_logic_impl.delete_guild_emoji(guild, emoji) is None
        rest_guild_logic_impl._session.delete_guild_emoji.assert_called_once_with(
            guild_id="93443949", emoji_id="4123321"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("region", [mock.MagicMock(voices.VoiceRegion, id="LONDON"), "LONDON"])
    async def test_create_guild_with_optionals(self, rest_guild_logic_impl, region):
        mock_guild_payload = {"id": "299292929292992", "region": "LONDON"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_guild_logic_impl._session.create_guild.return_value = mock_guild_payload
        mock_image_data = mock.MagicMock(bytes)
        mock_image_obj = mock.MagicMock(files.File)
        mock_image_obj.read_all = mock.AsyncMock(return_value=mock_image_data)
        mock_role_payload = {"permissions": 123123}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        mock_role_obj.serialize = mock.MagicMock(return_value=mock_role_payload)
        mock_channel_payload = {"type": 2, "name": "aChannel"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannelBuilder)
        mock_channel_obj.serialize = mock.MagicMock(return_value=mock_channel_payload)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj))
        with stack:
            result = await rest_guild_logic_impl.create_guild(
                name="OK",
                region=region,
                icon=mock_image_obj,
                verification_level=guilds.GuildVerificationLevel.NONE,
                default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                explicit_content_filter=guilds.GuildExplicitContentFilterLevel.MEMBERS_WITHOUT_ROLES,
                roles=[mock_role_obj],
                channels=[mock_channel_obj],
            )
            assert result is mock_guild_obj
            mock_image_obj.read_all.assert_awaited_once()
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)
        mock_channel_obj.serialize.assert_called_once()
        mock_role_obj.serialize.assert_called_once()
        rest_guild_logic_impl._session.create_guild.assert_called_once_with(
            name="OK",
            region="LONDON",
            icon=mock_image_data,
            verification_level=0,
            default_message_notifications=1,
            explicit_content_filter=1,
            roles=[mock_role_payload],
            channels=[mock_channel_payload],
        )

    @pytest.mark.asyncio
    async def test_create_guild_without_optionals(self, rest_guild_logic_impl):
        mock_guild_payload = {"id": "299292929292992", "region": "LONDON"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_guild_logic_impl._session.create_guild.return_value = mock_guild_payload
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            assert await rest_guild_logic_impl.create_guild(name="OK") is mock_guild_obj
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)
        rest_guild_logic_impl._session.create_guild.assert_called_once_with(
            name="OK",
            region=...,
            icon=...,
            verification_level=...,
            default_message_notifications=...,
            explicit_content_filter=...,
            roles=...,
            channels=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild(self, rest_guild_logic_impl, guild):
        mock_guild_payload = {"id": "94949494", "name": "A guild", "roles": []}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_guild_logic_impl._session.get_guild.return_value = mock_guild_payload
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            assert await rest_guild_logic_impl.fetch_guild(guild) is mock_guild_obj
            rest_guild_logic_impl._session.get_guild.assert_called_once_with(guild_id="379953393319542784")
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_preview(self, rest_guild_logic_impl, guild):
        mock_guild_preview_payload = {"id": "94949494", "name": "A guild", "emojis": []}
        mock_guild_preview_obj = mock.MagicMock(guilds.GuildPreview)
        rest_guild_logic_impl._session.get_guild_preview.return_value = mock_guild_preview_payload
        with mock.patch.object(guilds.GuildPreview, "deserialize", return_value=mock_guild_preview_obj):
            assert await rest_guild_logic_impl.fetch_guild_preview(guild) is mock_guild_preview_obj
            rest_guild_logic_impl._session.get_guild_preview.assert_called_once_with(guild_id="379953393319542784")
            guilds.GuildPreview.deserialize.assert_called_once_with(mock_guild_preview_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("afk_channel", 669517187031105607, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("owner", 379953393319542784, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("system_channel", 537340989808050216, users.User)
    @pytest.mark.parametrize("region", ["LONDON", mock.MagicMock(voices.VoiceRegion, id="LONDON")])
    @pytest.mark.parametrize("afk_timeout", [300, datetime.timedelta(seconds=300)])
    async def test_update_guild_with_optionals(
        self, rest_guild_logic_impl, guild, region, afk_channel, afk_timeout, owner, system_channel
    ):
        mock_guild_payload = {"id": "424242", "splash": "2lmKmklsdlksalkd"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_guild_logic_impl._session.modify_guild.return_value = mock_guild_payload
        mock_icon_data = mock.MagicMock(bytes)
        mock_icon_obj = mock.MagicMock(files.File)
        mock_icon_obj.read_all = mock.AsyncMock(return_value=mock_icon_data)
        mock_splash_data = mock.MagicMock(bytes)
        mock_splash_obj = mock.MagicMock(files.File)
        mock_splash_obj.read_all = mock.AsyncMock(return_value=mock_splash_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj))
        with stack:
            result = await rest_guild_logic_impl.update_guild(
                guild,
                name="aNewName",
                region=region,
                verification_level=guilds.GuildVerificationLevel.LOW,
                default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
                afk_channel=afk_channel,
                afk_timeout=afk_timeout,
                icon=mock_icon_obj,
                owner=owner,
                splash=mock_splash_obj,
                system_channel=system_channel,
                reason="A good reason",
            )
            assert result is mock_guild_obj
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)
            mock_icon_obj.read_all.assert_awaited_once()
            mock_splash_obj.read_all.assert_awaited_once()
        rest_guild_logic_impl._session.modify_guild.assert_called_once_with(
            guild_id="379953393319542784",
            name="aNewName",
            region="LONDON",
            verification_level=1,
            default_message_notifications=1,
            explicit_content_filter=2,
            afk_channel_id="669517187031105607",
            afk_timeout=300,
            icon=mock_icon_data,
            owner_id="379953393319542784",
            splash=mock_splash_data,
            system_channel_id="537340989808050216",
            reason="A good reason",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_update_guild_without_optionals(self, rest_guild_logic_impl, guild):
        mock_guild_payload = {"id": "424242", "splash": "2lmKmklsdlksalkd"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_guild_logic_impl._session.modify_guild.return_value = mock_guild_payload
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            assert await rest_guild_logic_impl.update_guild(guild) is mock_guild_obj
            rest_guild_logic_impl._session.modify_guild.assert_called_once_with(
                guild_id="379953393319542784",
                name=...,
                region=...,
                verification_level=...,
                default_message_notifications=...,
                explicit_content_filter=...,
                afk_channel_id=...,
                afk_timeout=...,
                icon=...,
                owner_id=...,
                splash=...,
                system_channel_id=...,
                reason=...,
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_delete_guild(self, rest_guild_logic_impl, guild):
        rest_guild_logic_impl._session.delete_guild.return_value = ...
        assert await rest_guild_logic_impl.delete_guild(guild) is None
        rest_guild_logic_impl._session.delete_guild.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_channels(self, rest_guild_logic_impl, guild):
        mock_channel_payload = {"id": "292929", "type": 1, "description": "A CHANNEL"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannel)
        rest_guild_logic_impl._session.list_guild_channels.return_value = [mock_channel_payload]
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            assert await rest_guild_logic_impl.fetch_guild_channels(guild) == [mock_channel_obj]
            rest_guild_logic_impl._session.list_guild_channels.assert_called_once_with(guild_id="379953393319542784")
            channels.deserialize_channel.assert_called_once_with(mock_channel_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("category", 5555, channels.GuildCategory)
    @pytest.mark.parametrize("rate_limit_per_user", [500, datetime.timedelta(seconds=500)])
    async def test_create_guild_channel_with_optionals(
        self, rest_guild_logic_impl, guild, category, rate_limit_per_user
    ):
        mock_channel_payload = {"id": "22929292", "type": "5", "description": "A  C H A N N E L"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannel)
        mock_overwrite_payload = {"type": "member", "id": "30303030"}
        mock_overwrite_obj = mock.MagicMock(
            channels.PermissionOverwrite, serialize=mock.MagicMock(return_value=mock_overwrite_payload)
        )
        rest_guild_logic_impl._session.create_guild_channel.return_value = mock_channel_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            result = await rest_guild_logic_impl.create_guild_channel(
                guild,
                "Hi-i-am-a-name",
                channel_type=channels.ChannelType.GUILD_VOICE,
                position=42,
                topic="A TOPIC",
                nsfw=True,
                rate_limit_per_user=rate_limit_per_user,
                bitrate=36000,
                user_limit=5,
                permission_overwrites=[mock_overwrite_obj],
                parent_category=category,
                reason="A GOOD REASON!",
            )
            assert result is mock_channel_obj
            mock_overwrite_obj.serialize.assert_called_once()
            rest_guild_logic_impl._session.create_guild_channel.assert_called_once_with(
                guild_id="123123123",
                name="Hi-i-am-a-name",
                type_=2,
                position=42,
                topic="A TOPIC",
                nsfw=True,
                rate_limit_per_user=500,
                bitrate=36000,
                user_limit=5,
                permission_overwrites=[mock_overwrite_payload],
                parent_id="5555",
                reason="A GOOD REASON!",
            )
            channels.deserialize_channel.assert_called_once_with(mock_channel_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    async def test_create_guild_channel_without_optionals(self, rest_guild_logic_impl, guild):
        mock_channel_payload = {"id": "22929292", "type": "5", "description": "A  C H A N N E L"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannel)
        rest_guild_logic_impl._session.create_guild_channel.return_value = mock_channel_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            assert await rest_guild_logic_impl.create_guild_channel(guild, "Hi-i-am-a-name") is mock_channel_obj
            rest_guild_logic_impl._session.create_guild_channel.assert_called_once_with(
                guild_id="123123123",
                name="Hi-i-am-a-name",
                type_=...,
                position=...,
                topic=...,
                nsfw=...,
                rate_limit_per_user=...,
                bitrate=...,
                user_limit=...,
                permission_overwrites=...,
                parent_id=...,
                reason=...,
            )
            channels.deserialize_channel.assert_called_once_with(mock_channel_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.GuildChannel)
    @_helpers.parametrize_valid_id_formats_for_models("second_channel", 115590097100865541, channels.GuildChannel)
    async def test_reposition_guild_channels(self, rest_guild_logic_impl, guild, channel, second_channel):
        rest_guild_logic_impl._session.modify_guild_channel_positions.return_value = ...
        assert await rest_guild_logic_impl.reposition_guild_channels(guild, (1, channel), (2, second_channel)) is None
        rest_guild_logic_impl._session.modify_guild_channel_positions.assert_called_once_with(
            "123123123", ("379953393319542784", 1), ("115590097100865541", 2)
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 444444, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 123123123123, users.User)
    async def test_fetch_member(self, rest_guild_logic_impl, guild, user):
        mock_member_payload = {"user": {}, "nick": "! Agent 47"}
        mock_member_obj = mock.MagicMock(guilds.GuildMember)
        rest_guild_logic_impl._session.get_guild_member.return_value = mock_member_payload
        with mock.patch.object(guilds.GuildMember, "deserialize", return_value=mock_member_obj):
            assert await rest_guild_logic_impl.fetch_member(guild, user) is mock_member_obj
            rest_guild_logic_impl._session.get_guild_member.assert_called_once_with(
                guild_id="444444", user_id="123123123123"
            )
            guilds.GuildMember.deserialize.assert_called_once_with(mock_member_payload)

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 115590097100865541, users.User)
    def test_fetch_members_after_with_optionals(self, rest_guild_logic_impl, guild, user):
        mock_generator = mock.AsyncMock()
        with mock.patch.object(helpers, "pagination_handler", return_value=mock_generator):
            assert rest_guild_logic_impl.fetch_members_after(guild, after=user, limit=34) is mock_generator
            helpers.pagination_handler.assert_called_once_with(
                guild_id="574921006817476608",
                deserializer=guilds.GuildMember.deserialize,
                direction="after",
                request=rest_guild_logic_impl._session.list_guild_members,
                reversing=False,
                start="115590097100865541",
                limit=34,
                id_getter=_guild._get_member_id,
            )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_members_after_without_optionals(self, rest_guild_logic_impl, guild):
        mock_generator = mock.AsyncMock()
        with mock.patch.object(helpers, "pagination_handler", return_value=mock_generator):
            assert rest_guild_logic_impl.fetch_members_after(guild) is mock_generator
            helpers.pagination_handler.assert_called_once_with(
                guild_id="574921006817476608",
                deserializer=guilds.GuildMember.deserialize,
                direction="after",
                request=rest_guild_logic_impl._session.list_guild_members,
                reversing=False,
                start="0",
                limit=None,
                id_getter=_guild._get_member_id,
            )

    def test_fetch_members_after_with_datetime_object(self, rest_guild_logic_impl):
        mock_generator = mock.AsyncMock()
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        with mock.patch.object(helpers, "pagination_handler", return_value=mock_generator):
            assert rest_guild_logic_impl.fetch_members_after(574921006817476608, after=date) is mock_generator
            helpers.pagination_handler.assert_called_once_with(
                guild_id="574921006817476608",
                deserializer=guilds.GuildMember.deserialize,
                direction="after",
                request=rest_guild_logic_impl._session.list_guild_members,
                reversing=False,
                start="537340988620800000",
                limit=None,
                id_getter=_guild._get_member_id,
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 229292992, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 1010101010, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 11100010, guilds.GuildRole)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.GuildVoiceChannel)
    async def test_update_member_with_optionals(self, rest_guild_logic_impl, guild, user, role, channel):
        rest_guild_logic_impl._session.modify_guild_member.return_value = ...
        result = await rest_guild_logic_impl.update_member(
            guild,
            user,
            nickname="Nick's Name",
            roles=[role],
            mute=True,
            deaf=False,
            voice_channel=channel,
            reason="Get Tagged.",
        )
        assert result is None
        rest_guild_logic_impl._session.modify_guild_member.assert_called_once_with(
            guild_id="229292992",
            user_id="1010101010",
            nick="Nick's Name",
            roles=["11100010"],
            mute=True,
            deaf=False,
            channel_id="33333333",
            reason="Get Tagged.",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 229292992, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 1010101010, users.User)
    async def test_update_member_without_optionals(self, rest_guild_logic_impl, guild, user):
        rest_guild_logic_impl._session.modify_guild_member.return_value = ...
        assert await rest_guild_logic_impl.update_member(guild, user) is None
        rest_guild_logic_impl._session.modify_guild_member.assert_called_once_with(
            guild_id="229292992",
            user_id="1010101010",
            nick=...,
            roles=...,
            mute=...,
            deaf=...,
            channel_id=...,
            reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 229292992, guilds.Guild)
    async def test_update_my_member_nickname_with_reason(self, rest_guild_logic_impl, guild):
        rest_guild_logic_impl._session.modify_current_user_nick.return_value = ...
        result = await rest_guild_logic_impl.update_my_member_nickname(
            guild, "Nick's nick", reason="I want to drink your blood."
        )
        assert result is None
        rest_guild_logic_impl._session.modify_current_user_nick.assert_called_once_with(
            guild_id="229292992", nick="Nick's nick", reason="I want to drink your blood."
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 229292992, guilds.Guild)
    async def test_update_my_member_nickname_without_reason(self, rest_guild_logic_impl, guild):
        rest_guild_logic_impl._session.modify_current_user_nick.return_value = ...
        assert await rest_guild_logic_impl.update_my_member_nickname(guild, "Nick's nick") is None
        rest_guild_logic_impl._session.modify_current_user_nick.assert_called_once_with(
            guild_id="229292992", nick="Nick's nick", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_add_role_to_member_with_reason(self, rest_guild_logic_impl, guild, user, role):
        rest_guild_logic_impl._session.add_guild_member_role.return_value = ...
        assert await rest_guild_logic_impl.add_role_to_member(guild, user, role, reason="Get role'd") is None
        rest_guild_logic_impl._session.add_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason="Get role'd"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_add_role_to_member_without_reason(self, rest_guild_logic_impl, guild, user, role):
        rest_guild_logic_impl._session.add_guild_member_role.return_value = ...
        assert await rest_guild_logic_impl.add_role_to_member(guild, user, role) is None
        rest_guild_logic_impl._session.add_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_remove_role_from_member_with_reason(self, rest_guild_logic_impl, guild, user, role):
        rest_guild_logic_impl._session.remove_guild_member_role.return_value = ...
        assert await rest_guild_logic_impl.remove_role_from_member(guild, user, role, reason="Get role'd") is None
        rest_guild_logic_impl._session.remove_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason="Get role'd"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_remove_role_from_member_without_reason(self, rest_guild_logic_impl, guild, user, role):
        rest_guild_logic_impl._session.remove_guild_member_role.return_value = ...
        assert await rest_guild_logic_impl.remove_role_from_member(guild, user, role) is None
        rest_guild_logic_impl._session.remove_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_kick_member_with_reason(self, rest_guild_logic_impl, guild, user):
        rest_guild_logic_impl._session.remove_guild_member.return_value = ...
        assert await rest_guild_logic_impl.kick_member(guild, user, reason="TO DO") is None
        rest_guild_logic_impl._session.remove_guild_member.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason="TO DO"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_kick_member_without_reason(self, rest_guild_logic_impl, guild, user):
        rest_guild_logic_impl._session.remove_guild_member.return_value = ...
        assert await rest_guild_logic_impl.kick_member(guild, user) is None
        rest_guild_logic_impl._session.remove_guild_member.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_fetch_ban(self, rest_guild_logic_impl, guild, user):
        mock_ban_payload = {"reason": "42'd", "user": {}}
        mock_ban_obj = mock.MagicMock(guilds.GuildMemberBan)
        rest_guild_logic_impl._session.get_guild_ban.return_value = mock_ban_payload
        with mock.patch.object(guilds.GuildMemberBan, "deserialize", return_value=mock_ban_obj):
            assert await rest_guild_logic_impl.fetch_ban(guild, user) is mock_ban_obj
            rest_guild_logic_impl._session.get_guild_ban.assert_called_once_with(
                guild_id="123123123", user_id="4444444"
            )
            guilds.GuildMemberBan.deserialize.assert_called_once_with(mock_ban_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    async def test_fetch_bans(self, rest_guild_logic_impl, guild):
        mock_ban_payload = {"reason": "42'd", "user": {}}
        mock_ban_obj = mock.MagicMock(guilds.GuildMemberBan)
        rest_guild_logic_impl._session.get_guild_bans.return_value = [mock_ban_payload]
        with mock.patch.object(guilds.GuildMemberBan, "deserialize", return_value=mock_ban_obj):
            assert await rest_guild_logic_impl.fetch_bans(guild) == [mock_ban_obj]
            rest_guild_logic_impl._session.get_guild_bans.assert_called_once_with(guild_id="123123123")
            guilds.GuildMemberBan.deserialize.assert_called_once_with(mock_ban_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @pytest.mark.parametrize("delete_message_days", [datetime.timedelta(days=12), 12])
    async def test_ban_member_with_optionals(self, rest_guild_logic_impl, guild, user, delete_message_days):
        rest_guild_logic_impl._session.create_guild_ban.return_value = ...
        result = await rest_guild_logic_impl.ban_member(
            guild, user, delete_message_days=delete_message_days, reason="bye"
        )
        assert result is None
        rest_guild_logic_impl._session.create_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", delete_message_days=12, reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_ban_member_without_optionals(self, rest_guild_logic_impl, guild, user):
        rest_guild_logic_impl._session.create_guild_ban.return_value = ...
        assert await rest_guild_logic_impl.ban_member(guild, user) is None
        rest_guild_logic_impl._session.create_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", delete_message_days=..., reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_unban_member_with_reason(self, rest_guild_logic_impl, guild, user):
        rest_guild_logic_impl._session.remove_guild_ban.return_value = ...
        result = await rest_guild_logic_impl.unban_member(guild, user, reason="bye")
        assert result is None
        rest_guild_logic_impl._session.remove_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_unban_member_without_reason(self, rest_guild_logic_impl, guild, user):
        rest_guild_logic_impl._session.remove_guild_ban.return_value = ...
        assert await rest_guild_logic_impl.unban_member(guild, user) is None
        rest_guild_logic_impl._session.remove_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_roles(self, rest_guild_logic_impl, guild):
        mock_role_payload = {"id": "33030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole, id=33030)
        rest_guild_logic_impl._session.get_guild_roles.return_value = [mock_role_payload]
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            assert await rest_guild_logic_impl.fetch_roles(guild) == {33030: mock_role_obj}
            rest_guild_logic_impl._session.get_guild_roles.assert_called_once_with(guild_id="574921006817476608")
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_create_role_with_optionals(self, rest_guild_logic_impl, guild):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_guild_logic_impl._session.create_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_guild_logic_impl.create_role(
                guild,
                name="Roleington",
                permissions=permissions.Permission.STREAM | permissions.Permission.EMBED_LINKS,
                color=colors.Color(21312),
                hoist=True,
                mentionable=False,
                reason="And then there was a role.",
            )
            assert result is mock_role_obj
            rest_guild_logic_impl._session.create_guild_role.assert_called_once_with(
                guild_id="574921006817476608",
                name="Roleington",
                permissions=16896,
                color=21312,
                hoist=True,
                mentionable=False,
                reason="And then there was a role.",
            )
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_create_role_without_optionals(self, rest_guild_logic_impl, guild):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_guild_logic_impl._session.create_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_guild_logic_impl.create_role(guild)
            assert result is mock_role_obj
            rest_guild_logic_impl._session.create_guild_role.assert_called_once_with(
                guild_id="574921006817476608",
                name=...,
                permissions=...,
                color=...,
                hoist=...,
                mentionable=...,
                reason=...,
            )
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123, guilds.GuildRole)
    @_helpers.parametrize_valid_id_formats_for_models("additional_role", 123456, guilds.GuildRole)
    async def test_reposition_roles(self, rest_guild_logic_impl, guild, role, additional_role):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_guild_logic_impl._session.modify_guild_role_positions.return_value = [mock_role_payload]
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_guild_logic_impl.reposition_roles(guild, (1, role), (2, additional_role))
            assert result == [mock_role_obj]
            rest_guild_logic_impl._session.modify_guild_role_positions.assert_called_once_with(
                "574921006817476608", ("123123", 1), ("123456", 2)
            )
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123, guilds.GuildRole)
    async def test_update_role_with_optionals(self, rest_guild_logic_impl, guild, role):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_guild_logic_impl._session.modify_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_guild_logic_impl.update_role(
                guild,
                role,
                name="ROLE",
                permissions=permissions.Permission.STREAM | permissions.Permission.EMBED_LINKS,
                color=colors.Color(12312),
                hoist=True,
                mentionable=False,
                reason="Why not?",
            )
            assert result is mock_role_obj
            rest_guild_logic_impl._session.modify_guild_role.assert_called_once_with(
                guild_id="574921006817476608",
                role_id="123123",
                name="ROLE",
                permissions=16896,
                color=12312,
                hoist=True,
                mentionable=False,
                reason="Why not?",
            )
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123, guilds.GuildRole)
    async def test_update_role_without_optionals(self, rest_guild_logic_impl, guild, role):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_guild_logic_impl._session.modify_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            assert await rest_guild_logic_impl.update_role(guild, role) is mock_role_obj
            rest_guild_logic_impl._session.modify_guild_role.assert_called_once_with(
                guild_id="574921006817476608",
                role_id="123123",
                name=...,
                permissions=...,
                color=...,
                hoist=...,
                mentionable=...,
                reason=...,
            )
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123, guilds.GuildRole)
    async def test_delete_role(self, rest_guild_logic_impl, guild, role):
        rest_guild_logic_impl._session.delete_guild_role.return_value = ...
        assert await rest_guild_logic_impl.delete_role(guild, role) is None
        rest_guild_logic_impl._session.delete_guild_role.assert_called_once_with(
            guild_id="574921006817476608", role_id="123123"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("days", [7, datetime.timedelta(days=7)])
    async def test_estimate_guild_prune_count(self, rest_guild_logic_impl, guild, days):
        rest_guild_logic_impl._session.get_guild_prune_count.return_value = 42
        assert await rest_guild_logic_impl.estimate_guild_prune_count(guild, days) == 42
        rest_guild_logic_impl._session.get_guild_prune_count.assert_called_once_with(
            guild_id="574921006817476608", days=7
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("days", [7, datetime.timedelta(days=7)])
    async def test_estimate_guild_with_optionals(self, rest_guild_logic_impl, guild, days):
        rest_guild_logic_impl._session.begin_guild_prune.return_value = None
        assert (
            await rest_guild_logic_impl.begin_guild_prune(guild, days, compute_prune_count=True, reason="nah m8")
            is None
        )
        rest_guild_logic_impl._session.begin_guild_prune.assert_called_once_with(
            guild_id="574921006817476608", days=7, compute_prune_count=True, reason="nah m8"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("days", [7, datetime.timedelta(days=7)])
    async def test_estimate_guild_without_optionals(self, rest_guild_logic_impl, guild, days):
        rest_guild_logic_impl._session.begin_guild_prune.return_value = 42
        assert await rest_guild_logic_impl.begin_guild_prune(guild, days) == 42
        rest_guild_logic_impl._session.begin_guild_prune.assert_called_once_with(
            guild_id="574921006817476608", days=7, compute_prune_count=..., reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_voice_regions(self, rest_guild_logic_impl, guild):
        mock_voice_payload = {"name": "london", "id": "LONDON"}
        mock_voice_obj = mock.MagicMock(voices.VoiceRegion)
        rest_guild_logic_impl._session.get_guild_voice_regions.return_value = [mock_voice_payload]
        with mock.patch.object(voices.VoiceRegion, "deserialize", return_value=mock_voice_obj):
            assert await rest_guild_logic_impl.fetch_guild_voice_regions(guild) == [mock_voice_obj]
            rest_guild_logic_impl._session.get_guild_voice_regions.assert_called_once_with(
                guild_id="574921006817476608"
            )
            voices.VoiceRegion.deserialize.assert_called_once_with(mock_voice_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_invites(self, rest_guild_logic_impl, guild):
        mock_invite_payload = {"code": "dododo"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_guild_logic_impl._session.get_guild_invites.return_value = [mock_invite_payload]
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            assert await rest_guild_logic_impl.fetch_guild_invites(guild) == [mock_invite_obj]
            invites.InviteWithMetadata.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_integrations(self, rest_guild_logic_impl, guild):
        mock_integration_payload = {"id": "123123", "name": "Integrated", "type": "twitch"}
        mock_integration_obj = mock.MagicMock(guilds.GuildIntegration)
        rest_guild_logic_impl._session.get_guild_integrations.return_value = [mock_integration_payload]
        with mock.patch.object(guilds.GuildIntegration, "deserialize", return_value=mock_integration_obj):
            assert await rest_guild_logic_impl.fetch_integrations(guild) == [mock_integration_obj]
            rest_guild_logic_impl._session.get_guild_integrations.assert_called_once_with(guild_id="574921006817476608")
            guilds.GuildIntegration.deserialize.assert_called_once_with(mock_integration_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    @pytest.mark.parametrize("period", [datetime.timedelta(days=7), 7])
    async def test_update_integration_with_optionals(self, rest_guild_logic_impl, guild, integration, period):
        rest_guild_logic_impl._session.modify_guild_integration.return_value = ...
        result = await rest_guild_logic_impl.update_integration(
            guild,
            integration,
            expire_behaviour=guilds.IntegrationExpireBehaviour.KICK,
            expire_grace_period=period,
            enable_emojis=True,
            reason="GET YEET'D",
        )
        assert result is None
        rest_guild_logic_impl._session.modify_guild_integration.assert_called_once_with(
            guild_id="574921006817476608",
            integration_id="379953393319542784",
            expire_behaviour=1,
            expire_grace_period=7,
            enable_emojis=True,
            reason="GET YEET'D",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    async def test_update_integration_without_optionals(self, rest_guild_logic_impl, guild, integration):
        rest_guild_logic_impl._session.modify_guild_integration.return_value = ...
        assert await rest_guild_logic_impl.update_integration(guild, integration) is None
        rest_guild_logic_impl._session.modify_guild_integration.assert_called_once_with(
            guild_id="574921006817476608",
            integration_id="379953393319542784",
            expire_behaviour=...,
            expire_grace_period=...,
            enable_emojis=...,
            reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    async def test_delete_integration_with_reason(self, rest_guild_logic_impl, guild, integration):
        rest_guild_logic_impl._session.delete_guild_integration.return_value = ...
        assert await rest_guild_logic_impl.delete_integration(guild, integration, reason="B Y E") is None
        rest_guild_logic_impl._session.delete_guild_integration.assert_called_once_with(
            guild_id="574921006817476608", integration_id="379953393319542784", reason="B Y E"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    async def test_delete_integration_without_reason(self, rest_guild_logic_impl, guild, integration):
        rest_guild_logic_impl._session.delete_guild_integration.return_value = ...
        assert await rest_guild_logic_impl.delete_integration(guild, integration) is None
        rest_guild_logic_impl._session.delete_guild_integration.assert_called_once_with(
            guild_id="574921006817476608", integration_id="379953393319542784", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    async def test_sync_guild_integration(self, rest_guild_logic_impl, guild, integration):
        rest_guild_logic_impl._session.sync_guild_integration.return_value = ...
        assert await rest_guild_logic_impl.sync_guild_integration(guild, integration) is None
        rest_guild_logic_impl._session.sync_guild_integration.assert_called_once_with(
            guild_id="574921006817476608", integration_id="379953393319542784",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_embed(self, rest_guild_logic_impl, guild):
        mock_embed_payload = {"enabled": True, "channel_id": "2020202"}
        mock_embed_obj = mock.MagicMock(guilds.GuildEmbed)
        rest_guild_logic_impl._session.get_guild_embed.return_value = mock_embed_payload
        with mock.patch.object(guilds.GuildEmbed, "deserialize", return_value=mock_embed_obj):
            assert await rest_guild_logic_impl.fetch_guild_embed(guild) is mock_embed_obj
            rest_guild_logic_impl._session.get_guild_embed.assert_called_once_with(guild_id="574921006817476608")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123, channels.GuildChannel)
    async def test_update_guild_embed_with_optionnal(self, rest_guild_logic_impl, guild, channel):
        mock_embed_payload = {"enabled": True, "channel_id": "2020202"}
        mock_embed_obj = mock.MagicMock(guilds.GuildEmbed)
        rest_guild_logic_impl._session.modify_guild_embed.return_value = mock_embed_payload
        with mock.patch.object(guilds.GuildEmbed, "deserialize", return_value=mock_embed_obj):
            result = await rest_guild_logic_impl.update_guild_embed(
                guild, channel=channel, enabled=True, reason="Nyaa!!!"
            )
            assert result is mock_embed_obj
            rest_guild_logic_impl._session.modify_guild_embed.assert_called_once_with(
                guild_id="574921006817476608", channel_id="123123", enabled=True, reason="Nyaa!!!"
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_update_guild_embed_without_optionnal(self, rest_guild_logic_impl, guild):
        mock_embed_payload = {"enabled": True, "channel_id": "2020202"}
        mock_embed_obj = mock.MagicMock(guilds.GuildEmbed)
        rest_guild_logic_impl._session.modify_guild_embed.return_value = mock_embed_payload
        with mock.patch.object(guilds.GuildEmbed, "deserialize", return_value=mock_embed_obj):
            assert await rest_guild_logic_impl.update_guild_embed(guild) is mock_embed_obj
            rest_guild_logic_impl._session.modify_guild_embed.assert_called_once_with(
                guild_id="574921006817476608", channel_id=..., enabled=..., reason=...
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_vanity_url(self, rest_guild_logic_impl, guild):
        mock_vanity_payload = {"code": "akfdk", "uses": 5}
        mock_vanity_obj = mock.MagicMock(invites.VanityUrl)
        rest_guild_logic_impl._session.get_guild_vanity_url.return_value = mock_vanity_payload
        with mock.patch.object(invites.VanityUrl, "deserialize", return_value=mock_vanity_obj):
            assert await rest_guild_logic_impl.fetch_guild_vanity_url(guild) is mock_vanity_obj
            rest_guild_logic_impl._session.get_guild_vanity_url.assert_called_once_with(guild_id="574921006817476608")
            invites.VanityUrl.deserialize.assert_called_once_with(mock_vanity_payload)

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_guild_widget_image_with_style(self, rest_guild_logic_impl, guild):
        mock_url = "not/a/url"
        rest_guild_logic_impl._session.get_guild_widget_image_url.return_value = mock_url
        assert rest_guild_logic_impl.format_guild_widget_image(guild, style="notAStyle") == mock_url
        rest_guild_logic_impl._session.get_guild_widget_image_url.assert_called_once_with(
            guild_id="574921006817476608", style="notAStyle",
        )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_guild_widget_image_without_style(self, rest_guild_logic_impl, guild):
        mock_url = "not/a/url"
        rest_guild_logic_impl._session.get_guild_widget_image_url.return_value = mock_url
        assert rest_guild_logic_impl.format_guild_widget_image(guild) == mock_url
        rest_guild_logic_impl._session.get_guild_widget_image_url.assert_called_once_with(
            guild_id="574921006817476608", style=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.GuildChannel)
    async def test_fetch_guild_webhooks(self, rest_guild_logic_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_guild_logic_impl._session.get_guild_webhooks.return_value = [mock_webhook_payload]
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_guild_logic_impl.fetch_guild_webhooks(channel) == [mock_webhook_obj]
            rest_guild_logic_impl._session.get_guild_webhooks.assert_called_once_with(guild_id="115590097100865541")
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

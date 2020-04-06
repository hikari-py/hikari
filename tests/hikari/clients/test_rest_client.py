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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime
import io

import cymock as mock
import datetime
import pytest


from hikari.internal import conversions
from hikari.clients import configs
from hikari.clients import rest_clients
from hikari.net import rest
from hikari import audit_logs
from hikari import channels
from hikari import colors
from hikari import embeds
from hikari import emojis
from hikari import gateway_entities
from hikari import guilds
from hikari import invites
from hikari import media
from hikari import messages
from hikari import oauth2
from hikari import permissions
from hikari import snowflakes
from hikari import users
from hikari import voices
from hikari import webhooks

from tests.hikari import _helpers


def test__get_member_id():
    member = mock.create_autospec(
        guilds.GuildMember, user=mock.create_autospec(users.User, id=123123123, __int__=users.User.__int__)
    )
    assert rest_clients._get_member_id(member) == "123123123"


class TestRESTClient:
    @pytest.fixture()
    def mock_config(self):
        # Mocking the Configs leads to attribute errors regardless of spec set.
        return configs.RESTConfig(token="blah.blah.blah")

    def test_init(self, mock_config):
        mock_low_level_rest_clients = mock.MagicMock(rest.LowLevelRestfulClient)
        with mock.patch.object(rest, "LowLevelRestfulClient", return_value=mock_low_level_rest_clients) as patched_init:
            cli = rest_clients.RESTClient(mock_config)
            patched_init.assert_called_once_with(
                allow_redirects=mock_config.allow_redirects,
                connector=mock_config.tcp_connector,
                proxy_headers=mock_config.proxy_headers,
                proxy_auth=mock_config.proxy_auth,
                ssl_context=mock_config.ssl_context,
                verify_ssl=mock_config.verify_ssl,
                timeout=mock_config.request_timeout,
                token=mock_config.token,
                version=mock_config.rest_version,
            )
            assert cli._session is mock_low_level_rest_clients

    @pytest.fixture()
    def low_level_rest_impl(self) -> rest.LowLevelRestfulClient:
        return mock.create_autospec(rest.LowLevelRestfulClient, auto_spec=True)

    @pytest.fixture()
    def rest_clients_impl(self, low_level_rest_impl) -> rest_clients.RESTClient:
        class RESTClient(rest_clients.RESTClient):
            def __init__(self):
                self._session: rest.LowLevelRestfulClient = low_level_rest_impl

        return RESTClient()

    @pytest.mark.asyncio
    async def test_close_awaits_session_close(self, rest_clients_impl):
        await rest_clients_impl.close()
        rest_clients_impl._session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test___aenter___and___aexit__(self, rest_clients_impl):
        rest_clients_impl.close = mock.AsyncMock()
        async with rest_clients_impl as client:
            assert client is rest_clients_impl
        rest_clients_impl.close.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_fetch_gateway_url(self, rest_clients_impl):
        mock_url = "wss://gateway.discord.gg/"
        rest_clients_impl._session.get_gateway.return_value = mock_url
        assert await rest_clients_impl.fetch_gateway_url() == mock_url
        rest_clients_impl._session.get_gateway.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_gateway_bot(self, rest_clients_impl):
        mock_payload = {"url": "wss://gateway.discord.gg/", "shards": 9, "session_start_limit": {}}
        mock_gateway_bot_obj = mock.MagicMock(gateway_entities.GatewayBot)
        rest_clients_impl._session.get_gateway_bot.return_value = mock_payload
        with mock.patch.object(gateway_entities.GatewayBot, "deserialize", return_value=mock_gateway_bot_obj):
            assert await rest_clients_impl.fetch_gateway_bot() is mock_gateway_bot_obj
            rest_clients_impl._session.get_gateway_bot.assert_called_once()
            gateway_entities.GatewayBot.deserialize.assert_called_once_with(mock_payload)

    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 22222222, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("before", 123123123123, audit_logs.AuditLogEntry)
    def test_fetch_audit_log_entries_before_with_optionals(self, rest_clients_impl, guild, before, user):
        mock_audit_log_iterator = mock.MagicMock(audit_logs.AuditLogIterator)
        with mock.patch.object(audit_logs, "AuditLogIterator", return_value=mock_audit_log_iterator):
            result = rest_clients_impl.fetch_audit_log_entries_before(
                guild, before=before, user=user, action_type=audit_logs.AuditLogEventType.MEMBER_MOVE, limit=42,
            )
            assert result is mock_audit_log_iterator
            audit_logs.AuditLogIterator.assert_called_once_with(
                guild_id="379953393319542784",
                request=rest_clients_impl._session.get_guild_audit_log,
                before="123123123123",
                user_id="22222222",
                action_type=26,
                limit=42,
            )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    def test_fetch_audit_log_entries_before_without_optionals(self, rest_clients_impl, guild):
        mock_audit_log_iterator = mock.MagicMock(audit_logs.AuditLogIterator)
        with mock.patch.object(audit_logs, "AuditLogIterator", return_value=mock_audit_log_iterator):
            assert rest_clients_impl.fetch_audit_log_entries_before(guild) is mock_audit_log_iterator
            audit_logs.AuditLogIterator.assert_called_once_with(
                guild_id="379953393319542784",
                request=rest_clients_impl._session.get_guild_audit_log,
                before=None,
                user_id=...,
                action_type=...,
                limit=None,
            )

    def test_fetch_audit_log_entries_before_with_datetime_object(self, rest_clients_impl):
        mock_audit_log_iterator = mock.MagicMock(audit_logs.AuditLogIterator)
        with mock.patch.object(audit_logs, "AuditLogIterator", return_value=mock_audit_log_iterator):
            date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
            result = rest_clients_impl.fetch_audit_log_entries_before(123123123, before=date)
            assert result is mock_audit_log_iterator
            audit_logs.AuditLogIterator.assert_called_once_with(
                guild_id="123123123",
                request=rest_clients_impl._session.get_guild_audit_log,
                before="537340988620800000",
                user_id=...,
                action_type=...,
                limit=None,
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 115590097100865541, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("before", 1231231123, audit_logs.AuditLogEntry)
    async def test_fetch_audit_log_with_optionals(self, rest_clients_impl, guild, user, before):
        mock_audit_log_payload = {"entries": [], "integrations": [], "webhooks": [], "users": []}
        mock_audit_log_obj = mock.MagicMock(audit_logs.AuditLog)
        rest_clients_impl._session.get_guild_audit_log.return_value = mock_audit_log_payload
        with mock.patch.object(audit_logs.AuditLog, "deserialize", return_value=mock_audit_log_obj):
            result = await rest_clients_impl.fetch_audit_log(
                guild, user=user, action_type=audit_logs.AuditLogEventType.MEMBER_MOVE, limit=100, before=before,
            )
            assert result is mock_audit_log_obj
            rest_clients_impl._session.get_guild_audit_log.assert_called_once_with(
                guild_id="379953393319542784",
                user_id="115590097100865541",
                action_type=26,
                limit=100,
                before="1231231123",
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_audit_log_without_optionals(self, rest_clients_impl, guild):
        mock_audit_log_payload = {"entries": [], "integrations": [], "webhooks": [], "users": []}
        mock_audit_log_obj = mock.MagicMock(audit_logs.AuditLog)
        rest_clients_impl._session.get_guild_audit_log.return_value = mock_audit_log_payload
        with mock.patch.object(audit_logs.AuditLog, "deserialize", return_value=mock_audit_log_obj):
            assert await rest_clients_impl.fetch_audit_log(guild) is mock_audit_log_obj
            rest_clients_impl._session.get_guild_audit_log.assert_called_once_with(
                guild_id="379953393319542784", user_id=..., action_type=..., limit=..., before=...
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_audit_log_handles_datetime_object(self, rest_clients_impl, guild):
        mock_audit_log_payload = {"entries": [], "integrations": [], "webhooks": [], "users": []}
        mock_audit_log_obj = mock.MagicMock(audit_logs.AuditLog)
        rest_clients_impl._session.get_guild_audit_log.return_value = mock_audit_log_payload
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        with mock.patch.object(audit_logs.AuditLog, "deserialize", return_value=mock_audit_log_obj):
            assert await rest_clients_impl.fetch_audit_log(guild, before=date) is mock_audit_log_obj
            rest_clients_impl._session.get_guild_audit_log.assert_called_once_with(
                guild_id="379953393319542784", user_id=..., action_type=..., limit=..., before="537340988620800000"
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 1234, channels.Channel)
    async def test_fetch_channel(self, rest_clients_impl, channel):
        mock_payload = {"id": "49494994", "type": 3}
        mock_channel_obj = mock.MagicMock(channels.Channel)
        rest_clients_impl._session.get_channel.return_value = mock_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            assert await rest_clients_impl.fetch_channel(channel) is mock_channel_obj
            rest_clients_impl._session.get_channel.assert_called_once_with(channel_id="1234")
            channels.deserialize_channel.assert_called_once_with(mock_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("parent_channel", 115590097100865541, channels.Channel)
    @pytest.mark.parametrize("rate_limit_per_user", [42, datetime.timedelta(seconds=42)])
    async def test_update_channel_with_optionals(self, rest_clients_impl, channel, parent_channel, rate_limit_per_user):
        mock_payload = {"name": "Qts", "type": 2}
        mock_channel_obj = mock.MagicMock(channels.Channel)
        mock_overwrite_payload = {"type": "user", "id": 543543543}
        mock_overwrite_obj = mock.create_autospec(
            channels.PermissionOverwrite, serialize=mock.MagicMock(return_value=mock_overwrite_payload)
        )
        rest_clients_impl._session.modify_channel.return_value = mock_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            result = await rest_clients_impl.update_channel(
                channel=channel,
                name="ohNo",
                position=7,
                topic="camelsAreGreat",
                nsfw=True,
                bitrate=32000,
                user_limit=42,
                rate_limit_per_user=rate_limit_per_user,
                permission_overwrites=[mock_overwrite_obj],
                parent_category=parent_channel,
                reason="Get Nyaa'd.",
            )
            assert result is mock_channel_obj
            rest_clients_impl._session.modify_channel.assert_called_once_with(
                channel_id="379953393319542784",
                name="ohNo",
                position=7,
                topic="camelsAreGreat",
                nsfw=True,
                rate_limit_per_user=42,
                bitrate=32000,
                user_limit=42,
                permission_overwrites=[mock_overwrite_payload],
                parent_id="115590097100865541",
                reason="Get Nyaa'd.",
            )
            mock_overwrite_obj.serialize.assert_called_once()
            channels.deserialize_channel.assert_called_once_with(mock_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.Channel)
    async def test_update_channel_without_optionals(
        self, rest_clients_impl, channel,
    ):
        mock_payload = {"name": "Qts", "type": 2}
        mock_channel_obj = mock.MagicMock(channels.Channel)
        rest_clients_impl._session.modify_channel.return_value = mock_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            result = await rest_clients_impl.update_channel(channel=channel,)
            assert result is mock_channel_obj
            rest_clients_impl._session.modify_channel.assert_called_once_with(
                channel_id="379953393319542784",
                name=...,
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
            channels.deserialize_channel.assert_called_once_with(mock_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 55555, channels.Channel)
    async def test_delete_channel(self, rest_clients_impl, channel):
        rest_clients_impl._session.delete_close_channel.return_value = ...
        assert await rest_clients_impl.delete_channel(channel) is None
        rest_clients_impl._session.delete_close_channel.assert_called_once_with(channel_id="55555")

    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 777777777, messages.Message)
    def test_fetch_messages_after_with_optionals(self, rest_clients_impl, channel, message):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        result = rest_clients_impl.fetch_messages_after(channel=channel, after=message, limit=52)
        assert result is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123123123",
            deserializer=messages.Message.deserialize,
            direction="after",
            start="777777777",
            request=rest_clients_impl._session.get_channel_messages,
            reversing=True,
            limit=52,
        )

    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    def test_fetch_messages_after_without_optionals(self, rest_clients_impl, channel):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_messages_after(channel=channel) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123123123",
            deserializer=messages.Message.deserialize,
            direction="after",
            start="0",
            request=rest_clients_impl._session.get_channel_messages,
            reversing=True,
            limit=None,
        )

    def test_fetch_messages_after_with_datetime_object(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        assert rest_clients_impl.fetch_messages_after(channel=123123123, after=date) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123123123",
            deserializer=messages.Message.deserialize,
            direction="after",
            start="537340988620800000",
            request=rest_clients_impl._session.get_channel_messages,
            reversing=True,
            limit=None,
        )

    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 777777777, messages.Message)
    def test_fetch_messages_before_with_optionals(self, rest_clients_impl, channel, message):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        result = rest_clients_impl.fetch_messages_before(channel=channel, before=message, limit=52)
        assert result is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123123123",
            deserializer=messages.Message.deserialize,
            direction="before",
            start="777777777",
            request=rest_clients_impl._session.get_channel_messages,
            reversing=False,
            limit=52,
        )

    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    def test_fetch_messages_before_without_optionals(self, rest_clients_impl, channel):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_messages_before(channel=channel) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123123123",
            deserializer=messages.Message.deserialize,
            direction="before",
            start=None,
            request=rest_clients_impl._session.get_channel_messages,
            reversing=False,
            limit=None,
        )

    def test_fetch_messages_before_with_datetime_object(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        assert rest_clients_impl.fetch_messages_before(channel=123123123, before=date) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123123123",
            deserializer=messages.Message.deserialize,
            direction="before",
            start="537340988620800000",
            request=rest_clients_impl._session.get_channel_messages,
            reversing=False,
            limit=None,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 777777777, messages.Message)
    async def test_fetch_messages_around_with_limit(self, rest_clients_impl, channel, message):
        mock_message_payloads = [{"id": "202020", "content": "Nyaa"}, {"id": "2020222", "content": "Nyaa 2"}]
        mock_message_objects = [mock.MagicMock(messages.Message), mock.MagicMock(messages.Message)]
        rest_clients_impl._session.get_channel_messages.return_value = mock_message_payloads
        with mock.patch.object(messages.Message, "deserialize", side_effect=mock_message_objects):
            results = []
            async for result in rest_clients_impl.fetch_messages_around(channel, message, limit=2):
                results.append(result)
            assert results == mock_message_objects
            messages.Message.deserialize.assert_has_calls(
                [mock.call(mock_message_payloads[0]), mock.call(mock_message_payloads[1])]
            )
            rest_clients_impl._session.get_channel_messages.assert_called_once_with(
                channel_id="123123123", around="777777777", limit=2
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 777777777, messages.Message)
    async def test_fetch_messages_around_without_limit(self, rest_clients_impl, channel, message):
        mock_message_payloads = [{"id": "202020", "content": "Nyaa"}, {"id": "2020222", "content": "Nyaa 2"}]
        mock_message_objects = [mock.MagicMock(messages.Message), mock.MagicMock(messages.Message)]
        rest_clients_impl._session.get_channel_messages.return_value = mock_message_payloads
        with mock.patch.object(messages.Message, "deserialize", side_effect=mock_message_objects):
            results = []
            async for result in rest_clients_impl.fetch_messages_around(channel, message):
                results.append(result)
            assert results == mock_message_objects
            messages.Message.deserialize.assert_has_calls(
                [mock.call(mock_message_payloads[0]), mock.call(mock_message_payloads[1])]
            )
            rest_clients_impl._session.get_channel_messages.assert_called_once_with(
                channel_id="123123123", around="777777777", limit=...
            )

    @pytest.mark.asyncio
    async def test_fetch_messages_around_with_datetime_object(self, rest_clients_impl):
        mock_message_payloads = [{"id": "202020", "content": "Nyaa"}, {"id": "2020222", "content": "Nyaa 2"}]
        mock_message_objects = [mock.MagicMock(messages.Message), mock.MagicMock(messages.Message)]
        rest_clients_impl._session.get_channel_messages.return_value = mock_message_payloads
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        with mock.patch.object(messages.Message, "deserialize", side_effect=mock_message_objects):
            results = []
            async for result in rest_clients_impl.fetch_messages_around(123123123, date):
                results.append(result)
            assert results == mock_message_objects
            messages.Message.deserialize.assert_has_calls(
                [mock.call(mock_message_payloads[0]), mock.call(mock_message_payloads[1])]
            )
            rest_clients_impl._session.get_channel_messages.assert_called_once_with(
                channel_id="123123123", around="537340988620800000", limit=...
            )

    @pytest.mark.asyncio
    async def test__pagination_handler_ends_handles_empty_resource(self, rest_clients_impl):
        mock_deserialize = mock.MagicMock()
        mock_request = mock.AsyncMock(side_effect=[[]])
        async for _ in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=True,
            start="123123123",
            limit=42,
        ):
            assert False, "Async generator shouldn't have yielded anything."
        mock_request.assert_called_once_with(
            limit=42, before="123123123", random_kwarg="test",
        )
        mock_deserialize.assert_not_called()

    @pytest.mark.asyncio
    async def test__pagination_handler_ends_without_limit_with_start(self, rest_clients_impl):
        mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
        mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
        mock_deserialize = mock.MagicMock(side_effect=mock_models)
        mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
        results = []
        async for result in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=True,
            start="123123123",
            limit=None,
        ):
            results.append(result)
        assert results == mock_models
        mock_request.assert_has_calls(
            [
                mock.call(limit=100, before="123123123", random_kwarg="test"),
                mock.call(limit=100, before="20202020", random_kwarg="test"),
            ],
        )
        mock_deserialize.assert_has_calls(
            [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
        )

    @pytest.mark.asyncio
    async def test__pagination_handler_ends_without_limit_without_start(self, rest_clients_impl):
        mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
        mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
        mock_deserialize = mock.MagicMock(side_effect=mock_models)
        mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
        results = []
        async for result in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=True,
            start=None,
            limit=None,
        ):
            results.append(result)
        assert results == mock_models
        mock_request.assert_has_calls(
            [
                mock.call(limit=100, before=..., random_kwarg="test"),
                mock.call(limit=100, before="20202020", random_kwarg="test"),
            ],
        )
        mock_deserialize.assert_has_calls(
            [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
        )

    @pytest.mark.asyncio
    async def test__pagination_handler_tracks_ends_when_hits_limit(self, rest_clients_impl):
        mock_payloads = [{"id": "312312312"}, {"id": "31231231"}]
        mock_models = [mock.MagicMock(), mock.MagicMock(id=20202020)]
        mock_deserialize = mock.MagicMock(side_effect=mock_models)
        mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
        results = []
        async for result in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=False,
            start=None,
            limit=2,
        ):
            results.append(result)
        assert results == mock_models
        mock_request.assert_called_once_with(limit=2, before=..., random_kwarg="test")
        mock_deserialize.assert_has_calls([mock.call({"id": "312312312"}), mock.call({"id": "31231231"})])

    @pytest.mark.asyncio
    async def test__pagination_handler_tracks_ends_when_limit_set_but_exhausts_requested_data(self, rest_clients_impl):
        mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
        mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
        mock_deserialize = mock.MagicMock(side_effect=mock_models)
        mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
        results = []
        async for result in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=False,
            start=None,
            limit=42,
        ):
            results.append(result)
        assert results == mock_models
        mock_request.assert_has_calls(
            [
                mock.call(limit=42, before=..., random_kwarg="test"),
                mock.call(limit=39, before="20202020", random_kwarg="test"),
            ],
        )
        mock_deserialize.assert_has_calls(
            [mock.call({"id": "312312312"}), mock.call({"id": "31231231"}), mock.call({"id": "20202020"})]
        )

    @pytest.mark.asyncio
    async def test__pagination_handler_reverses_data_when_reverse_is_true(self, rest_clients_impl):
        mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
        mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
        mock_deserialize = mock.MagicMock(side_effect=mock_models)
        mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
        results = []
        async for result in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=True,
            start=None,
            limit=None,
        ):
            results.append(result)
        assert results == mock_models
        mock_request.assert_has_calls(
            [
                mock.call(limit=100, before=..., random_kwarg="test"),
                mock.call(limit=100, before="20202020", random_kwarg="test"),
            ],
        )
        mock_deserialize.assert_has_calls(
            [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
        )

    @pytest.mark.asyncio
    async def test__pagination_handler_id_getter(self, rest_clients_impl):
        mock_payloads = [{"id": "312312312"}, {"id": "20202020"}]
        mock_models = [mock.MagicMock(), mock.MagicMock(user=mock.MagicMock(__int__=lambda x: 20202020))]
        mock_deserialize = mock.MagicMock(side_effect=mock_models)
        mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
        results = []
        async for result in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=False,
            start=None,
            id_getter=lambda entity: str(int(entity.user)),
            limit=None,
        ):
            results.append(result)
        assert results == mock_models
        mock_request.assert_has_calls(
            [
                mock.call(limit=100, before=..., random_kwarg="test"),
                mock.call(limit=100, before="20202020", random_kwarg="test"),
            ],
        )
        mock_deserialize.assert_has_calls([mock.call({"id": "312312312"}), mock.call({"id": "20202020"})])

    @pytest.mark.asyncio
    async def test__pagination_handler_handles_no_initial_data(self, rest_clients_impl):
        mock_deserialize = mock.MagicMock()
        mock_request = mock.AsyncMock(side_effect=[[]])
        async for _ in rest_clients_impl._pagination_handler(
            random_kwarg="test",
            deserializer=mock_deserialize,
            direction="before",
            request=mock_request,
            reversing=True,
            start=None,
            limit=None,
        ):
            assert False, "Async generator shouldn't have yielded anything."
        mock_request.assert_called_once_with(
            limit=100, before=..., random_kwarg="test",
        )
        mock_deserialize.assert_not_called()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 55555, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 565656, messages.Message)
    async def test_fetch_message(self, rest_clients_impl, channel, message):
        mock_payload = {"id": "9409404", "content": "I AM A MESSAGE!"}
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl._session.get_channel_message.return_value = mock_payload
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_clients_impl.fetch_message(channel=channel, message=message) is mock_message_obj
            rest_clients_impl._session.get_channel_message.assert_called_once_with(
                channel_id="55555", message_id="565656",
            )
            messages.Message.deserialize.assert_called_once_with(mock_payload)

    @pytest.mark.parametrize(
        ("kwargs", "expected_result"),
        [
            (
                {"mentions_everyone": True, "user_mentions": True, "role_mentions": True},
                {"parse": ["everyone", "users", "roles"]},
            ),
            (
                {"mentions_everyone": False, "user_mentions": False, "role_mentions": False},
                {"parse": [], "users": [], "roles": []},
            ),
            (
                {"mentions_everyone": True, "user_mentions": ["1123123"], "role_mentions": True},
                {"parse": ["everyone", "roles"], "users": ["1123123"]},
            ),
            (
                {"mentions_everyone": True, "user_mentions": True, "role_mentions": ["1231123"]},
                {"parse": ["everyone", "users"], "roles": ["1231123"]},
            ),
            (
                {"mentions_everyone": False, "user_mentions": ["1123123"], "role_mentions": True},
                {"parse": ["roles"], "users": ["1123123"]},
            ),
            (
                {"mentions_everyone": False, "user_mentions": True, "role_mentions": ["1231123"]},
                {"parse": ["users"], "roles": ["1231123"]},
            ),
            (
                {"mentions_everyone": False, "user_mentions": ["1123123"], "role_mentions": False},
                {"parse": [], "roles": [], "users": ["1123123"]},
            ),
            (
                {"mentions_everyone": False, "user_mentions": False, "role_mentions": ["1231123"]},
                {"parse": [], "roles": ["1231123"], "users": []},
            ),
            (
                {"mentions_everyone": False, "user_mentions": ["22222"], "role_mentions": ["1231123"]},
                {"parse": [], "users": ["22222"], "roles": ["1231123"]},
            ),
            (
                {"mentions_everyone": True, "user_mentions": ["22222"], "role_mentions": ["1231123"]},
                {"parse": ["everyone"], "users": ["22222"], "roles": ["1231123"]},
            ),
        ],
    )
    def test_generate_allowed_mentions(self, rest_clients_impl, kwargs, expected_result):
        assert rest_clients_impl._generate_allowed_mentions(**kwargs) == expected_result

    @_helpers.parametrize_valid_id_formats_for_models("role", 3, guilds.GuildRole)
    def test_generate_allowed_mentions_removes_duplicate_role_ids(self, rest_clients_impl, role):
        result = rest_clients_impl._generate_allowed_mentions(
            role_mentions=["1", "2", "1", "3", "5", "7", "2", role], user_mentions=True, mentions_everyone=True
        )
        assert result == {"roles": ["1", "2", "3", "5", "7"], "parse": ["everyone", "users"]}

    @_helpers.parametrize_valid_id_formats_for_models("user", 3, users.User)
    def test_generate_allowed_mentions_removes_duplicate_user_ids(self, rest_clients_impl, user):
        result = rest_clients_impl._generate_allowed_mentions(
            role_mentions=True, user_mentions=["1", "2", "1", "3", "5", "7", "2", user], mentions_everyone=True
        )
        assert result == {"users": ["1", "2", "3", "5", "7"], "parse": ["everyone", "roles"]}

    @_helpers.parametrize_valid_id_formats_for_models("role", 190007233919057920, guilds.GuildRole)
    def test_generate_allowed_mentions_handles_all_role_formats(self, rest_clients_impl, role):
        result = rest_clients_impl._generate_allowed_mentions(
            role_mentions=[role], user_mentions=True, mentions_everyone=True
        )
        assert result == {"roles": ["190007233919057920"], "parse": ["everyone", "users"]}

    @_helpers.parametrize_valid_id_formats_for_models("user", 190007233919057920, users.User)
    def test_generate_allowed_mentions_handles_all_user_formats(self, rest_clients_impl, user):
        result = rest_clients_impl._generate_allowed_mentions(
            role_mentions=True, user_mentions=[user], mentions_everyone=True
        )
        assert result == {"users": ["190007233919057920"], "parse": ["everyone", "roles"]}

    @_helpers.assert_raises(type_=ValueError)
    def test_generate_allowed_mentions_raises_error_on_too_many_roles(self, rest_clients_impl):
        rest_clients_impl._generate_allowed_mentions(
            user_mentions=False, role_mentions=list(range(101)), mentions_everyone=False
        )

    @_helpers.assert_raises(type_=ValueError)
    def test_generate_allowed_mentions_raises_error_on_too_many_users(self, rest_clients_impl):
        rest_clients_impl._generate_allowed_mentions(
            user_mentions=list(range(101)), role_mentions=False, mentions_everyone=False
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 694463529998352394, channels.Channel)
    async def test_create_message_with_optionals(self, rest_clients_impl, channel):
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_message_payload = {"id": "2929292992", "content": "222922"}
        rest_clients_impl._session.create_message.return_value = mock_message_payload
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        mock_embed_payload = {"description": "424242"}
        mock_embed_obj = mock.create_autospec(
            embeds.Embed, auto_spec=True, serialize=mock.MagicMock(return_value=mock_embed_payload)
        )
        mock_media_obj = mock.MagicMock()
        mock_media_payload = ("aName.png", mock.MagicMock())
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            with mock.patch.object(media, "safe_read_file", return_value=mock_media_payload):
                result = await rest_clients_impl.create_message(
                    channel,
                    content="A CONTENT",
                    nonce="69696969696969",
                    tts=True,
                    files=[mock_media_obj],
                    embed=mock_embed_obj,
                    mentions_everyone=False,
                    user_mentions=False,
                    role_mentions=False,
                )
                assert result is mock_message_obj
                media.safe_read_file.assert_called_once_with(mock_media_obj)
                messages.Message.deserialize.assert_called_once_with(mock_message_payload)
        rest_clients_impl._session.create_message.assert_called_once_with(
            channel_id="694463529998352394",
            content="A CONTENT",
            nonce="69696969696969",
            tts=True,
            files=[mock_media_payload],
            embed=mock_embed_payload,
            allowed_mentions=mock_allowed_mentions_payload,
        )
        mock_embed_obj.serialize.assert_called_once()
        rest_clients_impl._generate_allowed_mentions.assert_called_once_with(
            mentions_everyone=False, user_mentions=False, role_mentions=False
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 694463529998352394, channels.Channel)
    async def test_create_message_without_optionals(self, rest_clients_impl, channel):
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_message_payload = {"id": "2929292992", "content": "222922"}
        rest_clients_impl._session.create_message.return_value = mock_message_payload
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_clients_impl.create_message(channel) is mock_message_obj
            messages.Message.deserialize.assert_called_once_with(mock_message_payload)
        rest_clients_impl._session.create_message.assert_called_once_with(
            channel_id="694463529998352394",
            content=...,
            nonce=...,
            tts=...,
            files=...,
            embed=...,
            allowed_mentions=mock_allowed_mentions_payload,
        )
        rest_clients_impl._generate_allowed_mentions.assert_called_once_with(
            mentions_everyone=True, user_mentions=True, role_mentions=True
        )

    @pytest.mark.asyncio
    async def test_safe_create_message_without_optionals(self, rest_clients_impl):
        channel = mock.MagicMock(channels.Channel)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl.create_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_clients_impl.safe_create_message(channel,)
        assert result is mock_message_obj
        rest_clients_impl.create_message.assert_called_once_with(
            channel=channel,
            content=...,
            nonce=...,
            tts=...,
            files=...,
            embed=...,
            mentions_everyone=False,
            user_mentions=False,
            role_mentions=False,
        )

    @pytest.mark.asyncio
    async def test_safe_create_message_with_optionals(self, rest_clients_impl):
        channel = mock.MagicMock(channels.Channel)
        mock_embed_obj = mock.create_autospec(embeds.Embed)
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_media_obj = mock.MagicMock(bytes)
        rest_clients_impl.create_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_clients_impl.safe_create_message(
            channel=channel,
            content="A CONTENT",
            nonce="69696969696969",
            tts=True,
            files=[mock_media_obj],
            embed=mock_embed_obj,
            mentions_everyone=True,
            user_mentions=True,
            role_mentions=True,
        )
        assert result is mock_message_obj
        rest_clients_impl.create_message.assert_called_once_with(
            channel=channel,
            content="A CONTENT",
            nonce="69696969696969",
            tts=True,
            files=[mock_media_obj],
            embed=mock_embed_obj,
            mentions_everyone=True,
            user_mentions=True,
            role_mentions=True,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.UnknownEmoji(name="blah", id=123, is_animated=False)])
    async def test_create_reaction(self, rest_clients_impl, channel, message, emoji):
        rest_clients_impl._session.create_reaction.return_value = ...
        assert await rest_clients_impl.create_reaction(channel=channel, message=message, emoji=emoji) is None
        rest_clients_impl._session.create_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.UnknownEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_reaction(self, rest_clients_impl, channel, message, emoji):
        rest_clients_impl._session.delete_own_reaction.return_value = ...
        assert await rest_clients_impl.delete_reaction(channel=channel, message=message, emoji=emoji) is None
        rest_clients_impl._session.delete_own_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    async def test_delete_all_reactions(self, rest_clients_impl, channel, message):
        rest_clients_impl._session.delete_all_reactions.return_value = ...
        assert await rest_clients_impl.delete_all_reactions(channel=channel, message=message) is None
        rest_clients_impl._session.delete_all_reactions.assert_called_once_with(
            channel_id="213123", message_id="987654321",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.UnknownEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_all_reactions_for_emoji(self, rest_clients_impl, channel, message, emoji):
        rest_clients_impl._session.delete_all_reactions_for_emoji.return_value = ...
        assert (
            await rest_clients_impl.delete_all_reactions_for_emoji(channel=channel, message=message, emoji=emoji)
            is None
        )
        rest_clients_impl._session.delete_all_reactions_for_emoji.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.Channel)
    @pytest.mark.parametrize(
        "emoji", ["tutu1:456371206225002499", mock.MagicMock(emojis.GuildEmoji, url_name="tutu1:456371206225002499")]
    )
    @_helpers.parametrize_valid_id_formats_for_models("user", 140502780547694592, users.User)
    def test_fetch_reactors_after_with_optionals(self, rest_clients_impl, message, channel, emoji, user):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        result = rest_clients_impl.fetch_reactors_after(channel, message, emoji, after=user, limit=47)
        assert result is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123",
            message_id="432",
            emoji="tutu1:456371206225002499",
            deserializer=users.User.deserialize,
            direction="after",
            request=rest_clients_impl._session.get_reactions,
            reversing=False,
            start="140502780547694592",
            limit=47,
        )

    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.Channel)
    @pytest.mark.parametrize(
        "emoji", ["tutu1:456371206225002499", mock.MagicMock(emojis.GuildEmoji, url_name="tutu1:456371206225002499")]
    )
    def test_fetch_reactors_after_without_optionals(self, rest_clients_impl, message, channel, emoji):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_reactors_after(channel, message, emoji) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123",
            message_id="432",
            emoji="tutu1:456371206225002499",
            deserializer=users.User.deserialize,
            direction="after",
            request=rest_clients_impl._session.get_reactions,
            reversing=False,
            start="0",
            limit=None,
        )

    def test_fetch_reactors_after_with_datetime_object(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        result = rest_clients_impl.fetch_reactors_after(123, 432, "tutu1:456371206225002499", after=date)
        assert result is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            channel_id="123",
            message_id="432",
            emoji="tutu1:456371206225002499",
            deserializer=users.User.deserialize,
            direction="after",
            request=rest_clients_impl._session.get_reactions,
            reversing=False,
            start="537340988620800000",
            limit=None,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.Channel)
    async def test_update_message_with_optionals(self, rest_clients_impl, message, channel):
        mock_payload = {"id": "4242", "content": "I HAVE BEEN UPDATED!"}
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_embed_payload = {"description": "blahblah"}
        mock_embed = mock.create_autospec(
            embeds.Embed, auto_spec=True, serialize=mock.MagicMock(return_value=mock_embed_payload)
        )
        mock_allowed_mentions_payload = {"parse": [], "users": ["123"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        rest_clients_impl._session.edit_message.return_value = mock_payload
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            result = await rest_clients_impl.update_message(
                message=message,
                channel=channel,
                content="C O N T E N T",
                embed=mock_embed,
                flags=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
                mentions_everyone=False,
                role_mentions=False,
                user_mentions=[123123123],
            )
            assert result is mock_message_obj
            rest_clients_impl._session.edit_message.assert_called_once_with(
                channel_id="123",
                message_id="432",
                content="C O N T E N T",
                embed=mock_embed_payload,
                flags=6,
                allowed_mentions=mock_allowed_mentions_payload,
            )
            mock_embed.serialize.assert_called_once()
            messages.Message.deserialize.assert_called_once_with(mock_payload)
            rest_clients_impl._generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=False, role_mentions=False, user_mentions=[123123123]
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.Channel)
    async def test_update_message_without_optionals(self, rest_clients_impl, message, channel):
        mock_payload = {"id": "4242", "content": "I HAVE BEEN UPDATED!"}
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        rest_clients_impl._session.edit_message.return_value = mock_payload
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_clients_impl.update_message(message=message, channel=channel) is mock_message_obj
            rest_clients_impl._session.edit_message.assert_called_once_with(
                channel_id="123",
                message_id="432",
                content=...,
                embed=...,
                flags=...,
                allowed_mentions=mock_allowed_mentions_payload,
            )
            messages.Message.deserialize.assert_called_once_with(mock_payload)
            rest_clients_impl._generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=True, user_mentions=True, role_mentions=True
            )

    @pytest.mark.asyncio
    async def test_safe_update_message_without_optionals(self, rest_clients_impl):
        message = mock.MagicMock(messages.Message)
        channel = mock.MagicMock(channels.Channel)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl.update_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_clients_impl.safe_update_message(message=message, channel=channel,)
        assert result is mock_message_obj
        rest_clients_impl.update_message.safe_update_message(
            message=message,
            channel=channel,
            content=...,
            embed=...,
            flags=...,
            mentions_everyone=False,
            role_mentions=False,
            user_mentions=False,
        )

    @pytest.mark.asyncio
    async def test_safe_update_message_with_optionals(self, rest_clients_impl):
        message = mock.MagicMock(messages.Message)
        channel = mock.MagicMock(channels.Channel)
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl.update_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_clients_impl.safe_update_message(
            message=message,
            channel=channel,
            content="C O N T E N T",
            embed=mock_embed,
            flags=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
            mentions_everyone=True,
            role_mentions=True,
            user_mentions=True,
        )
        assert result is mock_message_obj
        rest_clients_impl.update_message.assert_called_once_with(
            message=message,
            channel=channel,
            content="C O N T E N T",
            embed=mock_embed,
            flags=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
            mentions_everyone=True,
            role_mentions=True,
            user_mentions=True,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 115590097100865541, messages.Message)
    async def test_delete_messages_singular(self, rest_clients_impl, channel, message):
        rest_clients_impl._session.delete_message.return_value = ...
        assert await rest_clients_impl.delete_messages(channel, message) is None
        rest_clients_impl._session.delete_message.assert_called_once_with(
            channel_id="379953393319542784", message_id="115590097100865541",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 115590097100865541, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 115590097100865541, messages.Message)
    async def test_delete_messages_singular_after_duplicate_removal(
        self, rest_clients_impl, channel, message, additional_message
    ):
        rest_clients_impl._session.delete_message.return_value = ...
        assert await rest_clients_impl.delete_messages(channel, message, additional_message) is None
        rest_clients_impl._session.delete_message.assert_called_once_with(
            channel_id="379953393319542784", message_id="115590097100865541",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 115590097100865541, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 572144340277919754, messages.Message)
    async def test_delete_messages_bulk_removes_duplicates(
        self, rest_clients_impl, channel, message, additional_message
    ):
        rest_clients_impl._session.bulk_delete_messages.return_value = ...
        assert await rest_clients_impl.delete_messages(channel, message, additional_message, 115590097100865541) is None
        rest_clients_impl._session.bulk_delete_messages.assert_called_once_with(
            channel_id="379953393319542784", messages=["115590097100865541", "572144340277919754"],
        )
        rest_clients_impl._session.delete_message.assert_not_called()

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=ValueError)
    async def test_delete_messages_raises_value_error_on_over_100_messages(self, rest_clients_impl):
        rest_clients_impl._session.bulk_delete_messages.return_value = ...
        assert await rest_clients_impl.delete_messages(123123, *list(range(0, 111))) is None

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 4123123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 9999, channels.PermissionOverwrite)
    async def test_update_channel_overwrite_with_optionals(self, rest_clients_impl, channel, overwrite):
        rest_clients_impl._session.edit_channel_permissions.return_value = ...
        result = await rest_clients_impl.update_channel_overwrite(
            channel=channel,
            overwrite=overwrite,
            target_type="member",
            allow=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
            deny=21,
            reason="get Nyaa'd",
        )
        assert result is None
        rest_clients_impl._session.edit_channel_permissions.assert_called_once_with(
            channel_id="4123123", overwrite_id="9999", type_="member", allow=6, deny=21, reason="get Nyaa'd",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 4123123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 9999, channels.PermissionOverwrite)
    async def test_update_channel_overwrite_without_optionals(self, rest_clients_impl, channel, overwrite):
        rest_clients_impl._session.edit_channel_permissions.return_value = ...
        result = await rest_clients_impl.update_channel_overwrite(
            channel=channel, overwrite=overwrite, target_type="member"
        )
        assert result is None
        rest_clients_impl._session.edit_channel_permissions.assert_called_once_with(
            channel_id="4123123", overwrite_id="9999", type_="member", allow=..., deny=..., reason=...,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "target",
        [
            mock.MagicMock(guilds.GuildRole, id=snowflakes.Snowflake(9999), __int__=guilds.GuildRole.__int__),
            mock.MagicMock(users.User, id=snowflakes.Snowflake(9999), __int__=users.User.__int__),
        ],
    )
    async def test_update_channel_overwrite_with_alternative_target_object(self, rest_clients_impl, target):
        rest_clients_impl._session.edit_channel_permissions.return_value = ...
        result = await rest_clients_impl.update_channel_overwrite(
            channel=4123123, overwrite=target, target_type="member"
        )
        assert result is None
        rest_clients_impl._session.edit_channel_permissions.assert_called_once_with(
            channel_id="4123123", overwrite_id="9999", type_="member", allow=..., deny=..., reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    async def test_fetch_invites_for_channel(self, rest_clients_impl, channel):
        mock_invite_payload = {"code": "ogogogogogogogo", "guild_id": "123123123"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_clients_impl._session.get_channel_invites.return_value = [mock_invite_payload]
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            assert await rest_clients_impl.fetch_invites_for_channel(channel=channel) == [mock_invite_obj]
            rest_clients_impl._session.get_channel_invites.assert_called_once_with(channel_id="123123123")
            invites.InviteWithMetadata.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 234123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("user", 333333, users.User)
    @pytest.mark.parametrize("max_age", [4444, datetime.timedelta(seconds=4444)])
    async def test_create_invite_for_channel_with_optionals(self, rest_clients_impl, channel, user, max_age):
        mock_invite_payload = {"code": "ogogogogogogogo", "guild_id": "123123123"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_clients_impl._session.create_channel_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            result = await rest_clients_impl.create_invite_for_channel(
                channel,
                max_age=max_age,
                max_uses=444,
                temporary=True,
                unique=False,
                target_user=user,
                target_user_type=invites.TargetUserType.STREAM,
                reason="Hello there.",
            )
            assert result is mock_invite_obj
            rest_clients_impl._session.create_channel_invite.assert_called_once_with(
                channel_id="234123",
                max_age=4444,
                max_uses=444,
                temporary=True,
                unique=False,
                target_user="333333",
                target_user_type=1,
                reason="Hello there.",
            )
            invites.InviteWithMetadata.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 234123, channels.Channel)
    async def test_create_invite_for_channel_without_optionals(self, rest_clients_impl, channel):
        mock_invite_payload = {"code": "ogogogogogogogo", "guild_id": "123123123"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_clients_impl._session.create_channel_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            assert await rest_clients_impl.create_invite_for_channel(channel) is mock_invite_obj
            rest_clients_impl._session.create_channel_invite.assert_called_once_with(
                channel_id="234123",
                max_age=...,
                max_uses=...,
                temporary=...,
                unique=...,
                target_user=...,
                target_user_type=...,
                reason=...,
            )
            invites.InviteWithMetadata.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 123123123, channels.PermissionOverwrite)
    async def test_delete_channel_overwrite(self, rest_clients_impl, channel, overwrite):
        rest_clients_impl._session.delete_channel_permission.return_value = ...
        assert await rest_clients_impl.delete_channel_overwrite(channel=channel, overwrite=overwrite) is None
        rest_clients_impl._session.delete_channel_permission.assert_called_once_with(
            channel_id="379953393319542784", overwrite_id="123123123",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "target",
        [
            mock.MagicMock(guilds.GuildRole, id=snowflakes.Snowflake(123123123), __int__=guilds.GuildRole.__int__),
            mock.MagicMock(users.User, id=snowflakes.Snowflake(123123123), __int__=users.User.__int__),
        ],
    )
    async def test_delete_channel_overwrite_with_alternative_target_objects(self, rest_clients_impl, target):
        rest_clients_impl._session.delete_channel_permission.return_value = ...
        assert await rest_clients_impl.delete_channel_overwrite(channel=379953393319542784, overwrite=target) is None
        rest_clients_impl._session.delete_channel_permission.assert_called_once_with(
            channel_id="379953393319542784", overwrite_id="123123123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PermissionOverwrite)
    async def test_trigger_typing(self, rest_clients_impl, channel):
        rest_clients_impl._session.trigger_typing_indicator.return_value = ...
        assert await rest_clients_impl.trigger_typing(channel) is None
        rest_clients_impl._session.trigger_typing_indicator.assert_called_once_with(channel_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.Channel)
    async def test_fetch_pins(self, rest_clients_impl, channel):
        mock_message_payload = {"id": "21232", "content": "CONTENT"}
        mock_message_obj = mock.MagicMock(messages.Message, id=21232)
        rest_clients_impl._session.get_pinned_messages.return_value = [mock_message_payload]
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_clients_impl.fetch_pins(channel) == {21232: mock_message_obj}
            rest_clients_impl._session.get_pinned_messages.assert_called_once_with(channel_id="123123123")
            messages.Message.deserialize.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 292929, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 123123, messages.Message)
    async def test_pin_message(self, rest_clients_impl, channel, message):
        rest_clients_impl._session.add_pinned_channel_message.return_value = ...
        assert await rest_clients_impl.pin_message(channel, message) is None
        rest_clients_impl._session.add_pinned_channel_message.assert_called_once_with(
            channel_id="292929", message_id="123123"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 292929, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 123123, messages.Message)
    async def test_unpin_message(self, rest_clients_impl, channel, message):
        rest_clients_impl._session.delete_pinned_channel_message.return_value = ...
        assert await rest_clients_impl.unpin_message(channel, message) is None
        rest_clients_impl._session.delete_pinned_channel_message.assert_called_once_with(
            channel_id="292929", message_id="123123"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 40404040404, emojis.GuildEmoji)
    async def test_fetch_guild_emoji(self, rest_clients_impl, guild, emoji):
        mock_emoji_payload = {"id": "92929", "name": "nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_clients_impl._session.get_guild_emoji.return_value = mock_emoji_payload
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            assert await rest_clients_impl.fetch_guild_emoji(guild=guild, emoji=emoji) is mock_emoji_obj
            rest_clients_impl._session.get_guild_emoji.assert_called_once_with(
                guild_id="93443949", emoji_id="40404040404",
            )
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    async def test_fetch_guild_emojis(self, rest_clients_impl, guild):
        mock_emoji_payload = {"id": "92929", "name": "nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_clients_impl._session.list_guild_emojis.return_value = [mock_emoji_payload]
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            assert await rest_clients_impl.fetch_guild_emojis(guild=guild) == [mock_emoji_obj]
            rest_clients_impl._session.list_guild_emojis.assert_called_once_with(guild_id="93443949",)
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 537340989808050216, guilds.GuildRole)
    async def test_create_guild_emoji_with_optionals(self, rest_clients_impl, guild, role):
        mock_emoji_payload = {"id": "229292929", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_clients_impl._session.create_guild_emoji.return_value = mock_emoji_payload
        mock_image_obj = mock.MagicMock(io.BytesIO)
        mock_image_data = mock.MagicMock(bytes)
        with mock.patch.object(conversions, "get_bytes_from_resource", return_value=mock_image_data):
            with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
                result = await rest_clients_impl.create_guild_emoji(
                    guild=guild, name="fairEmoji", image_data=mock_image_obj, roles=[role], reason="hello",
                )
                assert result is mock_emoji_obj
                emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)
            conversions.get_bytes_from_resource.assert_called_once_with(mock_image_obj)
        rest_clients_impl._session.create_guild_emoji.assert_called_once_with(
            guild_id="93443949", name="fairEmoji", image=mock_image_data, roles=["537340989808050216"], reason="hello",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    async def test_create_guild_emoji_without_optionals(self, rest_clients_impl, guild):
        mock_emoji_payload = {"id": "229292929", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_clients_impl._session.create_guild_emoji.return_value = mock_emoji_payload
        mock_image_obj = mock.MagicMock(io.BytesIO)
        mock_image_data = mock.MagicMock(bytes)
        with mock.patch.object(conversions, "get_bytes_from_resource", return_value=mock_image_data):
            with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
                result = await rest_clients_impl.create_guild_emoji(
                    guild=guild, name="fairEmoji", image_data=mock_image_obj,
                )
                assert result is mock_emoji_obj
                emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)
            conversions.get_bytes_from_resource.assert_called_once_with(mock_image_obj)
        rest_clients_impl._session.create_guild_emoji.assert_called_once_with(
            guild_id="93443949", name="fairEmoji", image=mock_image_data, roles=..., reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 4123321, emojis.GuildEmoji)
    async def test_update_guild_emoji_without_optionals(self, rest_clients_impl, guild, emoji):
        mock_emoji_payload = {"id": "202020", "name": "Nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_clients_impl._session.modify_guild_emoji.return_value = mock_emoji_payload
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            assert await rest_clients_impl.update_guild_emoji(guild, emoji) is mock_emoji_obj
            rest_clients_impl._session.modify_guild_emoji.assert_called_once_with(
                guild_id="93443949", emoji_id="4123321", name=..., roles=..., reason=...,
            )
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 4123321, emojis.GuildEmoji)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123123, guilds.GuildRole)
    async def test_update_guild_emoji_with_optionals(self, rest_clients_impl, guild, emoji, role):
        mock_emoji_payload = {"id": "202020", "name": "Nyaa", "animated": True}
        mock_emoji_obj = mock.MagicMock(emojis.GuildEmoji)
        rest_clients_impl._session.modify_guild_emoji.return_value = mock_emoji_payload
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji_obj):
            result = await rest_clients_impl.update_guild_emoji(
                guild, emoji, name="Nyaa", roles=[role], reason="Agent 42"
            )
            assert result is mock_emoji_obj
            rest_clients_impl._session.modify_guild_emoji.assert_called_once_with(
                guild_id="93443949", emoji_id="4123321", name="Nyaa", roles=["123123123"], reason="Agent 42",
            )
            emojis.GuildEmoji.deserialize.assert_called_once_with(mock_emoji_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 93443949, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("emoji", 4123321, emojis.GuildEmoji)
    async def test_delete_guild_emoji(self, rest_clients_impl, guild, emoji):
        rest_clients_impl._session.delete_guild_emoji.return_value = ...
        assert await rest_clients_impl.delete_guild_emoji(guild, emoji) is None
        rest_clients_impl._session.delete_guild_emoji.assert_called_once_with(guild_id="93443949", emoji_id="4123321")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("region", [mock.MagicMock(voices.VoiceRegion, id="LONDON"), "LONDON"])
    async def test_create_guild_with_optionals(self, rest_clients_impl, region):
        mock_guild_payload = {"id": "299292929292992", "region": "LONDON"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_clients_impl._session.create_guild.return_value = mock_guild_payload
        mock_image_obj = mock.MagicMock(io.BytesIO)
        mock_image_data = mock.MagicMock(bytes)
        mock_role_payload = {"permissions": 123123}
        mock_role_obj = mock.create_autospec(
            guilds.GuildRole, spec_set=True, serialize=mock.MagicMock(return_value=mock_role_payload)
        )
        mock_channel_payload = {"type": 2, "name": "aChannel"}
        mock_channel_obj = mock.create_autospec(
            channels.GuildChannel, spec_set=True, serialize=mock.MagicMock(return_value=mock_channel_payload)
        )
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            with mock.patch.object(conversions, "get_bytes_from_resource", return_value=mock_image_data):
                result = await rest_clients_impl.create_guild(
                    name="OK",
                    region=region,
                    icon_data=mock_image_obj,
                    verification_level=guilds.GuildVerificationLevel.NONE,
                    default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                    explicit_content_filter=guilds.GuildExplicitContentFilterLevel.MEMBERS_WITHOUT_ROLES,
                    roles=[mock_role_obj],
                    channels=[mock_channel_obj],
                )
                assert result is mock_guild_obj
                conversions.get_bytes_from_resource.assert_called_once_with(mock_image_obj)
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)
        mock_channel_obj.serialize.assert_called_once()
        mock_role_obj.serialize.assert_called_once()
        rest_clients_impl._session.create_guild.assert_called_once_with(
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
    async def test_create_guild_without_optionals(self, rest_clients_impl):
        mock_guild_payload = {"id": "299292929292992", "region": "LONDON"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_clients_impl._session.create_guild.return_value = mock_guild_payload
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            assert await rest_clients_impl.create_guild(name="OK") is mock_guild_obj
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)
        rest_clients_impl._session.create_guild.assert_called_once_with(
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
    async def test_fetch_guild(self, rest_clients_impl, guild):
        mock_guild_payload = {"id": "94949494", "name": "A guild", "roles": []}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_clients_impl._session.get_guild.return_value = mock_guild_payload
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            assert await rest_clients_impl.fetch_guild(guild) is mock_guild_obj
            rest_clients_impl._session.get_guild.assert_called_once_with(guild_id="379953393319542784")
            guilds.Guild.deserialize.assert_called_once_with(mock_guild_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("afk_channel", 669517187031105607, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("owner", 379953393319542784, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("system_channel", 537340989808050216, users.User)
    @pytest.mark.parametrize("region", ["LONDON", mock.MagicMock(voices.VoiceRegion, id="LONDON")])
    @pytest.mark.parametrize("afk_timeout", [300, datetime.timedelta(seconds=300)])
    async def test_update_guild_with_optionals(
        self, rest_clients_impl, guild, region, afk_channel, afk_timeout, owner, system_channel
    ):
        mock_guild_payload = {"id": "424242", "splash": "2lmKmklsdlksalkd"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_clients_impl._session.modify_guild.return_value = mock_guild_payload
        mock_icon_data = mock.MagicMock(bytes)
        mock_icon_obj = mock.MagicMock(io.BytesIO)
        mock_splash_data = mock.MagicMock(bytes)
        mock_splash_obj = mock.MagicMock(io.BytesIO)
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            with mock.patch.object(
                conversions, "get_bytes_from_resource", side_effect=[mock_icon_data, mock_splash_data]
            ):
                result = await rest_clients_impl.update_guild(
                    guild,
                    name="aNewName",
                    region=region,
                    verification_level=guilds.GuildVerificationLevel.LOW,
                    default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                    explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
                    afk_channel=afk_channel,
                    afk_timeout=afk_timeout,
                    icon_data=mock_icon_obj,
                    owner=owner,
                    splash_data=mock_splash_obj,
                    system_channel=system_channel,
                    reason="A good reason",
                )
                assert result is mock_guild_obj
            rest_clients_impl._session.modify_guild.assert_called_once_with(
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
    async def test_update_guild_without_optionals(self, rest_clients_impl, guild):
        mock_guild_payload = {"id": "424242", "splash": "2lmKmklsdlksalkd"}
        mock_guild_obj = mock.MagicMock(guilds.Guild)
        rest_clients_impl._session.modify_guild.return_value = mock_guild_payload
        with mock.patch.object(guilds.Guild, "deserialize", return_value=mock_guild_obj):
            assert await rest_clients_impl.update_guild(guild) is mock_guild_obj
            rest_clients_impl._session.modify_guild.assert_called_once_with(
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
    async def test_delete_guild(self, rest_clients_impl, guild):
        rest_clients_impl._session.delete_guild.return_value = ...
        assert await rest_clients_impl.delete_guild(guild) is None
        rest_clients_impl._session.delete_guild.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_channels(self, rest_clients_impl, guild):
        mock_channel_payload = {"id": "292929", "type": 1, "description": "A CHANNEL"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannel)
        rest_clients_impl._session.list_guild_channels.return_value = [mock_channel_payload]
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            assert await rest_clients_impl.fetch_guild_channels(guild) == [mock_channel_obj]
            rest_clients_impl._session.list_guild_channels.assert_called_once_with(guild_id="379953393319542784")
            channels.deserialize_channel.assert_called_once_with(mock_channel_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("category", 5555, channels.GuildCategory)
    @pytest.mark.parametrize("rate_limit_per_user", [500, datetime.timedelta(seconds=500)])
    async def test_create_guild_channel_with_optionals(self, rest_clients_impl, guild, category, rate_limit_per_user):
        mock_channel_payload = {"id": "22929292", "type": "5", "description": "A  C H A N N E L"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannel)
        mock_overwrite_payload = {"type": "member", "id": "30303030"}
        mock_overwrite_obj = mock.MagicMock(
            channels.PermissionOverwrite, serialize=mock.MagicMock(return_value=mock_overwrite_payload)
        )
        rest_clients_impl._session.create_guild_channel.return_value = mock_channel_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            result = await rest_clients_impl.create_guild_channel(
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
            rest_clients_impl._session.create_guild_channel.assert_called_once_with(
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
    async def test_create_guild_channel_without_optionals(self, rest_clients_impl, guild):
        mock_channel_payload = {"id": "22929292", "type": "5", "description": "A  C H A N N E L"}
        mock_channel_obj = mock.MagicMock(channels.GuildChannel)
        rest_clients_impl._session.create_guild_channel.return_value = mock_channel_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            assert await rest_clients_impl.create_guild_channel(guild, "Hi-i-am-a-name") is mock_channel_obj
            rest_clients_impl._session.create_guild_channel.assert_called_once_with(
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
    async def test_reposition_guild_channels(self, rest_clients_impl, guild, channel, second_channel):
        rest_clients_impl._session.modify_guild_channel_positions.return_value = ...
        assert await rest_clients_impl.reposition_guild_channels(guild, (1, channel), (2, second_channel)) is None
        rest_clients_impl._session.modify_guild_channel_positions.assert_called_once_with(
            "123123123", ("379953393319542784", 1), ("115590097100865541", 2)
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 444444, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 123123123123, users.User)
    async def test_fetch_member(self, rest_clients_impl, guild, user):
        mock_member_payload = {"user": {}, "nick": "! Agent 47"}
        mock_member_obj = mock.MagicMock(guilds.GuildMember)
        rest_clients_impl._session.get_guild_member.return_value = mock_member_payload
        with mock.patch.object(guilds.GuildMember, "deserialize", return_value=mock_member_obj):
            assert await rest_clients_impl.fetch_member(guild, user) is mock_member_obj
            rest_clients_impl._session.get_guild_member.assert_called_once_with(
                guild_id="444444", user_id="123123123123"
            )
            guilds.GuildMember.deserialize.assert_called_once_with(mock_member_payload)

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 115590097100865541, users.User)
    def test_fetch_members_after_with_optionals(self, rest_clients_impl, guild, user):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_members_after(guild, after=user, limit=34) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            guild_id="574921006817476608",
            deserializer=guilds.GuildMember.deserialize,
            direction="after",
            request=rest_clients_impl._session.list_guild_members,
            reversing=False,
            start="115590097100865541",
            limit=34,
            id_getter=rest_clients._get_member_id,
        )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_members_after_without_optionals(self, rest_clients_impl, guild):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_members_after(guild) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            guild_id="574921006817476608",
            deserializer=guilds.GuildMember.deserialize,
            direction="after",
            request=rest_clients_impl._session.list_guild_members,
            reversing=False,
            start="0",
            limit=None,
            id_getter=rest_clients._get_member_id,
        )

    def test_fetch_members_after_with_datetime_object(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        assert rest_clients_impl.fetch_members_after(574921006817476608, after=date) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            guild_id="574921006817476608",
            deserializer=guilds.GuildMember.deserialize,
            direction="after",
            request=rest_clients_impl._session.list_guild_members,
            reversing=False,
            start="537340988620800000",
            limit=None,
            id_getter=rest_clients._get_member_id,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 229292992, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 1010101010, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 11100010, guilds.GuildRole)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.GuildVoiceChannel)
    async def test_update_member_with_optionals(self, rest_clients_impl, guild, user, role, channel):
        rest_clients_impl._session.modify_guild_member.return_value = ...
        result = await rest_clients_impl.update_member(
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
        rest_clients_impl._session.modify_guild_member.assert_called_once_with(
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
    async def test_update_member_without_optionals(self, rest_clients_impl, guild, user):
        rest_clients_impl._session.modify_guild_member.return_value = ...
        assert await rest_clients_impl.update_member(guild, user) is None
        rest_clients_impl._session.modify_guild_member.assert_called_once_with(
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
    async def test_update_my_member_nickname_with_reason(self, rest_clients_impl, guild):
        rest_clients_impl._session.modify_current_user_nick.return_value = ...
        result = await rest_clients_impl.update_my_member_nickname(
            guild, "Nick's nick", reason="I want to drink your blood."
        )
        assert result is None
        rest_clients_impl._session.modify_current_user_nick.assert_called_once_with(
            guild_id="229292992", nick="Nick's nick", reason="I want to drink your blood."
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 229292992, guilds.Guild)
    async def test_update_my_member_nickname_without_reason(self, rest_clients_impl, guild):
        rest_clients_impl._session.modify_current_user_nick.return_value = ...
        assert await rest_clients_impl.update_my_member_nickname(guild, "Nick's nick") is None
        rest_clients_impl._session.modify_current_user_nick.assert_called_once_with(
            guild_id="229292992", nick="Nick's nick", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_add_role_to_member_with_reason(self, rest_clients_impl, guild, user, role):
        rest_clients_impl._session.add_guild_member_role.return_value = ...
        assert await rest_clients_impl.add_role_to_member(guild, user, role, reason="Get role'd") is None
        rest_clients_impl._session.add_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason="Get role'd"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_add_role_to_member_without_reason(self, rest_clients_impl, guild, user, role):
        rest_clients_impl._session.add_guild_member_role.return_value = ...
        assert await rest_clients_impl.add_role_to_member(guild, user, role) is None
        rest_clients_impl._session.add_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_remove_role_from_member_with_reason(self, rest_clients_impl, guild, user, role):
        rest_clients_impl._session.remove_guild_member_role.return_value = ...
        assert await rest_clients_impl.remove_role_from_member(guild, user, role, reason="Get role'd") is None
        rest_clients_impl._session.remove_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason="Get role'd"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @_helpers.parametrize_valid_id_formats_for_models("role", 101010101, guilds.GuildRole)
    async def test_remove_role_from_member_without_reason(self, rest_clients_impl, guild, user, role):
        rest_clients_impl._session.remove_guild_member_role.return_value = ...
        assert await rest_clients_impl.remove_role_from_member(guild, user, role) is None
        rest_clients_impl._session.remove_guild_member_role.assert_called_once_with(
            guild_id="123123123", user_id="4444444", role_id="101010101", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_kick_member_with_reason(self, rest_clients_impl, guild, user):
        rest_clients_impl._session.remove_guild_member.return_value = ...
        assert await rest_clients_impl.kick_member(guild, user, reason="TO DO") is None
        rest_clients_impl._session.remove_guild_member.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason="TO DO"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_kick_member_without_reason(self, rest_clients_impl, guild, user):
        rest_clients_impl._session.remove_guild_member.return_value = ...
        assert await rest_clients_impl.kick_member(guild, user) is None
        rest_clients_impl._session.remove_guild_member.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_fetch_ban(self, rest_clients_impl, guild, user):
        mock_ban_payload = {"reason": "42'd", "user": {}}
        mock_ban_obj = mock.MagicMock(guilds.GuildMemberBan)
        rest_clients_impl._session.get_guild_ban.return_value = mock_ban_payload
        with mock.patch.object(guilds.GuildMemberBan, "deserialize", return_value=mock_ban_obj):
            assert await rest_clients_impl.fetch_ban(guild, user) is mock_ban_obj
            rest_clients_impl._session.get_guild_ban.assert_called_once_with(guild_id="123123123", user_id="4444444")
            guilds.GuildMemberBan.deserialize.assert_called_once_with(mock_ban_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    async def test_fetch_bans(self, rest_clients_impl, guild):
        mock_ban_payload = {"reason": "42'd", "user": {}}
        mock_ban_obj = mock.MagicMock(guilds.GuildMemberBan)
        rest_clients_impl._session.get_guild_bans.return_value = [mock_ban_payload]
        with mock.patch.object(guilds.GuildMemberBan, "deserialize", return_value=mock_ban_obj):
            assert await rest_clients_impl.fetch_bans(guild) == [mock_ban_obj]
            rest_clients_impl._session.get_guild_bans.assert_called_once_with(guild_id="123123123")
            guilds.GuildMemberBan.deserialize.assert_called_once_with(mock_ban_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    @pytest.mark.parametrize("delete_message_days", [datetime.timedelta(days=12), 12])
    async def test_ban_member_with_optionals(self, rest_clients_impl, guild, user, delete_message_days):
        rest_clients_impl._session.create_guild_ban.return_value = ...
        result = await rest_clients_impl.ban_member(guild, user, delete_message_days=delete_message_days, reason="bye")
        assert result is None
        rest_clients_impl._session.create_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", delete_message_days=12, reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_ban_member_without_optionals(self, rest_clients_impl, guild, user):
        rest_clients_impl._session.create_guild_ban.return_value = ...
        assert await rest_clients_impl.ban_member(guild, user) is None
        rest_clients_impl._session.create_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", delete_message_days=..., reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_unban_member_with_reason(self, rest_clients_impl, guild, user):
        rest_clients_impl._session.remove_guild_ban.return_value = ...
        result = await rest_clients_impl.unban_member(guild, user, reason="bye")
        assert result is None
        rest_clients_impl._session.remove_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason="bye"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 123123123, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 4444444, users.User)
    async def test_unban_member_without_reason(self, rest_clients_impl, guild, user):
        rest_clients_impl._session.remove_guild_ban.return_value = ...
        assert await rest_clients_impl.unban_member(guild, user) is None
        rest_clients_impl._session.remove_guild_ban.assert_called_once_with(
            guild_id="123123123", user_id="4444444", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_roles(self, rest_clients_impl, guild):
        mock_role_payload = {"id": "33030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole, id=33030)
        rest_clients_impl._session.get_guild_roles.return_value = [mock_role_payload]
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            assert await rest_clients_impl.fetch_roles(guild) == {33030: mock_role_obj}
            rest_clients_impl._session.get_guild_roles.assert_called_once_with(guild_id="574921006817476608")
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_create_role_with_optionals(self, rest_clients_impl, guild):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_clients_impl._session.create_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_clients_impl.create_role(
                guild,
                name="Roleington",
                permissions=permissions.Permission.STREAM | permissions.Permission.EMBED_LINKS,
                color=colors.Color(21312),
                hoist=True,
                mentionable=False,
                reason="And then there was a role.",
            )
            assert result is mock_role_obj
            rest_clients_impl._session.create_guild_role.assert_called_once_with(
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
    async def test_create_role_without_optionals(self, rest_clients_impl, guild):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_clients_impl._session.create_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_clients_impl.create_role(guild)
            assert result is mock_role_obj
            rest_clients_impl._session.create_guild_role.assert_called_once_with(
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
    async def test_reposition_roles(self, rest_clients_impl, guild, role, additional_role):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_clients_impl._session.modify_guild_role_positions.return_value = [mock_role_payload]
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_clients_impl.reposition_roles(guild, (1, role), (2, additional_role))
            assert result == [mock_role_obj]
            rest_clients_impl._session.modify_guild_role_positions.assert_called_once_with(
                "574921006817476608", ("123123", 1), ("123456", 2)
            )
            guilds.GuildRole.deserialize.assert_called_once_with(mock_role_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("role", 123123, guilds.GuildRole)
    async def test_update_role_with_optionals(self, rest_clients_impl, guild, role):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_clients_impl._session.modify_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            result = await rest_clients_impl.update_role(
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
            rest_clients_impl._session.modify_guild_role.assert_called_once_with(
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
    async def test_update_role_without_optionals(self, rest_clients_impl, guild, role):
        mock_role_payload = {"id": "033030", "permissions": 333, "name": "ROlE"}
        mock_role_obj = mock.MagicMock(guilds.GuildRole)
        rest_clients_impl._session.modify_guild_role.return_value = mock_role_payload
        with mock.patch.object(guilds.GuildRole, "deserialize", return_value=mock_role_obj):
            assert await rest_clients_impl.update_role(guild, role) is mock_role_obj
            rest_clients_impl._session.modify_guild_role.assert_called_once_with(
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
    async def test_delete_role(self, rest_clients_impl, guild, role):
        rest_clients_impl._session.delete_guild_role.return_value = ...
        assert await rest_clients_impl.delete_role(guild, role) is None
        rest_clients_impl._session.delete_guild_role.assert_called_once_with(
            guild_id="574921006817476608", role_id="123123"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("days", [7, datetime.timedelta(days=7)])
    async def test_estimate_guild_prune_count(self, rest_clients_impl, guild, days):
        rest_clients_impl._session.get_guild_prune_count.return_value = 42
        assert await rest_clients_impl.estimate_guild_prune_count(guild, days) == 42
        rest_clients_impl._session.get_guild_prune_count.assert_called_once_with(guild_id="574921006817476608", days=7)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("days", [7, datetime.timedelta(days=7)])
    async def test_estimate_guild_with_optionals(self, rest_clients_impl, guild, days):
        rest_clients_impl._session.begin_guild_prune.return_value = None
        assert await rest_clients_impl.begin_guild_prune(guild, days, compute_prune_count=True, reason="nah m8") is None
        rest_clients_impl._session.begin_guild_prune.assert_called_once_with(
            guild_id="574921006817476608", days=7, compute_prune_count=True, reason="nah m8"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @pytest.mark.parametrize("days", [7, datetime.timedelta(days=7)])
    async def test_estimate_guild_without_optionals(self, rest_clients_impl, guild, days):
        rest_clients_impl._session.begin_guild_prune.return_value = 42
        assert await rest_clients_impl.begin_guild_prune(guild, days) == 42
        rest_clients_impl._session.begin_guild_prune.assert_called_once_with(
            guild_id="574921006817476608", days=7, compute_prune_count=..., reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_voice_regions(self, rest_clients_impl, guild):
        mock_voice_payload = {"name": "london", "id": "LONDON"}
        mock_voice_obj = mock.MagicMock(voices.VoiceRegion)
        rest_clients_impl._session.get_guild_voice_regions.return_value = [mock_voice_payload]
        with mock.patch.object(voices.VoiceRegion, "deserialize", return_value=mock_voice_obj):
            assert await rest_clients_impl.fetch_guild_voice_regions(guild) == [mock_voice_obj]
            rest_clients_impl._session.get_guild_voice_regions.assert_called_once_with(guild_id="574921006817476608")
            voices.VoiceRegion.deserialize.assert_called_once_with(mock_voice_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_invites(self, rest_clients_impl, guild):
        mock_invite_payload = {"code": "dododo"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_clients_impl._session.get_guild_invites.return_value = [mock_invite_payload]
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            assert await rest_clients_impl.fetch_guild_invites(guild) == [mock_invite_obj]
            invites.InviteWithMetadata.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_integrations(self, rest_clients_impl, guild):
        mock_integration_payload = {"id": "123123", "name": "Integrated", "type": "twitch"}
        mock_integration_obj = mock.MagicMock(guilds.GuildIntegration)
        rest_clients_impl._session.get_guild_integrations.return_value = [mock_integration_payload]
        with mock.patch.object(guilds.GuildIntegration, "deserialize", return_value=mock_integration_obj):
            assert await rest_clients_impl.fetch_integrations(guild) == [mock_integration_obj]
            rest_clients_impl._session.get_guild_integrations.assert_called_once_with(guild_id="574921006817476608")
            guilds.GuildIntegration.deserialize.assert_called_once_with(mock_integration_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    @pytest.mark.parametrize("period", [datetime.timedelta(days=7), 7])
    async def test_update_integration_with_optionals(self, rest_clients_impl, guild, integration, period):
        rest_clients_impl._session.modify_guild_integration.return_value = ...
        result = await rest_clients_impl.update_integration(
            guild,
            integration,
            expire_behaviour=guilds.IntegrationExpireBehaviour.KICK,
            expire_grace_period=period,
            enable_emojis=True,
            reason="GET YEET'D",
        )
        assert result is None
        rest_clients_impl._session.modify_guild_integration.assert_called_once_with(
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
    async def test_update_integration_without_optionals(self, rest_clients_impl, guild, integration):
        rest_clients_impl._session.modify_guild_integration.return_value = ...
        assert await rest_clients_impl.update_integration(guild, integration) is None
        rest_clients_impl._session.modify_guild_integration.assert_called_once_with(
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
    async def test_delete_integration_with_reason(self, rest_clients_impl, guild, integration):
        rest_clients_impl._session.delete_guild_integration.return_value = ...
        assert await rest_clients_impl.delete_integration(guild, integration, reason="B Y E") is None
        rest_clients_impl._session.delete_guild_integration.assert_called_once_with(
            guild_id="574921006817476608", integration_id="379953393319542784", reason="B Y E"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    async def test_delete_integration_without_reason(self, rest_clients_impl, guild, integration):
        rest_clients_impl._session.delete_guild_integration.return_value = ...
        assert await rest_clients_impl.delete_integration(guild, integration) is None
        rest_clients_impl._session.delete_guild_integration.assert_called_once_with(
            guild_id="574921006817476608", integration_id="379953393319542784", reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("integration", 379953393319542784, guilds.GuildIntegration)
    async def test_sync_guild_integration(self, rest_clients_impl, guild, integration):
        rest_clients_impl._session.sync_guild_integration.return_value = ...
        assert await rest_clients_impl.sync_guild_integration(guild, integration) is None
        rest_clients_impl._session.sync_guild_integration.assert_called_once_with(
            guild_id="574921006817476608", integration_id="379953393319542784",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_embed(self, rest_clients_impl, guild):
        mock_embed_payload = {"enabled": True, "channel_id": "2020202"}
        mock_embed_obj = mock.MagicMock(guilds.GuildEmbed)
        rest_clients_impl._session.get_guild_embed.return_value = mock_embed_payload
        with mock.patch.object(guilds.GuildEmbed, "deserialize", return_value=mock_embed_obj):
            assert await rest_clients_impl.fetch_guild_embed(guild) is mock_embed_obj
            rest_clients_impl._session.get_guild_embed.assert_called_once_with(guild_id="574921006817476608")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123, channels.GuildChannel)
    async def test_update_guild_embed_with_optionnal(self, rest_clients_impl, guild, channel):
        mock_embed_payload = {"enabled": True, "channel_id": "2020202"}
        mock_embed_obj = mock.MagicMock(guilds.GuildEmbed)
        rest_clients_impl._session.modify_guild_embed.return_value = mock_embed_payload
        with mock.patch.object(guilds.GuildEmbed, "deserialize", return_value=mock_embed_obj):
            result = await rest_clients_impl.update_guild_embed(guild, channel=channel, enabled=True, reason="Nyaa!!!")
            assert result is mock_embed_obj
            rest_clients_impl._session.modify_guild_embed.assert_called_once_with(
                guild_id="574921006817476608", channel_id="123123", enabled=True, reason="Nyaa!!!"
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_update_guild_embed_without_optionnal(self, rest_clients_impl, guild):
        mock_embed_payload = {"enabled": True, "channel_id": "2020202"}
        mock_embed_obj = mock.MagicMock(guilds.GuildEmbed)
        rest_clients_impl._session.modify_guild_embed.return_value = mock_embed_payload
        with mock.patch.object(guilds.GuildEmbed, "deserialize", return_value=mock_embed_obj):
            assert await rest_clients_impl.update_guild_embed(guild) is mock_embed_obj
            rest_clients_impl._session.modify_guild_embed.assert_called_once_with(
                guild_id="574921006817476608", channel_id=..., enabled=..., reason=...
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_guild_vanity_url(self, rest_clients_impl, guild):
        mock_vanity_payload = {"code": "akfdk", "uses": 5}
        mock_vanity_obj = mock.MagicMock(invites.VanityUrl)
        rest_clients_impl._session.get_guild_vanity_url.return_value = mock_vanity_payload
        with mock.patch.object(invites.VanityUrl, "deserialize", return_value=mock_vanity_obj):
            assert await rest_clients_impl.fetch_guild_vanity_url(guild) is mock_vanity_obj
            rest_clients_impl._session.get_guild_vanity_url.assert_called_once_with(guild_id="574921006817476608")
            invites.VanityUrl.deserialize.assert_called_once_with(mock_vanity_payload)

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_guild_widget_image_with_style(self, rest_clients_impl, guild):
        mock_url = "not/a/url"
        rest_clients_impl._session.get_guild_widget_image_url.return_value = mock_url
        assert rest_clients_impl.format_guild_widget_image(guild, style="notAStyle") == mock_url
        rest_clients_impl._session.get_guild_widget_image_url.assert_called_once_with(
            guild_id="574921006817476608", style="notAStyle",
        )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_guild_widget_image_without_style(self, rest_clients_impl, guild):
        mock_url = "not/a/url"
        rest_clients_impl._session.get_guild_widget_image_url.return_value = mock_url
        assert rest_clients_impl.format_guild_widget_image(guild) == mock_url
        rest_clients_impl._session.get_guild_widget_image_url.assert_called_once_with(
            guild_id="574921006817476608", style=...,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invite", [mock.MagicMock(invites.Invite, code="AAAAAAAAAAAAAAAA"), "AAAAAAAAAAAAAAAA"])
    async def test_fetch_invite_with_counts(self, rest_clients_impl, invite):
        mock_invite_payload = {"code": "AAAAAAAAAAAAAAAA", "guild": {}, "channel": {}}
        mock_invite_obj = mock.MagicMock(invites.Invite)
        rest_clients_impl._session.get_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.Invite, "deserialize", return_value=mock_invite_obj):
            assert await rest_clients_impl.fetch_invite(invite, with_counts=True) is mock_invite_obj
            rest_clients_impl._session.get_invite.assert_called_once_with(
                invite_code="AAAAAAAAAAAAAAAA", with_counts=True,
            )
            invites.Invite.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invite", [mock.MagicMock(invites.Invite, code="AAAAAAAAAAAAAAAA"), "AAAAAAAAAAAAAAAA"])
    async def test_fetch_invite_without_counts(self, rest_clients_impl, invite):
        mock_invite_payload = {"code": "AAAAAAAAAAAAAAAA", "guild": {}, "channel": {}}
        mock_invite_obj = mock.MagicMock(invites.Invite)
        rest_clients_impl._session.get_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.Invite, "deserialize", return_value=mock_invite_obj):
            assert await rest_clients_impl.fetch_invite(invite) is mock_invite_obj
            rest_clients_impl._session.get_invite.assert_called_once_with(
                invite_code="AAAAAAAAAAAAAAAA", with_counts=...,
            )
            invites.Invite.deserialize.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invite", [mock.MagicMock(invites.Invite, code="AAAAAAAAAAAAAAAA"), "AAAAAAAAAAAAAAAA"])
    async def test_delete_invite(self, rest_clients_impl, invite):
        rest_clients_impl._session.delete_invite.return_value = ...
        assert await rest_clients_impl.delete_invite(invite) is None
        rest_clients_impl._session.delete_invite.assert_called_once_with(invite_code="AAAAAAAAAAAAAAAA")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 123123123, users.User)
    async def test_fetch_user(self, rest_clients_impl, user):
        mock_user_payload = {"id": "123", "username": "userName"}
        mock_user_obj = mock.MagicMock(users.User)
        rest_clients_impl._session.get_user.return_value = mock_user_payload
        with mock.patch.object(users.User, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.fetch_user(user) is mock_user_obj
            rest_clients_impl._session.get_user.assert_called_once_with(user_id="123123123")
            users.User.deserialize.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_fetch_application_info(self, rest_clients_impl):
        mock_application_payload = {"id": "2929292", "name": "blah blah", "description": "an app"}
        mock_application_obj = mock.MagicMock(oauth2.Application)
        rest_clients_impl._session.get_current_application_info.return_value = mock_application_payload
        with mock.patch.object(oauth2.Application, "deserialize", return_value=mock_application_obj):
            assert await rest_clients_impl.fetch_my_application_info() is mock_application_obj
            rest_clients_impl._session.get_current_application_info.assert_called_once_with()
            oauth2.Application.deserialize.assert_called_once_with(mock_application_payload)

    @pytest.mark.asyncio
    async def test_fetch_me(self, rest_clients_impl):
        mock_user_payload = {"username": "A User", "id": "202020200202"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.get_current_user.return_value = mock_user_payload
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.fetch_me() is mock_user_obj
            rest_clients_impl._session.get_current_user.assert_called_once()
            users.MyUser.deserialize.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_update_me_with_optionals(self, rest_clients_impl):
        mock_user_payload = {"id": "424242", "flags": "420", "discriminator": "6969"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.modify_current_user.return_value = mock_user_payload
        mock_avatar_obj = mock.MagicMock(io.BytesIO)
        mock_avatar_data = mock.MagicMock(bytes)
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            with mock.patch.object(conversions, "get_bytes_from_resource", return_value=mock_avatar_data):
                assert (
                    await rest_clients_impl.update_me(username="aNewName", avatar_data=mock_avatar_obj) is mock_user_obj
                )
                rest_clients_impl._session.modify_current_user.assert_called_once_with(
                    username="aNewName", avatar=mock_avatar_data
                )
                conversions.get_bytes_from_resource.assert_called_once_with(mock_avatar_obj)
            users.MyUser.deserialize.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_update_me_without_optionals(self, rest_clients_impl):
        mock_user_payload = {"id": "424242", "flags": "420", "discriminator": "6969"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.modify_current_user.return_value = mock_user_payload
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.update_me() is mock_user_obj
            rest_clients_impl._session.modify_current_user.assert_called_once_with(username=..., avatar=...)
            users.MyUser.deserialize.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_fetch_my_connections(self, rest_clients_impl):
        mock_connection_payload = {"id": "odnkwu", "type": "twitch", "name": "eric"}
        mock_connection_obj = mock.MagicMock(oauth2.OwnConnection)
        rest_clients_impl._session.get_current_user_connections.return_value = [mock_connection_payload]
        with mock.patch.object(oauth2.OwnConnection, "deserialize", return_value=mock_connection_obj):
            assert await rest_clients_impl.fetch_my_connections() == [mock_connection_obj]
            rest_clients_impl._session.get_current_user_connections.assert_called_once()
            oauth2.OwnConnection.deserialize.assert_called_once_with(mock_connection_payload)

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_my_guilds_after_with_optionals(self, rest_clients_impl, guild):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_my_guilds_after(after=guild, limit=50) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="after",
            request=rest_clients_impl._session.get_current_user_guilds,
            reversing=False,
            start="574921006817476608",
            limit=50,
        )

    def test_fetch_my_guilds_after_without_optionals(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_my_guilds_after() is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="after",
            request=rest_clients_impl._session.get_current_user_guilds,
            reversing=False,
            start="0",
            limit=None,
        )

    def test_fetch_my_guilds_after_with_datetime_object(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        assert rest_clients_impl.fetch_my_guilds_after(after=date) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="after",
            request=rest_clients_impl._session.get_current_user_guilds,
            reversing=False,
            start="537340988620800000",
            limit=None,
        )

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_my_guilds_before_with_optionals(self, rest_clients_impl, guild):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_my_guilds_before(before=guild, limit=50) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="before",
            request=rest_clients_impl._session.get_current_user_guilds,
            reversing=False,
            start="574921006817476608",
            limit=50,
        )

    def test_fetch_my_guilds_before_without_optionals(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        assert rest_clients_impl.fetch_my_guilds_before() is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="before",
            request=rest_clients_impl._session.get_current_user_guilds,
            reversing=False,
            start=None,
            limit=None,
        )

    def test_fetch_my_guilds_before_with_datetime_object(self, rest_clients_impl):
        mock_generator = mock.AsyncMock()
        rest_clients_impl._pagination_handler = mock.MagicMock(return_value=mock_generator)
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        assert rest_clients_impl.fetch_my_guilds_before(before=date) is mock_generator
        rest_clients_impl._pagination_handler.assert_called_once_with(
            deserializer=oauth2.OwnGuild.deserialize,
            direction="before",
            request=rest_clients_impl._session.get_current_user_guilds,
            reversing=False,
            start="537340988620800000",
            limit=None,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_leave_guild(self, rest_clients_impl, guild):
        rest_clients_impl._session.leave_guild.return_value = ...
        assert await rest_clients_impl.leave_guild(guild) is None
        rest_clients_impl._session.leave_guild.assert_called_once_with(guild_id="574921006817476608")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("recipient", 115590097100865541, users.User)
    async def test_create_dm_channel(self, rest_clients_impl, recipient):
        mock_dm_payload = {"id": "2202020", "type": 2, "recipients": []}
        mock_dm_obj = mock.MagicMock(channels.DMChannel)
        rest_clients_impl._session.create_dm.return_value = mock_dm_payload
        with mock.patch.object(channels.DMChannel, "deserialize", return_value=mock_dm_obj):
            assert await rest_clients_impl.create_dm_channel(recipient) is mock_dm_obj
            rest_clients_impl._session.create_dm.assert_called_once_with(recipient_id="115590097100865541")
            channels.DMChannel.deserialize.assert_called_once_with(mock_dm_payload)

    @pytest.mark.asyncio
    async def test_fetch_voice_regions(self, rest_clients_impl):
        mock_voice_payload = {"id": "LONDON", "name": "london"}
        mock_voice_obj = mock.MagicMock(voices.VoiceRegion)
        rest_clients_impl._session.list_voice_regions.return_value = [mock_voice_payload]
        with mock.patch.object(voices.VoiceRegion, "deserialize", return_value=mock_voice_obj):
            assert await rest_clients_impl.fetch_voice_regions() == [mock_voice_obj]
            rest_clients_impl._session.list_voice_regions.assert_called_once()
            voices.VoiceRegion.deserialize.assert_called_once_with(mock_voice_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.Channel)
    async def test_create_webhook_with_optionals(self, rest_clients_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_clients_impl._session.create_webhook.return_value = mock_webhook_payload
        mock_image_obj = mock.MagicMock(io.BytesIO)
        mock_image_data = mock.MagicMock(bytes)
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            with mock.patch.object(conversions, "get_bytes_from_resource", return_value=mock_image_data):
                result = await rest_clients_impl.create_webhook(
                    channel=channel, name="aWebhook", avatar_data=mock_image_obj, reason="And a webhook is born."
                )
                assert result is mock_webhook_obj
                conversions.get_bytes_from_resource.assert_called_once_with(mock_image_obj)
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)
        rest_clients_impl._session.create_webhook.assert_called_once_with(
            channel_id="115590097100865541", name="aWebhook", avatar=mock_image_data, reason="And a webhook is born."
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.Channel)
    async def test_create_webhook_without_optionals(self, rest_clients_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_clients_impl._session.create_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_clients_impl.create_webhook(channel=channel, name="aWebhook") is mock_webhook_obj
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)
        rest_clients_impl._session.create_webhook.assert_called_once_with(
            channel_id="115590097100865541", name="aWebhook", avatar=..., reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.GuildChannel)
    async def test_fetch_channel_webhooks(self, rest_clients_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_clients_impl._session.get_channel_webhooks.return_value = [mock_webhook_payload]
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_clients_impl.fetch_channel_webhooks(channel) == [mock_webhook_obj]
            rest_clients_impl._session.get_channel_webhooks.assert_called_once_with(channel_id="115590097100865541")
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.GuildChannel)
    async def test_fetch_guild_webhooks(self, rest_clients_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_clients_impl._session.get_guild_webhooks.return_value = [mock_webhook_payload]
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_clients_impl.fetch_guild_webhooks(channel) == [mock_webhook_obj]
            rest_clients_impl._session.get_guild_webhooks.assert_called_once_with(guild_id="115590097100865541")
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_fetch_webhook_with_webhook_token(self, rest_clients_impl, webhook):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_clients_impl._session.get_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_clients_impl.fetch_webhook(webhook, webhook_token="dsawqoepql.kmsdao") is mock_webhook_obj
            rest_clients_impl._session.get_webhook.assert_called_once_with(
                webhook_id="379953393319542784", webhook_token="dsawqoepql.kmsdao",
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_fetch_webhook_without_webhook_token(self, rest_clients_impl, webhook):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_clients_impl._session.get_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_clients_impl.fetch_webhook(webhook) is mock_webhook_obj
            rest_clients_impl._session.get_webhook.assert_called_once_with(
                webhook_id="379953393319542784", webhook_token=...,
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, webhooks.Webhook)
    async def test_update_webhook_with_optionals(self, rest_clients_impl, webhook, channel):
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        mock_webhook_payload = {"id": "123123", "avatar": "1wedoklpasdoiksdoka"}
        rest_clients_impl._session.modify_webhook.return_value = mock_webhook_payload
        mock_image_obj = mock.MagicMock(io.BytesIO)
        mock_image_data = mock.MagicMock(bytes)
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            with mock.patch.object(conversions, "get_bytes_from_resource", return_value=mock_image_data):
                result = await rest_clients_impl.update_webhook(
                    webhook,
                    webhook_token="a.wEbHoOk.ToKeN",
                    name="blah_blah_blah",
                    avatar_data=mock_image_obj,
                    channel=channel,
                    reason="A reason",
                )
                assert result is mock_webhook_obj
                rest_clients_impl._session.modify_webhook.assert_called_once_with(
                    webhook_id="379953393319542784",
                    webhook_token="a.wEbHoOk.ToKeN",
                    name="blah_blah_blah",
                    avatar=mock_image_data,
                    channel_id="115590097100865541",
                    reason="A reason",
                )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_update_webhook_without_optionals(self, rest_clients_impl, webhook):
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        mock_webhook_payload = {"id": "123123", "avatar": "1wedoklpasdoiksdoka"}
        rest_clients_impl._session.modify_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_clients_impl.update_webhook(webhook) is mock_webhook_obj
            rest_clients_impl._session.modify_webhook.assert_called_once_with(
                webhook_id="379953393319542784", webhook_token=..., name=..., avatar=..., channel_id=..., reason=...,
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_delete_webhook_with_webhook_token(self, rest_clients_impl, webhook):
        rest_clients_impl._session.delete_webhook.return_value = ...
        assert await rest_clients_impl.delete_webhook(webhook, webhook_token="dsawqoepql.kmsdao") is None
        rest_clients_impl._session.delete_webhook.assert_called_once_with(
            webhook_id="379953393319542784", webhook_token="dsawqoepql.kmsdao"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_delete_webhook_without_webhook_token(self, rest_clients_impl, webhook):
        rest_clients_impl._session.delete_webhook.return_value = ...
        assert await rest_clients_impl.delete_webhook(webhook) is None
        rest_clients_impl._session.delete_webhook.assert_called_once_with(
            webhook_id="379953393319542784", webhook_token=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_execute_webhook_without_optionals(self, rest_clients_impl, webhook):
        rest_clients_impl._session.execute_webhook.return_value = ...
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        assert await rest_clients_impl.execute_webhook(webhook, "a.webhook.token") is None
        rest_clients_impl._session.execute_webhook.assert_called_once_with(
            webhook_id="379953393319542784",
            webhook_token="a.webhook.token",
            content=...,
            username=...,
            avatar_url=...,
            tts=...,
            wait=False,
            file=...,
            embeds=...,
            allowed_mentions=mock_allowed_mentions_payload,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_execute_webhook_with_optionals(self, rest_clients_impl, webhook):
        rest_clients_impl._session.execute_webhook.return_value = ...
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        mock_embed_payload = {"description": "424242"}
        mock_embed_obj = mock.create_autospec(
            embeds.Embed, auto_spec=True, serialize=mock.MagicMock(return_value=mock_embed_payload)
        )
        mock_media_obj = mock.MagicMock()
        mock_media_payload = ("aName.png", mock.MagicMock())
        with mock.patch.object(media, "safe_read_file", return_value=mock_media_payload):
            with mock.patch.object(messages.Message, "deserialize"):
                await rest_clients_impl.execute_webhook(
                    webhook,
                    "a.webhook.token",
                    content="THE TRUTH",
                    username="User 97",
                    avatar_url="httttttt/L//",
                    tts=True,
                    wait=True,
                    file=mock_media_obj,
                    embeds=[mock_embed_obj],
                    mentions_everyone=False,
                    role_mentions=False,
                    user_mentions=False,
                )
            media.safe_read_file.assert_called_once_with(mock_media_obj)
        rest_clients_impl._session.execute_webhook.assert_called_once_with(
            webhook_id="379953393319542784",
            webhook_token="a.webhook.token",
            content="THE TRUTH",
            username="User 97",
            avatar_url="httttttt/L//",
            tts=True,
            wait=True,
            file=mock_media_payload,
            embeds=[mock_embed_payload],
            allowed_mentions=mock_allowed_mentions_payload,
        )
        mock_embed_obj.serialize.assert_called_once()
        rest_clients_impl._generate_allowed_mentions.assert_called_once_with(
            mentions_everyone=False, user_mentions=False, role_mentions=False
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_execute_webhook_returns_message_when_wait_is_true(self, rest_clients_impl, webhook):
        mock_message_payload = {"id": "6796959949034", "content": "Nyaa Nyaa"}
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl._session.execute_webhook.return_value = mock_message_payload
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_clients_impl._generate_allowed_mentions = mock.MagicMock(return_value=mock_allowed_mentions_payload)
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_clients_impl.execute_webhook(webhook, "a.webhook.token", wait=True) is mock_message_obj
            messages.Message.deserialize.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    async def test_safe_execute_webhook_without_optionals(self, rest_clients_impl):
        webhook = mock.MagicMock(webhooks.Webhook)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl.execute_webhook = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_clients_impl.safe_webhook_execute(webhook, "a.webhook.token",)
        assert result is mock_message_obj
        rest_clients_impl.execute_webhook.assert_called_once_with(
            webhook=webhook,
            webhook_token="a.webhook.token",
            content=...,
            username=...,
            avatar_url=...,
            tts=...,
            wait=False,
            file=...,
            embeds=...,
            mentions_everyone=False,
            user_mentions=False,
            role_mentions=False,
        )

    @pytest.mark.asyncio
    async def test_safe_execute_webhook_with_optionals(self, rest_clients_impl):
        webhook = mock.MagicMock(webhooks.Webhook)
        mock_media_obj = mock.MagicMock(bytes)
        mock_embed_obj = mock.MagicMock(embeds.Embed)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_clients_impl.execute_webhook = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_clients_impl.safe_webhook_execute(
            webhook,
            "a.webhook.token",
            content="THE TRUTH",
            username="User 97",
            avatar_url="httttttt/L//",
            tts=True,
            wait=True,
            file=mock_media_obj,
            embeds=[mock_embed_obj],
            mentions_everyone=False,
            role_mentions=False,
            user_mentions=False,
        )
        assert result is mock_message_obj
        rest_clients_impl.execute_webhook.assert_called_once_with(
            webhook=webhook,
            webhook_token="a.webhook.token",
            content="THE TRUTH",
            username="User 97",
            avatar_url="httttttt/L//",
            tts=True,
            wait=True,
            file=mock_media_obj,
            embeds=[mock_embed_obj],
            mentions_everyone=False,
            role_mentions=False,
            user_mentions=False,
        )

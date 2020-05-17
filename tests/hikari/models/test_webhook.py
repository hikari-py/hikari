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
import mock
import pytest

from hikari import rest
from hikari import application
from hikari.internal import urls
from hikari.models import bases
from hikari.models import channels
from hikari.models import embeds
from hikari.models import files
from hikari.models import messages
from hikari.models import users
from hikari.models import webhooks
from tests.hikari import _helpers


@pytest.fixture()
def mock_app() -> application.Application:
    return mock.MagicMock(application.Application, rest=mock.AsyncMock(rest.RESTClient))


class TestWebhook:
    def test_deserialize(self, mock_app):
        test_user_payload = {"id": "123456", "username": "hikari", "discriminator": "0000", "avatar": None}
        payload = {
            "id": "1234",
            "type": 1,
            "guild_id": "123",
            "channel_id": "456",
            "user": test_user_payload,
            "name": "hikari webhook",
            "avatar": "bb71f469c158984e265093a81b3397fb",
            "token": "ueoqrialsdfaKJLKfajslkdf",
        }
        mock_user = mock.MagicMock(users.User)

        with _helpers.patch_marshal_attr(
            webhooks.Webhook, "author", deserializer=users.User.deserialize, return_value=mock_user
        ) as mock_user_deserializer:
            webhook_obj = webhooks.Webhook.deserialize(payload, app=mock_app)
            mock_user_deserializer.assert_called_once_with(test_user_payload, app=mock_app)

        assert webhook_obj.id == 1234
        assert webhook_obj.type == webhooks.WebhookType.INCOMING
        assert webhook_obj.guild_id == 123
        assert webhook_obj.channel_id == 456
        assert webhook_obj.author is mock_user
        assert webhook_obj.name == "hikari webhook"
        assert webhook_obj.avatar_hash == "bb71f469c158984e265093a81b3397fb"
        assert webhook_obj.token == "ueoqrialsdfaKJLKfajslkdf"

    @pytest.fixture()
    def webhook_obj(self, mock_app):
        return webhooks.Webhook(
            app=mock_app,
            id=bases.Snowflake(123123),
            type=None,
            guild_id=None,
            channel_id=None,
            author=None,
            name=None,
            avatar_hash="b3b24c6d7cbcdec129d5d537067061a8",
            token="blah.blah.blah",
        )

    @pytest.mark.asyncio
    async def test_execute_without_optionals(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(messages.Message)
        mock_app.rest.execute_webhook.return_value = mock_webhook
        assert await webhook_obj.execute() is mock_webhook
        mock_app.rest.execute_webhook.assert_called_once_with(
            webhook=123123,
            webhook_token="blah.blah.blah",
            content=...,
            username=...,
            avatar_url=...,
            tts=...,
            wait=False,
            files=...,
            embeds=...,
            mentions_everyone=True,
            user_mentions=True,
            role_mentions=True,
        )

    @pytest.mark.asyncio
    async def test_execute_with_optionals(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(messages.Message)
        mock_files = mock.MagicMock(files.BaseStream)
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_app.rest.execute_webhook.return_value = mock_webhook
        result = await webhook_obj.execute(
            content="A CONTENT",
            username="Name user",
            avatar_url=">///<",
            tts=True,
            wait=True,
            files=[mock_files],
            embeds=[mock_embed],
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[444],
        )
        assert result is mock_webhook
        mock_app.rest.execute_webhook.assert_called_once_with(
            webhook=123123,
            webhook_token="blah.blah.blah",
            content="A CONTENT",
            username="Name user",
            avatar_url=">///<",
            tts=True,
            wait=True,
            files=[mock_files],
            embeds=[mock_embed],
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[444],
        )

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.asyncio
    async def test_execute_raises_value_error_without_token(self, webhook_obj):
        webhook_obj.token = None
        await webhook_obj.execute()

    @pytest.mark.asyncio
    async def test_safe_execute_without_optionals(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(messages.Message)
        mock_app.rest.safe_webhook_execute = mock.AsyncMock(return_value=mock_webhook)
        assert await webhook_obj.safe_execute() is mock_webhook
        mock_app.rest.safe_webhook_execute.assert_called_once_with(
            webhook=123123,
            webhook_token="blah.blah.blah",
            content=...,
            username=...,
            avatar_url=...,
            tts=...,
            wait=False,
            files=...,
            embeds=...,
            mentions_everyone=False,
            user_mentions=False,
            role_mentions=False,
        )

    @pytest.mark.asyncio
    async def test_safe_execute_with_optionals(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(messages.Message)
        mock_files = mock.MagicMock(files.BaseStream)
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_app.rest.safe_webhook_execute = mock.AsyncMock(return_value=mock_webhook)
        result = await webhook_obj.safe_execute(
            content="A CONTENT",
            username="Name user",
            avatar_url=">///<",
            tts=True,
            wait=True,
            files=[mock_files],
            embeds=[mock_embed],
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[444],
        )
        assert result is mock_webhook
        mock_app.rest.safe_webhook_execute.assert_called_once_with(
            webhook=123123,
            webhook_token="blah.blah.blah",
            content="A CONTENT",
            username="Name user",
            avatar_url=">///<",
            tts=True,
            wait=True,
            files=[mock_files],
            embeds=[mock_embed],
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[444],
        )

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.asyncio
    async def test_safe_execute_raises_value_error_without_token(self, webhook_obj):
        webhook_obj.token = None
        await webhook_obj.safe_execute()

    @pytest.mark.asyncio
    async def test_delete_with_token(self, webhook_obj, mock_app):
        mock_app.rest.delete_webhook.return_value = ...
        assert await webhook_obj.delete() is None
        mock_app.rest.delete_webhook.assert_called_once_with(webhook=123123, webhook_token="blah.blah.blah")

    @pytest.mark.asyncio
    async def test_delete_without_token(self, webhook_obj, mock_app):
        webhook_obj.token = None
        mock_app.rest.delete_webhook.return_value = ...
        assert await webhook_obj.delete() is None
        mock_app.rest.delete_webhook.assert_called_once_with(webhook=123123, webhook_token=...)

    @pytest.mark.asyncio
    async def test_delete_with_use_token_set_to_true(self, webhook_obj, mock_app):
        mock_app.rest.delete_webhook.return_value = ...
        assert await webhook_obj.delete(use_token=True) is None
        mock_app.rest.delete_webhook.assert_called_once_with(webhook=123123, webhook_token="blah.blah.blah")

    @pytest.mark.asyncio
    async def test_delete_with_use_token_set_to_false(self, webhook_obj, mock_app):
        mock_app.rest.delete_webhook.return_value = ...
        assert await webhook_obj.delete(use_token=False) is None
        mock_app.rest.delete_webhook.assert_called_once_with(webhook=123123, webhook_token=...)

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.asyncio
    async def test_delete_raises_value_error_when_use_token_set_to_true_without_token(self, webhook_obj, mock_app):
        webhook_obj.token = None
        await webhook_obj.delete(use_token=True)

    @pytest.mark.asyncio
    async def test_edit_without_optionals_nor_token(self, webhook_obj, mock_app):
        webhook_obj.token = None
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.update_webhook.return_value = mock_webhook
        assert await webhook_obj.edit() is mock_webhook
        mock_app.rest.update_webhook.assert_called_once_with(
            webhook=123123, webhook_token=..., name=..., avatar=..., channel=..., reason=...
        )

    @pytest.mark.asyncio
    async def test_edit_with_optionals_and_token(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_avatar = mock.MagicMock(files.BaseStream)
        mock_channel = mock.MagicMock(channels.GuildChannel)
        mock_app.rest.update_webhook.return_value = mock_webhook
        result = await webhook_obj.edit(name="A name man", avatar=mock_avatar, channel=mock_channel, reason="xd420")
        assert result is mock_webhook
        mock_app.rest.update_webhook.assert_called_once_with(
            webhook=123123,
            webhook_token="blah.blah.blah",
            name="A name man",
            avatar=mock_avatar,
            channel=mock_channel,
            reason="xd420",
        )

    @pytest.mark.asyncio
    async def test_edit_with_use_token_set_to_true(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.update_webhook.return_value = mock_webhook
        assert await webhook_obj.edit(use_token=True) is mock_webhook
        mock_app.rest.update_webhook.assert_called_once_with(
            webhook=123123, webhook_token="blah.blah.blah", name=..., avatar=..., channel=..., reason=...
        )

    @pytest.mark.asyncio
    async def test_edit_with_use_token_set_to_false(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.update_webhook.return_value = mock_webhook
        assert await webhook_obj.edit(use_token=False) is mock_webhook
        mock_app.rest.update_webhook.assert_called_once_with(
            webhook=123123, webhook_token=..., name=..., avatar=..., channel=..., reason=...
        )

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.asyncio
    async def test_edit_raises_value_error_when_use_token_set_to_true_without_token(self, webhook_obj, mock_app):
        webhook_obj.token = None
        await webhook_obj.edit(use_token=True)

    @pytest.mark.asyncio
    async def test_fetch_channel(self, webhook_obj, mock_app):
        webhook_obj.channel_id = bases.Snowflake(202020)
        mock_channel = mock.MagicMock(channels.GuildChannel)
        mock_app.rest.fetch_channel.return_value = mock_channel
        assert await webhook_obj.fetch_channel() is mock_channel
        mock_app.rest.fetch_channel.assert_called_once_with(channel=202020)

    @pytest.mark.asyncio
    async def test_fetch_guild(self, webhook_obj, mock_app):
        webhook_obj.guild_id = bases.Snowflake(202020)
        mock_channel = mock.MagicMock(channels.GuildChannel)
        mock_app.rest.fetch_guild.return_value = mock_channel
        assert await webhook_obj.fetch_guild() is mock_channel
        mock_app.rest.fetch_guild.assert_called_once_with(guild=202020)

    @pytest.mark.asyncio
    async def test_fetch_self_with_token(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.fetch_webhook.return_value = mock_webhook
        assert await webhook_obj.fetch_self() is mock_webhook
        mock_app.rest.fetch_webhook.assert_called_once_with(webhook=123123, webhook_token="blah.blah.blah")

    @pytest.mark.asyncio
    async def test_fetch_self_without_token(self, webhook_obj, mock_app):
        webhook_obj.token = None
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.fetch_webhook.return_value = mock_webhook
        assert await webhook_obj.fetch_self() is mock_webhook
        mock_app.rest.fetch_webhook.assert_called_once_with(webhook=123123, webhook_token=...)

    @pytest.mark.asyncio
    async def test_fetch_self_with_use_token_set_to_true(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.fetch_webhook.return_value = mock_webhook
        assert await webhook_obj.fetch_self(use_token=True) is mock_webhook
        mock_app.rest.fetch_webhook.assert_called_once_with(webhook=123123, webhook_token="blah.blah.blah")

    @pytest.mark.asyncio
    async def test_fetch_self_with_use_token_set_to_false(self, webhook_obj, mock_app):
        mock_webhook = mock.MagicMock(webhooks.Webhook)
        mock_app.rest.fetch_webhook.return_value = mock_webhook
        assert await webhook_obj.fetch_self(use_token=False) is mock_webhook
        mock_app.rest.fetch_webhook.assert_called_once_with(webhook=123123, webhook_token=...)

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.asyncio
    async def test_fetch_self_raises_value_error_when_use_token_set_to_true_without_token(self, webhook_obj, mock_app):
        webhook_obj.token = None
        assert await webhook_obj.fetch_self(use_token=True)

    def test_avatar_url(self, webhook_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = webhook_obj.avatar_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_test_default_avatar_index(self, webhook_obj):
        assert webhook_obj.default_avatar_index == 0

    def test_default_avatar_url(self, webhook_obj):
        mock_url = "https://cdn.discordapp.com/embed/avatars/2.png"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = webhook_obj.default_avatar_url
            urls.generate_cdn_url.assert_called_once_with("embed", "avatars", "0", format_="png", size=None)
        assert url == mock_url

    def test_format_avatar_url_default(self, webhook_obj):
        webhook_obj.avatar_hash = None
        mock_url = "https://cdn.discordapp.com/embed/avatars/2.png"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = webhook_obj.format_avatar_url(size=3232)
            urls.generate_cdn_url.assert_called_once_with("embed", "avatars", "0", format_="png", size=None)
        assert url == mock_url

    def test_format_avatar_url_when_format_specified(self, webhook_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541/b3b24c6d7c37067061a8.nyaapeg?size=1024"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = webhook_obj.format_avatar_url(format_="nyaapeg", size=1024)
            urls.generate_cdn_url.assert_called_once_with(
                "avatars", "123123", "b3b24c6d7cbcdec129d5d537067061a8", format_="nyaapeg", size=1024
            )
        assert url == mock_url

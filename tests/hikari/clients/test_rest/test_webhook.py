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
import io

import mock
import pytest

from hikari import embeds
from hikari import files
from hikari import messages
from hikari import webhooks
from hikari.clients.rest import webhook
from hikari.internal import helpers
from hikari.net import rest
from tests.hikari import _helpers


class TestRESTUserLogic:
    @pytest.fixture()
    def rest_webhook_logic_impl(self):
        mock_low_level_restful_client = mock.MagicMock(rest.REST)

        class RESTWebhookLogicImpl(webhook.RESTWebhookComponent):
            def __init__(self):
                super().__init__(mock_low_level_restful_client)

        return RESTWebhookLogicImpl()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_fetch_webhook_with_webhook_token(self, rest_webhook_logic_impl, webhook):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_webhook_logic_impl._session.get_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert (
                await rest_webhook_logic_impl.fetch_webhook(webhook, webhook_token="dsawqoepql.kmsdao")
                is mock_webhook_obj
            )
            rest_webhook_logic_impl._session.get_webhook.assert_called_once_with(
                webhook_id="379953393319542784", webhook_token="dsawqoepql.kmsdao",
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_fetch_webhook_without_webhook_token(self, rest_webhook_logic_impl, webhook):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_webhook_logic_impl._session.get_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_webhook_logic_impl.fetch_webhook(webhook) is mock_webhook_obj
            rest_webhook_logic_impl._session.get_webhook.assert_called_once_with(
                webhook_id="379953393319542784", webhook_token=...,
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, webhooks.Webhook)
    async def test_update_webhook_with_optionals(self, rest_webhook_logic_impl, webhook, channel):
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        mock_webhook_payload = {"id": "123123", "avatar": "1wedoklpasdoiksdoka"}
        rest_webhook_logic_impl._session.modify_webhook.return_value = mock_webhook_payload
        mock_image_data = mock.MagicMock(bytes)
        mock_image_obj = mock.MagicMock(files.File)
        mock_image_obj.read_all = mock.AsyncMock(return_value=mock_image_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj))
        with stack:
            result = await rest_webhook_logic_impl.update_webhook(
                webhook,
                webhook_token="a.wEbHoOk.ToKeN",
                name="blah_blah_blah",
                avatar=mock_image_obj,
                channel=channel,
                reason="A reason",
            )
            assert result is mock_webhook_obj
            rest_webhook_logic_impl._session.modify_webhook.assert_called_once_with(
                webhook_id="379953393319542784",
                webhook_token="a.wEbHoOk.ToKeN",
                name="blah_blah_blah",
                avatar=mock_image_data,
                channel_id="115590097100865541",
                reason="A reason",
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)
            mock_image_obj.read_all.assert_awaited_once()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_update_webhook_without_optionals(self, rest_webhook_logic_impl, webhook):
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        mock_webhook_payload = {"id": "123123", "avatar": "1wedoklpasdoiksdoka"}
        rest_webhook_logic_impl._session.modify_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_webhook_logic_impl.update_webhook(webhook) is mock_webhook_obj
            rest_webhook_logic_impl._session.modify_webhook.assert_called_once_with(
                webhook_id="379953393319542784", webhook_token=..., name=..., avatar=..., channel_id=..., reason=...,
            )
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_delete_webhook_with_webhook_token(self, rest_webhook_logic_impl, webhook):
        rest_webhook_logic_impl._session.delete_webhook.return_value = ...
        assert await rest_webhook_logic_impl.delete_webhook(webhook, webhook_token="dsawqoepql.kmsdao") is None
        rest_webhook_logic_impl._session.delete_webhook.assert_called_once_with(
            webhook_id="379953393319542784", webhook_token="dsawqoepql.kmsdao"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_delete_webhook_without_webhook_token(self, rest_webhook_logic_impl, webhook):
        rest_webhook_logic_impl._session.delete_webhook.return_value = ...
        assert await rest_webhook_logic_impl.delete_webhook(webhook) is None
        rest_webhook_logic_impl._session.delete_webhook.assert_called_once_with(
            webhook_id="379953393319542784", webhook_token=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_execute_webhook_without_optionals(self, rest_webhook_logic_impl, webhook):
        rest_webhook_logic_impl._session.execute_webhook.return_value = ...
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        with mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload):
            assert await rest_webhook_logic_impl.execute_webhook(webhook, "a.webhook.token") is None
            helpers.generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=True, user_mentions=True, role_mentions=True
            )
        rest_webhook_logic_impl._session.execute_webhook.assert_called_once_with(
            webhook_id="379953393319542784",
            webhook_token="a.webhook.token",
            content=...,
            username=...,
            avatar_url=...,
            tts=...,
            wait=False,
            files=...,
            embeds=...,
            allowed_mentions=mock_allowed_mentions_payload,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_execute_webhook_with_optionals(self, rest_webhook_logic_impl, webhook):
        rest_webhook_logic_impl._session.execute_webhook.return_value = ...
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        mock_embed_payload = {"description": "424242"}
        mock_file_obj = mock.MagicMock(files.File)
        mock_embed_obj = mock.MagicMock(embeds.Embed)
        mock_embed_obj.assets_to_upload = [mock_file_obj]
        mock_embed_obj.serialize = mock.MagicMock(return_value=mock_embed_payload)
        mock_file_obj2 = mock.MagicMock(files.File)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(messages.Message, "deserialize"))
        stack.enter_context(
            mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload)
        )
        with stack:
            await rest_webhook_logic_impl.execute_webhook(
                webhook,
                "a.webhook.token",
                content="THE TRUTH",
                username="User 97",
                avatar_url="httttttt/L//",
                tts=True,
                wait=True,
                files=[mock_file_obj2],
                embeds=[mock_embed_obj],
                mentions_everyone=False,
                role_mentions=False,
                user_mentions=False,
            )
            helpers.generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=False, user_mentions=False, role_mentions=False
            )
        rest_webhook_logic_impl._session.execute_webhook.assert_called_once_with(
            webhook_id="379953393319542784",
            webhook_token="a.webhook.token",
            content="THE TRUTH",
            username="User 97",
            avatar_url="httttttt/L//",
            tts=True,
            wait=True,
            files=[mock_file_obj, mock_file_obj2],
            embeds=[mock_embed_payload],
            allowed_mentions=mock_allowed_mentions_payload,
        )
        mock_embed_obj.serialize.assert_called_once()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 379953393319542784, webhooks.Webhook)
    async def test_execute_webhook_returns_message_when_wait_is_true(self, rest_webhook_logic_impl, webhook):
        mock_message_payload = {"id": "6796959949034", "content": "Nyaa Nyaa"}
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_webhook_logic_impl._session.execute_webhook.return_value = mock_message_payload
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload)
        )
        stack.enter_context(mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj))
        with stack:
            assert (
                await rest_webhook_logic_impl.execute_webhook(webhook, "a.webhook.token", wait=True) is mock_message_obj
            )
            messages.Message.deserialize.assert_called_once_with(mock_message_payload)

    @pytest.mark.asyncio
    async def test_safe_execute_webhook_without_optionals(self, rest_webhook_logic_impl):
        webhook = mock.MagicMock(webhooks.Webhook)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_webhook_logic_impl.execute_webhook = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_webhook_logic_impl.safe_webhook_execute(webhook, "a.webhook.token",)
        assert result is mock_message_obj
        rest_webhook_logic_impl.execute_webhook.assert_called_once_with(
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
    async def test_safe_execute_webhook_with_optionals(self, rest_webhook_logic_impl):
        webhook = mock.MagicMock(webhooks.Webhook)
        mock_file_obj = mock.MagicMock(files.File)
        mock_embed_obj = mock.MagicMock(embeds.Embed)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_webhook_logic_impl.execute_webhook = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_webhook_logic_impl.safe_webhook_execute(
            webhook,
            "a.webhook.token",
            content="THE TRUTH",
            username="User 97",
            avatar_url="httttttt/L//",
            tts=True,
            wait=True,
            file=mock_file_obj,
            embeds=[mock_embed_obj],
            mentions_everyone=False,
            role_mentions=False,
            user_mentions=False,
        )
        assert result is mock_message_obj
        rest_webhook_logic_impl.execute_webhook.assert_called_once_with(
            webhook=webhook,
            webhook_token="a.webhook.token",
            content="THE TRUTH",
            username="User 97",
            avatar_url="httttttt/L//",
            tts=True,
            wait=True,
            file=mock_file_obj,
            embeds=[mock_embed_obj],
            mentions_everyone=False,
            role_mentions=False,
            user_mentions=False,
        )

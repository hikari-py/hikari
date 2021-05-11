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
import mock
import pytest

from hikari import undefined
from hikari import webhooks
from tests.hikari import hikari_test_helpers


class TestExecutableWebhook:
    @pytest.fixture()
    def executable_webhook(self):
        return hikari_test_helpers.mock_class_namespace(
            webhooks.ExecutableWebhook, slots_=False, app=mock.AsyncMock()
        )()

    @pytest.mark.asyncio
    async def test_execute_with_optionals(self, executable_webhook):
        mock_attachment_1 = object()
        mock_attachment_2 = object()
        mock_embed = object()

        result = await executable_webhook.execute(
            content="coooo",
            username="oopp",
            avatar_url="urlurlurl",
            tts=True,
            attachment=mock_attachment_1,
            attachments=mock_attachment_2,
            embeds=mock_embed,
            mentions_everyone=False,
            user_mentions=[1235432],
            role_mentions=[65234123],
        )

        assert result is executable_webhook.app.rest.execute_webhook.return_value
        executable_webhook.app.rest.execute_webhook.assert_awaited_once_with(
            webhook=executable_webhook.webhook_id,
            token=executable_webhook.token,
            content="coooo",
            username="oopp",
            avatar_url="urlurlurl",
            tts=True,
            attachment=mock_attachment_1,
            attachments=mock_attachment_2,
            embeds=mock_embed,
            mentions_everyone=False,
            user_mentions=[1235432],
            role_mentions=[65234123],
        )

    @pytest.mark.asyncio
    async def test_execute_without_optionals(self, executable_webhook):
        result = await executable_webhook.execute()

        assert result is executable_webhook.app.rest.execute_webhook.return_value
        executable_webhook.app.rest.execute_webhook.assert_awaited_once_with(
            webhook=executable_webhook.webhook_id,
            token=executable_webhook.token,
            content=undefined.UNDEFINED,
            username=undefined.UNDEFINED,
            avatar_url=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio()
    async def test_fetch_message(self, executable_webhook):
        message = object()
        returned_message = object()
        executable_webhook.app.rest.fetch_webhook_message = mock.AsyncMock(return_value=returned_message)

        returned = await executable_webhook.fetch_message(message)

        assert returned is returned_message

        executable_webhook.app.rest.fetch_webhook_message.assert_called_once_with(
            executable_webhook.webhook_id, token=executable_webhook.token, message=message
        )

    @pytest.mark.asyncio()
    async def test_fetch_message_when_no_token(self, executable_webhook):
        executable_webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot fetch a message using a webhook where we don't know the token"):
            await executable_webhook.fetch_message(987)

    @pytest.mark.asyncio()
    async def test_edit_message(self, executable_webhook):
        message = object()
        embed = object()
        attachment = object()

        returned = await executable_webhook.edit_message(
            message,
            content="test",
            embed=embed,
            embeds=[embed, embed],
            attachment=attachment,
            attachments=[attachment, attachment],
            replace_attachments=True,
            mentions_everyone=False,
            user_mentions=True,
            role_mentions=[567, 890],
        )

        assert returned is executable_webhook.app.rest.edit_webhook_message.return_value

        executable_webhook.app.rest.edit_webhook_message.assert_awaited_once_with(
            executable_webhook.webhook_id,
            token=executable_webhook.token,
            message=message,
            content="test",
            embed=embed,
            embeds=[embed, embed],
            attachment=attachment,
            attachments=[attachment, attachment],
            replace_attachments=True,
            mentions_everyone=False,
            user_mentions=True,
            role_mentions=[567, 890],
        )

    @pytest.mark.asyncio()
    async def test_edit_message_when_no_token(self, executable_webhook):
        executable_webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot edit a message using a webhook where we don't know the token"):
            await executable_webhook.edit_message(987)

    @pytest.mark.asyncio()
    async def test_delete_message(self, executable_webhook):
        message = object()

        await executable_webhook.delete_message(message)

        executable_webhook.app.rest.delete_webhook_message.assert_awaited_once_with(
            executable_webhook.webhook_id, token=executable_webhook.token, message=message
        )

    @pytest.mark.asyncio()
    async def test_delete_message_when_no_token(self, executable_webhook):
        executable_webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot delete a message using a webhook where we don't know the token"):
            assert await executable_webhook.delete_message(987)


class TestWebhook:
    @pytest.fixture()
    def webhook(self):
        return webhooks.Webhook(
            app=mock.Mock(),
            id=987654321,
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            guild_id=123,
            channel_id=456,
            author=None,
            name="not a webhook",
            avatar_hash=None,
            token="abc123bca",
            application_id=None,
            source_channel=object(),
            source_guild=object(),
        )

    def test_str(self, webhook):
        assert str(webhook) == "not a webhook"

    def test_str_when_name_is_None(self, webhook):
        webhook.name = None
        assert str(webhook) == "Unnamed webhook ID 987654321"

    def test_webhook_id_property(self, webhook):
        assert webhook.webhook_id is webhook.id

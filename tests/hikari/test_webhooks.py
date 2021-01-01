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

from hikari import webhooks


def test_WebhookType_str_operator():
    webhook_type = webhooks.WebhookType(1)
    assert str(webhook_type) == "INCOMING"


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

    @pytest.mark.asyncio
    async def test_edit_message(self, webhook):
        message = object()
        embed = object()
        returned_message = object()
        webhook.app.rest.edit_webhook_message = mock.AsyncMock(return_value=returned_message)

        returned = await webhook.edit_message(
            message,
            content="test",
            embed=embed,
            embeds=[embed, embed],
            mentions_everyone=False,
            user_mentions=True,
            role_mentions=[567, 890],
        )

        assert returned == returned_message

        webhook.app.rest.edit_webhook_message.assert_called_once_with(
            987654321,
            token="abc123bca",
            message=message,
            content="test",
            embed=embed,
            embeds=[embed, embed],
            mentions_everyone=False,
            user_mentions=True,
            role_mentions=[567, 890],
        )

    @pytest.mark.asyncio
    async def test_edit_message_when_no_token(self, webhook):
        webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot edit a message using a webhook where we don't know the token"):
            assert await webhook.edit_message(987)

    @pytest.mark.asyncio
    async def test_delete_message(self, webhook):
        message = object()
        webhook.app.rest.delete_webhook_message = mock.AsyncMock()

        await webhook.delete_message(message)

        webhook.app.rest.delete_webhook_message.assert_called_once_with(987654321, token="abc123bca", message=message)

    @pytest.mark.asyncio
    async def test_delete_message_when_no_token(self, webhook):
        webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot delete a message using a webhook where we don't know the token"):
            assert await webhook.delete_message(987)

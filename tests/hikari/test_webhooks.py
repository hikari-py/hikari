# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

from hikari import channels
from hikari import undefined
from hikari import webhooks
from tests.hikari import hikari_test_helpers


class TestExecutableWebhook:
    @pytest.fixture
    def executable_webhook(self):
        return hikari_test_helpers.mock_class_namespace(
            webhooks.ExecutableWebhook, slots_=False, app=mock.AsyncMock()
        )()

    @pytest.mark.asyncio
    async def test_execute_when_no_token(self, executable_webhook):
        executable_webhook.token = None

        with pytest.raises(ValueError, match=r"Cannot send a message using a webhook where we don't know the token"):
            await executable_webhook.execute()

    @pytest.mark.asyncio
    async def test_execute_with_optionals(self, executable_webhook):
        mock_attachment_1 = object()
        mock_attachment_2 = object()
        mock_component = object()
        mock_components = object(), object()
        mock_embed = object()
        mock_embeds = object(), object()

        result = await executable_webhook.execute(
            content="coooo",
            username="oopp",
            avatar_url="urlurlurl",
            tts=True,
            attachment=mock_attachment_1,
            attachments=mock_attachment_2,
            component=mock_component,
            components=mock_components,
            embed=mock_embed,
            embeds=mock_embeds,
            mentions_everyone=False,
            user_mentions=[1235432],
            role_mentions=[65234123],
            flags=64,
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
            component=mock_component,
            components=mock_components,
            embed=mock_embed,
            embeds=mock_embeds,
            mentions_everyone=False,
            user_mentions=[1235432],
            role_mentions=[65234123],
            flags=64,
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
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio
    async def test_fetch_message(self, executable_webhook):
        message = object()
        returned_message = object()
        executable_webhook.app.rest.fetch_webhook_message = mock.AsyncMock(return_value=returned_message)

        returned = await executable_webhook.fetch_message(message)

        assert returned is returned_message

        executable_webhook.app.rest.fetch_webhook_message.assert_awaited_once_with(
            executable_webhook.webhook_id, token=executable_webhook.token, message=message
        )

    @pytest.mark.asyncio
    async def test_fetch_message_when_no_token(self, executable_webhook):
        executable_webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot fetch a message using a webhook where we don't know the token"):
            await executable_webhook.fetch_message(987)

    @pytest.mark.asyncio
    async def test_edit_message(self, executable_webhook):
        message = object()
        embed = object()
        attachment = object()
        component = object()
        components = object()

        returned = await executable_webhook.edit_message(
            message,
            content="test",
            embed=embed,
            embeds=[embed, embed],
            attachment=attachment,
            attachments=[attachment, attachment],
            component=component,
            components=components,
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
            component=component,
            components=components,
            mentions_everyone=False,
            user_mentions=True,
            role_mentions=[567, 890],
        )

    @pytest.mark.asyncio
    async def test_edit_message_when_no_token(self, executable_webhook):
        executable_webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot edit a message using a webhook where we don't know the token"):
            await executable_webhook.edit_message(987)

    @pytest.mark.asyncio
    async def test_delete_message(self, executable_webhook):
        message = object()

        await executable_webhook.delete_message(message)

        executable_webhook.app.rest.delete_webhook_message.assert_awaited_once_with(
            executable_webhook.webhook_id, token=executable_webhook.token, message=message
        )

    @pytest.mark.asyncio
    async def test_delete_message_when_no_token(self, executable_webhook):
        executable_webhook.token = None
        with pytest.raises(ValueError, match=r"Cannot delete a message using a webhook where we don't know the token"):
            assert await executable_webhook.delete_message(987)


class TestPartialWebhook:
    @pytest.fixture
    def webhook(self):
        return webhooks.PartialWebhook(
            app=mock.Mock(rest=mock.AsyncMock()),
            id=987654321,
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            name="not a webhook",
            avatar_hash="hook",
            application_id=None,
        )

    def test_str(self, webhook):
        assert str(webhook) == "not a webhook"

    def test_str_when_name_is_None(self, webhook):
        webhook.name = None
        assert str(webhook) == "Unnamed webhook ID 987654321"

    def test_mention_property(self, webhook):
        assert webhook.mention == "<@987654321>"

    def test_avatar_url_property(self, webhook):
        assert webhook.avatar_url == webhook.make_avatar_url()

    def test_default_avatar_url(self, webhook):
        assert webhook.default_avatar_url.url == "https://cdn.discordapp.com/embed/avatars/0.png"

    def test_make_avatar_url(self, webhook):
        result = webhook.make_avatar_url(ext="jpeg", size=2048)

        assert result.url == "https://cdn.discordapp.com/avatars/987654321/hook.jpeg?size=2048"

    def test_make_avatar_url_when_no_avatar(self, webhook):
        webhook.avatar_hash = None

        assert webhook.make_avatar_url() is None


class TestIncomingWebhook:
    @pytest.fixture
    def webhook(self):
        return webhooks.IncomingWebhook(
            app=mock.Mock(rest=mock.AsyncMock()),
            id=987654321,
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            guild_id=123,
            channel_id=456,
            author=None,
            name="not a webhook",
            avatar_hash=None,
            token="abc123bca",
            application_id=None,
        )

    def test_webhook_id_property(self, webhook):
        assert webhook.webhook_id is webhook.id

    @pytest.mark.asyncio
    async def test_delete(self, webhook):
        webhook.token = None

        await webhook.delete()

        webhook.app.rest.delete_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_delete_uses_token_property(self, webhook):
        webhook.token = "123321"

        await webhook.delete()

        webhook.app.rest.delete_webhook.assert_awaited_once_with(987654321, token="123321")

    @pytest.mark.asyncio
    async def test_delete_use_token_is_true(self, webhook):
        webhook.token = "322312"

        await webhook.delete(use_token=True)

        webhook.app.rest.delete_webhook.assert_awaited_once_with(987654321, token="322312")

    @pytest.mark.asyncio
    async def test_delete_use_token_is_true_without_token(self, webhook):
        webhook.token = None

        with pytest.raises(ValueError, match="This webhook's token is unknown, so cannot be used"):
            await webhook.delete(use_token=True)

        webhook.app.rest.delete_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_use_token_is_false(self, webhook):
        webhook.token = "322312"

        await webhook.delete(use_token=False)

        webhook.app.rest.delete_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_edit(self, webhook):
        webhook.token = None
        webhook.app.rest.edit_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)
        mock_avatar = object()

        result = await webhook.edit(name="OK", avatar=mock_avatar, channel=33333, reason="byebye")

        assert result is webhook.app.rest.edit_webhook.return_value
        webhook.app.rest.edit_webhook.assert_awaited_once_with(
            987654321, token=undefined.UNDEFINED, name="OK", avatar=mock_avatar, channel=33333, reason="byebye"
        )

    @pytest.mark.asyncio
    async def test_edit_uses_token_property(self, webhook):
        webhook.token = "aye"
        webhook.app.rest.edit_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)
        mock_avatar = object()

        result = await webhook.edit(name="bye", avatar=mock_avatar, channel=33333, reason="byebye")

        assert result is webhook.app.rest.edit_webhook.return_value
        webhook.app.rest.edit_webhook.assert_awaited_once_with(
            987654321, token="aye", name="bye", avatar=mock_avatar, channel=33333, reason="byebye"
        )

    @pytest.mark.asyncio
    async def test_edit_when_use_token_is_true(self, webhook):
        webhook.token = "owoowow"
        webhook.app.rest.edit_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)
        mock_avatar = object()

        result = await webhook.edit(use_token=True, name="hiu", avatar=mock_avatar, channel=231, reason="sus")

        assert result is webhook.app.rest.edit_webhook.return_value
        webhook.app.rest.edit_webhook.assert_awaited_once_with(
            987654321, token="owoowow", name="hiu", avatar=mock_avatar, channel=231, reason="sus"
        )

    @pytest.mark.asyncio
    async def test_edit_when_use_token_is_true_and_no_token(self, webhook):
        webhook.token = None

        with pytest.raises(ValueError, match="This webhook's token is unknown, so cannot be used"):
            await webhook.edit(use_token=True)

        webhook.app.rest.edit_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_edit_when_use_token_is_false(self, webhook):
        webhook.token = "owoowow"
        webhook.app.rest.edit_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)
        mock_avatar = object()

        result = await webhook.edit(use_token=False, name="eee", avatar=mock_avatar, channel=231, reason="rrr")

        assert result is webhook.app.rest.edit_webhook.return_value
        webhook.app.rest.edit_webhook.assert_awaited_once_with(
            987654321, token=undefined.UNDEFINED, name="eee", avatar=mock_avatar, channel=231, reason="rrr"
        )

    @pytest.mark.asyncio
    async def test_fetch_channel(self, webhook):
        webhook.app.rest.fetch_channel.return_value = mock.Mock(channels.GuildTextChannel)

        assert await webhook.fetch_channel() is webhook.app.rest.fetch_channel.return_value

        webhook.app.rest.fetch_channel.assert_awaited_once_with(webhook.channel_id)

    @pytest.mark.asyncio
    async def test_fetch_self(self, webhook):
        webhook.token = None
        webhook.app.rest.fetch_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)

        result = await webhook.fetch_self()

        assert result is webhook.app.rest.fetch_webhook.return_value
        webhook.app.rest.fetch_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_fetch_self_uses_token_property(self, webhook):
        webhook.token = "no gnomo"
        webhook.app.rest.fetch_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)

        result = await webhook.fetch_self()

        assert result is webhook.app.rest.fetch_webhook.return_value
        webhook.app.rest.fetch_webhook.assert_awaited_once_with(987654321, token="no gnomo")

    @pytest.mark.asyncio
    async def test_fetch_self_when_use_token_is_true(self, webhook):
        webhook.token = "no momo"
        webhook.app.rest.fetch_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)

        result = await webhook.fetch_self(use_token=True)

        assert result is webhook.app.rest.fetch_webhook.return_value
        webhook.app.rest.fetch_webhook.assert_awaited_once_with(987654321, token="no momo")

    @pytest.mark.asyncio
    async def test_fetch_self_when_use_token_is_true_without_token_property(self, webhook):
        webhook.token = None

        with pytest.raises(ValueError, match="This webhook's token is unknown, so cannot be used"):
            await webhook.fetch_self(use_token=True)

        webhook.app.rest.fetch_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_self_when_use_token_is_false(self, webhook):
        webhook.token = "no momo"
        webhook.app.rest.fetch_webhook.return_value = mock.Mock(webhooks.IncomingWebhook)

        result = await webhook.fetch_self(use_token=False)

        assert result is webhook.app.rest.fetch_webhook.return_value
        webhook.app.rest.fetch_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)


class TestChannelFollowerWebhook:
    @pytest.fixture
    def webhook(self):
        return webhooks.ChannelFollowerWebhook(
            app=mock.Mock(rest=mock.AsyncMock()),
            id=987654321,
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            guild_id=123,
            channel_id=456,
            author=None,
            name="not a webhook",
            avatar_hash=None,
            application_id=None,
            source_channel=object(),
            source_guild=object(),
        )

    @pytest.mark.asyncio
    async def test_delete(self, webhook):
        await webhook.delete()

        webhook.app.rest.delete_webhook.assert_awaited_once_with(987654321)

    @pytest.mark.asyncio
    async def test_edit(self, webhook):
        mock_avatar = object()
        webhook.app.rest.edit_webhook.return_value = mock.Mock(webhooks.ChannelFollowerWebhook)

        result = await webhook.edit(name="hi", avatar=mock_avatar, channel=43123, reason="ok")

        assert result is webhook.app.rest.edit_webhook.return_value
        webhook.app.rest.edit_webhook.assert_awaited_once_with(
            987654321, name="hi", avatar=mock_avatar, channel=43123, reason="ok"
        )

    @pytest.mark.asyncio
    async def test_fetch_channel(self, webhook):
        webhook.app.rest.fetch_channel.return_value = mock.Mock(channels.GuildTextChannel)

        assert await webhook.fetch_channel() is webhook.app.rest.fetch_channel.return_value

        webhook.app.rest.fetch_channel.assert_awaited_once_with(webhook.channel_id)

    @pytest.mark.asyncio
    async def test_fetch_self(self, webhook):
        webhook.app.rest.fetch_webhook.return_value = mock.Mock(webhooks.ChannelFollowerWebhook)

        result = await webhook.fetch_self()

        assert result is webhook.app.rest.fetch_webhook.return_value
        webhook.app.rest.fetch_webhook.assert_awaited_once_with(987654321)

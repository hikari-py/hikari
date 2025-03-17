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
from __future__ import annotations

import typing

import mock
import pytest

from hikari import channels
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import webhooks


@pytest.fixture
def mock_app() -> traits.RESTAware:
    return mock.AsyncMock(traits.RESTAware)


class TestExecutableWebhook:
    class MockedExecutableWebhook(webhooks.ExecutableWebhook):
        def __init__(self, app: traits.RESTAware):
            super().__init__()

            self._app = app
            self._webhook_id = snowflakes.Snowflake(548398213)
            self._token = "webhook_token"

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def webhook_id(self) -> snowflakes.Snowflake:
            return self._webhook_id

        @property
        def token(self) -> typing.Optional[str]:
            return self._token

    @pytest.fixture
    def executable_webhook(self, mock_app: traits.RESTAware) -> webhooks.ExecutableWebhook:
        return TestExecutableWebhook.MockedExecutableWebhook(mock_app)

    @pytest.mark.asyncio
    async def test_execute_when_no_token(self, executable_webhook: webhooks.ExecutableWebhook):
        with (
            mock.patch.object(executable_webhook, "_token", None),
            pytest.raises(ValueError, match=r"Cannot send a message using a webhook where we don't know the token"),
        ):
            await executable_webhook.execute()

    @pytest.mark.asyncio
    async def test_execute_with_optionals(self, executable_webhook: webhooks.ExecutableWebhook):
        mock_attachment_1 = mock.Mock()
        mock_attachment_2 = mock.Mock()
        mock_component = mock.Mock()
        mock_components = mock.Mock(), mock.Mock()
        mock_embed = mock.Mock()
        mock_embeds = mock.Mock(), mock.Mock()

        with mock.patch.object(
            executable_webhook.app.rest, "execute_webhook", new_callable=mock.AsyncMock
        ) as patched_execute_webhook:
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

            assert result is patched_execute_webhook.return_value
            patched_execute_webhook.assert_awaited_once_with(
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
    async def test_execute_without_optionals(self, executable_webhook: webhooks.ExecutableWebhook):
        with mock.patch.object(
            executable_webhook.app.rest, "execute_webhook", new_callable=mock.AsyncMock
        ) as patched_execute_webhook:
            result = await executable_webhook.execute()

            assert result is patched_execute_webhook.return_value
            patched_execute_webhook.assert_awaited_once_with(
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
    async def test_fetch_message(self, executable_webhook: webhooks.ExecutableWebhook):
        message = mock.Mock()
        returned_message = mock.Mock()

        with mock.patch.object(
            executable_webhook.app.rest, "fetch_webhook_message", new=mock.AsyncMock(return_value=returned_message)
        ) as patched_fetch_webhook_message:
            returned = await executable_webhook.fetch_message(message)

            assert returned is returned_message

            patched_fetch_webhook_message.assert_awaited_once_with(
                executable_webhook.webhook_id, token=executable_webhook.token, message=message
            )

    @pytest.mark.asyncio
    async def test_fetch_message_when_no_token(self, executable_webhook: webhooks.ExecutableWebhook):
        with (
            mock.patch.object(executable_webhook, "_token", None),
            pytest.raises(ValueError, match=r"Cannot fetch a message using a webhook where we don't know the token"),
        ):
            await executable_webhook.fetch_message(987)

    @pytest.mark.asyncio
    async def test_edit_message(self, executable_webhook: webhooks.ExecutableWebhook):
        message = mock.Mock()
        embed = mock.Mock()
        attachment = mock.Mock()
        component = mock.Mock()
        components = mock.Mock()

        with (
            mock.patch.object(executable_webhook.app, "rest") as patched_rest,
            mock.patch.object(
                patched_rest, "edit_webhook_message", new_callable=mock.AsyncMock
            ) as patched_edit_webhook_message,
        ):
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

            assert returned is patched_edit_webhook_message.return_value

            patched_edit_webhook_message.assert_awaited_once_with(
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
    async def test_edit_message_when_no_token(self, executable_webhook: webhooks.ExecutableWebhook):
        with (
            mock.patch.object(executable_webhook, "_token", None),
            pytest.raises(ValueError, match=r"Cannot edit a message using a webhook where we don't know the token"),
        ):
            await executable_webhook.edit_message(987)

    @pytest.mark.asyncio
    async def test_delete_message(self, executable_webhook: webhooks.ExecutableWebhook):
        message = mock.Mock()

        with (
            mock.patch.object(executable_webhook.app, "rest") as patched_rest,
            mock.patch.object(
                patched_rest, "delete_webhook_message", new_callable=mock.AsyncMock
            ) as patched_delete_webhook_message,
        ):
            await executable_webhook.delete_message(message)

            patched_delete_webhook_message.assert_awaited_once_with(
                executable_webhook.webhook_id, token=executable_webhook.token, message=message
            )

    @pytest.mark.asyncio
    async def test_delete_message_when_no_token(self, executable_webhook: webhooks.ExecutableWebhook):
        with (
            mock.patch.object(executable_webhook, "_token", None),
            pytest.raises(ValueError, match=r"Cannot delete a message using a webhook where we don't know the token"),
        ):
            assert await executable_webhook.delete_message(987)


class TestPartialWebhook:
    @pytest.fixture
    def webhook(self) -> webhooks.PartialWebhook:
        return webhooks.PartialWebhook(
            app=mock.Mock(rest=mock.AsyncMock()),
            id=snowflakes.Snowflake(987654321),
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            name="not a webhook",
            avatar_hash="hook",
            application_id=None,
        )

    def test_str(self, webhook: webhooks.PartialWebhook):
        assert str(webhook) == "not a webhook"

    def test_str_when_name_is_None(self, webhook: webhooks.PartialWebhook):
        with mock.patch.object(webhook, "name", None):
            assert str(webhook) == "Unnamed webhook ID 987654321"

    def test_mention_property(self, webhook: webhooks.PartialWebhook):
        assert webhook.mention == "<@987654321>"

    def test_avatar_url_property(self, webhook: webhooks.PartialWebhook):
        assert webhook.avatar_url == webhook.make_avatar_url()

    def test_default_avatar_url(self, webhook: webhooks.PartialWebhook):
        assert webhook.default_avatar_url.url == "https://cdn.discordapp.com/embed/avatars/0.png"

    def test_make_avatar_url(self, webhook: webhooks.PartialWebhook):
        result = webhook.make_avatar_url(ext="jpeg", size=2048)

        assert result is not None
        assert result.url == "https://cdn.discordapp.com/avatars/987654321/hook.jpeg?size=2048"

    def test_make_avatar_url_when_no_avatar(self, webhook: webhooks.PartialWebhook):
        webhook.avatar_hash = None

        assert webhook.make_avatar_url() is None


class TestIncomingWebhook:
    @pytest.fixture
    def webhook(self) -> webhooks.IncomingWebhook:
        return webhooks.IncomingWebhook(
            app=mock.Mock(rest=mock.AsyncMock()),
            id=snowflakes.Snowflake(987654321),
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            guild_id=snowflakes.Snowflake(123),
            channel_id=snowflakes.Snowflake(456),
            author=None,
            name="not a webhook",
            avatar_hash=None,
            token="abc123bca",
            application_id=None,
        )

    def test_webhook_id_property(self, webhook: webhooks.IncomingWebhook):
        assert webhook.webhook_id is webhook.id

    @pytest.mark.asyncio
    async def test_delete(self, webhook: webhooks.IncomingWebhook):
        webhook.token = None

        with mock.patch.object(
            webhook.app.rest, "delete_webhook", new_callable=mock.AsyncMock
        ) as patched_delete_webhook:
            await webhook.delete()

            patched_delete_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_delete_uses_token_property(self, webhook: webhooks.IncomingWebhook):
        webhook.token = "123321"

        with mock.patch.object(
            webhook.app.rest, "delete_webhook", new_callable=mock.AsyncMock
        ) as patched_delete_webhook:
            await webhook.delete()

            patched_delete_webhook.assert_awaited_once_with(987654321, token="123321")

    @pytest.mark.asyncio
    async def test_delete_use_token_is_true(self, webhook: webhooks.IncomingWebhook):
        webhook.token = "322312"

        with mock.patch.object(
            webhook.app.rest, "delete_webhook", new_callable=mock.AsyncMock
        ) as patched_delete_webhook:
            await webhook.delete(use_token=True)

            patched_delete_webhook.assert_awaited_once_with(987654321, token="322312")

    @pytest.mark.asyncio
    async def test_delete_use_token_is_true_without_token(self, webhook: webhooks.IncomingWebhook):
        webhook.token = None

        with mock.patch.object(
            webhook.app.rest, "delete_webhook", new_callable=mock.AsyncMock
        ) as patched_delete_webhook:
            with pytest.raises(ValueError, match="This webhook's token is unknown, so cannot be used"):
                await webhook.delete(use_token=True)

            patched_delete_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_use_token_is_false(self, webhook: webhooks.IncomingWebhook):
        webhook.token = "322312"

        with mock.patch.object(
            webhook.app.rest, "delete_webhook", new_callable=mock.AsyncMock
        ) as patched_delete_webhook:
            await webhook.delete(use_token=False)

            patched_delete_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_edit(self, webhook: webhooks.IncomingWebhook):
        webhook.token = None
        with mock.patch.object(
            webhook.app.rest, "edit_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
        ) as patched_edit_webhook:
            mock_avatar = mock.Mock()

            result = await webhook.edit(name="OK", avatar=mock_avatar, channel=33333, reason="byebye")

            assert result is patched_edit_webhook.return_value
            patched_edit_webhook.assert_awaited_once_with(
                987654321, token=undefined.UNDEFINED, name="OK", avatar=mock_avatar, channel=33333, reason="byebye"
            )

    @pytest.mark.asyncio
    async def test_edit_uses_token_property(self, webhook: webhooks.IncomingWebhook):
        webhook.token = "aye"
        with mock.patch.object(
            webhook.app.rest, "edit_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
        ) as patched_edit_webhook:
            mock_avatar = mock.Mock()

            result = await webhook.edit(name="bye", avatar=mock_avatar, channel=33333, reason="byebye")

            assert result is patched_edit_webhook.return_value
            patched_edit_webhook.assert_awaited_once_with(
                987654321, token="aye", name="bye", avatar=mock_avatar, channel=33333, reason="byebye"
            )

    @pytest.mark.asyncio
    async def test_edit_when_use_token_is_true(self, webhook: webhooks.IncomingWebhook):
        webhook.token = "owoowow"
        with mock.patch.object(
            webhook.app.rest, "edit_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
        ) as patched_edit_webhook:
            mock_avatar = mock.Mock()

            result = await webhook.edit(use_token=True, name="hiu", avatar=mock_avatar, channel=231, reason="sus")

            assert result is patched_edit_webhook.return_value
            patched_edit_webhook.assert_awaited_once_with(
                987654321, token="owoowow", name="hiu", avatar=mock_avatar, channel=231, reason="sus"
            )

    @pytest.mark.asyncio
    async def test_edit_when_use_token_is_true_and_no_token(self, webhook: webhooks.IncomingWebhook):
        webhook.token = None

        with (
            mock.patch.object(
                webhook.app.rest, "edit_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
            ) as patched_edit_webhook,
            pytest.raises(ValueError, match="This webhook's token is unknown, so cannot be used"),
        ):
            await webhook.edit(use_token=True)

        patched_edit_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_edit_when_use_token_is_false(self, webhook: webhooks.IncomingWebhook):
        webhook.token = "owoowow"
        with mock.patch.object(
            webhook.app.rest, "edit_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
        ) as patched_edit_webhook:
            mock_avatar = mock.Mock()

            result = await webhook.edit(use_token=False, name="eee", avatar=mock_avatar, channel=231, reason="rrr")

            assert result is patched_edit_webhook.return_value
            patched_edit_webhook.assert_awaited_once_with(
                987654321, token=undefined.UNDEFINED, name="eee", avatar=mock_avatar, channel=231, reason="rrr"
            )

    @pytest.mark.asyncio
    async def test_fetch_channel(self, webhook: webhooks.IncomingWebhook):
        with mock.patch.object(
            webhook.app.rest, "fetch_channel", new=mock.AsyncMock(return_value=mock.Mock(channels.GuildTextChannel))
        ) as patched_fetch_channel:
            assert await webhook.fetch_channel() is patched_fetch_channel.return_value

            patched_fetch_channel.assert_awaited_once_with(webhook.channel_id)

    @pytest.mark.asyncio
    async def test_fetch_self(self, webhook: webhooks.IncomingWebhook):
        with (
            mock.patch.object(webhook, "token", None),
            mock.patch.object(
                webhook.app.rest, "fetch_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
            ) as patched_fetch_webhook,
        ):
            result = await webhook.fetch_self()

            assert result is patched_fetch_webhook.return_value
            patched_fetch_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_fetch_self_uses_token_property(self, webhook: webhooks.IncomingWebhook):
        with (
            mock.patch.object(webhook, "token", "no gnomo"),
            mock.patch.object(
                webhook.app.rest, "fetch_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
            ) as patched_fetch_webhook,
        ):
            result = await webhook.fetch_self()

            assert result is patched_fetch_webhook.return_value
            patched_fetch_webhook.assert_awaited_once_with(987654321, token="no gnomo")

    @pytest.mark.asyncio
    async def test_fetch_self_when_use_token_is_true(self, webhook: webhooks.IncomingWebhook):
        with (
            mock.patch.object(webhook, "token", "no momo"),
            mock.patch.object(
                webhook.app.rest, "fetch_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
            ) as patched_fetch_webhook,
        ):
            result = await webhook.fetch_self(use_token=True)

            assert result is patched_fetch_webhook.return_value
            patched_fetch_webhook.assert_awaited_once_with(987654321, token="no momo")

    @pytest.mark.asyncio
    async def test_fetch_self_when_use_token_is_true_without_token_property(self, webhook: webhooks.IncomingWebhook):
        webhook.token = None

        with mock.patch.object(webhook.app.rest, "fetch_webhook") as patched_fetch_webhook:
            with pytest.raises(ValueError, match="This webhook's token is unknown, so cannot be used"):
                await webhook.fetch_self(use_token=True)

            patched_fetch_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_self_when_use_token_is_false(self, webhook: webhooks.IncomingWebhook):
        with (
            mock.patch.object(webhook, "token", "no momo"),
            mock.patch.object(
                webhook.app.rest, "fetch_webhook", new=mock.AsyncMock(return_value=mock.Mock(webhooks.IncomingWebhook))
            ) as patched_fetch_webhook,
        ):
            result = await webhook.fetch_self(use_token=False)

            assert result is patched_fetch_webhook.return_value
            patched_fetch_webhook.assert_awaited_once_with(987654321, token=undefined.UNDEFINED)


class TestChannelFollowerWebhook:
    @pytest.fixture
    def webhook(self) -> webhooks.ChannelFollowerWebhook:
        return webhooks.ChannelFollowerWebhook(
            app=mock.Mock(rest=mock.AsyncMock()),
            id=snowflakes.Snowflake(987654321),
            type=webhooks.WebhookType.CHANNEL_FOLLOWER,
            guild_id=snowflakes.Snowflake(123),
            channel_id=snowflakes.Snowflake(456),
            author=None,
            name="not a webhook",
            avatar_hash=None,
            application_id=None,
            source_channel=mock.Mock(),
            source_guild=mock.Mock(),
        )

    @pytest.mark.asyncio
    async def test_delete(self, webhook: webhooks.ChannelFollowerWebhook):
        with mock.patch.object(webhook.app.rest, "delete_webhook") as patched_delete_webhook:
            await webhook.delete()

            patched_delete_webhook.assert_awaited_once_with(987654321)

    @pytest.mark.asyncio
    async def test_edit(self, webhook: webhooks.ChannelFollowerWebhook):
        mock_avatar = mock.Mock()

        with mock.patch.object(
            webhook.app.rest,
            "edit_webhook",
            new=mock.AsyncMock(return_value=mock.Mock(webhooks.ChannelFollowerWebhook)),
        ) as patched_edit_webhook:
            result = await webhook.edit(name="hi", avatar=mock_avatar, channel=43123, reason="ok")

            assert result is patched_edit_webhook.return_value
            patched_edit_webhook.assert_awaited_once_with(
                987654321, name="hi", avatar=mock_avatar, channel=43123, reason="ok"
            )

    @pytest.mark.asyncio
    async def test_fetch_channel(self, webhook: webhooks.ChannelFollowerWebhook):
        with mock.patch.object(
            webhook.app.rest, "fetch_channel", new=mock.AsyncMock(return_value=mock.Mock(channels.GuildTextChannel))
        ) as patched_fetch_channel:
            assert await webhook.fetch_channel() is patched_fetch_channel.return_value

            patched_fetch_channel.assert_awaited_once_with(webhook.channel_id)

    @pytest.mark.asyncio
    async def test_fetch_self(self, webhook: webhooks.ChannelFollowerWebhook):
        with mock.patch.object(
            webhook.app.rest,
            "fetch_webhook",
            new=mock.AsyncMock(return_value=mock.Mock(webhooks.ChannelFollowerWebhook)),
        ) as patched_fetch_webhook:
            result = await webhook.fetch_self()

            assert result is patched_fetch_webhook.return_value
            patched_fetch_webhook.assert_awaited_once_with(987654321)

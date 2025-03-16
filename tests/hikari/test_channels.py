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

import datetime

import mock
import pytest

from hikari import channels
from hikari import files
from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari import users
from hikari import webhooks
from tests.hikari import hikari_test_helpers


@pytest.fixture
def mock_app() -> traits.RESTAware:
    return mock.Mock(traits.RESTAware)


class TestChannelFollow:
    @pytest.mark.asyncio
    async def test_fetch_channel(self, mock_app: traits.RESTAware):
        mock_channel = mock.Mock(spec=channels.GuildNewsChannel)
        mock_app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)
        follow = channels.ChannelFollow(
            channel_id=snowflakes.Snowflake(9459234123), app=mock_app, webhook_id=snowflakes.Snowflake(3123123)
        )

        result = await follow.fetch_channel()

        assert result is mock_channel
        mock_app.rest.fetch_channel.assert_awaited_once_with(9459234123)

    @pytest.mark.asyncio
    async def test_fetch_webhook(self, mock_app: traits.RESTAware):
        mock_app.rest.fetch_webhook = mock.AsyncMock(return_value=mock.Mock(webhooks.ChannelFollowerWebhook))
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(54123123), app=mock_app, channel_id=snowflakes.Snowflake(94949494)
        )

        result = await follow.fetch_webhook()

        assert result is mock_app.rest.fetch_webhook.return_value
        mock_app.rest.fetch_webhook.assert_awaited_once_with(54123123)

    def test_get_channel(self):
        mock_channel = mock.Mock(spec=channels.GuildNewsChannel)

        app = mock.Mock(traits.CacheAware, rest=mock.Mock())
        with mock.patch.object(
            app.cache, "get_guild_channel", mock.Mock(return_value=mock_channel)
        ) as patched_get_guild_channel:
            follow = channels.ChannelFollow(
                webhook_id=snowflakes.Snowflake(993883), app=app, channel_id=snowflakes.Snowflake(696969)
            )

            result = follow.get_channel()

            assert result is mock_channel
            patched_get_guild_channel.assert_called_once_with(696969)

    def test_get_channel_when_no_cache_trait(self):
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(993883),
            app=mock.Mock(traits.RESTAware),
            channel_id=snowflakes.Snowflake(696969),
        )

        assert follow.get_channel() is None


class TestPermissionOverwrite:
    def test_unset(self):
        overwrite = channels.PermissionOverwrite(
            type=channels.PermissionOverwriteType.MEMBER, id=snowflakes.Snowflake(1234321)
        )
        overwrite.allow = permissions.Permissions.CREATE_INSTANT_INVITE
        overwrite.deny = permissions.Permissions.CHANGE_NICKNAME
        assert overwrite.unset == permissions.Permissions(-67108866)


class TestPartialChannel:
    @pytest.fixture
    def partial_channel(self, mock_app: traits.RESTAware) -> channels.PartialChannel:
        return hikari_test_helpers.mock_class_namespace(channels.PartialChannel, rename_impl_=False)(
            app=mock_app, id=snowflakes.Snowflake(1234567), name="foo", type=channels.ChannelType.GUILD_NEWS
        )

    def test_str_operator(self, partial_channel: channels.PartialChannel):
        assert str(partial_channel) == "foo"

    def test_str_operator_when_name_is_None(self, partial_channel: channels.PartialChannel):
        partial_channel.name = None
        assert str(partial_channel) == "Unnamed PartialChannel ID 1234567"

    def test_mention_property(self, partial_channel: channels.PartialChannel):
        assert partial_channel.mention == "<#1234567>"

    @pytest.mark.asyncio
    async def test_delete(self, partial_channel: channels.PartialChannel):
        with mock.patch.object(partial_channel.app.rest, "delete_channel", mock.AsyncMock()) as patched_delete_channel:
            assert await partial_channel.delete() is patched_delete_channel.return_value
            patched_delete_channel.assert_called_once_with(1234567)


class TestDMChannel:
    @pytest.fixture
    def dm_channel(self, mock_app: traits.RESTAware) -> channels.DMChannel:
        return channels.DMChannel(
            id=snowflakes.Snowflake(12345),
            name="steve",
            type=channels.ChannelType.DM,
            last_message_id=snowflakes.Snowflake(12345),
            recipient=mock.Mock(spec_set=users.UserImpl, __str__=mock.Mock(return_value="snoop#0420")),
            app=mock_app,
        )

    def test_str_operator(self, dm_channel: channels.DMChannel):
        assert str(dm_channel) == "DMChannel with: snoop#0420"

    def test_shard_id(self, dm_channel: channels.DMChannel):
        assert dm_channel.shard_id == 0


class TestGroupDMChannel:
    @pytest.fixture
    def group_dm_channel(self, mock_app: traits.RESTAware) -> channels.GroupDMChannel:
        return channels.GroupDMChannel(
            app=mock_app,
            id=snowflakes.Snowflake(136134),
            name="super cool group dm",
            type=channels.ChannelType.DM,
            last_message_id=snowflakes.Snowflake(3232),
            owner_id=snowflakes.Snowflake(1066),
            icon_hash="1a2b3c",
            nicknames={snowflakes.Snowflake(1): "person 1", snowflakes.Snowflake(2): "person 2"},
            recipients={
                snowflakes.Snowflake(1): mock.Mock(spec_set=users.User, __str__=mock.Mock(return_value="snoop#0420")),
                snowflakes.Snowflake(2): mock.Mock(spec_set=users.User, __str__=mock.Mock(return_value="yeet#1012")),
                snowflakes.Snowflake(3): mock.Mock(spec_set=users.User, __str__=mock.Mock(return_value="nice#6969")),
            },
            application_id=None,
        )

    def test_str_operator(self, group_dm_channel: channels.GroupDMChannel):
        assert str(group_dm_channel) == "super cool group dm"

    def test_str_operator_when_name_is_None(self, group_dm_channel: channels.GroupDMChannel):
        group_dm_channel.name = None
        assert str(group_dm_channel) == "GroupDMChannel with: snoop#0420, yeet#1012, nice#6969"

    def test_icon_url(self, group_dm_channel: channels.GroupDMChannel):
        with mock.patch.object(
            channels.GroupDMChannel, "make_icon_url", mock.Mock(return_value="icon-url-here.com")
        ) as patched_make_icon_url:
            assert group_dm_channel.icon_url == "icon-url-here.com"
            patched_make_icon_url.assert_called_once()

    def test_make_icon_url(self, group_dm_channel: channels.GroupDMChannel):
        assert group_dm_channel.make_icon_url(ext="jpeg", size=16) == files.URL(
            "https://cdn.discordapp.com/channel-icons/136134/1a2b3c.jpeg?size=16"
        )

    def test_make_icon_url_without_optional_params(self, group_dm_channel: channels.GroupDMChannel):
        assert group_dm_channel.make_icon_url() == files.URL(
            "https://cdn.discordapp.com/channel-icons/136134/1a2b3c.png?size=4096"
        )

    def test_make_icon_url_when_hash_is_None(self, group_dm_channel: channels.GroupDMChannel):
        group_dm_channel.icon_hash = None
        assert group_dm_channel.make_icon_url() is None


class TestTextChannel:
    @pytest.fixture
    def text_channel(self, mock_app: traits.RESTAware) -> channels.TextableChannel:
        return hikari_test_helpers.mock_class_namespace(channels.TextableChannel)(
            app=mock_app, id=snowflakes.Snowflake(12345679), name="foo1", type=channels.ChannelType.GUILD_TEXT
        )

    @pytest.mark.asyncio
    async def test_fetch_history(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.fetch_messages = mock.AsyncMock()

        await text_channel.fetch_history(
            before=datetime.datetime(2020, 4, 1, 1, 0, 0),
            after=datetime.datetime(2020, 4, 1, 0, 0, 0),
            around=datetime.datetime(2020, 4, 1, 0, 30, 0),
        )

        text_channel.app.rest.fetch_messages.assert_awaited_once_with(
            12345679,
            before=datetime.datetime(2020, 4, 1, 1, 0, 0),
            after=datetime.datetime(2020, 4, 1, 0, 0, 0),
            around=datetime.datetime(2020, 4, 1, 0, 30, 0),
        )

    @pytest.mark.asyncio
    async def test_fetch_message(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.fetch_message = mock.AsyncMock()

        assert await text_channel.fetch_message(133742069) is text_channel.app.rest.fetch_message.return_value

        text_channel.app.rest.fetch_message.assert_awaited_once_with(12345679, 133742069)

    @pytest.mark.asyncio
    async def test_fetch_pins(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.fetch_pins = mock.AsyncMock()

        await text_channel.fetch_pins()

        text_channel.app.rest.fetch_pins.assert_awaited_once_with(12345679)

    @pytest.mark.asyncio
    async def test_pin_message(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.pin_message = mock.AsyncMock()

        assert await text_channel.pin_message(77790) is text_channel.app.rest.pin_message.return_value

        text_channel.app.rest.pin_message.assert_awaited_once_with(12345679, 77790)

    @pytest.mark.asyncio
    async def test_unpin_message(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.unpin_message = mock.AsyncMock()

        assert await text_channel.unpin_message(77790) is text_channel.app.rest.unpin_message.return_value

        text_channel.app.rest.unpin_message.assert_awaited_once_with(12345679, 77790)

    @pytest.mark.asyncio
    async def test_delete_messages(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.delete_messages = mock.AsyncMock()

        await text_channel.delete_messages([77790, 88890, 1800], 1337)

        text_channel.app.rest.delete_messages.assert_awaited_once_with(12345679, [77790, 88890, 1800], 1337)

    @pytest.mark.asyncio
    async def test_send(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.create_message = mock.AsyncMock()
        mock_attachment = mock.Mock()
        mock_component = mock.Mock()
        mock_components = [mock.Mock(), mock.Mock()]
        mock_embed = mock.Mock()
        mock_embeds = mock.Mock()
        mock_attachments = [mock.Mock(), mock.Mock(), mock.Mock()]
        mock_reply = mock.Mock()

        await text_channel.send(
            content="test content",
            tts=True,
            attachment=mock_attachment,
            attachments=mock_attachments,
            component=mock_component,
            components=mock_components,
            embed=mock_embed,
            embeds=mock_embeds,
            sticker=543,
            stickers=[132, 65423],
            reply=mock_reply,
            reply_must_exist=False,
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[789, 567],
            mentions_reply=True,
            flags=6969,
        )

        text_channel.app.rest.create_message.assert_awaited_once_with(
            channel=12345679,
            content="test content",
            tts=True,
            attachment=mock_attachment,
            attachments=mock_attachments,
            component=mock_component,
            components=mock_components,
            embed=mock_embed,
            embeds=mock_embeds,
            sticker=543,
            stickers=[132, 65423],
            reply=mock_reply,
            reply_must_exist=False,
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[789, 567],
            mentions_reply=True,
            flags=6969,
        )

    def test_trigger_typing(self, text_channel: channels.TextableChannel):
        text_channel.app.rest.trigger_typing = mock.Mock()

        text_channel.trigger_typing()

        text_channel.app.rest.trigger_typing.assert_called_once_with(12345679)


class TestGuildChannel:
    @pytest.fixture
    def guild_channel(self, mock_app: traits.RESTAware) -> channels.GuildChannel:
        return channels.GuildChannel(
            app=mock_app,
            id=snowflakes.Snowflake(69420),
            name="foo1",
            type=channels.ChannelType.GUILD_VOICE,
            guild_id=snowflakes.Snowflake(123456789),
            parent_id=None,
        )

    def test_shard_id_property_when_not_shard_aware(self, guild_channel: channels.GuildChannel):
        with mock.patch.object(guild_channel, "app", None):
            assert guild_channel.shard_id is None

    def test_shard_id_property_when_guild_id_is_not_None(self, guild_channel: channels.GuildChannel):
        with (
            mock.patch.object(guild_channel, "app", mock.Mock(traits.ShardAware, rest=mock.Mock())) as patched_app,
            mock.patch.object(patched_app, "shard_count", 3),
        ):
            assert guild_channel.shard_id == 2

    @pytest.mark.asyncio
    async def test_fetch_guild(self, guild_channel: channels.GuildChannel):
        guild_channel.app.rest.fetch_guild = mock.AsyncMock()

        assert await guild_channel.fetch_guild() is guild_channel.app.rest.fetch_guild.return_value

        guild_channel.app.rest.fetch_guild.assert_awaited_once_with(123456789)

    @pytest.mark.asyncio
    async def test_edit(self, guild_channel: channels.GuildChannel):
        guild_channel.app.rest.edit_channel = mock.AsyncMock()

        permission_overwrite = mock.Mock(channels.PermissionOverwrite, id=123)

        result = await guild_channel.edit(
            name="Supa fast boike",
            bitrate=420,
            reason="left right",
            default_auto_archive_duration=123312,
            position=4423,
            topic="hi",
            nsfw=True,
            video_quality_mode=channels.VideoQualityMode.AUTO,
            user_limit=123321,
            rate_limit_per_user=54123123,
            region="us-west",
            parent_category=341123123123,
            permission_overwrites=[permission_overwrite],
            flags=channels.ChannelFlag.REQUIRE_TAG,
            archived=True,
            auto_archive_duration=1234,
            locked=True,
            invitable=True,
            applied_tags=[12345, 54321],
        )

        assert result is guild_channel.app.rest.edit_channel.return_value
        guild_channel.app.rest.edit_channel.assert_awaited_once_with(
            69420,
            name="Supa fast boike",
            position=4423,
            topic="hi",
            nsfw=True,
            bitrate=420,
            video_quality_mode=channels.VideoQualityMode.AUTO,
            user_limit=123321,
            rate_limit_per_user=54123123,
            region="us-west",
            permission_overwrites=[permission_overwrite],
            parent_category=341123123123,
            default_auto_archive_duration=123312,
            flags=channels.ChannelFlag.REQUIRE_TAG,
            archived=True,
            auto_archive_duration=1234,
            locked=True,
            invitable=True,
            applied_tags=[12345, 54321],
            reason="left right",
        )


class TestPermissibleGuildChannel:
    @pytest.fixture
    def permissible_guild_channel(self, mock_app: traits.RESTAware) -> channels.PermissibleGuildChannel:
        return hikari_test_helpers.mock_class_namespace(channels.PermissibleGuildChannel)(
            app=mock_app,
            id=snowflakes.Snowflake(69420),
            name="foo1",
            type=channels.ChannelType.GUILD_VOICE,
            guild_id=snowflakes.Snowflake(123456789),
            is_nsfw=True,
            parent_id=None,
            position=54,
            permission_overwrites={},
        )

    @pytest.mark.asyncio
    async def test_edit_overwrite(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        permissible_guild_channel.app.rest.edit_permission_overwrite = mock.AsyncMock()
        user = mock.Mock(users.PartialUser)
        await permissible_guild_channel.edit_overwrite(
            333,
            target_type=user,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CONNECT,
            reason="vrooom vroom",
        )

        permissible_guild_channel.app.rest.edit_permission_overwrite.assert_called_once_with(
            69420,
            333,
            target_type=user,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CONNECT,
            reason="vrooom vroom",
        )

    @pytest.mark.asyncio
    async def test_edit_overwrite_target_type_none(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        permissible_guild_channel.app.rest.edit_permission_overwrite = mock.AsyncMock()
        user = mock.Mock(users.PartialUser)
        await permissible_guild_channel.edit_overwrite(
            user, allow=permissions.Permissions.BAN_MEMBERS, deny=permissions.Permissions.CONNECT, reason="vrooom vroom"
        )

        permissible_guild_channel.app.rest.edit_permission_overwrite.assert_called_once_with(
            69420,
            user,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CONNECT,
            reason="vrooom vroom",
        )

    @pytest.mark.asyncio
    async def test_remove_overwrite(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        permissible_guild_channel.app.rest.delete_permission_overwrite = mock.AsyncMock()

        await permissible_guild_channel.remove_overwrite(333)

        permissible_guild_channel.app.rest.delete_permission_overwrite.assert_called_once_with(69420, 333)

    def test_get_guild(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        guild = mock.Mock(id=123456789)

        with (
            mock.patch.object(
                permissible_guild_channel, "app", mock.Mock(traits.CacheAware, rest=mock.Mock())
            ) as patched_app,
            mock.patch.object(patched_app.cache, "get_guild", side_effect=[guild]) as patched_get_guild,
        ):
            assert permissible_guild_channel.get_guild() == guild
            patched_get_guild.assert_called_once_with(123456789)

    def test_get_guild_when_guild_not_in_cache(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        with (
            mock.patch.object(
                permissible_guild_channel, "app", mock.Mock(traits.CacheAware, rest=mock.Mock())
            ) as patched_app,
            mock.patch.object(patched_app.cache, "get_guild", side_effect=[None]) as patched_get_guild,
        ):
            assert permissible_guild_channel.get_guild() is None
            patched_get_guild.assert_called_once_with(123456789)

    def test_get_guild_when_no_cache_trait(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        permissible_guild_channel.app = mock.Mock(traits.RESTAware)

        assert permissible_guild_channel.get_guild() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, permissible_guild_channel: channels.PermissibleGuildChannel):
        permissible_guild_channel.app.rest.fetch_guild = mock.AsyncMock()

        assert (
            await permissible_guild_channel.fetch_guild() == permissible_guild_channel.app.rest.fetch_guild.return_value
        )

        permissible_guild_channel.app.rest.fetch_guild.assert_awaited_once_with(123456789)


class TestForumTag:
    @pytest.mark.parametrize(
        ("emoji", "expected_unicode_emoji", "expected_emoji_id"),
        [(123, None, 123), ("emoji", "emoji", None), (None, None, None)],
    )
    def test_emoji_parameters(
        self, emoji: int | str | None, expected_emoji_id: str | None, expected_unicode_emoji: int | None
    ):
        tag = channels.ForumTag(name="testing", emoji=emoji)

        assert tag.emoji_id == expected_emoji_id
        assert tag.unicode_emoji == expected_unicode_emoji

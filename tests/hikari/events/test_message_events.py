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
from hikari import messages
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import users
from hikari.api import shard as shard_api
from hikari.events import message_events


class TestMessageCreateEvent:
    class MockMessageCreateEvent(message_events.MessageCreateEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._message = mock.Mock(channel_id=snowflakes.Snowflake(123), id=snowflakes.Snowflake(456))

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def message(self) -> messages.Message:
            return self._message

    @pytest.fixture
    def message_create_event(self, hikari_app: traits.RESTAware) -> message_events.MessageCreateEvent:
        return TestMessageCreateEvent.MockMessageCreateEvent(hikari_app)

    def test_app_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.app is message_create_event.message.app

    def test_author_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.author is message_create_event.message.author

    def test_author_id_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.author_id is message_create_event.author.id

    def test_channel_id_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.channel_id is message_create_event.message.channel_id

    def test_content_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.content is message_create_event.message.content

    def test_embeds_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.embeds is message_create_event.message.embeds

    @pytest.mark.parametrize("is_bot", [True, False])
    def test_is_bot_property(self, message_create_event: message_events.MessageCreateEvent, is_bot: bool):
        with mock.patch.object(message_create_event.message.author, "is_bot", is_bot):
            assert message_create_event.is_bot is is_bot

    @pytest.mark.parametrize(
        ("author_is_bot", "webhook_id", "expected_is_human"),
        [(True, 123, False), (True, None, False), (False, 123, False), (False, None, True)],
    )
    def test_is_human_property(
        self,
        message_create_event: message_events.MessageCreateEvent,
        author_is_bot: bool,
        webhook_id: snowflakes.Snowflake,
        expected_is_human: bool,
    ):
        with (
            mock.patch.object(message_create_event.message.author, "is_bot", author_is_bot),
            mock.patch.object(message_create_event.message, "webhook_id", webhook_id),
        ):
            assert message_create_event.is_human is expected_is_human

    @pytest.mark.parametrize(("webhook_id", "is_webhook"), [(123, True), (None, False)])
    def test_is_webhook_property(
        self,
        message_create_event: message_events.MessageCreateEvent,
        webhook_id: typing.Optional[int],
        is_webhook: bool,
    ):
        with mock.patch.object(message_create_event.message, "webhook_id", webhook_id):
            assert message_create_event.is_webhook is is_webhook

    def test_message_id_property(self, message_create_event: message_events.MessageCreateEvent):
        assert message_create_event.message_id is message_create_event.message.id


class TestMessageUpdateEvent:
    class MockMessageUpdateEvent(message_events.MessageUpdateEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._message = mock.Mock(channel_id=snowflakes.Snowflake(123), id=snowflakes.Snowflake(456))

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def message(self) -> messages.Message:
            return self._message

    @pytest.fixture
    def message_update_event(self, hikari_app: traits.RESTAware) -> message_events.MessageUpdateEvent:
        return TestMessageUpdateEvent.MockMessageUpdateEvent(hikari_app)

    def test_app_property(self, message_update_event: message_events.MessageUpdateEvent):
        assert message_update_event.app is message_update_event.message.app

    @pytest.mark.parametrize("author", [mock.Mock(spec_set=users.User), undefined.UNDEFINED])
    def test_author_property(self, message_update_event: message_events.MessageUpdateEvent, author: users.User):
        message_update_event.message.author = author
        assert message_update_event.author is author

    @pytest.mark.parametrize(
        ("author", "expected_id"),
        [(mock.Mock(spec_set=users.User, id=91827), 91827), (undefined.UNDEFINED, undefined.UNDEFINED)],
    )
    def test_author_id_property(
        self,
        message_update_event: message_events.MessageUpdateEvent,
        author: undefined.UndefinedOr[users.User],
        expected_id: undefined.UndefinedOr[int],
    ):
        message_update_event.message.author = author
        assert message_update_event.author_id == expected_id

    def test_channel_id_property(self, message_update_event: message_events.MessageUpdateEvent):
        assert message_update_event.channel_id is message_update_event.message.channel_id

    def test_content_property(self, message_update_event: message_events.MessageUpdateEvent):
        assert message_update_event.content is message_update_event.message.content

    def test_embeds_property(self, message_update_event: message_events.MessageUpdateEvent):
        assert message_update_event.embeds is message_update_event.message.embeds

    @pytest.mark.parametrize("is_bot", [True, False])
    def test_is_bot_property(self, message_update_event: message_events.MessageUpdateEvent, is_bot: bool):
        with mock.patch.object(message_update_event.message.author, "is_bot", is_bot):
            assert message_update_event.is_bot is is_bot

    def test_is_bot_property_if_no_author(self, message_update_event: message_events.MessageUpdateEvent):
        message_update_event.message.author = undefined.UNDEFINED
        assert message_update_event.is_bot is undefined.UNDEFINED

    @pytest.mark.parametrize(
        ("author", "webhook_id", "expected_is_human"),
        [
            (mock.Mock(spec_set=users.User, is_bot=True), 123, False),
            (mock.Mock(spec_set=users.User, is_bot=True), undefined.UNDEFINED, False),
            (mock.Mock(spec_set=users.User, is_bot=False), 123, False),
            (mock.Mock(spec_set=users.User, is_bot=False), undefined.UNDEFINED, True),
            (undefined.UNDEFINED, 123, False),
            (undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED),
        ],
    )
    def test_is_human_property(
        self,
        message_update_event: message_events.MessageUpdateEvent,
        author: undefined.UndefinedOr[users.User],
        webhook_id: undefined.UndefinedOr[snowflakes.Snowflake],
        expected_is_human: undefined.UndefinedOr[bool],
    ):
        message_update_event.message.author = author
        message_update_event.message.webhook_id = webhook_id
        assert message_update_event.is_human is expected_is_human

    @pytest.mark.parametrize(
        ("webhook_id", "is_webhook"), [(123, True), (None, False), (undefined.UNDEFINED, undefined.UNDEFINED)]
    )
    def test_is_webhook_property(
        self,
        message_update_event: message_events.MessageUpdateEvent,
        webhook_id: undefined.UndefinedOr[snowflakes.Snowflake],
        is_webhook: undefined.UndefinedOr[bool],
    ):
        message_update_event.message.webhook_id = webhook_id
        assert message_update_event.is_webhook is is_webhook

    def test_message_id_property(self, message_update_event: message_events.MessageUpdateEvent):
        assert message_update_event.message_id is message_update_event.message.id


class TestGuildMessageCreateEvent:
    @pytest.fixture
    def guild_message_create_event(self) -> message_events.GuildMessageCreateEvent:
        return message_events.GuildMessageCreateEvent(
            message=mock.Mock(
                spec=messages.Message,
                guild_id=snowflakes.Snowflake(342123123),
                channel_id=snowflakes.Snowflake(9121234),
            ),
            shard=mock.Mock(),
        )

    def test_guild_id_property(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        assert guild_message_create_event.guild_id == snowflakes.Snowflake(342123123)

    def test_get_channel_when_no_cache_trait(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        with mock.patch.object(message_events.GuildMessageCreateEvent, "app", None):
            assert guild_message_create_event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_get_channel(
        self,
        guild_message_create_event: message_events.GuildMessageCreateEvent,
        guild_channel_impl: typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel],
    ):
        with (
            mock.patch.object(
                message_events.GuildMessageCreateEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
            ) as patched_get_guild_channel,
        ):
            result = guild_message_create_event.get_channel()
            assert result is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(9121234)

    def test_get_guild_when_no_cache_trait(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        with mock.patch.object(message_events.GuildMessageCreateEvent, "app", None):
            assert guild_message_create_event.get_guild() is None

    def test_get_guild(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        with (
            mock.patch.object(
                message_events.GuildMessageCreateEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild") as patched_get_guild,
        ):
            result = guild_message_create_event.get_guild()

            assert result is patched_get_guild.return_value
            patched_get_guild.assert_called_once_with(342123123)

    def test_author_property(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        assert guild_message_create_event.author is guild_message_create_event.message.author

    def test_member_property(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        assert guild_message_create_event.member is guild_message_create_event.message.member

    def test_get_member_when_cacheless(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        with mock.patch.object(guild_message_create_event.message, "app", None):
            assert guild_message_create_event.get_member() is None

    def test_get_member(self, guild_message_create_event: message_events.GuildMessageCreateEvent):
        with (
            mock.patch.object(
                message_events.GuildMessageCreateEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_member") as patched_get_member,
        ):
            result = guild_message_create_event.get_member()

            assert result is patched_get_member.return_value
            patched_get_member.assert_called_once_with(
                guild_message_create_event.guild_id, guild_message_create_event.author_id
            )


class TestGuildMessageUpdateEvent:
    @pytest.fixture
    def guild_message_update_event(self) -> message_events.GuildMessageUpdateEvent:
        return message_events.GuildMessageUpdateEvent(
            message=mock.Mock(
                spec_set=messages.Message,
                guild_id=snowflakes.Snowflake(54123123123),
                channel_id=snowflakes.Snowflake(800001066),
            ),
            old_message=mock.Mock(messages.Message, id=123),
            shard=mock.Mock(),
        )

    def test_author_property(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        assert guild_message_update_event.author is guild_message_update_event.message.author

    def test_member_property(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        assert guild_message_update_event.member is guild_message_update_event.message.member

    def test_guild_id_property(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        assert guild_message_update_event.guild_id == snowflakes.Snowflake(54123123123)

    def test_get_channel_when_no_cache_trait(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        with mock.patch.object(message_events.GuildMessageUpdateEvent, "app", None):
            assert guild_message_update_event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_get_channel(
        self,
        guild_message_update_event: message_events.GuildMessageUpdateEvent,
        guild_channel_impl: typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel],
    ):
        with (
            mock.patch.object(
                message_events.GuildMessageUpdateEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
            ) as patched_get_guild_channel,
        ):
            result = guild_message_update_event.get_channel()
            assert result is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(800001066)

    def test_get_member_when_cacheless(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        with mock.patch.object(guild_message_update_event.message, "app", None):
            assert guild_message_update_event.get_member() is None

    def test_get_member(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        with (
            mock.patch.object(
                message_events.GuildMessageUpdateEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_member") as patched_get_member,
        ):
            result = guild_message_update_event.get_member()

            assert result is patched_get_member.return_value
            patched_get_member.assert_called_once_with(
                guild_message_update_event.guild_id, guild_message_update_event.author_id
            )

    def test_get_guild_when_no_cache_trait(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        with mock.patch.object(message_events.GuildMessageUpdateEvent, "app", None):
            assert guild_message_update_event.get_guild() is None

    def test_get_guild(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        with (
            mock.patch.object(
                message_events.GuildMessageUpdateEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild") as patched_get_guild,
        ):
            result = guild_message_update_event.get_guild()

            assert result is patched_get_guild.return_value
            patched_get_guild.assert_called_once_with(54123123123)

    def test_old_message(self, guild_message_update_event: message_events.GuildMessageUpdateEvent):
        assert guild_message_update_event.old_message is not None
        assert guild_message_update_event.old_message.id == 123


class TestDMMessageUpdateEvent:
    @pytest.fixture
    def dm_message_update_event(self) -> message_events.DMMessageUpdateEvent:
        return message_events.DMMessageUpdateEvent(
            message=mock.Mock(
                spec_set=messages.Message, author=mock.Mock(spec_set=users.User, id=snowflakes.Snowflake(8000010662))
            ),
            old_message=mock.Mock(messages.Message, id=123),
            shard=mock.Mock(),
        )

    def test_old_message(self, dm_message_update_event: message_events.DMMessageUpdateEvent):
        assert dm_message_update_event.old_message is not None
        assert dm_message_update_event.old_message.id == 123


class TestGuildMessageDeleteEvent:
    @pytest.fixture
    def guild_message_delete_event(self) -> message_events.GuildMessageDeleteEvent:
        return message_events.GuildMessageDeleteEvent(
            guild_id=snowflakes.Snowflake(542342354564),
            channel_id=snowflakes.Snowflake(54213123123),
            app=mock.Mock(),
            shard=mock.Mock(),
            message_id=snowflakes.Snowflake(9),
            old_message=mock.Mock(),
        )

    def test_get_channel_when_no_cache_trait(self, guild_message_delete_event: message_events.GuildMessageDeleteEvent):
        guild_message_delete_event.app = mock.Mock(traits.RESTAware)

        assert guild_message_delete_event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_get_channel(
        self,
        guild_message_delete_event: message_events.GuildMessageDeleteEvent,
        guild_channel_impl: typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel],
    ):
        with (
            mock.patch.object(
                message_events.GuildMessageDeleteEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
            ) as patched_get_guild_channel,
        ):
            result = guild_message_delete_event.get_channel()

            assert result is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(54213123123)

    def test_get_guild_when_no_cache_trait(self, guild_message_delete_event: message_events.GuildMessageDeleteEvent):
        guild_message_delete_event.app = mock.Mock(traits.RESTAware)

        assert guild_message_delete_event.get_guild() is None

    def test_get_guild_property(self, guild_message_delete_event: message_events.GuildMessageDeleteEvent):
        with (
            mock.patch.object(
                message_events.GuildMessageDeleteEvent, "app", mock.Mock(traits.CacheAware)
            ) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild") as patched_get_guild,
        ):
            result = guild_message_delete_event.get_guild()

            assert result is patched_get_guild.return_value
            patched_get_guild.assert_called_once_with(542342354564)

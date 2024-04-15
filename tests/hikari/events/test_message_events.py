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
from hikari import messages
from hikari import snowflakes
from hikari import undefined
from hikari import users
from hikari.events import message_events
from tests.hikari import hikari_test_helpers


class TestMessageCreateEvent:
    @pytest.fixture
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            message_events.MessageCreateEvent,
            message=mock.Mock(spec_set=messages.Message, author=mock.Mock(spec_set=users.User)),
            shard=mock.Mock(),
        )

        return cls()

    def test_app_property(self, event):
        assert event.app is event.message.app

    def test_author_property(self, event):
        assert event.author is event.message.author

    def test_author_id_property(self, event):
        assert event.author_id is event.author.id

    def test_channel_id_property(self, event):
        assert event.channel_id is event.message.channel_id

    def test_content_property(self, event):
        assert event.content is event.message.content

    def test_embeds_property(self, event):
        assert event.embeds is event.message.embeds

    @pytest.mark.parametrize("is_bot", [True, False])
    def test_is_bot_property(self, event, is_bot):
        event.message.author.is_bot = is_bot
        assert event.is_bot is is_bot

    @pytest.mark.parametrize(
        ("author_is_bot", "webhook_id", "expected_is_human"),
        [(True, 123, False), (True, None, False), (False, 123, False), (False, None, True)],
    )
    def test_is_human_property(self, event, author_is_bot, webhook_id, expected_is_human):
        event.message.author.is_bot = author_is_bot
        event.message.webhook_id = webhook_id
        assert event.is_human is expected_is_human

    @pytest.mark.parametrize(("webhook_id", "is_webhook"), [(123, True), (None, False)])
    def test_is_webhook_property(self, event, webhook_id, is_webhook):
        event.message.webhook_id = webhook_id
        assert event.is_webhook is is_webhook

    def test_message_id_property(self, event):
        assert event.message_id is event.message.id


class TestMessageUpdateEvent:
    @pytest.fixture
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            message_events.MessageUpdateEvent,
            message=mock.Mock(spec_set=messages.Message, author=mock.Mock(spec_set=users.User)),
            shard=mock.Mock(),
        )

        return cls()

    def test_app_property(self, event):
        assert event.app is event.message.app

    @pytest.mark.parametrize("author", [mock.Mock(spec_set=users.User), undefined.UNDEFINED])
    def test_author_property(self, event, author):
        event.message.author = author
        assert event.author is author

    @pytest.mark.parametrize(
        ("author", "expected_id"),
        [(mock.Mock(spec_set=users.User, id=91827), 91827), (undefined.UNDEFINED, undefined.UNDEFINED)],
    )
    def test_author_id_property(self, event, author, expected_id):
        event.message.author = author
        assert event.author_id == expected_id

    def test_channel_id_property(self, event):
        assert event.channel_id is event.message.channel_id

    def test_content_property(self, event):
        assert event.content is event.message.content

    def test_embeds_property(self, event):
        assert event.embeds is event.message.embeds

    @pytest.mark.parametrize("is_bot", [True, False])
    def test_is_bot_property(self, event, is_bot):
        event.message.author.is_bot = is_bot
        assert event.is_bot is is_bot

    def test_is_bot_property_if_no_author(self, event):
        event.message.author = undefined.UNDEFINED
        assert event.is_bot is undefined.UNDEFINED

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
    def test_is_human_property(self, event, author, webhook_id, expected_is_human):
        event.message.author = author
        event.message.webhook_id = webhook_id
        assert event.is_human is expected_is_human

    @pytest.mark.parametrize(
        ("webhook_id", "is_webhook"), [(123, True), (None, False), (undefined.UNDEFINED, undefined.UNDEFINED)]
    )
    def test_is_webhook_property(self, event, webhook_id, is_webhook):
        event.message.webhook_id = webhook_id
        assert event.is_webhook is is_webhook

    def test_message_id_property(self, event):
        assert event.message_id is event.message.id


class TestGuildMessageCreateEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageCreateEvent(
            message=mock.Mock(
                spec_set=messages.Message,
                guild_id=snowflakes.Snowflake(342123123),
                channel_id=snowflakes.Snowflake(9121234),
            ),
            shard=mock.Mock(),
        )

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(342123123)

    def test_get_channel_when_no_cache_trait(self):
        event = hikari_test_helpers.mock_class_namespace(
            message_events.GuildMessageCreateEvent, app=None, init_=False
        )()

        assert event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_get_channel(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))

        result = event.get_channel()
        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(9121234)

    def test_get_guild_when_no_cache_trait(self):
        event = hikari_test_helpers.mock_class_namespace(
            message_events.GuildMessageCreateEvent, app=None, init_=False
        )()

        assert event.get_guild() is None

    def test_get_guild(self, event):
        result = event.get_guild()

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(342123123)

    def test_author_property(self, event):
        assert event.author is event.message.author

    def test_member_property(self, event):
        assert event.member is event.message.member

    def test_get_member_when_cacheless(self, event):
        event.message.app = None

        result = event.get_member()

        assert result is None

    def test_get_member(self, event):
        result = event.get_member()

        assert result is event.app.cache.get_member.return_value
        event.app.cache.get_member.assert_called_once_with(event.guild_id, event.author_id)


class TestGuildMessageUpdateEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageUpdateEvent(
            message=mock.Mock(
                spec_set=messages.Message,
                guild_id=snowflakes.Snowflake(54123123123),
                channel_id=snowflakes.Snowflake(800001066),
            ),
            old_message=mock.Mock(messages.Message, id=123),
            shard=mock.Mock(),
        )

    def test_author_property(self, event):
        assert event.author is event.message.author

    def test_member_property(self, event):
        assert event.member is event.message.member

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(54123123123)

    def test_get_channel_when_no_cache_trait(self):
        event = hikari_test_helpers.mock_class_namespace(
            message_events.GuildMessageUpdateEvent, app=None, init_=False
        )()

        assert event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_get_channel(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))

        result = event.get_channel()
        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(800001066)

    def test_get_member_when_cacheless(self, event):
        event.message.app = None

        result = event.get_member()

        assert result is None

    def test_get_member(self, event):
        result = event.get_member()

        assert result is event.app.cache.get_member.return_value
        event.app.cache.get_member.assert_called_once_with(event.guild_id, event.author_id)

    def test_get_guild_when_no_cache_trait(self):
        event = hikari_test_helpers.mock_class_namespace(
            message_events.GuildMessageUpdateEvent, app=None, init_=False
        )()

        assert event.get_guild() is None

    def test_get_guild(self, event):
        result = event.get_guild()

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(54123123123)

    def test_old_message(self, event):
        assert event.old_message.id == 123


class TestDMMessageUpdateEvent:
    @pytest.fixture
    def event(self):
        return message_events.DMMessageUpdateEvent(
            message=mock.Mock(
                spec_set=messages.Message, author=mock.Mock(spec_set=users.User, id=snowflakes.Snowflake(8000010662))
            ),
            old_message=mock.Mock(messages.Message, id=123),
            shard=mock.Mock(),
        )

    def test_old_message(self, event):
        assert event.old_message.id == 123


class TestGuildMessageDeleteEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageDeleteEvent(
            guild_id=snowflakes.Snowflake(542342354564),
            channel_id=snowflakes.Snowflake(54213123123),
            app=mock.Mock(),
            shard=object(),
            message_id=9,
            old_message=object(),
        )

    def test_get_channel_when_no_cache_trait(self, event):
        event.app = object()

        assert event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_get_channel(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
        result = event.get_channel()

        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(54213123123)

    def test_get_guild_when_no_cache_trait(self, event):
        event.app = object()

        assert event.get_guild() is None

    def test_get_guild_property(self, event):
        result = event.get_guild()

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(542342354564)

# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
from hikari import guilds
from hikari import messages
from hikari import snowflakes
from hikari import undefined
from hikari import users
from hikari.events import message_events
from tests.hikari import hikari_test_helpers


class TestMessageCreateEvent:
    @pytest.fixture()
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            message_events.MessageCreateEvent,
            app=object(),
            message=mock.Mock(
                spec_set=messages.Message,
                author=mock.Mock(
                    spec_set=users.User,
                ),
            ),
            shard=mock.Mock(),
        )

        return cls()

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
        [
            (True, 123, False),
            (True, None, False),
            (False, 123, False),
            (False, None, True),
        ],
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
    @pytest.fixture()
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            message_events.MessageUpdateEvent,
            app=object(),
            message=mock.Mock(
                spec_set=messages.Message,
                author=mock.Mock(
                    spec_set=users.User,
                ),
            ),
            shard=mock.Mock(),
        )

        return cls()

    @pytest.mark.parametrize("author", [mock.Mock(spec_set=users.User), undefined.UNDEFINED])
    def test_author_property(self, event, author):
        event.message.author = author
        assert event.author is author

    @pytest.mark.parametrize(
        ("author", "expected_id"),
        [(mock.Mock(spec_set=users.User, id=91827), 91827), (None, None)],
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
        event.message.author = None
        assert event.is_bot is None

    @pytest.mark.parametrize(
        ("author", "webhook_id", "expected_is_human"),
        [
            (mock.Mock(spec_set=users.User, is_bot=True), 123, False),
            (mock.Mock(spec_set=users.User, is_bot=True), None, False),
            (mock.Mock(spec_set=users.User, is_bot=False), 123, False),
            (mock.Mock(spec_set=users.User, is_bot=False), None, True),
            (None, 123, False),
            (None, None, None),
        ],
    )
    def test_is_human_property(self, event, author, webhook_id, expected_is_human):
        event.message.author = author
        event.message.webhook_id = webhook_id
        assert event.is_human is expected_is_human

    @pytest.mark.parametrize(("webhook_id", "is_webhook"), [(123, True), (None, False)])
    def test_is_webhook_property(self, event, webhook_id, is_webhook):
        event.message.webhook_id = webhook_id
        assert event.is_webhook is is_webhook

    def test_message_id_property(self, event):
        assert event.message_id is event.message.id


class TestGuildMessageCreateEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageCreateEvent(
            app=mock.Mock(),
            message=mock.Mock(
                spec_set=messages.Message,
                guild_id=snowflakes.Snowflake(342123123),
                channel_id=snowflakes.Snowflake(9121234),
            ),
            shard=mock.Mock(),
        )

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(342123123)

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_channel_property(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))

        result = event.channel
        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(9121234)

    def test_guild_property(self, event):
        result = event.guild

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(342123123)

    def test_author_property(self, event):
        assert event.author is event.message.member


class TestGuildMessageUpdateEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageUpdateEvent(
            app=mock.Mock(),
            message=mock.Mock(
                spec_set=messages.Message,
                guild_id=snowflakes.Snowflake(54123123123),
                channel_id=snowflakes.Snowflake(800001066),
            ),
            shard=mock.Mock(),
        )

    def test_author_property_when_member_defined(self, event):
        event.message.member = mock.Mock(spec_set=guilds.Member)
        event.message.author = undefined.UNDEFINED

        assert event.author is event.message.member

    def test_author_property_when_member_none_but_cached(self, event):
        event.message.member = None
        event.message.author = mock.Mock(spec_set=users.User, id=1234321)
        event.message.guild_id = snowflakes.Snowflake(696969)
        real_member = mock.Mock(spec_set=guilds.Member)
        event.app.cache.get_member = mock.Mock(return_value=real_member)

        assert event.author is real_member

        event.app.cache.get_member.assert_called_once_with(696969, 1234321)

    def test_author_property_when_member_none_but_author_also_none(self, event):
        event.message.author = None
        event.message.member = None

        assert event.author is None

        event.app.cache.get_member.assert_not_called()

    def test_author_property_when_member_none_and_uncached_but_author_defined(self, event):
        event.message.member = None
        event.app.cache.get_member = mock.Mock(return_value=None)
        event.message.author = mock.Mock(spec_set=users.User)

        assert event.author is event.message.author

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(54123123123)

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_channel_property(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))

        result = event.channel
        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(800001066)

    def test_guild_property(self, event):
        result = event.guild

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(54123123123)


class TestDMMessageUpdateEvent:
    @pytest.fixture()
    def event(self):
        return message_events.DMMessageUpdateEvent(
            app=mock.Mock(),
            message=mock.Mock(
                spec_set=messages.Message, author=mock.Mock(spec_set=users.User, id=snowflakes.Snowflake(8000010662))
            ),
            shard=mock.Mock(),
        )


class TestMessageDeleteEvent:
    def test_message_id_property(self):
        event = hikari_test_helpers.mock_class_namespace(message_events.MessageDeleteEvent, message_ids=[9, 18, 27])()
        assert event.message_id == 9

    def test_message_id_property_if_empty_errors(self):
        event = hikari_test_helpers.mock_class_namespace(message_events.MessageDeleteEvent, message_ids=[])()
        with pytest.raises(RuntimeError):
            _ = event.message_id


class TestGuildMessageDeleteEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageDeleteEvent(
            guild_id=snowflakes.Snowflake(542342354564),
            channel_id=snowflakes.Snowflake(54213123123),
            app=mock.Mock(),
            shard=mock.Mock(),
            message_ids={9, 18, 27, 36},
            is_bulk=True,
        )

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_channel_property(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
        result = event.channel

        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(54213123123)

    def test_guild_property(self, event):
        result = event.guild

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(542342354564)

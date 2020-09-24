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
from hikari import messages
from hikari import snowflakes
from hikari import users
from hikari.events import message_events
from tests.hikari import hikari_test_helpers


class TestGuildMessageEvent:
    @pytest.fixture()
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            message_events.GuildMessageEvent,
            guild_id=mock.PropertyMock(return_value=snowflakes.Snowflake(342123123)),
            channel_id=mock.PropertyMock(return_value=snowflakes.Snowflake(54123123123)),
        )
        return cls()

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_channel(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))

        result = event.channel
        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(54123123123)

    def test_guild_when_available(self, event):
        result = event.guild

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(342123123)

    def test_guild_when_unavailable(self, event):
        event.app.cache.get_available_guild.return_value = None
        result = event.guild

        assert result is event.app.cache.get_guild.return_value
        event.app.cache.get_guild.assert_called_once_with(342123123)


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
            shard=object(),
            channel=object(),
            author=object(),
        )

        return cls()

    def test_message_id_property(self, event):
        event.message.id = 123
        assert event.message_id == 123

    def test_channel_id_property(self, event):
        event.message.channel_id = 123
        assert event.channel_id == 123

    def test_author_id_property(self, event):
        event.message.author.id = 123
        assert event.author_id == 123


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
            shard=object(),
            channel=object(),
            author=object(),
        )

        return cls()

    def test_message_id_property(self, event):
        event.message.id = snowflakes.Snowflake(123)
        assert event.message_id == snowflakes.Snowflake(123)

    def test_channel_id_property(self, event):
        event.message.channel_id = snowflakes.Snowflake(456)
        assert event.channel_id == snowflakes.Snowflake(456)

    def test_author_id_property(self, event):
        event.message.author.id = snowflakes.Snowflake(911)
        assert event.author_id == snowflakes.Snowflake(911)


class TestMessageDeleteEvent:
    @pytest.fixture()
    def event(self):
        class MessageDeleteEvent(message_events.MessageDeleteEvent):
            app = None
            message = mock.Mock(messages.Message)
            shard = object()
            channel = object()

        return MessageDeleteEvent()

    def test_message_id_property(self, event):
        event.message.id = 123
        assert event.message_id == 123

    def test_channel_id_property(self, event):
        event.message.channel_id = 123
        assert event.channel_id == 123


class TestGuildMessageCreateEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageCreateEvent(
            app=None,
            message=mock.Mock(spec_set=messages.Message, guild_id=snowflakes.Snowflake(998866)),
            shard=object(),
        )

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(998866)


class TestGuildMessageUpdateEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageUpdateEvent(
            app=None,
            message=mock.Mock(spec_set=messages.Message, guild_id=snowflakes.Snowflake(9182736)),
            shard=object(),
        )

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(9182736)


class TestGuildMessageDeleteEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageDeleteEvent(
            app=None,
            message=mock.Mock(spec_set=messages.Message, guild_id=snowflakes.Snowflake(9182736)),
            shard=object(),
        )

    def test_guild_id_property(self, event):
        assert event.guild_id == snowflakes.Snowflake(9182736)


class TestGuildMessageBulkDeleteEvent:
    @pytest.fixture()
    def event(self):
        return message_events.GuildMessageBulkDeleteEvent(
            guild_id=snowflakes.Snowflake(542342354564),
            channel_id=snowflakes.Snowflake(54213123123),
            app=mock.Mock(),
            shard=None,
            message_ids=None,
        )

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildTextChannel, channels.GuildNewsChannel])
    def test_channel(self, event, guild_channel_impl):
        event.app.cache.get_guild_channel = mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
        result = event.channel

        assert result is event.app.cache.get_guild_channel.return_value
        event.app.cache.get_guild_channel.assert_called_once_with(54213123123)

    def test_guild_when_available(self, event):
        result = event.guild

        assert result is event.app.cache.get_available_guild.return_value
        event.app.cache.get_available_guild.assert_called_once_with(542342354564)
        event.app.cache.get_unavailable_guild.assert_not_called()

    def test_guild_when_unavailable(self, event):
        event.app.cache.get_available_guild.return_value = None
        result = event.guild

        assert result is event.app.cache.get_unavailable_guild.return_value
        event.app.cache.get_unavailable_guild.assert_called_once_with(542342354564)
        event.app.cache.get_available_guild.assert_called_once_with(542342354564)

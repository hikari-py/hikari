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

from hikari import messages
from hikari.events import message_events


class TestMessageCreateEvent:
    @pytest.fixture
    def event(self):
        class MessageCreateEvent(message_events.MessageCreateEvent):
            app = None
            message = mock.Mock(messages.Message)
            shard = object()
            channel = object()

        return MessageCreateEvent()

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
    @pytest.fixture
    def event(self):
        class MessageUpdateEvent(message_events.MessageUpdateEvent):
            app = None
            message = mock.Mock(messages.Message)
            shard = object()
            channel = object()

        return MessageUpdateEvent()

    def test_message_id_property(self, event):
        event.message.id = 123
        assert event.message_id == 123

    def test_channel_id_property(self, event):
        event.message.channel_id = 123
        assert event.channel_id == 123

    def test_author_id_property(self, event):
        event.message.author.id = 123
        assert event.author_id == 123


class TestMessageDeleteEvent:
    @pytest.fixture
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
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageCreateEvent(app=None, message=mock.Mock(messages.Message), shard=object())

    def test_guild_id_property(self, event):
        event.message.guild_id = 123
        assert event.guild_id == 123


class TestGuildMessageUpdateEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageUpdateEvent(app=None, message=mock.Mock(messages.Message), shard=object())

    def test_guild_id_property(self, event):
        event.message.guild_id = 123
        assert event.guild_id == 123


class TestGuildMessageDeleteEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageDeleteEvent(app=None, message=mock.Mock(messages.Message), shard=object())

    def test_guild_id_property(self, event):
        event.message.guild_id = 123
        assert event.guild_id == 123

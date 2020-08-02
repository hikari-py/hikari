# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.

import mock
import pytest

from hikari.events import message_events
from hikari.models import messages


class TestMessageCreateEvent:
    @pytest.fixture
    def event(self):
        class MessageCreateEvent(message_events.MessageCreateEvent):
            message = mock.Mock(messages.Message)
            shard = object()

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
            message = mock.Mock(messages.Message)
            shard = object()

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
            message = mock.Mock(messages.Message)
            shard = object()

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
        return message_events.GuildMessageCreateEvent(message=mock.Mock(messages.Message), shard=object())

    def test_guild_id_property(self, event):
        event.message.guild_id = 123
        assert event.guild_id == 123


class TestGuildMessageUpdateEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageUpdateEvent(message=mock.Mock(messages.Message), shard=object())

    def test_guild_id_property(self, event):
        event.message.guild_id = 123
        assert event.guild_id == 123


class TestGuildMessageDeleteEvent:
    @pytest.fixture
    def event(self):
        return message_events.GuildMessageDeleteEvent(message=mock.Mock(messages.Message), shard=object())

    def test_guild_id_property(self, event):
        event.message.guild_id = 123
        assert event.guild_id == 123

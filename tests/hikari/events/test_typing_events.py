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
from hikari import users
from hikari.events import typing_events


@pytest.mark.asyncio
class TestTypingEvent:
    @pytest.fixture
    def event(self):
        class StubEvent(typing_events.TypingEvent):
            channel_id = 123
            user_id = 456
            timestamp = None
            shard = None
            app = mock.Mock(rest=mock.AsyncMock())
            channel = object()
            guild = object()

        return StubEvent()

    async def test_fetch_channel(self, event):
        mock_channel = mock.Mock(spec_set=channels.TextChannel)
        event.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)
        assert await event.fetch_channel() is mock_channel

        event.app.rest.fetch_channel.assert_awaited_once_with(123)

    async def test_fetch_user(self, event):
        mock_user = mock.Mock(spec_set=users.User)
        event.app.rest.fetch_user = mock.AsyncMock(return_value=mock_user)

        assert await event.fetch_user() is mock_user

        event.app.rest.fetch_user.assert_awaited_once_with(456)


@pytest.mark.asyncio
class TestGuildTypingEvent:
    @pytest.fixture
    def event(self):
        return typing_events.GuildTypingEvent(
            app=mock.AsyncMock(), shard=None, channel_id=123, user_id=456, guild_id=789, timestamp=None, member=None,
        )

    async def test_fetch_channel(self, event):
        await event.fetch_member()

        event.app.rest.fetch_member.assert_awaited_once_with(789, 456)

    async def test_fetch_guild(self, event):
        await event.fetch_guild()

        event.app.rest.fetch_guild.assert_awaited_once_with(789)

    async def test_fetch_guild_preview(self, event):
        await event.fetch_guild_preview()

        event.app.rest.fetch_guild_preview.assert_awaited_once_with(789)

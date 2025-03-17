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
import typing

import mock
import pytest

from hikari import channels
from hikari import snowflakes
from hikari import traits
from hikari.api import shard as shard_api
from hikari.events import typing_events


@pytest.fixture
def mock_app() -> traits.RESTAware:
    return mock.Mock(traits.RESTAware)


class TestTypingEvent:
    class MockTypingEvent(typing_events.TypingEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._channel_id = snowflakes.Snowflake(123)
            self._user_id = snowflakes.Snowflake(456)
            self._timestamp = datetime.datetime.fromtimestamp(4000)

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def channel_id(self) -> snowflakes.Snowflake:
            return self._channel_id

        @property
        def user_id(self) -> snowflakes.Snowflake:
            return self._user_id

        @property
        def timestamp(self) -> datetime.datetime:
            return self._timestamp

    @pytest.fixture
    def typing_event(self, mock_app: traits.RESTAware) -> typing_events.TypingEvent:
        return TestTypingEvent.MockTypingEvent(mock_app)

    def test_get_user_when_no_cache(self, typing_event: typing_events.TypingEvent):
        with mock.patch.object(typing_event, "_app", None):
            assert typing_event.get_user() is None

    def test_get_user(self, typing_event: typing_events.TypingEvent):
        with (
            mock.patch.object(typing_event, "_app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_user") as patched_get_user,
        ):
            assert typing_event.get_user() is patched_get_user.return_value

    def test_trigger_typing(self, typing_event: typing_events.TypingEvent):
        typing_event.app.rest.trigger_typing = mock.Mock()
        result = typing_event.trigger_typing()
        typing_event.app.rest.trigger_typing.assert_called_once_with(123)
        assert result is typing_event.app.rest.trigger_typing.return_value


class TestGuildTypingEvent:
    @pytest.fixture
    def guild_typing_event(self) -> typing_events.GuildTypingEvent:
        return typing_events.GuildTypingEvent(
            channel_id=snowflakes.Snowflake(123),
            timestamp=mock.Mock(),
            shard=mock.Mock(),
            guild_id=snowflakes.Snowflake(789),
            member=mock.Mock(id=456, app=mock.Mock(rest=mock.AsyncMock())),
        )

    def test_app_property(self, guild_typing_event: typing_events.GuildTypingEvent):
        assert guild_typing_event.app is guild_typing_event.member.app

    def test_get_channel_when_no_cache(self, guild_typing_event: typing_events.GuildTypingEvent):
        with mock.patch.object(typing_events.GuildTypingEvent, "app", None):
            assert guild_typing_event.get_channel() is None

    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildNewsChannel, channels.GuildTextChannel])
    def test_get_channel(
        self,
        guild_typing_event: typing_events.GuildTypingEvent,
        guild_channel_impl: typing.Union[channels.GuildNewsChannel, channels.GuildTextChannel],
    ):
        with (
            mock.patch.object(typing_events.GuildTypingEvent, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", mock.Mock(return_value=mock.Mock(spec_set=guild_channel_impl))
            ) as patched_get_guild_channel,
        ):
            result = guild_typing_event.get_channel()

            assert result is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_guild_when_no_cache(self, guild_typing_event: typing_events.GuildTypingEvent):
        with mock.patch.object(typing_events.GuildTypingEvent, "app", None):
            assert guild_typing_event.get_guild() is None

    def test_get_guild_when_available(self, guild_typing_event: typing_events.GuildTypingEvent):
        with (
            mock.patch.object(typing_events.GuildTypingEvent, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild") as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = guild_typing_event.get_guild()

            assert result is patched_get_available_guild.return_value
            patched_get_available_guild.assert_called_once_with(789)
            patched_get_unavailable_guild.assert_not_called()

    def test_get_guild_when_unavailable(self, guild_typing_event: typing_events.GuildTypingEvent):
        with (
            mock.patch.object(typing_events.GuildTypingEvent, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_available_guild", return_value=None) as patched_get_available_guild,
            mock.patch.object(patched_cache, "get_unavailable_guild") as patched_get_unavailable_guild,
        ):
            result = guild_typing_event.get_guild()

            assert result is patched_get_unavailable_guild.return_value
            patched_get_unavailable_guild.assert_called_once_with(789)
            patched_get_available_guild.assert_called_once_with(789)

    def test_user_id(self, guild_typing_event: typing_events.GuildTypingEvent):
        assert guild_typing_event.user_id == guild_typing_event.member.id
        assert guild_typing_event.user_id == 456

    @pytest.mark.asyncio
    @pytest.mark.parametrize("guild_channel_impl", [channels.GuildNewsChannel, channels.GuildTextChannel])
    async def test_fetch_channel(
        self,
        guild_typing_event: typing_events.GuildTypingEvent,
        guild_channel_impl: typing.Union[channels.GuildNewsChannel, channels.GuildTextChannel],
    ):
        guild_typing_event.app.rest.fetch_channel = mock.AsyncMock(return_value=mock.Mock(spec_set=guild_channel_impl))
        await guild_typing_event.fetch_channel()

        guild_typing_event.app.rest.fetch_channel.assert_awaited_once_with(123)

    @pytest.mark.asyncio
    async def test_fetch_guild(self, guild_typing_event: typing_events.GuildTypingEvent):
        with mock.patch.object(guild_typing_event.app.rest, "fetch_guild") as patched_fetch_guild:
            await guild_typing_event.fetch_guild()

            patched_fetch_guild.assert_awaited_once_with(789)

    @pytest.mark.asyncio
    async def test_fetch_guild_preview(self, guild_typing_event: typing_events.GuildTypingEvent):
        with mock.patch.object(guild_typing_event.app.rest, "fetch_guild_preview") as patched_fetch_guild_preview:
            await guild_typing_event.fetch_guild_preview()

            patched_fetch_guild_preview.assert_awaited_once_with(789)

    @pytest.mark.asyncio
    async def test_fetch_member(self, guild_typing_event: typing_events.GuildTypingEvent):
        with mock.patch.object(guild_typing_event.app.rest, "fetch_member") as patched_fetch_member:
            await guild_typing_event.fetch_member()

            patched_fetch_member.assert_awaited_once_with(789, 456)


@pytest.mark.asyncio
class TestDMTypingEvent:
    @pytest.fixture
    def dm_typing_event(self) -> typing_events.DMTypingEvent:
        return typing_events.DMTypingEvent(
            channel_id=snowflakes.Snowflake(123),
            timestamp=mock.Mock(),
            shard=mock.Mock(),
            app=mock.Mock(rest=mock.AsyncMock()),
            user_id=snowflakes.Snowflake(456),
        )

    async def test_fetch_channel(self, dm_typing_event: typing_events.DMTypingEvent):
        dm_typing_event.app.rest.fetch_channel = mock.AsyncMock(return_value=mock.Mock(spec_set=channels.DMChannel))
        await dm_typing_event.fetch_channel()

        dm_typing_event.app.rest.fetch_channel.assert_awaited_once_with(123)

    async def test_fetch_user(self, dm_typing_event: typing_events.DMTypingEvent):
        with mock.patch.object(dm_typing_event.app.rest, "fetch_user") as patched_fetch_user:
            await dm_typing_event.fetch_user()

            patched_fetch_user.assert_awaited_once_with(456)

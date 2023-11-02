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
from hikari import snowflakes
from hikari import stage_instances


@pytest.fixture()
def mock_app():
    return mock.Mock()


class TestStageInstance:
    @pytest.fixture()
    def stage_instance(self, mock_app):
        return stage_instances.StageInstance(
            app=mock_app,
            id=snowflakes.Snowflake(123),
            channel_id=snowflakes.Snowflake(6969),
            guild_id=snowflakes.Snowflake(420),
            topic="beanos",
            discoverable_disabled=True,
            guild_scheduled_event_id=snowflakes.Snowflake(1337),
        )

    def test_id_property(self, stage_instance):
        assert stage_instance.id == 123

    def test_app_property(self, stage_instance, mock_app):
        assert stage_instance.app is mock_app

    def test_channel_id_property(self, stage_instance):
        assert stage_instance.channel_id == 6969

    def test_guild_id_property(self, stage_instance):
        assert stage_instance.guild_id == 420

    def test_topic_property(self, stage_instance):
        assert stage_instance.topic == "beanos"

    def test_discoverable_disabled_property(self, stage_instance):
        assert stage_instance.discoverable_disabled is True

    def test_guild_scheduled_event_id_property(self, stage_instance):
        assert stage_instance.guild_scheduled_event_id == 1337

    def test_get_channel(self, stage_instance):
        mock_stage_channel = mock.Mock(channels.GuildStageChannel, channel_id=snowflakes.Snowflake(6969))
        stage_instance.app.cache.get_guild_channel = mock.Mock(return_value=mock_stage_channel)

        assert stage_instance.get_channel() == mock_stage_channel
        stage_instance.app.cache.get_guild_channel.assert_called_once_with(6969)

    def test_get_channel_when_no_cache_trait(self, stage_instance):
        stage_instance.app = object()

        assert stage_instance.get_channel() is None

    @pytest.mark.asyncio()
    async def test_fetch_channel(self, stage_instance):
        mock_stage_channel = mock.Mock(channels.GuildStageChannel)
        stage_instance.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_stage_channel)

        assert await stage_instance.fetch_channel() == mock_stage_channel
        stage_instance.app.rest.fetch_channel.assert_awaited_once_with(6969)

    def test_get_guild(self, stage_instance):
        mock_guild = mock.Mock(channels.GuildStageChannel, guild_id=420)
        stage_instance.app.cache.get_guild = mock.Mock(return_value=mock_guild)

        assert stage_instance.get_guild() == mock_guild
        stage_instance.app.cache.get_guild.assert_called_once_with(420)

    def test_get_guild_when_no_cache_trait(self, stage_instance):
        stage_instance.app = object()

        assert stage_instance.get_guild() is None

    @pytest.mark.asyncio()
    async def test_fetch_guild(self, stage_instance):
        stage_instance.app.rest.fetch_guild = mock.AsyncMock()

        assert await stage_instance.fetch_guild() == stage_instance.app.rest.fetch_guild.return_value
        stage_instance.app.rest.fetch_guild.assert_awaited_once_with(420)

    @pytest.mark.asyncio()
    async def test_fetch_scheduled_event(self, stage_instance):
        stage_instance.app.rest.fetch_scheduled_event = mock.AsyncMock()

        f_s_e = await stage_instance.fetch_scheduled_event()

        assert f_s_e == stage_instance.app.rest.fetch_scheduled_event.return_value
        stage_instance.app.rest.fetch_scheduled_event.assert_awaited_once_with(420, 1337)

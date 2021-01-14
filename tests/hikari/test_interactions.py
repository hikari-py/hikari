# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
from hikari import interactions
from hikari import snowflakes
from hikari import traits
from hikari.internal import protocol


class _CacheAndRESTAwareProto(traits.RESTAware, traits.CacheAware, protocol.Protocol):
    ...


@pytest.fixture()
def mock_app():
    return mock.Mock(spec_set=_CacheAndRESTAwareProto, rest=mock.AsyncMock())


class TestCommandInteraction:
    @pytest.fixture()
    def mock_command_interaction(self, mock_app):
        return interactions.CommandInteraction(
            app=mock_app,
            id=snowflakes.Snowflake(2312312),
            type=interactions.InteractionType.APPLICATION_COMMAND,
            data=object(),
            channel_id=snowflakes.Snowflake(3123123),
            guild_id=snowflakes.Snowflake(5412231),
            member=object(),
            token="httptptptptptptptp",
            version=1,
            application_id=snowflakes.Snowflake(43123),
        )

    @pytest.mark.asyncio
    async def test_fetch_channel(self, mock_command_interaction, mock_app):
        mock_app.rest.fetch_channel.return_value = mock.Mock(channels.GuildChannel)
        assert await mock_command_interaction.fetch_channel() is mock_app.rest.fetch_channel.return_value

        mock_app.rest.fetch_channel.assert_awaited_once_with(3123123)

    def test_get_channel(self, mock_command_interaction, mock_app):
        assert mock_command_interaction.get_channel() is mock_app.cache.get_guild_channel.return_value
        mock_app.cache.get_guild_channel.assert_called_once_with(3123123)

    def test_get_channel_without_cache(self, mock_command_interaction):
        mock_command_interaction.app = mock.Mock(spec_set=traits.RESTAware)

        assert mock_command_interaction.get_channel() is None

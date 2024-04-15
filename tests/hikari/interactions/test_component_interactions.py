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
from hikari import monetization
from hikari import snowflakes
from hikari import traits
from hikari.interactions import base_interactions
from hikari.interactions import component_interactions


@pytest.fixture
def mock_app():
    return mock.Mock(rest=mock.AsyncMock())


class TestComponentInteraction:
    @pytest.fixture
    def mock_component_interaction(self, mock_app):
        return component_interactions.ComponentInteraction(
            app=mock_app,
            id=snowflakes.Snowflake(2312312),
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            channel_id=snowflakes.Snowflake(3123123),
            guild_id=snowflakes.Snowflake(5412231),
            member=object(),
            user=object(),
            token="httptptptptptptptp",
            version=1,
            application_id=snowflakes.Snowflake(43123),
            component_type=2,
            values=(),
            custom_id="OKOKOK",
            message=object(),
            locale="es-ES",
            guild_locale="en-US",
            app_permissions=123321,
            resolved=None,
            entitlements=[
                monetization.Entitlement(
                    id=snowflakes.Snowflake(123123),
                    sku_id=snowflakes.Snowflake(123123),
                    application_id=snowflakes.Snowflake(123123),
                    guild_id=snowflakes.Snowflake(123123),
                    user_id=snowflakes.Snowflake(123123),
                    type=monetization.EntitlementType.APPLICATION_SUBSCRIPTION,
                    starts_at=None,
                    ends_at=None,
                    is_deleted=False,
                    subscription_id=None,
                )
            ],
        )

    def test_build_response(self, mock_component_interaction, mock_app):
        mock_app.rest.interaction_message_builder = mock.Mock()
        response = mock_component_interaction.build_response(4)

        assert response is mock_app.rest.interaction_message_builder.return_value
        mock_app.rest.interaction_message_builder.assert_called_once_with(4)

    def test_build_response_with_invalid_type(self, mock_component_interaction):
        with pytest.raises(ValueError, match="Invalid type passed for an immediate response"):
            mock_component_interaction.build_response(999)

    def test_build_deferred_response(self, mock_component_interaction, mock_app):
        mock_app.rest.interaction_deferred_builder = mock.Mock()
        response = mock_component_interaction.build_deferred_response(5)

        assert response is mock_app.rest.interaction_deferred_builder.return_value
        mock_app.rest.interaction_deferred_builder.assert_called_once_with(5)

    def test_build_deferred_response_with_invalid_type(self, mock_component_interaction):
        with pytest.raises(ValueError, match="Invalid type passed for a deferred response"):
            mock_component_interaction.build_deferred_response(33333)

    @pytest.mark.asyncio
    async def test_fetch_channel(self, mock_component_interaction, mock_app):
        mock_app.rest.fetch_channel.return_value = mock.Mock(channels.TextableChannel)

        assert await mock_component_interaction.fetch_channel() is mock_app.rest.fetch_channel.return_value

        mock_app.rest.fetch_channel.assert_awaited_once_with(3123123)

    def test_get_channel(self, mock_component_interaction, mock_app):
        mock_app.cache.get_guild_channel.return_value = mock.Mock(channels.GuildTextChannel)

        assert mock_component_interaction.get_channel() is mock_app.cache.get_guild_channel.return_value

        mock_app.cache.get_guild_channel.assert_called_once_with(3123123)

    def test_get_channel_when_not_cached(self, mock_component_interaction, mock_app):
        mock_app.cache.get_guild_channel.return_value = None

        assert mock_component_interaction.get_channel() is None

        mock_app.cache.get_guild_channel.assert_called_once_with(3123123)

    def test_get_channel_without_cache(self, mock_component_interaction):
        mock_component_interaction.app = mock.Mock(traits.RESTAware)

        assert mock_component_interaction.get_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, mock_component_interaction, mock_app):
        mock_component_interaction.guild_id = 43123123

        assert await mock_component_interaction.fetch_guild() is mock_app.rest.fetch_guild.return_value

        mock_app.rest.fetch_guild.assert_awaited_once_with(43123123)

    @pytest.mark.asyncio
    async def test_fetch_guild_for_dm_interaction(self, mock_component_interaction, mock_app):
        mock_component_interaction.guild_id = None

        assert await mock_component_interaction.fetch_guild() is None

        mock_app.rest.fetch_guild.assert_not_called()

    def test_get_guild(self, mock_component_interaction, mock_app):
        mock_component_interaction.guild_id = 874356

        assert mock_component_interaction.get_guild() is mock_app.cache.get_guild.return_value

        mock_app.cache.get_guild.assert_called_once_with(874356)

    def test_get_guild_for_dm_interaction(self, mock_component_interaction, mock_app):
        mock_component_interaction.guild_id = None

        assert mock_component_interaction.get_guild() is None

        mock_app.cache.get_guild.assert_not_called()

    def test_get_guild_when_cacheless(self, mock_component_interaction, mock_app):
        mock_component_interaction.guild_id = 321123
        mock_component_interaction.app = mock.Mock(traits.RESTAware)

        assert mock_component_interaction.get_guild() is None

        mock_app.cache.get_guild.assert_not_called()

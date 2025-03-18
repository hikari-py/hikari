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

import mock
import pytest

from hikari import applications
from hikari import channels
from hikari import monetization
from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari.interactions import base_interactions
from hikari.interactions import component_interactions


class TestComponentInteraction:
    @pytest.fixture
    def mock_component_interaction(self, hikari_app: traits.RESTAware) -> component_interactions.ComponentInteraction:
        return component_interactions.ComponentInteraction(
            app=hikari_app,
            id=snowflakes.Snowflake(2312312),
            type=base_interactions.InteractionType.MESSAGE_COMPONENT,
            channel_id=snowflakes.Snowflake(3123123),
            guild_id=snowflakes.Snowflake(5412231),
            member=mock.Mock(),
            user=mock.Mock(),
            token="httptptptptptptptp",
            version=1,
            application_id=snowflakes.Snowflake(43123),
            component_type=2,
            values=(),
            custom_id="OKOKOK",
            message=mock.Mock(),
            locale="es-ES",
            guild_locale="en-US",
            app_permissions=permissions.Permissions.NONE,
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
            authorizing_integration_owners={
                applications.ApplicationIntegrationType.GUILD_INSTALL: snowflakes.Snowflake(123)
            },
            context=applications.ApplicationContextType.PRIVATE_CHANNEL,
        )

    def test_build_response(
        self, mock_component_interaction: component_interactions.ComponentInteraction, hikari_app: traits.RESTAware
    ):
        hikari_app.rest.interaction_message_builder = mock.Mock()
        response = mock_component_interaction.build_response(4)

        assert response is hikari_app.rest.interaction_message_builder.return_value
        hikari_app.rest.interaction_message_builder.assert_called_once_with(4)

    def test_build_response_with_invalid_type(
        self, mock_component_interaction: component_interactions.ComponentInteraction
    ):
        with pytest.raises(ValueError, match="Invalid type passed for an immediate response"):
            mock_component_interaction.build_response(999)  # pyright: ignore [reportArgumentType]

    def test_build_deferred_response(
        self, mock_component_interaction: component_interactions.ComponentInteraction, hikari_app: traits.RESTAware
    ):
        hikari_app.rest.interaction_deferred_builder = mock.Mock()
        response = mock_component_interaction.build_deferred_response(5)

        assert response is hikari_app.rest.interaction_deferred_builder.return_value
        hikari_app.rest.interaction_deferred_builder.assert_called_once_with(5)

    def test_build_deferred_response_with_invalid_type(
        self, mock_component_interaction: component_interactions.ComponentInteraction
    ):
        with pytest.raises(ValueError, match="Invalid type passed for a deferred response"):
            mock_component_interaction.build_deferred_response(33333)  # pyright: ignore [reportArgumentType]

    @pytest.mark.asyncio
    async def test_fetch_channel(self, mock_component_interaction: component_interactions.ComponentInteraction):
        with mock.patch.object(
            mock_component_interaction.app.rest,
            "fetch_channel",
            new_callable=mock.AsyncMock,
            return_value=mock.Mock(channels.TextableChannel),
        ) as patched_fetch_channel:
            assert await mock_component_interaction.fetch_channel() is patched_fetch_channel.return_value

            patched_fetch_channel.assert_awaited_once_with(3123123)

    def test_get_channel(self, mock_component_interaction: component_interactions.ComponentInteraction):
        with (
            mock.patch.object(mock_component_interaction, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", return_value=mock.Mock(channels.GuildTextChannel)
            ) as patched_get_guild_channel,
        ):
            assert mock_component_interaction.get_channel() is patched_get_guild_channel.return_value

            patched_get_guild_channel.assert_called_once_with(3123123)

    def test_get_channel_when_not_cached(self, mock_component_interaction: component_interactions.ComponentInteraction):
        with (
            mock.patch.object(mock_component_interaction, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild_channel", return_value=None) as patched_get_guild_channel,
        ):
            assert mock_component_interaction.get_channel() is None

            patched_get_guild_channel.assert_called_once_with(3123123)

    def test_get_channel_without_cache(self, mock_component_interaction: component_interactions.ComponentInteraction):
        mock_component_interaction.app = mock.Mock(traits.RESTAware)

        assert mock_component_interaction.get_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_guild(self, mock_component_interaction: component_interactions.ComponentInteraction):
        with (
            mock.patch.object(mock_component_interaction, "guild_id", snowflakes.Snowflake(43123123)),
            mock.patch.object(
                mock_component_interaction.app.rest, "fetch_guild", mock.AsyncMock()
            ) as patched_fetch_guild,
        ):
            assert await mock_component_interaction.fetch_guild() is patched_fetch_guild.return_value

            patched_fetch_guild.assert_awaited_once_with(43123123)

    @pytest.mark.asyncio
    async def test_fetch_guild_for_dm_interaction(
        self, mock_component_interaction: component_interactions.ComponentInteraction
    ):
        with (
            mock.patch.object(mock_component_interaction, "guild_id", None),
            mock.patch.object(mock_component_interaction.app.rest, "fetch_guild") as patched_fetch_guild,
        ):
            assert await mock_component_interaction.fetch_guild() is None

            patched_fetch_guild.assert_not_called()

    def test_get_guild(self, mock_component_interaction: component_interactions.ComponentInteraction):
        with (
            mock.patch.object(mock_component_interaction, "guild_id", snowflakes.Snowflake(874356)),
            mock.patch.object(mock_component_interaction, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild", return_value=None) as patched_get_guild,
        ):
            assert mock_component_interaction.get_guild() is patched_get_guild.return_value
            patched_get_guild.assert_called_once_with(874356)

    def test_get_guild_for_dm_interaction(
        self, mock_component_interaction: component_interactions.ComponentInteraction
    ):
        with (
            mock.patch.object(mock_component_interaction, "guild_id", None),
            mock.patch.object(mock_component_interaction, "app", mock.Mock(traits.CacheAware)) as patched_app,
            mock.patch.object(patched_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild", return_value=None) as patched_get_guild,
        ):
            assert mock_component_interaction.get_guild() is None
            patched_get_guild.assert_not_called()

    def test_get_guild_when_cacheless(
        self, mock_component_interaction: component_interactions.ComponentInteraction, hikari_app: traits.RESTAware
    ):
        mock_component_interaction.guild_id = snowflakes.Snowflake(321123)
        mock_component_interaction.app = mock.Mock(traits.RESTAware)

        assert mock_component_interaction.get_guild() is None

        # hikari_app.cache.get_guild.assert_not_called()  # FIXME: This isn't an easy thing to patch, because it complains that the mock app does not have the attribute cache anyways, so it can never be called.

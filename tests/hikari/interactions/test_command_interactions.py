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
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.interactions import base_interactions
from hikari.interactions import command_interactions


@pytest.fixture()
def mock_app():
    return mock.Mock(traits.CacheAware, rest=mock.AsyncMock())


class TestCommandInteraction:
    @pytest.fixture()
    def mock_command_interaction(self, mock_app):
        return command_interactions.CommandInteraction(
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
            command_id=snowflakes.Snowflake(3123123),
            command_name="OKOKOK",
            options=[],
            resolved=None,
        )

    def test_build_response(self, mock_command_interaction, mock_app):
        mock_app.rest.interaction_message_builder = mock.Mock()
        builder = mock_command_interaction.build_response()

        assert builder is mock_app.rest.interaction_message_builder.return_value
        mock_app.rest.interaction_message_builder.assert_called_once_with(base_interactions.ResponseType.MESSAGE_CREATE)

    def test_build_deferred_response(self, mock_command_interaction, mock_app):
        mock_app.rest.interaction_deferred_builder = mock.Mock()
        builder = mock_command_interaction.build_deferred_response()

        assert builder is mock_app.rest.interaction_deferred_builder.return_value
        mock_app.rest.interaction_deferred_builder.assert_called_once_with(
            base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE
        )

    @pytest.mark.asyncio()
    async def test_fetch_initial_response(self, mock_command_interaction, mock_app):
        result = await mock_command_interaction.fetch_initial_response()

        assert result is mock_app.rest.fetch_interaction_response.return_value
        mock_app.rest.fetch_interaction_response.assert_awaited_once_with(43123, "httptptptptptptptp")

    @pytest.mark.asyncio()
    async def test_create_initial_response_with_optional_args(self, mock_command_interaction, mock_app):
        mock_embed_1 = object()
        mock_embed_2 = object()
        await mock_command_interaction.create_initial_response(
            base_interactions.ResponseType.MESSAGE_CREATE,
            "content",
            tts=True,
            embed=mock_embed_1,
            flags=64,
            embeds=[mock_embed_2],
            mentions_everyone=False,
            user_mentions=[123432],
            role_mentions=[6324523],
        )

        mock_app.rest.create_interaction_response.assert_awaited_once_with(
            2312312,
            "httptptptptptptptp",
            base_interactions.ResponseType.MESSAGE_CREATE,
            "content",
            tts=True,
            flags=64,
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            mentions_everyone=False,
            user_mentions=[123432],
            role_mentions=[6324523],
        )

    @pytest.mark.asyncio()
    async def test_create_initial_response_without_optional_args(self, mock_command_interaction, mock_app):
        await mock_command_interaction.create_initial_response(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)

        mock_app.rest.create_interaction_response.assert_awaited_once_with(
            2312312,
            "httptptptptptptptp",
            base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE,
            undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio()
    async def test_edit_initial_response_with_optional_args(self, mock_command_interaction, mock_app):
        mock_embed_1 = object()
        mock_embed_2 = object()
        mock_attachment_1 = object()
        mock_attachment_2 = object()
        result = await mock_command_interaction.edit_initial_response(
            "new content",
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            attachment=mock_attachment_1,
            attachments=[mock_attachment_2],
            replace_attachments=True,
            mentions_everyone=False,
            user_mentions=[123123],
            role_mentions=[562134],
        )

        assert result is mock_app.rest.edit_interaction_response.return_value
        mock_app.rest.edit_interaction_response.assert_awaited_once_with(
            43123,
            "httptptptptptptptp",
            "new content",
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            attachment=mock_attachment_1,
            attachments=[mock_attachment_2],
            replace_attachments=True,
            mentions_everyone=False,
            user_mentions=[123123],
            role_mentions=[562134],
        )

    @pytest.mark.asyncio()
    async def test_edit_initial_response_without_optional_args(self, mock_command_interaction, mock_app):
        result = await mock_command_interaction.edit_initial_response()

        assert result is mock_app.rest.edit_interaction_response.return_value
        mock_app.rest.edit_interaction_response.assert_awaited_once_with(
            43123,
            "httptptptptptptptp",
            undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            replace_attachments=False,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio()
    async def test_delete_initial_response(self, mock_command_interaction, mock_app):
        await mock_command_interaction.delete_initial_response()

        mock_app.rest.delete_interaction_response.assert_awaited_once_with(43123, "httptptptptptptptp")

    @pytest.mark.asyncio()
    async def test_fetch_channel(self, mock_command_interaction, mock_app):
        mock_app.rest.fetch_channel.return_value = mock.Mock(channels.GuildChannel)
        assert await mock_command_interaction.fetch_channel() is mock_app.rest.fetch_channel.return_value

        mock_app.rest.fetch_channel.assert_awaited_once_with(3123123)

    def test_get_channel(self, mock_command_interaction, mock_app):
        assert mock_command_interaction.get_channel() is mock_app.cache.get_guild_channel.return_value
        mock_app.cache.get_guild_channel.assert_called_once_with(3123123)

    def test_get_channel_without_cache(self, mock_command_interaction):
        mock_command_interaction.app = mock.Mock(traits.RESTAware)

        assert mock_command_interaction.get_channel() is None

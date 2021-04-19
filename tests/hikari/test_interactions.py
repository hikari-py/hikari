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
from hikari import undefined


@pytest.fixture()
def mock_app():
    return mock.Mock(traits.CacheAware, rest=mock.AsyncMock())


class TestCommand:
    @pytest.fixture()
    def mock_command(self, mock_app):
        return interactions.Command(
            app=mock_app,
            id=snowflakes.Snowflake(34123123),
            application_id=snowflakes.Snowflake(65234123),
            name="Name",
            description="very descript",
            options=[],
            guild_id=snowflakes.Snowflake(31231235),
        )

    @pytest.mark.asyncio
    async def test_fetch_self(self, mock_command, mock_app):
        result = await mock_command.fetch_self()

        assert result is mock_app.rest.fetch_application_command.return_value
        mock_app.rest.fetch_application_command.assert_awaited_once_with(65234123, 34123123, 31231235)

    @pytest.mark.asyncio
    async def test_fetch_self_when_guild_id_is_none(self, mock_command, mock_app):
        mock_command.guild_id = None

        result = await mock_command.fetch_self()

        assert result is mock_app.rest.fetch_application_command.return_value
        mock_app.rest.fetch_application_command.assert_awaited_once_with(65234123, 34123123, undefined.UNDEFINED)

    @pytest.mark.asyncio
    async def test_edit_without_optional_args(self, mock_command, mock_app):
        result = await mock_command.edit()

        assert result is mock_app.rest.edit_application_command.return_value
        mock_app.rest.edit_application_command.assert_awaited_once_with(
            65234123,
            34123123,
            31231235,
            name=undefined.UNDEFINED,
            description=undefined.UNDEFINED,
            options=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio
    async def test_edit_with_optional_args(self, mock_command, mock_app):
        mock_option = object()
        result = await mock_command.edit(name="new name", description="very descrypt", options=[mock_option])

        assert result is mock_app.rest.edit_application_command.return_value
        mock_app.rest.edit_application_command.assert_awaited_once_with(
            65234123, 34123123, 31231235, name="new name", description="very descrypt", options=[mock_option]
        )

    @pytest.mark.asyncio
    async def test_edit_when_guild_id_is_none(self, mock_command, mock_app):
        mock_command.guild_id = None

        result = await mock_command.edit()

        assert result is mock_app.rest.edit_application_command.return_value
        mock_app.rest.edit_application_command.assert_awaited_once_with(
            65234123,
            34123123,
            undefined.UNDEFINED,
            name=undefined.UNDEFINED,
            description=undefined.UNDEFINED,
            options=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio
    async def test_delete(self, mock_command, mock_app):
        await mock_command.delete()

        mock_app.rest.delete_application_command.assert_awaited_once_with(65234123, 34123123, 31231235)

    @pytest.mark.asyncio
    async def test_delete_when_guild_id_is_none(self, mock_command, mock_app):
        mock_command.guild_id = None

        await mock_command.delete()

        mock_app.rest.delete_application_command.assert_awaited_once_with(65234123, 34123123, undefined.UNDEFINED)


class TestCommandInteraction:
    @pytest.fixture()
    def mock_command_interaction(self, mock_app):
        return interactions.CommandInteraction(
            app=mock_app,
            id=snowflakes.Snowflake(2312312),
            type=interactions.InteractionType.APPLICATION_COMMAND,
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
        )

    @pytest.mark.asyncio
    async def test_fetch_initial_response(self, mock_command_interaction, mock_app):
        result = await mock_command_interaction.fetch_initial_response()

        assert result is mock_app.rest.fetch_command_response.return_value
        mock_app.rest.fetch_command_response.assert_awaited_once_with(43123, "httptptptptptptptp")

    @pytest.mark.asyncio
    async def test_create_initial_response_with_optional_args(self, mock_command_interaction, mock_app):
        mock_embed_1 = object()
        mock_embed_2 = object()
        await mock_command_interaction.create_initial_response(
            interactions.ResponseType.SOURCED_RESPONSE,
            "content",
            tts=True,
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            mentions_everyone=False,
            user_mentions=[123432],
            role_mentions=[6324523],
        )

        mock_app.rest.create_command_response.assert_awaited_once_with(
            2312312,
            "httptptptptptptptp",
            interactions.ResponseType.SOURCED_RESPONSE,
            "content",
            tts=True,
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            mentions_everyone=False,
            user_mentions=[123432],
            role_mentions=[6324523],
        )

    @pytest.mark.asyncio
    async def test_create_initial_response_without_optional_args(self, mock_command_interaction, mock_app):
        await mock_command_interaction.create_initial_response(interactions.ResponseType.DEFERRED_SOURCED_RESPONSE)

        mock_app.rest.create_command_response.assert_awaited_once_with(
            2312312,
            "httptptptptptptptp",
            interactions.ResponseType.DEFERRED_SOURCED_RESPONSE,
            undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio
    async def test_edit_initial_response_with_optional_args(self, mock_command_interaction, mock_app):
        mock_embed_1 = object()
        mock_embed_2 = object()
        result = await mock_command_interaction.edit_initial_response(
            "new content",
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            mentions_everyone=False,
            user_mentions=[123123],
            role_mentions=[562134],
        )

        assert result is mock_app.rest.edit_command_response.return_value
        mock_app.rest.edit_command_response.assert_awaited_once_with(
            43123,
            "httptptptptptptptp",
            "new content",
            embed=mock_embed_1,
            embeds=[mock_embed_2],
            mentions_everyone=False,
            user_mentions=[123123],
            role_mentions=[562134],
        )

    @pytest.mark.asyncio
    async def test_edit_initial_response_without_optional_args(self, mock_command_interaction, mock_app):
        result = await mock_command_interaction.edit_initial_response()

        assert result is mock_app.rest.edit_command_response.return_value
        mock_app.rest.edit_command_response.assert_awaited_once_with(
            43123,
            "httptptptptptptptp",
            undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )

    @pytest.mark.asyncio
    async def test_delete_initial_response(self, mock_command_interaction, mock_app):
        await mock_command_interaction.delete_initial_response()

        mock_app.rest.delete_command_response.assert_awaited_once_with(43123, "httptptptptptptptp")

    @pytest.mark.asyncio
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

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

from hikari import commands
from hikari import snowflakes
from hikari import traits
from hikari import undefined


@pytest.fixture()
def mock_app():
    return mock.Mock(traits.CacheAware, rest=mock.AsyncMock())


class TestCommand:
    @pytest.fixture()
    def mock_command(self, mock_app):
        return commands.Command(
            app=mock_app,
            id=snowflakes.Snowflake(34123123),
            application_id=snowflakes.Snowflake(65234123),
            name="Name",
            description="very descript",
            options=[],
            guild_id=snowflakes.Snowflake(31231235),
        )

    @pytest.mark.asyncio()
    async def test_fetch_self(self, mock_command, mock_app):
        result = await mock_command.fetch_self()

        assert result is mock_app.rest.fetch_application_command.return_value
        mock_app.rest.fetch_application_command.assert_awaited_once_with(65234123, 34123123, 31231235)

    @pytest.mark.asyncio()
    async def test_fetch_self_when_guild_id_is_none(self, mock_command, mock_app):
        mock_command.guild_id = None

        result = await mock_command.fetch_self()

        assert result is mock_app.rest.fetch_application_command.return_value
        mock_app.rest.fetch_application_command.assert_awaited_once_with(65234123, 34123123, undefined.UNDEFINED)

    @pytest.mark.asyncio()
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

    @pytest.mark.asyncio()
    async def test_edit_with_optional_args(self, mock_command, mock_app):
        mock_option = object()
        result = await mock_command.edit(name="new name", description="very descrypt", options=[mock_option])

        assert result is mock_app.rest.edit_application_command.return_value
        mock_app.rest.edit_application_command.assert_awaited_once_with(
            65234123, 34123123, 31231235, name="new name", description="very descrypt", options=[mock_option]
        )

    @pytest.mark.asyncio()
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

    @pytest.mark.asyncio()
    async def test_delete(self, mock_command, mock_app):
        await mock_command.delete()

        mock_app.rest.delete_application_command.assert_awaited_once_with(65234123, 34123123, 31231235)

    @pytest.mark.asyncio()
    async def test_delete_when_guild_id_is_none(self, mock_command, mock_app):
        mock_command.guild_id = None

        await mock_command.delete()

        mock_app.rest.delete_application_command.assert_awaited_once_with(65234123, 34123123, undefined.UNDEFINED)

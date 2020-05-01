#!/usr/bin/env python3
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
import contextlib
import datetime

import mock
import pytest

from hikari import applications
from hikari import channels
from hikari import files
from hikari import guilds
from hikari import users
from hikari.clients import components
from hikari.clients.rest import me
from hikari.net import rest
from tests.hikari import _helpers


class TestRESTInviteLogic:
    @pytest.fixture()
    def rest_clients_impl(self):
        mock_components = mock.MagicMock(components.Components)
        mock_low_level_restful_client = mock.MagicMock(rest.REST)

        class RESTCurrentUserLogicImpl(me.RESTCurrentUserComponent):
            def __init__(self):
                super().__init__(mock_components, mock_low_level_restful_client)

        return RESTCurrentUserLogicImpl()

    @pytest.mark.asyncio
    async def test_fetch_me(self, rest_clients_impl):
        mock_user_payload = {"username": "A User", "id": "202020200202"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.get_current_user.return_value = mock_user_payload
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.fetch_me() is mock_user_obj
            rest_clients_impl._session.get_current_user.assert_called_once()
            users.MyUser.deserialize.assert_called_once_with(
                mock_user_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_update_me_with_optionals(self, rest_clients_impl):
        mock_user_payload = {"id": "424242", "flags": "420", "discriminator": "6969"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.modify_current_user.return_value = mock_user_payload
        mock_avatar_data = mock.MagicMock(bytes)
        mock_avatar_obj = mock.MagicMock(files.File)
        mock_avatar_obj.read_all = mock.AsyncMock(return_value=mock_avatar_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj))
        with stack:
            assert await rest_clients_impl.update_me(username="aNewName", avatar=mock_avatar_obj) is mock_user_obj
            rest_clients_impl._session.modify_current_user.assert_called_once_with(
                username="aNewName", avatar=mock_avatar_data
            )
            mock_avatar_obj.read_all.assert_awaited_once()
            users.MyUser.deserialize.assert_called_once_with(
                mock_user_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_update_me_without_optionals(self, rest_clients_impl):
        mock_user_payload = {"id": "424242", "flags": "420", "discriminator": "6969"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.modify_current_user.return_value = mock_user_payload
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.update_me() is mock_user_obj
            rest_clients_impl._session.modify_current_user.assert_called_once_with(username=..., avatar=...)
            users.MyUser.deserialize.assert_called_once_with(
                mock_user_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_fetch_my_connections(self, rest_clients_impl):
        mock_connection_payload = {"id": "odnkwu", "type": "twitch", "name": "eric"}
        mock_connection_obj = mock.MagicMock(applications.OwnConnection)
        rest_clients_impl._session.get_current_user_connections.return_value = [mock_connection_payload]
        with mock.patch.object(applications.OwnConnection, "deserialize", return_value=mock_connection_obj):
            assert await rest_clients_impl.fetch_my_connections() == [mock_connection_obj]
            rest_clients_impl._session.get_current_user_connections.assert_called_once()
            applications.OwnConnection.deserialize.assert_called_once_with(
                mock_connection_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_my_guilds_after_with_optionals(self, rest_clients_impl, guild):
        mock_guild_obj = mock.AsyncMock(applications.OwnGuild)
        mock_payload = {"id": "123123", "permissions": "292929"}
        mock_request = mock.AsyncMock(return_value=[mock_payload])
        rest_clients_impl._session.get_current_user_guilds = mock_request
        with mock.patch.object(applications.OwnGuild, "deserialize", return_value=mock_guild_obj):
            async for guild in rest_clients_impl.fetch_my_guilds_after(after=guild, limit=50):
                assert guild is mock_guild_obj
                break
            mock_request.assert_called_once_with(after="574921006817476608", limit=50)
            applications.OwnGuild.deserialize.assert_called_once_with(
                mock_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_fetch_my_guilds_after_without_optionals(self, rest_clients_impl):
        mock_guild_obj = mock.AsyncMock(applications.OwnGuild)
        mock_payload = {"id": "123123", "permissions": "292929"}
        mock_request = mock.AsyncMock(return_value=[mock_payload])
        rest_clients_impl._session.get_current_user_guilds = mock_request
        with mock.patch.object(applications.OwnGuild, "deserialize", return_value=mock_guild_obj):
            async for guild in rest_clients_impl.fetch_my_guilds_after():
                assert guild is mock_guild_obj
                break
            mock_request.assert_called_once_with(after="0", limit=100)
            applications.OwnGuild.deserialize.assert_called_once_with(
                mock_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_fetch_my_guilds_after_with_datetime_object(self, rest_clients_impl):
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        mock_guild_obj = mock.AsyncMock(applications.OwnGuild)
        mock_payload = {"id": "123123", "permissions": "292929"}
        mock_request = mock.AsyncMock(return_value=[mock_payload])
        rest_clients_impl._session.get_current_user_guilds = mock_request
        with mock.patch.object(applications.OwnGuild, "deserialize", return_value=mock_guild_obj):
            async for guild in rest_clients_impl.fetch_my_guilds_after(after=date):
                assert guild is mock_guild_obj
                break
            mock_request.assert_called_once_with(after="537340988620800000", limit=100)
            applications.OwnGuild.deserialize.assert_called_once_with(
                mock_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_fetch_my_guilds_before_with_optionals(self, rest_clients_impl, guild):
        mock_guild_obj = mock.AsyncMock(applications.OwnGuild)
        mock_payload = {"id": "123123", "permissions": "292929"}
        mock_request = mock.AsyncMock(return_value=[mock_payload])
        rest_clients_impl._session.get_current_user_guilds = mock_request
        with mock.patch.object(applications.OwnGuild, "deserialize", return_value=mock_guild_obj):
            async for guild in rest_clients_impl.fetch_my_guilds_before(before=guild, limit=50):
                assert guild is mock_guild_obj
                break
            mock_request.assert_called_once_with(before="574921006817476608", limit=50)
            applications.OwnGuild.deserialize.assert_called_once_with(
                mock_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_fetch_my_guilds_before_without_optionals(self, rest_clients_impl):
        mock_guild_obj = mock.AsyncMock(applications.OwnGuild)
        mock_payload = {"id": "123123", "permissions": "292929"}
        mock_request = mock.AsyncMock(return_value=[mock_payload])
        rest_clients_impl._session.get_current_user_guilds = mock_request
        with mock.patch.object(applications.OwnGuild, "deserialize", return_value=mock_guild_obj):
            async for guild in rest_clients_impl.fetch_my_guilds_before():
                assert guild is mock_guild_obj
                break
            mock_request.assert_called_once_with(before="9223372036854775807", limit=100)
            applications.OwnGuild.deserialize.assert_called_once_with(
                mock_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    async def test_fetch_my_guilds_before_with_datetime_object(self, rest_clients_impl):
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        mock_guild_obj = mock.AsyncMock(applications.OwnGuild)
        mock_payload = {"id": "123123", "permissions": "292929"}
        mock_request = mock.AsyncMock(return_value=[mock_payload])
        rest_clients_impl._session.get_current_user_guilds = mock_request
        with mock.patch.object(applications.OwnGuild, "deserialize", return_value=mock_guild_obj):
            async for guild in rest_clients_impl.fetch_my_guilds_before(before=date):
                assert guild is mock_guild_obj
                break
            mock_request.assert_called_once_with(before="537340988620800000", limit=100)
            applications.OwnGuild.deserialize.assert_called_once_with(
                mock_payload, components=rest_clients_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    async def test_leave_guild(self, rest_clients_impl, guild):
        rest_clients_impl._session.leave_guild.return_value = ...
        assert await rest_clients_impl.leave_guild(guild) is None
        rest_clients_impl._session.leave_guild.assert_called_once_with(guild_id="574921006817476608")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("recipient", 115590097100865541, users.User)
    async def test_create_dm_channel(self, rest_clients_impl, recipient):
        mock_dm_payload = {"id": "2202020", "type": 2, "recipients": []}
        mock_dm_obj = mock.MagicMock(channels.DMChannel)
        rest_clients_impl._session.create_dm.return_value = mock_dm_payload
        with mock.patch.object(channels.DMChannel, "deserialize", return_value=mock_dm_obj):
            assert await rest_clients_impl.create_dm_channel(recipient) is mock_dm_obj
            rest_clients_impl._session.create_dm.assert_called_once_with(recipient_id="115590097100865541")
            channels.DMChannel.deserialize.assert_called_once_with(
                mock_dm_payload, components=rest_clients_impl._components
            )

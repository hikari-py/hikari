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
import inspect

import mock
import pytest

from hikari import application
from hikari.models import applications
from hikari.models import bases
from hikari.models import channels
from hikari.models import files
from hikari.models import guilds
from hikari.models import users
from hikari.net.rest import me
from hikari.net.rest import session
from tests.hikari import _helpers


class TestGuildPaginator:
    @pytest.fixture()
    def mock_session(self):
        return mock.MagicMock(spec_set=session.RESTSession)

    @pytest.fixture()
    def mock_app(self):
        return mock.MagicMock(spec_set=application.Application)

    @pytest.fixture()
    def ownguild_cls(self):
        with mock.patch.object(applications, "OwnGuild") as own_guild_cls:
            yield own_guild_cls

    @pytest.mark.parametrize(
        ["newest_first", "expected_first_id"], [(True, str(bases.Snowflake.max())), (False, str(bases.Snowflake.min()))]
    )
    def test_init_with_no_explicit_first_element(self, newest_first, expected_first_id, mock_app, mock_session):
        pag = me._GuildPaginator(mock_app, newest_first, None, mock_session)
        assert pag._first_id == expected_first_id
        assert pag._newest_first is newest_first
        assert pag._app is mock_app
        assert pag._session is mock_session

    def test_init_with_explicit_first_element(self, mock_app, mock_session):
        pag = me._GuildPaginator(mock_app, False, 12345, mock_session)
        assert pag._first_id == "12345"
        assert pag._newest_first is False
        assert pag._app is mock_app
        assert pag._session is mock_session

    @pytest.mark.parametrize(["newest_first", "_direction"], [(True, "before"), (False, "after"),])
    @pytest.mark.asyncio
    async def test_next_chunk_performs_correct_api_call(
        self, mock_session, mock_app, newest_first, direction, ownguild_cls
    ):
        pag = me._GuildPaginator(mock_app, newest_first, None, mock_session)
        pag._first_id = "123456"

        await pag._next_chunk()

        mock_session.get_current_user_guilds.assert_awaited_once_with(**{direction: "123456"})

    @pytest.mark.asyncio
    async def test_next_chunk_returns_None_if_no_items_returned(self, mock_session, mock_app, ownguild_cls):
        pag = me._GuildPaginator(mock_app, False, None, mock_session)
        mock_session.get_current_user_guilds = mock.AsyncMock(return_value=[])
        assert await pag._next_chunk() is None

    @pytest.mark.asyncio
    async def test_next_chunk_updates_first_id_to_last_item(self, mock_session, mock_app, ownguild_cls):
        pag = me._GuildPaginator(mock_app, False, None, mock_session)

        return_payload = [
            {"id": "1234", ...: ...},
            {"id": "3456", ...: ...},
            {"id": "3333", ...: ...},
            {"id": "512", ...: ...},
        ]

        mock_session.get_current_user_guilds = mock.AsyncMock(return_value=return_payload)
        await pag._next_chunk()
        assert pag._first_id == "512"

    @pytest.mark.asyncio
    async def test_next_chunk_deserializes_payload_in_generator_lazily(self, mock_session, mock_app, ownguild_cls):
        pag = me._GuildPaginator(mock_app, False, None, mock_session)

        return_payload = [
            {"id": "1234", ...: ...},
            {"id": "3456", ...: ...},
            {"id": "3333", ...: ...},
            {"id": "512", ...: ...},
        ]

        real_values = [
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
        ]

        assert len(real_values) == len(return_payload)

        ownguild_cls.deserialize = mock.MagicMock(side_effect=real_values)

        mock_session.get_current_user_guilds = mock.AsyncMock(return_value=return_payload)
        generator = await pag._next_chunk()

        assert inspect.isgenerator(generator), "expected genexp result"

        # No calls, this should be lazy to be more performant for non-100-divisable limit counts.
        ownguild_cls.deserialize.assert_not_called()

        for i, input_payload in enumerate(return_payload):
            expected_value = real_values[i]
            assert next(generator) is expected_value
            ownguild_cls.deserialize.assert_called_with(input_payload, app=mock_app)

        # Clear the generator result.
        # This doesn't test anything, but there is an issue with coverage not detecting generator
        # exit conditions properly. This fixes something that would otherwise be marked as
        # uncovered behaviour erroneously.
        # https://stackoverflow.com/questions/35317757/python-unittest-branch-coverage-seems-to-miss-executed-generator-in-zip
        with pytest.raises(StopIteration):
            next(generator)

        assert locals()["i"] == len(return_payload) - 1, "Not iterated correctly somehow"


class TestRESTInviteLogic:
    @pytest.fixture()
    def rest_clients_impl(self):
        mock_app = mock.MagicMock(application.Application)
        mock_low_level_restful_client = mock.MagicMock(session.RESTSession)

        class RESTCurrentUserLogicImpl(me.RESTCurrentUserComponent):
            def __init__(self):
                super().__init__(mock_app, mock_low_level_restful_client)

        return RESTCurrentUserLogicImpl()

    @pytest.mark.asyncio
    async def test_fetch_me(self, rest_clients_impl):
        mock_user_payload = {"username": "A User", "id": "202020200202"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.get_current_user.return_value = mock_user_payload
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.fetch_me() is mock_user_obj
            rest_clients_impl._session.get_current_user.assert_called_once()
            users.MyUser.deserialize.assert_called_once_with(mock_user_payload, app=rest_clients_impl._app)

    @pytest.mark.asyncio
    async def test_update_me_with_optionals(self, rest_clients_impl):
        mock_user_payload = {"id": "424242", "flags": "420", "discriminator": "6969"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.modify_current_user.return_value = mock_user_payload
        mock_avatar_data = mock.MagicMock(bytes)
        mock_avatar_obj = mock.MagicMock(files.BaseStream)
        mock_avatar_obj.read = mock.AsyncMock(return_value=mock_avatar_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj))
        with stack:
            assert await rest_clients_impl.update_me(username="aNewName", avatar=mock_avatar_obj) is mock_user_obj
            rest_clients_impl._session.modify_current_user.assert_called_once_with(
                username="aNewName", avatar=mock_avatar_data
            )
            mock_avatar_obj.read.assert_awaited_once()
            users.MyUser.deserialize.assert_called_once_with(mock_user_payload, app=rest_clients_impl._app)

    @pytest.mark.asyncio
    async def test_update_me_without_optionals(self, rest_clients_impl):
        mock_user_payload = {"id": "424242", "flags": "420", "discriminator": "6969"}
        mock_user_obj = mock.MagicMock(users.MyUser)
        rest_clients_impl._session.modify_current_user.return_value = mock_user_payload
        with mock.patch.object(users.MyUser, "deserialize", return_value=mock_user_obj):
            assert await rest_clients_impl.update_me() is mock_user_obj
            rest_clients_impl._session.modify_current_user.assert_called_once_with(username=..., avatar=...)
            users.MyUser.deserialize.assert_called_once_with(mock_user_payload, app=rest_clients_impl._app)

    @pytest.mark.asyncio
    async def test_fetch_my_connections(self, rest_clients_impl):
        mock_connection_payload = {"id": "odnkwu", "type": "twitch", "name": "eric"}
        mock_connection_obj = mock.MagicMock(applications.OwnConnection)
        rest_clients_impl._session.get_current_user_connections.return_value = [mock_connection_payload]
        with mock.patch.object(applications.OwnConnection, "deserialize", return_value=mock_connection_obj):
            assert await rest_clients_impl.fetch_my_connections() == [mock_connection_obj]
            rest_clients_impl._session.get_current_user_connections.assert_called_once()
            applications.OwnConnection.deserialize.assert_called_once_with(
                mock_connection_payload, app=rest_clients_impl._app
            )

    @pytest.mark.parametrize("newest_first", [True, False])
    @pytest.mark.parametrize("start_at", [None, "abc", 123])
    def test_fetch_my_guilds(self, rest_clients_impl, newest_first, start_at):
        with mock.patch.object(me._GuildPaginator, "__init__", return_value=None) as init:
            result = rest_clients_impl.fetch_my_guilds(newest_first=newest_first, start_at=start_at)
        assert isinstance(result, me._GuildPaginator)
        init.assert_called_once_with(
            newest_first=newest_first,
            first_item=start_at,
            app=rest_clients_impl._app,
            session=rest_clients_impl._session,
        )

    def test_fetch_my_guilds_default_directionality(self, rest_clients_impl):
        with mock.patch.object(me._GuildPaginator, "__init__", return_value=None) as init:
            result = rest_clients_impl.fetch_my_guilds()
        assert isinstance(result, me._GuildPaginator)
        init.assert_called_once_with(
            newest_first=False, first_item=None, app=rest_clients_impl._app, session=rest_clients_impl._session,
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
            channels.DMChannel.deserialize.assert_called_once_with(mock_dm_payload, app=rest_clients_impl._app)

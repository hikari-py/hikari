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
import datetime
import inspect

import mock
import pytest

from hikari import application
from hikari.models import bases
from hikari.models import channels
from hikari.models import emojis
from hikari.models import messages
from hikari.models import users
from hikari.net.rest import react
from hikari.net.rest import session
from tests.hikari import _helpers


@pytest.mark.parametrize(
    "emoji",
    [
        "\N{OK HAND SIGN}",
        emojis.UnicodeEmoji(name="\N{OK HAND SIGN}"),
        emojis.CustomEmoji(id=bases.Snowflake(9876), name="foof"),
    ],
    ids=lambda arg: str(arg),
)
class TestMemberPaginator:
    @pytest.fixture()
    def mock_session(self):
        return mock.MagicMock(spec_set=session.RESTSession)

    @pytest.fixture()
    def mock_app(self):
        return mock.MagicMock(spec_set=application.Application)

    @pytest.fixture()
    def user_cls(self):
        with mock.patch.object(users, "User") as user_cls:
            yield user_cls

    def test_init_no_start_bounds(self, mock_session, mock_app, emoji):
        message = mock.MagicMock(__int__=lambda _: 22)
        channel = mock.MagicMock(__int__=lambda _: 33)

        pag = react._ReactionPaginator(mock_app, channel, message, emoji, None, mock_session)
        assert pag._app is mock_app
        assert pag._first_id == "0"
        assert pag._message_id == "22"
        assert pag._session is mock_session

    @pytest.mark.parametrize(
        ["start_at", "expected"],
        [
            (None, "0"),
            (53, "53"),
            (bases.Unique(id=bases.Snowflake(22)), "22"),
            (bases.Snowflake(22), "22"),
            (datetime.datetime(2019, 1, 22, 18, 41, 15, 283000, tzinfo=datetime.timezone.utc), "537340989807788032"),
        ],
    )
    def test_init_with_start_bounds(self, mock_session, mock_app, start_at, expected, emoji):
        message = mock.MagicMock(__int__=lambda _: 22)
        channel = mock.MagicMock(__int__=lambda _: 33)

        pag = react._ReactionPaginator(mock_app, channel, message, emoji, start_at, mock_session)
        assert pag._first_id == expected
        assert pag._message_id == "22"
        assert pag._channel_id == "33"
        assert pag._app is mock_app
        assert pag._session is mock_session

    @pytest.mark.asyncio
    async def test_next_chunk_performs_correct_api_call(self, mock_session, mock_app, user_cls, emoji):
        message = mock.MagicMock(__int__=lambda _: 44)
        channel = mock.MagicMock(__int__=lambda _: 55)

        pag = react._ReactionPaginator(mock_app, channel, message, emoji, None, mock_session)
        pag._first_id = "123456"

        await pag._next_chunk()

        mock_session.get_reactions.assert_awaited_once_with(
            channel_id="55", message_id="44", emoji=getattr(emoji, "url_name", emoji), after="123456"
        )

    @pytest.mark.asyncio
    async def test_next_chunk_when_empty_returns_None(self, mock_session, mock_app, user_cls, emoji):
        mock_session.get_reactions = mock.AsyncMock(return_value=[])
        message = mock.MagicMock(__int__=lambda _: 66)
        channel = mock.MagicMock(__int__=lambda _: 77)

        pag = react._ReactionPaginator(mock_app, channel, message, emoji, None, mock_session)

        assert await pag._next_chunk() is None

    @pytest.mark.asyncio
    async def test_next_chunk_updates_first_id_to_last_item(self, mock_session, mock_app, user_cls, emoji):
        return_payload = [
            {"id": "1234", ...: ...},
            {"id": "3456", ...: ...},
            {"id": "3333", ...: ...},
            {"id": "512", ...: ...},
        ]

        mock_session.get_reactions = mock.AsyncMock(return_value=return_payload)

        message = mock.MagicMock(__int__=lambda _: 88)
        channel = mock.MagicMock(__int__=lambda _: 99)

        pag = react._ReactionPaginator(mock_app, channel, message, emoji, None, mock_session)

        await pag._next_chunk()

        assert pag._first_id == "512"

    @pytest.mark.asyncio
    async def test_next_chunk_deserializes_payload_in_generator_lazily(self, mock_session, mock_app, user_cls, emoji):
        message = mock.MagicMock(__int__=lambda _: 91210)
        channel = mock.MagicMock(__int__=lambda _: 8008135)

        pag = react._ReactionPaginator(mock_app, channel, message, emoji, None, mock_session)

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

        user_cls.deserialize = mock.MagicMock(side_effect=real_values)

        mock_session.get_reactions = mock.AsyncMock(return_value=return_payload)
        generator = await pag._next_chunk()

        assert inspect.isgenerator(generator), "expected genexp result"

        # No calls, this should be lazy to be more performant for non-100-divisable limit counts.
        user_cls.deserialize.assert_not_called()

        for i, input_payload in enumerate(return_payload):
            expected_value = real_values[i]
            assert next(generator) is expected_value
            user_cls.deserialize.assert_called_with(input_payload, app=mock_app)

        # Clear the generator result.
        # This doesn't test anything, but there is an issue with coverage not detecting generator
        # exit conditions properly. This fixes something that would otherwise be marked as
        # uncovered behaviour erroneously.
        # https://stackoverflow.com/questions/35317757/python-unittest-branch-coverage-seems-to-miss-executed-generator-in-zip
        with pytest.raises(StopIteration):
            next(generator)

        assert locals()["i"] == len(return_payload) - 1, "Not iterated correctly somehow"


class TestRESTReactionLogic:
    @pytest.fixture()
    def rest_reaction_logic_impl(self):
        mock_app = mock.MagicMock(application.Application)
        mock_low_level_restful_client = mock.MagicMock(session.RESTSession)

        class RESTReactionLogicImpl(react.RESTReactionComponent):
            def __init__(self):
                super().__init__(mock_app, mock_low_level_restful_client)

        return RESTReactionLogicImpl()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.CustomEmoji(name="blah", id=123, is_animated=False)])
    async def test_create_reaction(self, rest_reaction_logic_impl, channel, message, emoji):
        rest_reaction_logic_impl._session.create_reaction.return_value = ...
        assert await rest_reaction_logic_impl.add_reaction(channel=channel, message=message, emoji=emoji) is None
        rest_reaction_logic_impl._session.create_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.CustomEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_reaction_for_bot_user(self, rest_reaction_logic_impl, channel, message, emoji):
        rest_reaction_logic_impl._session.delete_own_reaction.return_value = ...
        assert await rest_reaction_logic_impl.remove_reaction(channel=channel, message=message, emoji=emoji) is None
        rest_reaction_logic_impl._session.delete_own_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("user", 96969696, users.User)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.CustomEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_reaction_for_other_user(self, rest_reaction_logic_impl, channel, message, emoji, user):
        rest_reaction_logic_impl._session.delete_user_reaction.return_value = ...
        assert (
            await rest_reaction_logic_impl.remove_reaction(channel=channel, message=message, emoji=emoji, user=user)
            is None
        )
        rest_reaction_logic_impl._session.delete_user_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123", user_id="96969696",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", [None, "blah:123", emojis.CustomEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_all_reactions(self, rest_reaction_logic_impl, channel, message, emoji):
        rest_reaction_logic_impl._session = mock.MagicMock(spec_set=session.RESTSession)
        assert (
            await rest_reaction_logic_impl.remove_all_reactions(channel=channel, message=message, emoji=emoji) is None
        )

        if emoji is None:
            rest_reaction_logic_impl._session.delete_all_reactions.assert_called_once_with(
                channel_id="213123", message_id="987654321",
            )
        else:
            rest_reaction_logic_impl._session.delete_all_reactions_for_emoji.assert_called_once_with(
                channel_id="213123", message_id="987654321", emoji=getattr(emoji, "url_name", emoji)
            )

    def test_fetch_reactors(self, rest_reaction_logic_impl):
        with mock.patch.object(react._ReactionPaginator, "__init__", return_value=None) as init:
            paginator = rest_reaction_logic_impl.fetch_reactors(
                channel=1234, message=bases.Snowflake("3456"), emoji="\N{OK HAND SIGN}", after=None
            )

            assert isinstance(paginator, react._ReactionPaginator)

        init.assert_called_once_with(
            channel=1234,
            message=bases.Snowflake("3456"),
            users_after=None,
            emoji="\N{OK HAND SIGN}",
            app=rest_reaction_logic_impl._app,
            session=rest_reaction_logic_impl._session,
        )

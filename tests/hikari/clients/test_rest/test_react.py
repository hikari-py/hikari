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

import mock
import pytest

from hikari import channels
from hikari import emojis
from hikari import messages
from hikari import users
from hikari.clients.rest import react
from hikari.internal import helpers
from hikari.net import rest
from tests.hikari import _helpers


class TestRESTReactionLogic:
    @pytest.fixture()
    def rest_reaction_logic_impl(self):
        mock_low_level_restful_client = mock.MagicMock(rest.REST)

        class RESTReactionLogicImpl(react.RESTReactionComponent):
            def __init__(self):
                super().__init__(mock_low_level_restful_client)

        return RESTReactionLogicImpl()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.UnknownEmoji(name="blah", id=123, is_animated=False)])
    async def test_create_reaction(self, rest_reaction_logic_impl, channel, message, emoji):
        rest_reaction_logic_impl._session.create_reaction.return_value = ...
        assert await rest_reaction_logic_impl.create_reaction(channel=channel, message=message, emoji=emoji) is None
        rest_reaction_logic_impl._session.create_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.UnknownEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_reaction(self, rest_reaction_logic_impl, channel, message, emoji):
        rest_reaction_logic_impl._session.delete_own_reaction.return_value = ...
        assert await rest_reaction_logic_impl.delete_reaction(channel=channel, message=message, emoji=emoji) is None
        rest_reaction_logic_impl._session.delete_own_reaction.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    async def test_delete_all_reactions(self, rest_reaction_logic_impl, channel, message):
        rest_reaction_logic_impl._session.delete_all_reactions.return_value = ...
        assert await rest_reaction_logic_impl.delete_all_reactions(channel=channel, message=message) is None
        rest_reaction_logic_impl._session.delete_all_reactions.assert_called_once_with(
            channel_id="213123", message_id="987654321",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 213123, channels.Channel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 987654321, messages.Message)
    @pytest.mark.parametrize("emoji", ["blah:123", emojis.UnknownEmoji(name="blah", id=123, is_animated=False)])
    async def test_delete_all_reactions_for_emoji(self, rest_reaction_logic_impl, channel, message, emoji):
        rest_reaction_logic_impl._session.delete_all_reactions_for_emoji.return_value = ...
        assert (
            await rest_reaction_logic_impl.delete_all_reactions_for_emoji(channel=channel, message=message, emoji=emoji)
            is None
        )
        rest_reaction_logic_impl._session.delete_all_reactions_for_emoji.assert_called_once_with(
            channel_id="213123", message_id="987654321", emoji="blah:123",
        )

    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.Channel)
    @pytest.mark.parametrize(
        "emoji", ["tutu1:456371206225002499", mock.MagicMock(emojis.GuildEmoji, url_name="tutu1:456371206225002499")]
    )
    @_helpers.parametrize_valid_id_formats_for_models("user", 140502780547694592, users.User)
    def test_fetch_reactors_after_with_optionals(self, rest_reaction_logic_impl, message, channel, emoji, user):
        mock_generator = mock.AsyncMock()
        with mock.patch.object(helpers, "pagination_handler", return_value=mock_generator):
            result = rest_reaction_logic_impl.fetch_reactors_after(channel, message, emoji, after=user, limit=47)
            assert result is mock_generator
            helpers.pagination_handler.assert_called_once_with(
                channel_id="123",
                message_id="432",
                emoji="tutu1:456371206225002499",
                deserializer=users.User.deserialize,
                direction="after",
                request=rest_reaction_logic_impl._session.get_reactions,
                reversing=False,
                start="140502780547694592",
                limit=47,
            )

    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.Channel)
    @pytest.mark.parametrize(
        "emoji", ["tutu1:456371206225002499", mock.MagicMock(emojis.GuildEmoji, url_name="tutu1:456371206225002499")]
    )
    def test_fetch_reactors_after_without_optionals(self, rest_reaction_logic_impl, message, channel, emoji):
        mock_generator = mock.AsyncMock()
        with mock.patch.object(helpers, "pagination_handler", return_value=mock_generator):
            assert rest_reaction_logic_impl.fetch_reactors_after(channel, message, emoji) is mock_generator
            helpers.pagination_handler.assert_called_once_with(
                channel_id="123",
                message_id="432",
                emoji="tutu1:456371206225002499",
                deserializer=users.User.deserialize,
                direction="after",
                request=rest_reaction_logic_impl._session.get_reactions,
                reversing=False,
                start="0",
                limit=None,
            )

    def test_fetch_reactors_after_with_datetime_object(self, rest_reaction_logic_impl):
        mock_generator = mock.AsyncMock()
        date = datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        with mock.patch.object(helpers, "pagination_handler", return_value=mock_generator):
            result = rest_reaction_logic_impl.fetch_reactors_after(123, 432, "tutu1:456371206225002499", after=date)
            assert result is mock_generator
            helpers.pagination_handler.assert_called_once_with(
                channel_id="123",
                message_id="432",
                emoji="tutu1:456371206225002499",
                deserializer=users.User.deserialize,
                direction="after",
                request=rest_reaction_logic_impl._session.get_reactions,
                reversing=False,
                start="537340988620800000",
                limit=None,
            )

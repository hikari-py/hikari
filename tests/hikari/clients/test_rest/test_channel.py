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
import inspect

import attr
import mock
import pytest

from hikari.models import bases
from hikari.models import channels
from hikari.models import embeds
from hikari.models import files
from hikari.models import guilds
from hikari.models import invites
from hikari.models import messages
from hikari.models import users
from hikari.models import webhooks
from hikari.components import application
from hikari.rest import channel
from hikari.internal import helpers
from hikari.rest import session
from tests.hikari import _helpers


@pytest.mark.asyncio
class TestMessagePaginator:
    @pytest.fixture
    def mock_session(self):
        return mock.MagicMock(spec_set=session.RESTSession)

    @pytest.fixture
    def mock_components(self):
        return mock.MagicMock(spec_set=application.Application)

    @pytest.fixture
    def message_cls(self):
        with mock.patch.object(messages, "Message") as message_cls:
            yield message_cls

    @pytest.mark.parametrize("direction", ["before", "after", "around"])
    def test_init_first_id_is_date(self, mock_session, mock_components, direction):
        date = datetime.datetime(2015, 11, 15, 23, 13, 46, 709000, tzinfo=datetime.timezone.utc)
        expected_id = 115590097100865536
        channel_id = 1234567
        pag = channel._MessagePaginator(channel_id, direction, date, mock_components, mock_session)
        assert pag._first_id == str(expected_id)
        assert pag._channel_id == str(channel_id)
        assert pag._direction == direction
        assert pag._session is mock_session
        assert pag._components is mock_components

    @pytest.mark.parametrize("direction", ["before", "after", "around"])
    def test_init_first_id_is_id(self, mock_session, mock_components, direction):
        expected_id = 115590097100865536
        channel_id = 1234567
        pag = channel._MessagePaginator(channel_id, direction, expected_id, mock_components, mock_session)
        assert pag._first_id == str(expected_id)
        assert pag._channel_id == str(channel_id)
        assert pag._direction == direction
        assert pag._session is mock_session
        assert pag._components is mock_components

    @pytest.mark.parametrize("direction", ["before", "after", "around"])
    async def test_next_chunk_makes_api_call(self, mock_session, mock_components, message_cls, direction):
        channel_obj = mock.MagicMock(__int__=lambda _: 55)

        mock_session.get_channel_messages = mock.AsyncMock(return_value=[])
        pag = channel._MessagePaginator(channel_obj, direction, "12345", mock_components, mock_session)
        pag._first_id = "12345"

        await pag._next_chunk()

        mock_session.get_channel_messages.assert_awaited_once_with(
            **{direction: "12345", "channel_id": "55", "limit": 100}
        )

    @pytest.mark.parametrize("direction", ["before", "after", "around"])
    async def test_next_chunk_empty_response_returns_None(self, mock_session, mock_components, message_cls, direction):
        channel_obj = mock.MagicMock(__int__=lambda _: 55)

        pag = channel._MessagePaginator(channel_obj, direction, "12345", mock_components, mock_session)
        pag._first_id = "12345"

        mock_session.get_channel_messages = mock.AsyncMock(return_value=[])

        assert await pag._next_chunk() is None

    @pytest.mark.parametrize(["direction", "expect_reverse"], [("before", False), ("after", True), ("around", False)])
    async def test_next_chunk_updates_first_id(
        self, mock_session, mock_components, message_cls, expect_reverse, direction
    ):
        return_payload = [
            {"id": "1234", ...: ...},
            {"id": "3456", ...: ...},
            {"id": "3333", ...: ...},
            {"id": "512", ...: ...},
        ]

        mock_session.get_channel_messages = mock.AsyncMock(return_value=return_payload)

        channel_obj = mock.MagicMock(__int__=lambda _: 99)

        pag = channel._MessagePaginator(channel_obj, direction, "12345", mock_components, mock_session)
        pag._first_id = "12345"

        await pag._next_chunk()

        assert pag._first_id == "1234" if expect_reverse else "512"

    @pytest.mark.parametrize(["direction", "expect_reverse"], [("before", False), ("after", True), ("around", False)])
    async def test_next_chunk_returns_generator(
        self, mock_session, mock_components, message_cls, expect_reverse, direction
    ):
        return_payload = [
            {"id": "1234", ...: ...},
            {"id": "3456", ...: ...},
            {"id": "3333", ...: ...},
            {"id": "512", ...: ...},
        ]

        @attr.s(auto_attribs=True)
        class DummyResponse:
            id: int

        real_values = [
            DummyResponse(1234),
            DummyResponse(3456),
            DummyResponse(3333),
            DummyResponse(512),
        ]

        if expect_reverse:
            real_values.reverse()

        assert len(real_values) == len(return_payload)

        message_cls.deserialize = mock.MagicMock(side_effect=real_values.copy())
        mock_session.get_channel_messages = mock.AsyncMock(return_value=return_payload)

        channel_obj = mock.MagicMock(__int__=lambda _: 99)

        pag = channel._MessagePaginator(channel_obj, direction, "12345", mock_components, mock_session)
        pag._first_id = "12345"

        generator = await pag._next_chunk()

        assert inspect.isgenerator(generator)

        for i, item in enumerate(generator, start=1):
            assert item == real_values.pop(0)

        assert locals()["i"] == 4, "Not iterated correctly somehow"
        assert not real_values

        # Clear the generator result.
        # This doesn't test anything, but there is an issue with coverage not detecting generator
        # exit conditions properly. This fixes something that would otherwise be marked as
        # uncovered behaviour erroneously.
        # https://stackoverflow.com/questions/35317757/python-unittest-branch-coverage-seems-to-miss-executed-generator-in-zip
        with pytest.raises(StopIteration):
            next(generator)


class TestRESTChannel:
    @pytest.fixture()
    def rest_channel_logic_impl(self):
        mock_components = mock.MagicMock(application.Application)
        mock_low_level_restful_client = mock.MagicMock(session.RESTSession)

        class RESTChannelLogicImpl(channel.RESTChannelComponent):
            def __init__(self):
                super().__init__(mock_components, mock_low_level_restful_client)

        return RESTChannelLogicImpl()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 1234, channels.PartialChannel)
    async def test_fetch_channel(self, rest_channel_logic_impl, channel):
        mock_payload = {"id": "49494994", "type": 3}
        mock_channel_obj = mock.MagicMock(channels.PartialChannel)
        rest_channel_logic_impl._session.get_channel.return_value = mock_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            assert await rest_channel_logic_impl.fetch_channel(channel) is mock_channel_obj
            rest_channel_logic_impl._session.get_channel.assert_called_once_with(channel_id="1234")
            channels.deserialize_channel.assert_called_once_with(
                mock_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("parent_channel", 115590097100865541, channels.PartialChannel)
    @pytest.mark.parametrize("rate_limit_per_user", [42, datetime.timedelta(seconds=42)])
    async def test_update_channel_with_optionals(
        self, rest_channel_logic_impl, channel, parent_channel, rate_limit_per_user
    ):
        mock_payload = {"name": "Qts", "type": 2}
        mock_channel_obj = mock.MagicMock(channels.PartialChannel)
        mock_overwrite_payload = {"type": "user", "id": 543543543}
        mock_overwrite_obj = mock.MagicMock(channels.PermissionOverwrite)
        mock_overwrite_obj.serialize = mock.MagicMock(return_value=mock_overwrite_payload)
        rest_channel_logic_impl._session.modify_channel.return_value = mock_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            result = await rest_channel_logic_impl.update_channel(
                channel=channel,
                name="ohNo",
                position=7,
                topic="camelsAreGreat",
                nsfw=True,
                bitrate=32000,
                user_limit=42,
                rate_limit_per_user=rate_limit_per_user,
                permission_overwrites=[mock_overwrite_obj],
                parent_category=parent_channel,
                reason="Get Nyaa'd.",
            )
            assert result is mock_channel_obj
            rest_channel_logic_impl._session.modify_channel.assert_called_once_with(
                channel_id="379953393319542784",
                name="ohNo",
                position=7,
                topic="camelsAreGreat",
                nsfw=True,
                rate_limit_per_user=42,
                bitrate=32000,
                user_limit=42,
                permission_overwrites=[mock_overwrite_payload],
                parent_id="115590097100865541",
                reason="Get Nyaa'd.",
            )
            mock_overwrite_obj.serialize.assert_called_once()
            channels.deserialize_channel.assert_called_once_with(
                mock_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PartialChannel)
    async def test_update_channel_without_optionals(
        self, rest_channel_logic_impl, channel,
    ):
        mock_payload = {"name": "Qts", "type": 2}
        mock_channel_obj = mock.MagicMock(channels.PartialChannel)
        rest_channel_logic_impl._session.modify_channel.return_value = mock_payload
        with mock.patch.object(channels, "deserialize_channel", return_value=mock_channel_obj):
            result = await rest_channel_logic_impl.update_channel(channel=channel,)
            assert result is mock_channel_obj
            rest_channel_logic_impl._session.modify_channel.assert_called_once_with(
                channel_id="379953393319542784",
                name=...,
                position=...,
                topic=...,
                nsfw=...,
                rate_limit_per_user=...,
                bitrate=...,
                user_limit=...,
                permission_overwrites=...,
                parent_id=...,
                reason=...,
            )
            channels.deserialize_channel.assert_called_once_with(
                mock_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 55555, channels.PartialChannel)
    async def test_delete_channel(self, rest_channel_logic_impl, channel):
        rest_channel_logic_impl._session.delete_close_channel.return_value = ...
        assert await rest_channel_logic_impl.delete_channel(channel) is None
        rest_channel_logic_impl._session.delete_close_channel.assert_called_once_with(channel_id="55555")

    @pytest.mark.parametrize(
        ("direction", "expected_direction", "first", "expected_first"),
        [
            [None, "before", None, bases.Snowflake.max()],
            ["before", "before", "1234", "1234"],
            ["before", "before", datetime.datetime(2007, 1, 6, 13), datetime.datetime(2007, 1, 6, 13)],
            ["after", "after", 1235, 1235],
            ["after", "after", datetime.datetime(2007, 11, 1, 15, 33, 33), datetime.datetime(2007, 11, 1, 15, 33, 33)],
            ["around", "around", "1234", "1234"],
            ["around", "around", datetime.datetime(2005, 12, 15), datetime.datetime(2005, 12, 15)],
        ],
    )
    def test_fetch_messages(self, rest_channel_logic_impl, direction, expected_direction, first, expected_first):
        kwargs = {direction: first} if direction is not None else {}
        mock_channel = mock.MagicMock(__int__=90213)

        with mock.patch.object(channel._MessagePaginator, "__init__", return_value=None) as init:
            result = rest_channel_logic_impl.fetch_messages(mock_channel, **kwargs)

        assert isinstance(result, channel._MessagePaginator)
        init.assert_called_once_with(
            channel=mock_channel,
            direction=expected_direction,
            first=expected_first,
            components=rest_channel_logic_impl._components,
            session=rest_channel_logic_impl._session,
        )

    @_helpers.assert_raises(type_=TypeError)
    @pytest.mark.parametrize(
        "directions",
        (
            {"after": 123, "before": 324},
            {"after": 312, "around": 444},
            {"before": 444, "around": 1010},
            {"around": 123, "before": 432, "after": 19929},
        ),
    )
    def test_fetch_messages_raises_type_error_on_multiple_directions(self, rest_channel_logic_impl, directions):
        rest_channel_logic_impl.fetch_messages(123123, **directions)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 55555, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 565656, messages.Message)
    async def test_fetch_message(self, rest_channel_logic_impl, channel, message):
        mock_payload = {"id": "9409404", "content": "I AM A MESSAGE!"}
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_channel_logic_impl._session.get_channel_message.return_value = mock_payload
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_channel_logic_impl.fetch_message(channel=channel, message=message) is mock_message_obj
            rest_channel_logic_impl._session.get_channel_message.assert_called_once_with(
                channel_id="55555", message_id="565656",
            )
            messages.Message.deserialize.assert_called_once_with(
                mock_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 694463529998352394, channels.PartialChannel)
    async def test_create_message_with_optionals(self, rest_channel_logic_impl, channel):
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_message_payload = {"id": "2929292992", "content": "222922"}
        rest_channel_logic_impl._session.create_message.return_value = mock_message_payload
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        mock_embed_payload = {"description": "424242"}
        mock_file_obj = mock.MagicMock(files.BaseStream)
        mock_file_obj2 = mock.MagicMock(files.BaseStream)
        mock_embed_obj = mock.MagicMock(embeds.Embed)
        mock_embed_obj.assets_to_upload = [mock_file_obj2]
        mock_embed_obj.serialize = mock.MagicMock(return_value=mock_embed_payload)
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload)
        )
        stack.enter_context(mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj))
        with stack:
            result = await rest_channel_logic_impl.create_message(
                channel,
                content="A CONTENT",
                nonce="69696969696969",
                tts=True,
                files=[mock_file_obj],
                embed=mock_embed_obj,
                mentions_everyone=False,
                user_mentions=False,
                role_mentions=False,
            )
            assert result is mock_message_obj
            messages.Message.deserialize.assert_called_once_with(
                mock_message_payload, components=rest_channel_logic_impl._components
            )
            helpers.generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=False, user_mentions=False, role_mentions=False
            )
        rest_channel_logic_impl._session.create_message.assert_called_once_with(
            channel_id="694463529998352394",
            content="A CONTENT",
            nonce="69696969696969",
            tts=True,
            files=[mock_file_obj, mock_file_obj2],
            embed=mock_embed_payload,
            allowed_mentions=mock_allowed_mentions_payload,
        )
        mock_embed_obj.serialize.assert_called_once()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 694463529998352394, channels.PartialChannel)
    async def test_create_message_without_optionals(self, rest_channel_logic_impl, channel):
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_message_payload = {"id": "2929292992", "content": "222922"}
        rest_channel_logic_impl._session.create_message.return_value = mock_message_payload
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload)
        )
        stack.enter_context(mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj))
        with stack:
            assert await rest_channel_logic_impl.create_message(channel) is mock_message_obj
            messages.Message.deserialize.assert_called_once_with(
                mock_message_payload, components=rest_channel_logic_impl._components
            )
            helpers.generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=True, user_mentions=True, role_mentions=True
            )
        rest_channel_logic_impl._session.create_message.assert_called_once_with(
            channel_id="694463529998352394",
            content=...,
            nonce=...,
            tts=...,
            files=...,
            embed=...,
            allowed_mentions=mock_allowed_mentions_payload,
        )

    @pytest.mark.asyncio
    async def test_safe_create_message_without_optionals(self, rest_channel_logic_impl):
        channel = mock.MagicMock(channels.PartialChannel)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_channel_logic_impl.create_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_channel_logic_impl.safe_create_message(channel,)
        assert result is mock_message_obj
        rest_channel_logic_impl.create_message.assert_called_once_with(
            channel=channel,
            content=...,
            nonce=...,
            tts=...,
            files=...,
            embed=...,
            mentions_everyone=False,
            user_mentions=False,
            role_mentions=False,
        )

    @pytest.mark.asyncio
    async def test_safe_create_message_with_optionals(self, rest_channel_logic_impl):
        channel = mock.MagicMock(channels.PartialChannel)
        mock_embed_obj = mock.MagicMock(embeds.Embed)
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_file_obj = mock.MagicMock(files.BaseStream)
        mock_embed_obj = mock.MagicMock(embeds.Embed)
        rest_channel_logic_impl.create_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_channel_logic_impl.safe_create_message(
            channel=channel,
            content="A CONTENT",
            nonce="69696969696969",
            tts=True,
            files=[mock_file_obj],
            embed=mock_embed_obj,
            mentions_everyone=True,
            user_mentions=True,
            role_mentions=True,
        )
        assert result is mock_message_obj
        rest_channel_logic_impl.create_message.assert_called_once_with(
            channel=channel,
            content="A CONTENT",
            nonce="69696969696969",
            tts=True,
            files=[mock_file_obj],
            embed=mock_embed_obj,
            mentions_everyone=True,
            user_mentions=True,
            role_mentions=True,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.PartialChannel)
    async def test_update_message_with_optionals(self, rest_channel_logic_impl, message, channel):
        mock_payload = {"id": "4242", "content": "I HAVE BEEN UPDATED!"}
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_embed_payload = {"description": "blahblah"}
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_embed.serialize = mock.MagicMock(return_value=mock_embed_payload)
        mock_allowed_mentions_payload = {"parse": [], "users": ["123"]}
        rest_channel_logic_impl._session.edit_message.return_value = mock_payload
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload)
        )
        stack.enter_context(mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj))
        with stack:
            result = await rest_channel_logic_impl.update_message(
                message=message,
                channel=channel,
                content="C O N T E N T",
                embed=mock_embed,
                flags=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
                mentions_everyone=False,
                role_mentions=False,
                user_mentions=[123123123],
            )
            assert result is mock_message_obj
            rest_channel_logic_impl._session.edit_message.assert_called_once_with(
                channel_id="123",
                message_id="432",
                content="C O N T E N T",
                embed=mock_embed_payload,
                flags=6,
                allowed_mentions=mock_allowed_mentions_payload,
            )
            mock_embed.serialize.assert_called_once()
            messages.Message.deserialize.assert_called_once_with(
                mock_payload, components=rest_channel_logic_impl._components
            )
            helpers.generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=False, role_mentions=False, user_mentions=[123123123]
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("message", 432, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123, channels.PartialChannel)
    async def test_update_message_without_optionals(self, rest_channel_logic_impl, message, channel):
        mock_payload = {"id": "4242", "content": "I HAVE BEEN UPDATED!"}
        mock_message_obj = mock.MagicMock(messages.Message)
        mock_allowed_mentions_payload = {"parse": ["everyone", "users", "roles"]}
        rest_channel_logic_impl._session.edit_message.return_value = mock_payload
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(helpers, "generate_allowed_mentions", return_value=mock_allowed_mentions_payload)
        )
        stack.enter_context(mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj))
        with stack:
            assert await rest_channel_logic_impl.update_message(message=message, channel=channel) is mock_message_obj
            rest_channel_logic_impl._session.edit_message.assert_called_once_with(
                channel_id="123",
                message_id="432",
                content=...,
                embed=...,
                flags=...,
                allowed_mentions=mock_allowed_mentions_payload,
            )
            messages.Message.deserialize.assert_called_once_with(
                mock_payload, components=rest_channel_logic_impl._components
            )
            helpers.generate_allowed_mentions.assert_called_once_with(
                mentions_everyone=True, user_mentions=True, role_mentions=True
            )

    @pytest.mark.asyncio
    async def test_safe_update_message_without_optionals(self, rest_channel_logic_impl):
        message = mock.MagicMock(messages.Message)
        channel = mock.MagicMock(channels.PartialChannel)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_channel_logic_impl.update_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_channel_logic_impl.safe_update_message(message=message, channel=channel,)
        assert result is mock_message_obj
        rest_channel_logic_impl.update_message.assert_called_once_with(
            message=message,
            channel=channel,
            content=...,
            embed=...,
            flags=...,
            mentions_everyone=False,
            role_mentions=False,
            user_mentions=False,
        )

    @pytest.mark.asyncio
    async def test_safe_update_message_with_optionals(self, rest_channel_logic_impl):
        message = mock.MagicMock(messages.Message)
        channel = mock.MagicMock(channels.PartialChannel)
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_message_obj = mock.MagicMock(messages.Message)
        rest_channel_logic_impl.update_message = mock.AsyncMock(return_value=mock_message_obj)
        result = await rest_channel_logic_impl.safe_update_message(
            message=message,
            channel=channel,
            content="C O N T E N T",
            embed=mock_embed,
            flags=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
            mentions_everyone=True,
            role_mentions=True,
            user_mentions=True,
        )
        assert result is mock_message_obj
        rest_channel_logic_impl.update_message.assert_called_once_with(
            message=message,
            channel=channel,
            content="C O N T E N T",
            embed=mock_embed,
            flags=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
            mentions_everyone=True,
            role_mentions=True,
            user_mentions=True,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 115590097100865541, messages.Message)
    async def test_delete_messages_singular(self, rest_channel_logic_impl, channel, message):
        rest_channel_logic_impl._session.delete_message.return_value = ...
        assert await rest_channel_logic_impl.delete_messages(channel, message) is None
        rest_channel_logic_impl._session.delete_message.assert_called_once_with(
            channel_id="379953393319542784", message_id="115590097100865541",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 115590097100865541, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 115590097100865541, messages.Message)
    async def test_delete_messages_singular_after_duplicate_removal(
        self, rest_channel_logic_impl, channel, message, additional_message
    ):
        rest_channel_logic_impl._session.delete_message.return_value = ...
        assert await rest_channel_logic_impl.delete_messages(channel, message, additional_message) is None
        rest_channel_logic_impl._session.delete_message.assert_called_once_with(
            channel_id="379953393319542784", message_id="115590097100865541",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 115590097100865541, messages.Message)
    @_helpers.parametrize_valid_id_formats_for_models("additional_message", 572144340277919754, messages.Message)
    async def test_delete_messages_bulk_removes_duplicates(
        self, rest_channel_logic_impl, channel, message, additional_message
    ):
        rest_channel_logic_impl._session.bulk_delete_messages.return_value = ...
        assert (
            await rest_channel_logic_impl.delete_messages(channel, message, additional_message, 115590097100865541)
            is None
        )
        rest_channel_logic_impl._session.bulk_delete_messages.assert_called_once_with(
            channel_id="379953393319542784", messages=["115590097100865541", "572144340277919754"],
        )
        rest_channel_logic_impl._session.delete_message.assert_not_called()

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=ValueError)
    async def test_delete_messages_raises_value_error_on_over_100_messages(self, rest_channel_logic_impl):
        rest_channel_logic_impl._session.bulk_delete_messages.return_value = ...
        assert await rest_channel_logic_impl.delete_messages(123123, *list(range(0, 111))) is None

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 4123123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 9999, channels.PermissionOverwrite)
    async def test_update_channel_overwrite_with_optionals(self, rest_channel_logic_impl, channel, overwrite):
        rest_channel_logic_impl._session.edit_channel_permissions.return_value = ...
        result = await rest_channel_logic_impl.update_channel_overwrite(
            channel=channel,
            overwrite=overwrite,
            target_type="member",
            allow=messages.MessageFlag.IS_CROSSPOST | messages.MessageFlag.SUPPRESS_EMBEDS,
            deny=21,
            reason="get Nyaa'd",
        )
        assert result is None
        rest_channel_logic_impl._session.edit_channel_permissions.assert_called_once_with(
            channel_id="4123123", overwrite_id="9999", type_="member", allow=6, deny=21, reason="get Nyaa'd",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 4123123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 9999, channels.PermissionOverwrite)
    async def test_update_channel_overwrite_without_optionals(self, rest_channel_logic_impl, channel, overwrite):
        rest_channel_logic_impl._session.edit_channel_permissions.return_value = ...
        result = await rest_channel_logic_impl.update_channel_overwrite(
            channel=channel, overwrite=overwrite, target_type="member"
        )
        assert result is None
        rest_channel_logic_impl._session.edit_channel_permissions.assert_called_once_with(
            channel_id="4123123", overwrite_id="9999", type_="member", allow=..., deny=..., reason=...,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "target",
        [
            mock.MagicMock(guilds.GuildRole, id=bases.Snowflake(9999), __int__=guilds.GuildRole.__int__),
            mock.MagicMock(users.User, id=bases.Snowflake(9999), __int__=users.User.__int__),
        ],
    )
    async def test_update_channel_overwrite_with_alternative_target_object(self, rest_channel_logic_impl, target):
        rest_channel_logic_impl._session.edit_channel_permissions.return_value = ...
        result = await rest_channel_logic_impl.update_channel_overwrite(
            channel=4123123, overwrite=target, target_type="member"
        )
        assert result is None
        rest_channel_logic_impl._session.edit_channel_permissions.assert_called_once_with(
            channel_id="4123123", overwrite_id="9999", type_="member", allow=..., deny=..., reason=...,
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.PartialChannel)
    async def test_fetch_invites_for_channel(self, rest_channel_logic_impl, channel):
        mock_invite_payload = {"code": "ogogogogogogogo", "guild_id": "123123123"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_channel_logic_impl._session.get_channel_invites.return_value = [mock_invite_payload]
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            assert await rest_channel_logic_impl.fetch_invites_for_channel(channel=channel) == [mock_invite_obj]
            rest_channel_logic_impl._session.get_channel_invites.assert_called_once_with(channel_id="123123123")
            invites.InviteWithMetadata.deserialize.assert_called_once_with(
                mock_invite_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 234123, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("user", 333333, users.User)
    @pytest.mark.parametrize("max_age", [4444, datetime.timedelta(seconds=4444)])
    async def test_create_invite_for_channel_with_optionals(self, rest_channel_logic_impl, channel, user, max_age):
        mock_invite_payload = {"code": "ogogogogogogogo", "guild_id": "123123123"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_channel_logic_impl._session.create_channel_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            result = await rest_channel_logic_impl.create_invite_for_channel(
                channel,
                max_age=max_age,
                max_uses=444,
                temporary=True,
                unique=False,
                target_user=user,
                target_user_type=invites.TargetUserType.STREAM,
                reason="Hello there.",
            )
            assert result is mock_invite_obj
            rest_channel_logic_impl._session.create_channel_invite.assert_called_once_with(
                channel_id="234123",
                max_age=4444,
                max_uses=444,
                temporary=True,
                unique=False,
                target_user="333333",
                target_user_type=1,
                reason="Hello there.",
            )
            invites.InviteWithMetadata.deserialize.assert_called_once_with(
                mock_invite_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 234123, channels.PartialChannel)
    async def test_create_invite_for_channel_without_optionals(self, rest_channel_logic_impl, channel):
        mock_invite_payload = {"code": "ogogogogogogogo", "guild_id": "123123123"}
        mock_invite_obj = mock.MagicMock(invites.InviteWithMetadata)
        rest_channel_logic_impl._session.create_channel_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.InviteWithMetadata, "deserialize", return_value=mock_invite_obj):
            assert await rest_channel_logic_impl.create_invite_for_channel(channel) is mock_invite_obj
            rest_channel_logic_impl._session.create_channel_invite.assert_called_once_with(
                channel_id="234123",
                max_age=...,
                max_uses=...,
                temporary=...,
                unique=...,
                target_user=...,
                target_user_type=...,
                reason=...,
            )
            invites.InviteWithMetadata.deserialize.assert_called_once_with(
                mock_invite_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("overwrite", 123123123, channels.PermissionOverwrite)
    async def test_delete_channel_overwrite(self, rest_channel_logic_impl, channel, overwrite):
        rest_channel_logic_impl._session.delete_channel_permission.return_value = ...
        assert await rest_channel_logic_impl.delete_channel_overwrite(channel=channel, overwrite=overwrite) is None
        rest_channel_logic_impl._session.delete_channel_permission.assert_called_once_with(
            channel_id="379953393319542784", overwrite_id="123123123",
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "target",
        [
            mock.MagicMock(guilds.GuildRole, id=bases.Snowflake(123123123), __int__=guilds.GuildRole.__int__),
            mock.MagicMock(users.User, id=bases.Snowflake(123123123), __int__=users.User.__int__),
        ],
    )
    async def test_delete_channel_overwrite_with_alternative_target_objects(self, rest_channel_logic_impl, target):
        rest_channel_logic_impl._session.delete_channel_permission.return_value = ...
        assert (
            await rest_channel_logic_impl.delete_channel_overwrite(channel=379953393319542784, overwrite=target) is None
        )
        rest_channel_logic_impl._session.delete_channel_permission.assert_called_once_with(
            channel_id="379953393319542784", overwrite_id="123123123",
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 379953393319542784, channels.PermissionOverwrite)
    async def test_trigger_typing(self, rest_channel_logic_impl, channel):
        rest_channel_logic_impl._session.trigger_typing_indicator.return_value = ...
        assert await rest_channel_logic_impl.trigger_typing(channel) is None
        rest_channel_logic_impl._session.trigger_typing_indicator.assert_called_once_with(
            channel_id="379953393319542784"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 123123123, channels.PartialChannel)
    async def test_fetch_pins(self, rest_channel_logic_impl, channel):
        mock_message_payload = {"id": "21232", "content": "CONTENT"}
        mock_message_obj = mock.MagicMock(messages.Message, id=21232)
        rest_channel_logic_impl._session.get_pinned_messages.return_value = [mock_message_payload]
        with mock.patch.object(messages.Message, "deserialize", return_value=mock_message_obj):
            assert await rest_channel_logic_impl.fetch_pins(channel) == {21232: mock_message_obj}
            rest_channel_logic_impl._session.get_pinned_messages.assert_called_once_with(channel_id="123123123")
            messages.Message.deserialize.assert_called_once_with(
                mock_message_payload, components=rest_channel_logic_impl._components
            )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 292929, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 123123, messages.Message)
    async def test_pin_message(self, rest_channel_logic_impl, channel, message):
        rest_channel_logic_impl._session.add_pinned_channel_message.return_value = ...
        assert await rest_channel_logic_impl.pin_message(channel, message) is None
        rest_channel_logic_impl._session.add_pinned_channel_message.assert_called_once_with(
            channel_id="292929", message_id="123123"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 292929, channels.PartialChannel)
    @_helpers.parametrize_valid_id_formats_for_models("message", 123123, messages.Message)
    async def test_unpin_message(self, rest_channel_logic_impl, channel, message):
        rest_channel_logic_impl._session.delete_pinned_channel_message.return_value = ...
        assert await rest_channel_logic_impl.unpin_message(channel, message) is None
        rest_channel_logic_impl._session.delete_pinned_channel_message.assert_called_once_with(
            channel_id="292929", message_id="123123"
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.PartialChannel)
    async def test_create_webhook_with_optionals(self, rest_channel_logic_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_channel_logic_impl._session.create_webhook.return_value = mock_webhook_payload
        mock_image_data = mock.MagicMock(bytes)
        mock_image_obj = mock.MagicMock(files.BaseStream)
        mock_image_obj.read = mock.AsyncMock(return_value=mock_image_data)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj))
        with stack:
            result = await rest_channel_logic_impl.create_webhook(
                channel=channel, name="aWebhook", avatar=mock_image_obj, reason="And a webhook is born."
            )
            assert result is mock_webhook_obj
            mock_image_obj.read.assert_awaited_once()
            webhooks.Webhook.deserialize.assert_called_once_with(
                mock_webhook_payload, components=rest_channel_logic_impl._components
            )
        rest_channel_logic_impl._session.create_webhook.assert_called_once_with(
            channel_id="115590097100865541", name="aWebhook", avatar=mock_image_data, reason="And a webhook is born."
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.PartialChannel)
    async def test_create_webhook_without_optionals(self, rest_channel_logic_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_channel_logic_impl._session.create_webhook.return_value = mock_webhook_payload
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_channel_logic_impl.create_webhook(channel=channel, name="aWebhook") is mock_webhook_obj
            webhooks.Webhook.deserialize.assert_called_once_with(
                mock_webhook_payload, components=rest_channel_logic_impl._components
            )
        rest_channel_logic_impl._session.create_webhook.assert_called_once_with(
            channel_id="115590097100865541", name="aWebhook", avatar=..., reason=...
        )

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 115590097100865541, channels.GuildChannel)
    async def test_fetch_channel_webhooks(self, rest_channel_logic_impl, channel):
        mock_webhook_payload = {"id": "29292929", "channel_id": "2292992"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook)
        rest_channel_logic_impl._session.get_channel_webhooks.return_value = [mock_webhook_payload]
        with mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj):
            assert await rest_channel_logic_impl.fetch_channel_webhooks(channel) == [mock_webhook_obj]
            rest_channel_logic_impl._session.get_channel_webhooks.assert_called_once_with(
                channel_id="115590097100865541"
            )
            webhooks.Webhook.deserialize.assert_called_once_with(
                mock_webhook_payload, components=rest_channel_logic_impl._components
            )

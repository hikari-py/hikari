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

import typing

import mock
import pytest

from hikari import channels
from hikari import commands
from hikari import components
from hikari import emojis
from hikari import files
from hikari import locales
from hikari import messages
from hikari import permissions
from hikari import snowflakes
from hikari import undefined
from hikari.api import special_endpoints as special_endpoints_api
from hikari.impl import special_endpoints
from hikari.interactions import base_interactions
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


class TestTypingIndicator:
    @pytest.fixture()
    def typing_indicator(self):
        return hikari_test_helpers.mock_class_namespace(special_endpoints.TypingIndicator, init_=False)

    def test___enter__(self, typing_indicator):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            typing_indicator().__enter__()

    def test___exit__(self, typing_indicator):
        try:
            typing_indicator().__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)


class TestOwnGuildIterator:
    @pytest.mark.asyncio()
    async def test_aiter(self):
        mock_payload_1 = {"id": "123321123123"}
        mock_payload_2 = {"id": "123321123666"}
        mock_payload_3 = {"id": "123321124123"}
        mock_payload_4 = {"id": "123321124567"}
        mock_payload_5 = {"id": "12332112432234"}
        mock_result_1 = mock.Mock()
        mock_result_2 = mock.Mock()
        mock_result_3 = mock.Mock()
        mock_result_4 = mock.Mock()
        mock_result_5 = mock.Mock()
        expected_route = routes.GET_MY_GUILDS.compile()
        mock_entity_factory = mock.Mock()
        mock_entity_factory.deserialize_own_guild.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
            mock_result_5,
        ]
        mock_request = mock.AsyncMock(
            side_effect=[[mock_payload_1, mock_payload_2, mock_payload_3], [mock_payload_4, mock_payload_5], []]
        )
        iterator = special_endpoints.OwnGuildIterator(mock_entity_factory, mock_request, False, first_id="123321")

        result = await iterator

        assert result == [mock_result_1, mock_result_2, mock_result_3, mock_result_4, mock_result_5]
        mock_entity_factory.deserialize_own_guild.assert_has_calls(
            [
                mock.call(mock_payload_1),
                mock.call(mock_payload_2),
                mock.call(mock_payload_3),
                mock.call(mock_payload_4),
                mock.call(mock_payload_5),
            ]
        )
        mock_request.assert_has_awaits(
            [
                mock.call(compiled_route=expected_route, query={"after": "123321", "with_counts": "true"}),
                mock.call(compiled_route=expected_route, query={"after": "123321124123", "with_counts": "true"}),
                mock.call(compiled_route=expected_route, query={"after": "12332112432234", "with_counts": "true"}),
            ]
        )

    @pytest.mark.asyncio()
    async def test_aiter_when_newest_first(self):
        mock_payload_1 = {"id": "1213321123123"}
        mock_payload_2 = {"id": "1213321123666"}
        mock_payload_3 = {"id": "1213321124123"}
        mock_payload_4 = {"id": "1213321124567"}
        mock_payload_5 = {"id": "121332112432234"}
        mock_result_1 = mock.Mock()
        mock_result_2 = mock.Mock()
        mock_result_3 = mock.Mock()
        mock_result_4 = mock.Mock()
        mock_result_5 = mock.Mock()
        expected_route = routes.GET_MY_GUILDS.compile()
        mock_entity_factory = mock.Mock()
        mock_entity_factory.deserialize_own_guild.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
            mock_result_5,
        ]
        mock_request = mock.AsyncMock(
            side_effect=[[mock_payload_3, mock_payload_4, mock_payload_5], [mock_payload_1, mock_payload_2], []]
        )
        iterator = special_endpoints.OwnGuildIterator(
            mock_entity_factory, mock_request, True, first_id="55555555555555555"
        )

        result = await iterator

        assert result == [mock_result_1, mock_result_2, mock_result_3, mock_result_4, mock_result_5]
        mock_entity_factory.deserialize_own_guild.assert_has_calls(
            [
                mock.call(mock_payload_5),
                mock.call(mock_payload_4),
                mock.call(mock_payload_3),
                mock.call(mock_payload_2),
                mock.call(mock_payload_1),
            ]
        )
        mock_request.assert_has_awaits(
            [
                mock.call(compiled_route=expected_route, query={"before": "55555555555555555", "with_counts": "true"}),
                mock.call(compiled_route=expected_route, query={"before": "1213321124123", "with_counts": "true"}),
                mock.call(compiled_route=expected_route, query={"before": "1213321123123", "with_counts": "true"}),
            ]
        )

    @pytest.mark.parametrize("newest_first", [True, False])
    @pytest.mark.asyncio()
    async def test_aiter_when_empty_chunk(self, newest_first: bool):
        expected_route = routes.GET_MY_GUILDS.compile()
        mock_entity_factory = mock.Mock()
        mock_request = mock.AsyncMock(return_value=[])
        iterator = special_endpoints.OwnGuildIterator(
            mock_entity_factory, mock_request, newest_first, first_id="123321"
        )

        result = await iterator

        assert result == []
        mock_entity_factory.deserialize_own_guild.assert_not_called()
        order_key = "before" if newest_first else "after"
        query = {order_key: "123321", "with_counts": "true"}
        mock_request.assert_awaited_once_with(compiled_route=expected_route, query=query)


class TestGuildBanIterator:
    @pytest.mark.asyncio()
    async def test_aiter(self):
        expected_route = routes.GET_GUILD_BANS.compile(guild=10000)
        mock_entity_factory = mock.Mock()
        mock_payload_1 = {"user": {"id": "45234"}}
        mock_payload_2 = {"user": {"id": "452745"}}
        mock_payload_3 = {"user": {"id": "45237656"}}
        mock_payload_4 = {"user": {"id": "452345666"}}
        mock_payload_5 = {"user": {"id": "4523456744"}}
        mock_result_1 = mock.Mock()
        mock_result_2 = mock.Mock()
        mock_result_3 = mock.Mock()
        mock_result_4 = mock.Mock()
        mock_result_5 = mock.Mock()
        mock_entity_factory.deserialize_guild_member_ban.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
            mock_result_5,
        ]
        mock_request = mock.AsyncMock(
            side_effect=[[mock_payload_1, mock_payload_2, mock_payload_3], [mock_payload_4, mock_payload_5], []]
        )
        iterator = special_endpoints.GuildBanIterator(
            entity_factory=mock_entity_factory, request_call=mock_request, guild=10000, newest_first=False, first_id="0"
        )

        result = await iterator

        assert result == [mock_result_1, mock_result_2, mock_result_3, mock_result_4, mock_result_5]
        mock_entity_factory.deserialize_guild_member_ban.assert_has_calls(
            [
                mock.call(mock_payload_1),
                mock.call(mock_payload_2),
                mock.call(mock_payload_3),
                mock.call(mock_payload_4),
                mock.call(mock_payload_5),
            ]
        )
        mock_request.assert_has_awaits(
            [
                mock.call(compiled_route=expected_route, query={"after": "0", "limit": "1000"}),
                mock.call(compiled_route=expected_route, query={"after": "45237656", "limit": "1000"}),
                mock.call(compiled_route=expected_route, query={"after": "4523456744", "limit": "1000"}),
            ]
        )

    @pytest.mark.asyncio()
    async def test_aiter_when_newest_first(self):
        expected_route = routes.GET_GUILD_BANS.compile(guild=10000)
        mock_entity_factory = mock.Mock()
        mock_payload_1 = {"user": {"id": "432234"}}
        mock_payload_2 = {"user": {"id": "1233211"}}
        mock_payload_3 = {"user": {"id": "12332112"}}
        mock_payload_4 = {"user": {"id": "1233"}}
        mock_payload_5 = {"user": {"id": "54334"}}
        mock_result_1 = mock.Mock()
        mock_result_2 = mock.Mock()
        mock_result_3 = mock.Mock()
        mock_result_4 = mock.Mock()
        mock_result_5 = mock.Mock()
        mock_entity_factory.deserialize_guild_member_ban.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
            mock_result_5,
        ]
        mock_request = mock.AsyncMock(
            side_effect=[[mock_payload_1, mock_payload_2, mock_payload_3], [mock_payload_4, mock_payload_5], []]
        )
        iterator = special_endpoints.GuildBanIterator(
            entity_factory=mock_entity_factory,
            request_call=mock_request,
            guild=10000,
            newest_first=True,
            first_id="321123321",
        )

        result = await iterator

        assert result == [mock_result_1, mock_result_2, mock_result_3, mock_result_4, mock_result_5]
        mock_entity_factory.deserialize_guild_member_ban.assert_has_calls(
            [
                mock.call(mock_payload_3),
                mock.call(mock_payload_2),
                mock.call(mock_payload_1),
                mock.call(mock_payload_5),
                mock.call(mock_payload_4),
            ]
        )
        mock_request.assert_has_awaits(
            [
                mock.call(compiled_route=expected_route, query={"before": "321123321", "limit": "1000"}),
                mock.call(compiled_route=expected_route, query={"before": "432234", "limit": "1000"}),
                mock.call(compiled_route=expected_route, query={"before": "1233", "limit": "1000"}),
            ]
        )

    @pytest.mark.parametrize("newest_first", [True, False])
    @pytest.mark.asyncio()
    async def test_aiter_when_empty_chunk(self, newest_first: bool):
        expected_route = routes.GET_GUILD_BANS.compile(guild=10000)
        mock_entity_factory = mock.Mock()
        mock_request = mock.AsyncMock(return_value=[])
        iterator = special_endpoints.GuildBanIterator(
            entity_factory=mock_entity_factory,
            request_call=mock_request,
            guild=10000,
            newest_first=newest_first,
            first_id="54234123123",
        )

        result = await iterator

        assert result == []
        mock_entity_factory.deserialize_guild_member_ban.assert_not_called()
        query = {"before" if newest_first else "after": "54234123123", "limit": "1000"}
        mock_request.assert_awaited_once_with(compiled_route=expected_route, query=query)


class TestScheduledEventUserIterator:
    @pytest.mark.asyncio()
    async def test_aiter(self):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENT_USERS.compile(guild=54123, scheduled_event=564123)
        mock_entity_factory = mock.Mock()
        mock_payload_1 = {"user": {"id": "45234"}}
        mock_payload_2 = {"user": {"id": "452745"}}
        mock_payload_3 = {"user": {"id": "45237656"}}
        mock_payload_4 = {"user": {"id": "452345666"}}
        mock_payload_5 = {"user": {"id": "4523456744"}}
        mock_result_1 = mock.Mock()
        mock_result_2 = mock.Mock()
        mock_result_3 = mock.Mock()
        mock_result_4 = mock.Mock()
        mock_result_5 = mock.Mock()
        mock_entity_factory.deserialize_scheduled_event_user.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
            mock_result_5,
        ]
        mock_request = mock.AsyncMock(
            side_effect=[[mock_payload_1, mock_payload_2, mock_payload_3], [mock_payload_4, mock_payload_5], []]
        )
        iterator = special_endpoints.ScheduledEventUserIterator(
            entity_factory=mock_entity_factory,
            request_call=mock_request,
            newest_first=False,
            first_id="0",
            guild=54123,
            event=564123,
        )

        result = await iterator

        assert result == [mock_result_1, mock_result_2, mock_result_3, mock_result_4, mock_result_5]
        mock_entity_factory.deserialize_scheduled_event_user.assert_has_calls(
            [
                mock.call(mock_payload_1, guild_id=54123),
                mock.call(mock_payload_2, guild_id=54123),
                mock.call(mock_payload_3, guild_id=54123),
                mock.call(mock_payload_4, guild_id=54123),
                mock.call(mock_payload_5, guild_id=54123),
            ]
        )
        mock_request.assert_has_awaits(
            [
                mock.call(compiled_route=expected_route, query={"limit": "100", "with_member": "true", "after": "0"}),
                mock.call(
                    compiled_route=expected_route, query={"limit": "100", "with_member": "true", "after": "45237656"}
                ),
                mock.call(
                    compiled_route=expected_route, query={"limit": "100", "with_member": "true", "after": "4523456744"}
                ),
            ]
        )

    @pytest.mark.asyncio()
    async def test_aiter_when_newest_first(self):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENT_USERS.compile(guild=54123, scheduled_event=564123)
        mock_entity_factory = mock.Mock()
        mock_payload_1 = {"user": {"id": "432234"}}
        mock_payload_2 = {"user": {"id": "1233211"}}
        mock_payload_3 = {"user": {"id": "12332112"}}
        mock_payload_4 = {"user": {"id": "1233"}}
        mock_payload_5 = {"user": {"id": "54334"}}
        mock_result_1 = mock.Mock()
        mock_result_2 = mock.Mock()
        mock_result_3 = mock.Mock()
        mock_result_4 = mock.Mock()
        mock_result_5 = mock.Mock()
        mock_entity_factory.deserialize_scheduled_event_user.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
            mock_result_5,
        ]
        mock_request = mock.AsyncMock(
            side_effect=[[mock_payload_1, mock_payload_2, mock_payload_3], [mock_payload_4, mock_payload_5], []]
        )
        iterator = special_endpoints.ScheduledEventUserIterator(
            entity_factory=mock_entity_factory,
            request_call=mock_request,
            newest_first=True,
            first_id="321123321",
            guild=54123,
            event=564123,
        )

        result = await iterator

        assert result == [mock_result_1, mock_result_2, mock_result_3, mock_result_4, mock_result_5]
        mock_entity_factory.deserialize_scheduled_event_user.assert_has_calls(
            [
                mock.call(mock_payload_3, guild_id=54123),
                mock.call(mock_payload_2, guild_id=54123),
                mock.call(mock_payload_1, guild_id=54123),
                mock.call(mock_payload_5, guild_id=54123),
                mock.call(mock_payload_4, guild_id=54123),
            ]
        )
        mock_request.assert_has_awaits(
            [
                mock.call(
                    compiled_route=expected_route, query={"limit": "100", "with_member": "true", "before": "321123321"}
                ),
                mock.call(
                    compiled_route=expected_route, query={"limit": "100", "with_member": "true", "before": "432234"}
                ),
                mock.call(
                    compiled_route=expected_route, query={"limit": "100", "with_member": "true", "before": "1233"}
                ),
            ]
        )

    @pytest.mark.parametrize("newest_first", [True, False])
    @pytest.mark.asyncio()
    async def test_aiter_when_empty_chunk(self, newest_first: bool):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENT_USERS.compile(guild=543123, scheduled_event=541234)
        mock_entity_factory = mock.Mock()
        mock_request = mock.AsyncMock(return_value=[])
        iterator = special_endpoints.ScheduledEventUserIterator(
            entity_factory=mock_entity_factory,
            request_call=mock_request,
            first_id="54234123123",
            newest_first=newest_first,
            guild=543123,
            event=541234,
        )

        result = await iterator

        assert result == []
        mock_entity_factory.deserialize_scheduled_event_user.assert_not_called()
        query = {"limit": "100", "with_member": "true", "before" if newest_first else "after": "54234123123"}
        mock_request.assert_awaited_once_with(compiled_route=expected_route, query=query)


@pytest.mark.asyncio()
class TestGuildThreadIterator:
    @pytest.mark.parametrize("before_is_timestamp", [True, False])
    @pytest.mark.asyncio()
    async def test_aiter_when_empty_chunk(self, before_is_timestamp: bool):
        mock_deserialize = mock.Mock()
        mock_entity_factory = mock.Mock()
        mock_request = mock.AsyncMock(return_value={"threads": [], "has_more": False})
        mock_route = mock.Mock()

        results = await special_endpoints.GuildThreadIterator(
            deserialize=mock_deserialize,
            entity_factory=mock_entity_factory,
            request_call=mock_request,
            route=mock_route,
            before_is_timestamp=before_is_timestamp,
            before="123321",
        )

        assert results == []
        mock_request.assert_awaited_once_with(compiled_route=mock_route, query={"before": "123321", "limit": "100"})
        mock_entity_factory.deserialize_thread_member.assert_not_called()
        mock_deserialize.assert_not_called()

    @pytest.mark.asyncio()
    async def test_aiter_when_before_is_timestamp(self):
        mock_payload_1 = {"id": "9494949", "thread_metadata": {"archive_timestamp": "2022-02-28T11:33:09.220087+00:00"}}
        mock_payload_2 = {"id": "6576234", "thread_metadata": {"archive_timestamp": "2022-02-21T11:33:09.220087+00:00"}}
        mock_payload_3 = {
            "id": "1236524143",
            "thread_metadata": {"archive_timestamp": "2022-02-10T11:33:09.220087+00:00"},
        }
        mock_payload_4 = {
            "id": "12365241663",
            "thread_metadata": {"archive_timestamp": "2022-02-11T11:33:09.220087+00:00"},
        }
        mock_thread_1 = mock.Mock(id=9494949)
        mock_thread_2 = mock.Mock(id=6576234)
        mock_thread_3 = mock.Mock(id=1236524143)
        mock_thread_4 = mock.Mock(id=12365241663)
        mock_member_payload_1 = {"id": "9494949", "user_id": "4884844"}
        mock_member_payload_2 = {"id": "6576234", "user_id": "9030920932908"}
        mock_member_payload_3 = {"id": "1236524143", "user_id": "9549494934"}
        mock_member_1 = mock.Mock(thread_id=9494949)
        mock_member_2 = mock.Mock(thread_id=6576234)
        mock_member_3 = mock.Mock(thread_id=1236524143)
        mock_deserialize = mock.Mock(side_effect=[mock_thread_1, mock_thread_2, mock_thread_3, mock_thread_4])
        mock_entity_factory = mock.Mock()
        mock_entity_factory.deserialize_thread_member.side_effect = [mock_member_1, mock_member_2, mock_member_3]
        mock_request = mock.AsyncMock(
            side_effect=[
                {
                    "threads": [mock_payload_1, mock_payload_2],
                    "members": [mock_member_payload_1, mock_member_payload_2],
                    "has_more": True,
                },
                {"threads": [mock_payload_3, mock_payload_4], "members": [mock_member_payload_3], "has_more": False},
            ]
        )
        mock_route = mock.Mock()
        thread_iterator = special_endpoints.GuildThreadIterator(
            mock_deserialize, mock_entity_factory, mock_request, mock_route, "eatmyshinymetal", before_is_timestamp=True
        )

        results = await thread_iterator

        mock_request.assert_has_awaits(
            [
                mock.call(compiled_route=mock_route, query={"limit": "100", "before": "eatmyshinymetal"}),
                mock.call(
                    compiled_route=mock_route, query={"limit": "100", "before": "2022-02-21T11:33:09.220087+00:00"}
                ),
            ]
        )
        assert results == [mock_thread_1, mock_thread_2, mock_thread_3, mock_thread_4]
        mock_entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_member_payload_1), mock.call(mock_member_payload_2), mock.call(mock_member_payload_3)]
        )
        mock_deserialize.assert_has_calls(
            [
                mock.call(mock_payload_1, member=mock_member_1),
                mock.call(mock_payload_2, member=mock_member_2),
                mock.call(mock_payload_3, member=mock_member_3),
                mock.call(mock_payload_4, member=None),
            ]
        )

    async def test_aiter_when_before_is_timestamp_and_undefined(self):
        mock_payload_1 = {"id": "9494949", "thread_metadata": {"archive_timestamp": "2022-02-21T11:33:09.220087+00:00"}}
        mock_payload_2 = {"id": "6576234", "thread_metadata": {"archive_timestamp": "2022-02-08T11:33:09.220087+00:00"}}
        mock_payload_3 = {
            "id": "1236524143",
            "thread_metadata": {"archive_timestamp": "2022-02-28T11:33:09.220087+00:00"},
        }
        mock_member_payload_1 = {"id": "9494949", "user_id": "4884844"}
        mock_member_payload_2 = {"id": "6576234", "user_id": "9030920932908"}
        mock_member_payload_3 = {"id": "1236524143", "user_id": "9549494934"}
        mock_thread_1 = mock.Mock(id=9494949)
        mock_thread_2 = mock.Mock(id=6576234)
        mock_thread_3 = mock.Mock(id=1236524143)
        mock_member_1 = mock.Mock(thread_id=9494949)
        mock_member_2 = mock.Mock(thread_id=6576234)
        mock_member_3 = mock.Mock(thread_id=1236524143)
        mock_deserialize = mock.Mock(side_effect=[mock_thread_1, mock_thread_2, mock_thread_3])
        mock_entity_factory = mock.Mock()
        mock_entity_factory.deserialize_thread_member.side_effect = [mock_member_1, mock_member_2, mock_member_3]
        mock_request = mock.AsyncMock(
            return_value={
                "threads": [mock_payload_1, mock_payload_2, mock_payload_3],
                "members": [mock_member_payload_3, mock_member_payload_1, mock_member_payload_2],
                "has_more": False,
            }
        )
        mock_route = mock.Mock()
        thread_iterator = special_endpoints.GuildThreadIterator(
            mock_deserialize,
            mock_entity_factory,
            mock_request,
            mock_route,
            undefined.UNDEFINED,
            before_is_timestamp=True,
        )

        result = await thread_iterator

        assert result == [mock_thread_1, mock_thread_2, mock_thread_3]
        mock_entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_member_payload_1), mock.call(mock_member_payload_2), mock.call(mock_member_payload_3)]
        )
        mock_request.assert_awaited_once_with(compiled_route=mock_route, query={"limit": "100"})
        mock_deserialize.assert_has_calls(
            [
                mock.call(mock_payload_1, member=mock_member_1),
                mock.call(mock_payload_2, member=mock_member_2),
                mock.call(mock_payload_3, member=mock_member_3),
            ]
        )

    async def test_aiter_when_before_is_id(self):
        mock_payload_1 = {"id": "9494949", "thread_metadata": {"archive_timestamp": "2022-02-21T11:33:09.220087+00:00"}}
        mock_payload_2 = {"id": "6576234", "thread_metadata": {"archive_timestamp": "2022-02-10T11:33:09.220087+00:00"}}
        mock_payload_3 = {
            "id": "1236524143",
            "thread_metadata": {"archive_timestamp": "2022-02-28T11:33:09.220087+00:00"},
        }
        mock_member_payload_1 = {"id": "9494949", "user_id": "4884844"}
        mock_member_payload_2 = {"id": "6576234", "user_id": "9030920932908"}
        mock_member_payload_3 = {"id": "1236524143", "user_id": "9549494934"}
        mock_member_1 = mock.Mock(thread_id=9494949)
        mock_member_2 = mock.Mock(thread_id=6576234)
        mock_member_3 = mock.Mock(thread_id=1236524143)
        mock_thread_1 = mock.Mock(id=9494949)
        mock_thread_2 = mock.Mock(id=6576234)
        mock_thread_3 = mock.Mock(id=1236524143)
        mock_deserialize = mock.Mock(side_effect=[mock_thread_1, mock_thread_2, mock_thread_3])
        mock_entity_factory = mock.Mock()
        mock_entity_factory.deserialize_thread_member.side_effect = [mock_member_1, mock_member_3, mock_member_2]

        mock_request = mock.AsyncMock(
            return_value={
                "threads": [mock_payload_1, mock_payload_2, mock_payload_3],
                "members": [mock_member_payload_3, mock_member_payload_1, mock_member_payload_2],
                "has_more": False,
            }
        )
        mock_route = mock.Mock()
        thread_iterator = special_endpoints.GuildThreadIterator(
            mock_deserialize, mock_entity_factory, mock_request, mock_route, "3451231231231", before_is_timestamp=False
        )

        result = await thread_iterator

        assert result == [mock_thread_1, mock_thread_2, mock_thread_3]
        mock_request.assert_awaited_once_with(
            compiled_route=mock_route, query={"limit": "100", "before": "3451231231231"}
        )
        mock_deserialize.assert_has_calls(
            [
                mock.call(mock_payload_1, member=mock_member_1),
                mock.call(mock_payload_2, member=mock_member_3),
                mock.call(mock_payload_3, member=mock_member_2),
            ]
        )
        mock_entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_member_payload_1), mock.call(mock_member_payload_2), mock.call(mock_member_payload_3)]
        )

    async def test_aiter_when_before_is_id_and_undefined(self):
        mock_payload_1 = {"id": "9494949", "thread_metadata": {"archive_timestamp": "2022-02-21T11:33:09.220087+00:00"}}
        mock_payload_2 = {"id": "6576234", "thread_metadata": {"archive_timestamp": "2022-02-08T11:33:09.220087+00:00"}}
        mock_payload_3 = {
            "id": "1236524143",
            "thread_metadata": {"archive_timestamp": "2022-02-28T11:33:09.220087+00:00"},
        }
        mock_member_payload_1 = {"id": "9494949", "user_id": "4884844"}
        mock_member_payload_2 = {"id": "6576234", "user_id": "9030920932908"}
        mock_member_payload_3 = {"id": "1236524143", "user_id": "9549494934"}
        mock_thread_1 = mock.Mock(id=9494949)
        mock_thread_2 = mock.Mock(id=6576234)
        mock_thread_3 = mock.Mock(id=1236524143)
        mock_member_1 = mock.Mock(thread_id=9494949)
        mock_member_2 = mock.Mock(thread_id=6576234)
        mock_member_3 = mock.Mock(thread_id=1236524143)
        mock_deserialize = mock.Mock(side_effect=[mock_thread_1, mock_thread_2, mock_thread_3])
        mock_entity_factory = mock.Mock()
        mock_entity_factory.deserialize_thread_member.side_effect = [mock_member_1, mock_member_2, mock_member_3]
        mock_request = mock.AsyncMock(
            return_value={
                "threads": [mock_payload_1, mock_payload_2, mock_payload_3],
                "members": [mock_member_payload_3, mock_member_payload_1, mock_member_payload_2],
                "has_more": False,
            }
        )
        mock_route = mock.Mock()
        thread_iterator = special_endpoints.GuildThreadIterator(
            mock_deserialize,
            mock_entity_factory,
            mock_request,
            mock_route,
            undefined.UNDEFINED,
            before_is_timestamp=False,
        )

        result = await thread_iterator

        assert result == [mock_thread_1, mock_thread_2, mock_thread_3]
        mock_entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_member_payload_1), mock.call(mock_member_payload_2), mock.call(mock_member_payload_3)]
        )
        mock_request.assert_awaited_once_with(compiled_route=mock_route, query={"limit": "100"})
        mock_deserialize.assert_has_calls(
            [
                mock.call(mock_payload_1, member=mock_member_1),
                mock.call(mock_payload_2, member=mock_member_2),
                mock.call(mock_payload_3, member=mock_member_3),
            ]
        )


class TestInteractionAutocompleteBuilder:
    def test_type_property(self):
        assert special_endpoints.InteractionAutocompleteBuilder([])

    def test_choices(self):
        builder = special_endpoints.InteractionAutocompleteBuilder(
            [
                special_endpoints.AutocompleteChoiceBuilder(name="echo", value="charlie"),
                special_endpoints.AutocompleteChoiceBuilder(name="echo", value="charlie"),
            ]
        )

        assert builder.choices == [
            special_endpoints.AutocompleteChoiceBuilder(name="echo", value="charlie"),
            special_endpoints.AutocompleteChoiceBuilder(name="echo", value="charlie"),
        ]

    def test_set_choices(self):
        builder = special_endpoints.InteractionAutocompleteBuilder()

        builder.set_choices(
            [
                special_endpoints.AutocompleteChoiceBuilder("aaa", "bbb"),
                special_endpoints.AutocompleteChoiceBuilder("e", "a"),
            ]
        )

        assert builder.choices == [
            special_endpoints.AutocompleteChoiceBuilder("aaa", "bbb"),
            special_endpoints.AutocompleteChoiceBuilder("e", "a"),
        ]

    def test_build(self):
        builder = special_endpoints.InteractionAutocompleteBuilder(
            [
                special_endpoints.AutocompleteChoiceBuilder("meow", "waaaa"),
                special_endpoints.AutocompleteChoiceBuilder("lotta", "water"),
            ]
        )

        data, files = builder.build(mock.Mock())

        assert files == ()
        assert data == {
            "type": base_interactions.ResponseType.AUTOCOMPLETE,
            "data": {"choices": [{"name": "meow", "value": "waaaa"}, {"name": "lotta", "value": "water"}]},
        }


class TestAutocompleteChoiceBuilder:
    def test_name_property(self):
        choice = special_endpoints.AutocompleteChoiceBuilder("heavy", "value")

        assert choice.name == "heavy"

    def test_value_property(self):
        choice = special_endpoints.AutocompleteChoiceBuilder("name", "weapon")

        assert choice.value == "weapon"

    def test_set_name(self):
        choice = special_endpoints.AutocompleteChoiceBuilder("heavy", "value")

        choice.set_name("widen")

        assert choice.name == "widen"

    def test_set_value(self):
        choice = special_endpoints.AutocompleteChoiceBuilder("name", "weapon")

        choice.set_value(123)

        assert choice.value == 123

    def test_build(self):
        choice = special_endpoints.AutocompleteChoiceBuilder("atlantic", "slow")

        assert choice.build() == {"name": "atlantic", "value": "slow"}


class TestInteractionDeferredBuilder:
    def test_type_property(self):
        builder = special_endpoints.InteractionDeferredBuilder(5)

        assert builder.type == 5

    def test_set_flags(self):
        builder = special_endpoints.InteractionDeferredBuilder(5).set_flags(32)

        assert builder.flags == 32

    def test_build(self):
        builder = special_endpoints.InteractionDeferredBuilder(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)

        result, attachments = builder.build(object())

        assert result == {"type": base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE}
        assert attachments == ()

    def test_build_with_flags(self):
        builder = special_endpoints.InteractionDeferredBuilder(
            base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE
        ).set_flags(64)

        result, attachments = builder.build(object())

        assert result == {"type": base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, "data": {"flags": 64}}
        assert attachments == ()


class TestInteractionMessageBuilder:
    def test_type_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.type == 4

    def test_content_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_content("ayayayaya")

        assert builder.content == "ayayayaya"

    def test_set_content_casts_to_str(self):
        mock_thing = mock.Mock(__str__=mock.Mock(return_value="meow nya"))
        builder = special_endpoints.InteractionMessageBuilder(4).set_content(mock_thing)

        assert builder.content == "meow nya"

    def test_attachments_property(self):
        mock_attachment = mock.Mock()
        builder = special_endpoints.InteractionMessageBuilder(4).add_attachment(mock_attachment)

        assert builder.attachments == [mock_attachment]

    def test_attachments_property_when_undefined(self):
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.attachments is undefined.UNDEFINED

    def test_components_property(self):
        mock_component = object()
        builder = special_endpoints.InteractionMessageBuilder(4).add_component(mock_component)

        assert builder.components == [mock_component]

    def test_components_property_when_undefined(self):
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.components is undefined.UNDEFINED

    def test_embeds_property(self):
        mock_embed = object()
        builder = special_endpoints.InteractionMessageBuilder(4).add_embed(mock_embed)

        assert builder.embeds == [mock_embed]

    def test_embeds_property_when_undefined(self):
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.embeds is undefined.UNDEFINED

    def test_flags_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_flags(95995)

        assert builder.flags == 95995

    def test_is_tts_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_tts(False)

        assert builder.is_tts is False

    def test_mentions_everyone_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_mentions_everyone([123, 453])

        assert builder.mentions_everyone == [123, 453]

    def test_role_mentions_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_role_mentions([999])

        assert builder.role_mentions == [999]

    def test_user_mentions_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_user_mentions([33333, 44444])

        assert builder.user_mentions == [33333, 44444]

    def test_build(self):
        mock_entity_factory = mock.Mock()
        mock_component = mock.Mock()
        mock_embed = object()
        mock_serialized_embed = object()
        mock_entity_factory.serialize_embed.return_value = (mock_serialized_embed, [])
        builder = (
            special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_CREATE)
            .add_embed(mock_embed)
            .add_component(mock_component)
            .set_content("a content")
            .set_flags(2323)
            .set_tts(True)
            .set_mentions_everyone(False)
            .set_user_mentions([123])
            .set_role_mentions([54234])
        )

        result, attachments = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_called_once_with(mock_embed)
        mock_component.build.assert_called_once_with()
        assert result == {
            "type": base_interactions.ResponseType.MESSAGE_CREATE,
            "data": {
                "content": "a content",
                "components": [mock_component.build.return_value],
                "embeds": [mock_serialized_embed],
                "flags": 2323,
                "tts": True,
                "allowed_mentions": {"parse": [], "users": ["123"], "roles": ["54234"]},
            },
        }
        assert attachments == []

    def test_build_for_partial_when_message_create(self):
        mock_entity_factory = mock.Mock()
        builder = special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_CREATE)

        result, attachments = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_not_called()
        assert result == {
            "type": base_interactions.ResponseType.MESSAGE_CREATE,
            "data": {"allowed_mentions": {"parse": []}},
        }
        assert attachments == []

    def test_build_for_partial_when_message_update(self):
        mock_entity_factory = mock.Mock()
        builder = special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_UPDATE)

        result, attachments = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_not_called()
        assert result == {"type": base_interactions.ResponseType.MESSAGE_UPDATE, "data": {}}
        assert attachments == []

    def test_build_for_partial_when_empty_lists(self):
        mock_entity_factory = mock.Mock()
        builder = special_endpoints.InteractionMessageBuilder(
            base_interactions.ResponseType.MESSAGE_UPDATE, attachments=[], components=[], embeds=[]
        )

        result, attachments = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_not_called()
        assert result == {"type": base_interactions.ResponseType.MESSAGE_UPDATE, "data": {}}
        assert attachments == []

    def test_build_handles_attachments(self):
        mock_entity_factory = mock.Mock()
        mock_message_attachment = mock.Mock(messages.Attachment, id=123, filename="testing")
        mock_file_attachment = object()
        mock_embed = object()
        mock_embed_attachment = object()
        mock_entity_factory.serialize_embed.return_value = (mock_embed, [mock_embed_attachment])
        builder = (
            special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_CREATE)
            .add_attachment(mock_file_attachment)
            .add_attachment(mock_message_attachment)
            .add_embed(object())
        )

        with mock.patch.object(files, "ensure_resource") as ensure_resource:
            result, attachments = builder.build(mock_entity_factory)

        ensure_resource.assert_called_once_with(mock_file_attachment)
        assert result == {
            "type": base_interactions.ResponseType.MESSAGE_CREATE,
            "data": {
                "attachments": [{"id": 123, "filename": "testing"}],
                "embeds": [mock_embed],
                "allowed_mentions": {"parse": []},
            },
        }

        assert attachments == [ensure_resource.return_value, mock_embed_attachment]

    def test_build_handles_cleared_attachments(self):
        mock_entity_factory = mock.Mock()
        builder = special_endpoints.InteractionMessageBuilder(
            base_interactions.ResponseType.MESSAGE_UPDATE
        ).clear_attachments()

        result, attachments = builder.build(mock_entity_factory)

        assert result == {"type": base_interactions.ResponseType.MESSAGE_UPDATE, "data": {"attachments": None}}

        assert attachments == []


class TestInteractionModalBuilder:
    def test_type_property(self):
        builder = special_endpoints.InteractionModalBuilder("title", "custom_id")
        assert builder.type == 9

    def test_title_property(self):
        builder = special_endpoints.InteractionModalBuilder("title", "custom_id").set_title("title2")
        assert builder.title == "title2"

    def test_custom_id_property(self):
        builder = special_endpoints.InteractionModalBuilder("title", "custom_id").set_custom_id("better_custom_id")
        assert builder.custom_id == "better_custom_id"

    def test_components_property(self):
        component = mock.Mock()
        builder = special_endpoints.InteractionModalBuilder("title", "custom_id").add_component(component)
        assert builder.components == [component]

    def test_build(self):
        component = mock.Mock()
        builder = special_endpoints.InteractionModalBuilder("title", "custom_id").add_component(component)

        result, attachments = builder.build(mock.Mock())
        assert result == {
            "type": 9,
            "data": {"title": "title", "custom_id": "custom_id", "components": [component.build.return_value]},
        }
        assert attachments == ()


class TestCommandBuilder:
    @pytest.fixture()
    def stub_command(self) -> typing.Type[special_endpoints.CommandBuilder]:
        return hikari_test_helpers.mock_class_namespace(special_endpoints.CommandBuilder)

    def test_name_property(self, stub_command):
        builder = stub_command("NOOOOO").set_name("aaaaa")

        assert builder.name == "aaaaa"

    def test_id_property(self, stub_command):
        builder = stub_command("OKSKDKSDK").set_id(3212123)

        assert builder.id == 3212123

    def test_default_member_permissions(self, stub_command):
        builder = stub_command("oksksksk").set_default_member_permissions(permissions.Permissions.ADMINISTRATOR)

        assert builder.default_member_permissions == permissions.Permissions.ADMINISTRATOR

    def test_is_dm_enabled(self, stub_command):
        builder = stub_command("oksksksk").set_is_dm_enabled(True)

        assert builder.is_dm_enabled is True

    def test_is_nsfw_property(self, stub_command):
        builder = stub_command("oksksksk").set_is_nsfw(True)

        assert builder.is_nsfw is True

    def test_name_localizations_property(self, stub_command):
        builder = stub_command("oksksksk").set_name_localizations({"aaa": "bbb", "ccc": "DDd"})

        assert builder.name_localizations == {"aaa": "bbb", "ccc": "DDd"}


class TestSlashCommandBuilder:
    def test_description_property(self):
        builder = special_endpoints.SlashCommandBuilder("ok", "NO").set_description("meow")

        assert builder.description == "meow"

    def test_options_property(self):
        builder = special_endpoints.SlashCommandBuilder("OKSKDKSDK", "inmjfdsmjiooikjsa")
        mock_option = object()

        assert builder.options == []

        builder.add_option(mock_option)

        assert builder.options == [mock_option]

    def test_build_with_optional_data(self):
        mock_entity_factory = mock.Mock()
        mock_option = object()
        builder = (
            special_endpoints.SlashCommandBuilder(
                "we are number",
                "one",
                name_localizations={locales.Locale.TR: "merhaba"},
                description_localizations={locales.Locale.TR: "bir"},
            )
            .add_option(mock_option)
            .set_id(3412312)
            .set_default_member_permissions(permissions.Permissions.ADMINISTRATOR)
            .set_is_dm_enabled(True)
            .set_is_nsfw(True)
        )

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_command_option.assert_called_once_with(mock_option)
        assert result == {
            "name": "we are number",
            "description": "one",
            "type": 1,
            "dm_permission": True,
            "nsfw": True,
            "default_member_permissions": 8,
            "options": [mock_entity_factory.serialize_command_option.return_value],
            "id": "3412312",
            "name_localizations": {locales.Locale.TR: "merhaba"},
            "description_localizations": {locales.Locale.TR: "bir"},
        }

    def test_build_without_optional_data(self):
        builder = special_endpoints.SlashCommandBuilder("we are number", "oner")

        result = builder.build(mock.Mock())

        assert result == {
            "type": 1,
            "name": "we are number",
            "description": "oner",
            "options": [],
            "name_localizations": {},
            "description_localizations": {},
        }

    @pytest.mark.asyncio()
    async def test_create(self):
        builder = (
            special_endpoints.SlashCommandBuilder("we are number", "one")
            .add_option(mock.Mock())
            .set_id(3412312)
            .set_name_localizations({locales.Locale.TR: "sayı"})
            .set_description_localizations({locales.Locale.TR: "bir"})
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
            .set_is_dm_enabled(True)
            .set_is_nsfw(True)
        )
        mock_rest = mock.AsyncMock()

        result = await builder.create(mock_rest, 123431123)

        assert result is mock_rest.create_slash_command.return_value
        mock_rest.create_slash_command.assert_awaited_once_with(
            123431123,
            builder.name,
            builder.description,
            guild=undefined.UNDEFINED,
            options=builder.options,
            name_localizations={locales.Locale.TR: "sayı"},
            description_localizations={locales.Locale.TR: "bir"},
            default_member_permissions=permissions.Permissions.BAN_MEMBERS,
            dm_enabled=True,
            nsfw=True,
        )

    @pytest.mark.asyncio()
    async def test_create_with_guild(self):
        builder = (
            special_endpoints.SlashCommandBuilder("we are number", "one")
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
            .set_is_dm_enabled(True)
            .set_is_nsfw(True)
        )
        mock_rest = mock.AsyncMock()

        builder.set_name_localizations({locales.Locale.TR: "sayı"})
        builder.set_description_localizations({locales.Locale.TR: "bir"})

        result = await builder.create(mock_rest, 54455445, guild=54123123321)

        assert result is mock_rest.create_slash_command.return_value
        mock_rest.create_slash_command.assert_awaited_once_with(
            54455445,
            builder.name,
            builder.description,
            guild=54123123321,
            options=builder.options,
            name_localizations={locales.Locale.TR: "sayı"},
            description_localizations={locales.Locale.TR: "bir"},
            default_member_permissions=permissions.Permissions.BAN_MEMBERS,
            dm_enabled=True,
            nsfw=True,
        )


class TestContextMenuBuilder:
    def test_build_with_optional_data(self):
        builder = (
            special_endpoints.ContextMenuCommandBuilder(commands.CommandType.USER, "we are number")
            .set_id(3412312)
            .set_name_localizations({locales.Locale.TR: "merhaba"})
            .set_default_member_permissions(permissions.Permissions.ADMINISTRATOR)
            .set_is_dm_enabled(True)
            .set_is_nsfw(True)
        )

        result = builder.build(mock.Mock())

        assert result == {
            "name": "we are number",
            "type": 2,
            "dm_permission": True,
            "nsfw": True,
            "default_member_permissions": 8,
            "id": "3412312",
            "name_localizations": {locales.Locale.TR: "merhaba"},
        }

    def test_build_without_optional_data(self):
        builder = special_endpoints.ContextMenuCommandBuilder(commands.CommandType.MESSAGE, "nameeeee")

        result = builder.build(mock.Mock())

        assert result == {"type": 3, "name": "nameeeee", "name_localizations": {}}

    @pytest.mark.asyncio()
    async def test_create(self):
        builder = (
            special_endpoints.ContextMenuCommandBuilder(commands.CommandType.USER, "we are number")
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
            .set_name_localizations({"meow": "nyan"})
            .set_is_dm_enabled(True)
            .set_is_nsfw(True)
        )
        mock_rest = mock.AsyncMock()

        result = await builder.create(mock_rest, 123321)

        assert result is mock_rest.create_context_menu_command.return_value
        mock_rest.create_context_menu_command.assert_awaited_once_with(
            123321,
            builder.type,
            builder.name,
            guild=undefined.UNDEFINED,
            default_member_permissions=permissions.Permissions.BAN_MEMBERS,
            name_localizations={"meow": "nyan"},
            dm_enabled=True,
            nsfw=True,
        )

    @pytest.mark.asyncio()
    async def test_create_with_guild(self):
        builder = (
            special_endpoints.ContextMenuCommandBuilder(commands.CommandType.USER, "we are number")
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
            .set_name_localizations({"en-ghibli": "meow"})
            .set_is_dm_enabled(True)
            .set_is_nsfw(True)
        )
        mock_rest = mock.AsyncMock()

        result = await builder.create(mock_rest, 4444444, guild=765234123)

        assert result is mock_rest.create_context_menu_command.return_value
        mock_rest.create_context_menu_command.assert_awaited_once_with(
            4444444,
            builder.type,
            builder.name,
            guild=765234123,
            default_member_permissions=permissions.Permissions.BAN_MEMBERS,
            name_localizations={"en-ghibli": "meow"},
            dm_enabled=True,
            nsfw=True,
        )


@pytest.mark.parametrize("emoji", ["UNICORN", emojis.UnicodeEmoji("UNICORN")])
def test__build_emoji_with_unicode_emoji(emoji):
    result = special_endpoints._build_emoji(emoji)

    assert result == (undefined.UNDEFINED, "UNICORN")


@pytest.mark.parametrize(
    "emoji", [snowflakes.Snowflake(54123123), 54123123, emojis.CustomEmoji(id=54123123, name=None, is_animated=None)]
)
def test__build_emoji_with_custom_emoji(emoji):
    result = special_endpoints._build_emoji(emoji)

    assert result == ("54123123", undefined.UNDEFINED)


def test__build_emoji_when_undefined():
    assert special_endpoints._build_emoji(undefined.UNDEFINED) == (undefined.UNDEFINED, undefined.UNDEFINED)


class Test_ButtonBuilder:
    @pytest.fixture()
    def button(self):
        return special_endpoints._ButtonBuilder(
            style=components.ButtonStyle.DANGER,
            custom_id="sfdasdasd",
            url="hi there",
            emoji=543123,
            label="a lebel",
            is_disabled=True,
        )

    def test_type_property(self, button):
        assert button.type is components.ComponentType.BUTTON

    def test_style_property(self, button):
        assert button.style is components.ButtonStyle.DANGER

    def test_emoji_property(self, button):
        assert button.emoji == 543123

    @pytest.mark.parametrize("emoji", ["unicode", emojis.UnicodeEmoji("unicode")])
    def test_set_emoji_with_unicode_emoji(self, button, emoji):
        result = button.set_emoji(emoji)

        assert result is button
        assert button._emoji == emoji
        assert button._emoji_id is undefined.UNDEFINED
        assert button._emoji_name == "unicode"

    @pytest.mark.parametrize("emoji", [emojis.CustomEmoji(name="ok", id=34123123, is_animated=False), 34123123])
    def test_set_emoji_with_custom_emoji(self, button, emoji):
        result = button.set_emoji(emoji)

        assert result is button
        assert button._emoji == emoji
        assert button._emoji_id == "34123123"
        assert button._emoji_name is undefined.UNDEFINED

    def test_set_emoji_with_undefined(self, button):
        result = button.set_emoji(undefined.UNDEFINED)

        assert result is button
        assert button._emoji_id is undefined.UNDEFINED
        assert button._emoji_name is undefined.UNDEFINED
        assert button._emoji is undefined.UNDEFINED

    def test_set_label(self, button):
        assert button.set_label("hi hi") is button
        assert button.label == "hi hi"

    def test_set_is_disabled(self, button):
        assert button.set_is_disabled(False)
        assert button.is_disabled is False

    def test_build(self):
        button = special_endpoints._ButtonBuilder(
            style=components.ButtonStyle.DANGER,
            url="https://example.com",
            label="no u",
            custom_id="ooga booga",
            emoji="emoji_name",
            is_disabled=True,
        )

        assert button.build() == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.DANGER,
            "url": "https://example.com",
            "emoji": {"name": "emoji_name"},
            "label": "no u",
            "custom_id": "ooga booga",
            "disabled": True,
        }

    @pytest.mark.parametrize("emoji", [123321, emojis.CustomEmoji(id=123321, name="", is_animated=True)])
    def test_build_with_custom_emoji(self, emoji: typing.Union[int, emojis.Emoji]):
        button = special_endpoints._ButtonBuilder(
            style=components.ButtonStyle.DANGER, emoji=emoji, url=undefined.UNDEFINED, custom_id=undefined.UNDEFINED
        )

        assert button.build() == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.DANGER,
            "emoji": {"id": "123321"},
            "disabled": False,
        }

    def test_build_without_optional_fields(self):
        button = special_endpoints._ButtonBuilder(
            style=components.ButtonStyle.LINK, url=undefined.UNDEFINED, custom_id=undefined.UNDEFINED
        )

        assert button.build() == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.LINK,
            "disabled": False,
        }


class TestLinkButtonBuilder:
    def test_url_property(self):
        button = special_endpoints.LinkButtonBuilder(url="hihihihi", label="no u", is_disabled=True)

        assert button.url == "hihihihi"


class TestInteractiveButtonBuilder:
    def test_custom_id_property(self):
        button = special_endpoints.InteractiveButtonBuilder(
            style=components.ButtonStyle.DANGER, custom_id="oogie"
        ).set_custom_id("eeeeee")

        assert button.custom_id == "eeeeee"


class TestSelectOptionBuilder:
    @pytest.fixture()
    def option(self):
        return special_endpoints.SelectOptionBuilder(label="ok", value="ok2")

    def test_label_property(self, option):
        option.set_label("new_label")

        assert option.label == "new_label"

    def test_value_property(self, option):
        option.set_value("aaaaaaaaaaaa")

        assert option.value == "aaaaaaaaaaaa"

    def test_emoji_property(self, option):
        option._emoji = 123321
        assert option.emoji == 123321

    def test_set_description(self, option):
        assert option.set_description("a desk") is option
        assert option.description == "a desk"

    @pytest.mark.parametrize("emoji", ["unicode", emojis.UnicodeEmoji("unicode")])
    def test_set_emoji_with_unicode_emoji(self, option, emoji):
        result = option.set_emoji(emoji)

        assert result is option
        assert option._emoji == emoji
        assert option._emoji_id is undefined.UNDEFINED
        assert option._emoji_name == "unicode"

    @pytest.mark.parametrize("emoji", [emojis.CustomEmoji(name="ok", id=34123123, is_animated=False), 34123123])
    def test_set_emoji_with_custom_emoji(self, option, emoji):
        result = option.set_emoji(emoji)

        assert result is option
        assert option._emoji == emoji
        assert option._emoji_id == "34123123"
        assert option._emoji_name is undefined.UNDEFINED

    def test_set_emoji_with_undefined(self, option):
        result = option.set_emoji(undefined.UNDEFINED)

        assert result is option
        assert option._emoji_id is undefined.UNDEFINED
        assert option._emoji_name is undefined.UNDEFINED
        assert option._emoji is undefined.UNDEFINED

    def test_set_is_default(self, option):
        assert option.set_is_default(True) is option
        assert option.is_default is True

    def test_build_with_custom_emoji(self):
        option = special_endpoints.SelectOptionBuilder(
            label="ok", value="ok2", is_default=True, emoji=123312, description="very"
        )

        assert option.build() == {
            "label": "ok",
            "value": "ok2",
            "default": True,
            "emoji": {"id": "123312"},
            "description": "very",
        }

    def test_build_with_unicode_emoji(self):
        option = special_endpoints.SelectOptionBuilder(
            label="ok", value="ok2", is_default=True, emoji="hi", description="very"
        )

        assert option.build() == {
            "label": "ok",
            "value": "ok2",
            "default": True,
            "emoji": {"name": "hi"},
            "description": "very",
        }

    def test_build_partial(self):
        option = special_endpoints.SelectOptionBuilder(label="ok", value="ok2")

        assert option.build() == {"label": "ok", "value": "ok2", "default": False}


class TestSelectMenuBuilder:
    @pytest.fixture()
    def menu(self):
        return special_endpoints.SelectMenuBuilder(custom_id="o2o2o2", type=5)

    def test_type_property(self):
        menu = special_endpoints.SelectMenuBuilder(type=123, custom_id="hihihi")

        assert menu.type == 123

    def test_custom_id_property(self, menu):
        menu.set_custom_id("ooooo")

        assert menu.custom_id == "ooooo"

    def test_set_is_disabled(self, menu):
        assert menu.set_is_disabled(True) is menu
        assert menu.is_disabled is True

    def test_set_placeholder(self, menu):
        assert menu.set_placeholder("place") is menu
        assert menu.placeholder == "place"

    def test_set_min_values(self, menu):
        assert menu.set_min_values(1) is menu
        assert menu.min_values == 1

    def test_set_max_values(self, menu):
        assert menu.set_max_values(25) is menu
        assert menu.max_values == 25

    def test_build(self):
        menu = special_endpoints.SelectMenuBuilder(
            custom_id="45234fsdf",
            type=components.ComponentType.USER_SELECT_MENU,
            placeholder="meep",
            min_values=5,
            max_values=23,
            is_disabled=True,
        )

        assert menu.build() == {
            "type": components.ComponentType.USER_SELECT_MENU,
            "custom_id": "45234fsdf",
            "placeholder": "meep",
            "disabled": True,
            "min_values": 5,
            "max_values": 23,
        }

    def test_build_without_optional_fields(self):
        menu = special_endpoints.SelectMenuBuilder(custom_id="o2o2o2", type=components.ComponentType.ROLE_SELECT_MENU)

        assert menu.build() == {
            "type": components.ComponentType.ROLE_SELECT_MENU,
            "custom_id": "o2o2o2",
            "disabled": False,
            "min_values": 0,
            "max_values": 1,
        }


class TestTextSelectMenuBuilder:
    @pytest.fixture()
    def menu(self):
        return special_endpoints.TextSelectMenuBuilder(custom_id="o2o2o2")

    def test_parent_property(self):
        mock_parent = object()
        menu = special_endpoints.TextSelectMenuBuilder(custom_id="o2o2o2", parent=mock_parent)

        assert menu.parent is mock_parent

    def test_parent_property_when_none(self):
        menu = special_endpoints.TextSelectMenuBuilder(custom_id="o2o2o2")

        with pytest.raises(RuntimeError, match="This menu has no parent"):
            menu.parent

    def test_type_property(self, menu: special_endpoints.TextSelectMenuBuilder[typing.NoReturn]):
        assert menu.type is components.ComponentType.TEXT_SELECT_MENU

    def test_add_option(self, menu: special_endpoints.TextSelectMenuBuilder[typing.NoReturn]):
        menu.add_option("ok", "no u", description="meow", emoji="e", is_default=True)

        assert len(menu.options) == 1
        option = menu.options[0]
        assert option.label == "ok"
        assert option.value == "no u"
        assert option.description == "meow"
        assert option.emoji == "e"
        assert option.is_default is True

    def test_add_raw_option(self, menu):
        mock_option = object()

        menu.add_raw_option(mock_option)

        assert menu.options == [mock_option]

    def test_build(self):
        menu = special_endpoints.TextSelectMenuBuilder(
            custom_id="o2o2o2",
            placeholder="hi",
            min_values=22,
            max_values=53,
            is_disabled=True,
            options=[special_endpoints.SelectOptionBuilder("meow", "vault")],
        )

        assert menu.build() == {
            "type": components.ComponentType.TEXT_SELECT_MENU,
            "custom_id": "o2o2o2",
            "placeholder": "hi",
            "min_values": 22,
            "max_values": 53,
            "disabled": True,
            "options": [{"label": "meow", "value": "vault", "default": False}],
        }

    def test_build_without_optional_fields(self):
        menu = special_endpoints.TextSelectMenuBuilder(custom_id="fds  qw")

        assert menu.build() == {
            "type": components.ComponentType.TEXT_SELECT_MENU,
            "custom_id": "fds  qw",
            "min_values": 0,
            "max_values": 1,
            "disabled": False,
            "options": [],
        }


class TestChannelSelectMenuBuilder:
    def test_type_property(self):
        menu = special_endpoints.ChannelSelectMenuBuilder(custom_id="id")
        assert menu.type is components.ComponentType.CHANNEL_SELECT_MENU

    def test_set_channel_types(self):
        menu = special_endpoints.ChannelSelectMenuBuilder(custom_id="hi")

        menu.set_channel_types([channels.ChannelType.DM, channels.ChannelType.GUILD_FORUM])

        assert menu.channel_types == [channels.ChannelType.DM, channels.ChannelType.GUILD_FORUM]

    def test_build(self):
        menu = special_endpoints.ChannelSelectMenuBuilder(
            custom_id="o2o2o2",
            placeholder="hi",
            min_values=22,
            max_values=53,
            is_disabled=True,
            channel_types=[channels.ChannelType.GUILD_CATEGORY],
        )

        assert menu.build() == {
            "type": components.ComponentType.CHANNEL_SELECT_MENU,
            "custom_id": "o2o2o2",
            "placeholder": "hi",
            "min_values": 22,
            "max_values": 53,
            "disabled": True,
            "channel_types": [channels.ChannelType.GUILD_CATEGORY],
        }

    def test_build_without_optional_fields(self):
        menu = special_endpoints.ChannelSelectMenuBuilder(custom_id="42312312")

        assert menu.build() == {
            "type": components.ComponentType.CHANNEL_SELECT_MENU,
            "custom_id": "42312312",
            "min_values": 0,
            "max_values": 1,
            "disabled": False,
            "channel_types": [],
        }


class TestTextInput:
    @pytest.fixture()
    def text_input(self):
        return special_endpoints.TextInputBuilder(custom_id="o2o2o2", label="label")

    def test_type_property(self, text_input):
        assert text_input.type is components.ComponentType.TEXT_INPUT

    def test_set_style(self, text_input):
        assert text_input.set_style(components.TextInputStyle.PARAGRAPH) is text_input
        assert text_input.style == components.TextInputStyle.PARAGRAPH

    def test_set_custom_id(self, text_input):
        assert text_input.set_custom_id("custooom") is text_input
        assert text_input.custom_id == "custooom"

    def test_set_label(self, text_input):
        assert text_input.set_label("labeeeel") is text_input
        assert text_input.label == "labeeeel"

    def test_set_placeholder(self, text_input):
        assert text_input.set_placeholder("place") is text_input
        assert text_input.placeholder == "place"

    def test_set_required(self, text_input):
        assert text_input.set_required(True) is text_input
        assert text_input.is_required is True

    def test_set_value(self, text_input):
        assert text_input.set_value("valueeeee") is text_input
        assert text_input.value == "valueeeee"

    def test_set_min_length_(self, text_input):
        assert text_input.set_min_length(10) is text_input
        assert text_input.min_length == 10

    def test_set_max_length(self, text_input):
        assert text_input.set_max_length(250) is text_input
        assert text_input.max_length == 250

    def test_build_partial(self):
        text_input = special_endpoints.TextInputBuilder(custom_id="o2o2o2", label="label")

        assert text_input.build() == {
            "type": components.ComponentType.TEXT_INPUT,
            "style": 1,
            "custom_id": "o2o2o2",
            "label": "label",
            "required": True,
            "min_length": 0,
            "max_length": 4000,
        }

    def test_build(self):
        text_input = special_endpoints.TextInputBuilder(
            custom_id="o2o2o2",
            label="label",
            placeholder="placeholder",
            value="value",
            required=False,
            min_length=10,
            max_length=250,
        )

        assert text_input.build() == {
            "type": components.ComponentType.TEXT_INPUT,
            "style": 1,
            "custom_id": "o2o2o2",
            "label": "label",
            "placeholder": "placeholder",
            "value": "value",
            "required": False,
            "min_length": 10,
            "max_length": 250,
        }


class TestMessageActionRowBuilder:
    def test_type_property(self):
        row = special_endpoints.MessageActionRowBuilder()

        assert row.type is components.ComponentType.ACTION_ROW

    def test_components_property(self):
        mock_component = mock.Mock()
        row = special_endpoints.MessageActionRowBuilder().add_component(mock_component)
        assert row.components == [mock_component]

    def test_add_interactive_button(self):
        row = special_endpoints.MessageActionRowBuilder()

        row.add_interactive_button(
            components.ButtonStyle.DANGER, "go home", emoji="emoji", label="libal", is_disabled=True
        )

        assert len(row.components) == 1
        button = row.components[0]
        assert isinstance(button, special_endpoints_api.InteractiveButtonBuilder)
        assert button.type is components.ComponentType.BUTTON
        assert button.style is components.ButtonStyle.DANGER
        assert button.emoji == "emoji"
        assert button.custom_id == "go home"
        assert button.label == "libal"
        assert button.is_disabled is True

    def test_add_link_button(self):
        row = special_endpoints.MessageActionRowBuilder()

        row.add_link_button("https://example.com", emoji="e", label="American made", is_disabled=True)

        assert len(row.components) == 1
        button = row.components[0]
        assert isinstance(button, special_endpoints.LinkButtonBuilder)
        assert button.type is components.ComponentType.BUTTON
        assert button.style is components.ButtonStyle.LINK
        assert button.emoji == "e"
        assert button.url == "https://example.com"
        assert button.label == "American made"
        assert button.is_disabled is True

    def test_add_select_menu(self):
        row = special_endpoints.MessageActionRowBuilder()

        row.add_select_menu(
            components.ComponentType.ROLE_SELECT_MENU,
            "two trucks",
            placeholder="holding hands",
            min_values=6,
            max_values=9,
            is_disabled=True,
        )

        assert len(row.components) == 1
        component = row.components[0]
        assert isinstance(component, special_endpoints_api.SelectMenuBuilder)

    def test_add_channel_menu(self):
        row = special_endpoints.MessageActionRowBuilder()

        row.add_channel_menu(
            "flex",
            channel_types=[channels.ChannelType.GROUP_DM],
            placeholder="The pasion",
            min_values=4,
            max_values=9,
            is_disabled=True,
        )

        assert len(row.components) == 1
        component = row.components[0]
        assert isinstance(component, special_endpoints_api.SelectMenuBuilder)

    def test_add_text_menu(self):
        row = special_endpoints.MessageActionRowBuilder()

        row.add_text_menu(
            "Two pickup trucks", placeholder="American made", min_values=5, max_values=6, is_disabled=True
        )

        assert len(row.components) == 1
        component = row.components[0]
        assert isinstance(component, special_endpoints_api.SelectMenuBuilder)
        assert component.custom_id == "Two pickup trucks"
        assert component.placeholder == "American made"
        assert component.min_values == 5
        assert component.max_values == 6
        assert component.is_disabled is True

    def test_build(self):
        mock_component_1 = mock.Mock(type=components.ComponentType.BUTTON)
        mock_component_2 = mock.Mock(type=components.ComponentType.BUTTON)

        row = (
            special_endpoints.MessageActionRowBuilder().add_component(mock_component_1).add_component(mock_component_2)
        )

        assert row.build() == {
            "type": components.ComponentType.ACTION_ROW,
            "components": [mock_component_1.build.return_value, mock_component_2.build.return_value],
        }
        mock_component_1.build.assert_called_once_with()
        mock_component_2.build.assert_called_once_with()


class TestModalActionRow:
    def test_type_property(self):
        row = special_endpoints.ModalActionRowBuilder()

        assert row.type is components.ComponentType.ACTION_ROW

    def test_add_text_input(self):
        row = special_endpoints.ModalActionRowBuilder()
        menu = row.add_text_input(
            "hihihi",
            "lalbell",
            style=components.TextInputStyle.PARAGRAPH,
            placeholder="meep",
            value="beep",
            required=False,
            min_length=444,
            max_length=447,
        )

        assert len(row.components) == 1
        menu = row.components[0]
        assert isinstance(menu, special_endpoints_api.TextInputBuilder)
        assert menu.custom_id == "hihihi"
        assert menu.label == "lalbell"
        assert menu.style is components.TextInputStyle.PARAGRAPH
        assert menu.placeholder == "meep"
        assert menu.value == "beep"
        assert menu.is_required is False
        assert menu.min_length == 444
        assert menu.max_length == 447

    def test_build(self):
        mock_component_1 = mock.Mock(type=components.ComponentType.TEXT_INPUT)
        mock_component_2 = mock.Mock(type=components.ComponentType.TEXT_INPUT)

        row = special_endpoints.ModalActionRowBuilder().add_component(mock_component_1).add_component(mock_component_2)

        result = row.build()

        assert result == {
            "type": components.ComponentType.ACTION_ROW,
            "components": [mock_component_1.build.return_value, mock_component_2.build.return_value],
        }
        mock_component_1.build.assert_called_once_with()
        mock_component_2.build.assert_called_once_with()

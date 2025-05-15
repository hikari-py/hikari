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

import typing

import mock
import pytest

from hikari import applications
from hikari import auto_mod
from hikari import channels
from hikari import colors
from hikari import commands
from hikari import components
from hikari import emojis
from hikari import files
from hikari import locales
from hikari import messages
from hikari import permissions
from hikari import polls
from hikari import snowflakes
from hikari import undefined
from hikari.api import special_endpoints as special_endpoints_api
from hikari.impl import special_endpoints
from hikari.interactions import base_interactions
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


class TestTypingIndicator:
    @pytest.fixture
    def typing_indicator(self):
        return hikari_test_helpers.mock_class_namespace(special_endpoints.TypingIndicator, init_=False)

    def test___enter__(self, typing_indicator):
        # ruff gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            typing_indicator().__enter__()

    def test___exit__(self, typing_indicator):
        try:
            typing_indicator().__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)


class TestOwnGuildIterator:
    @pytest.mark.asyncio
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
        iterator = special_endpoints.OwnGuildIterator(
            mock_entity_factory, mock_request, newest_first=False, first_id="123321"
        )

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

    @pytest.mark.asyncio
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
            mock_entity_factory, mock_request, newest_first=True, first_id="55555555555555555"
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
    @pytest.mark.asyncio
    async def test_aiter_when_empty_chunk(self, newest_first: bool):
        expected_route = routes.GET_MY_GUILDS.compile()
        mock_entity_factory = mock.Mock()
        mock_request = mock.AsyncMock(return_value=[])
        iterator = special_endpoints.OwnGuildIterator(
            mock_entity_factory, mock_request, newest_first=newest_first, first_id="123321"
        )

        result = await iterator

        assert result == []
        mock_entity_factory.deserialize_own_guild.assert_not_called()
        order_key = "before" if newest_first else "after"
        query = {order_key: "123321", "with_counts": "true"}
        mock_request.assert_awaited_once_with(compiled_route=expected_route, query=query)


class TestGuildBanIterator:
    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
    @pytest.mark.asyncio
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


@pytest.mark.asyncio
class TestGuildThreadIterator:
    @pytest.mark.parametrize("before_is_timestamp", [True, False])
    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
    @pytest.fixture
    def stub_command(self) -> type[special_endpoints.CommandBuilder]:
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
            .set_is_nsfw(True)
            .set_integration_types([applications.ApplicationIntegrationType.GUILD_INSTALL])
            .set_context_types([applications.ApplicationContextType.GUILD])
        )

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_command_option.assert_called_once_with(mock_option)
        assert result == {
            "name": "we are number",
            "description": "one",
            "type": 1,
            "nsfw": True,
            "default_member_permissions": 8,
            "options": [mock_entity_factory.serialize_command_option.return_value],
            "id": "3412312",
            "name_localizations": {locales.Locale.TR: "merhaba"},
            "description_localizations": {locales.Locale.TR: "bir"},
            "contexts": [applications.ApplicationIntegrationType.GUILD_INSTALL.value],
            "integration_types": [applications.ApplicationContextType.GUILD.value],
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

    @pytest.mark.asyncio
    async def test_create(self):
        builder = (
            special_endpoints.SlashCommandBuilder("we are number", "one")
            .add_option(mock.Mock())
            .set_id(3412312)
            .set_name_localizations({locales.Locale.TR: "sayı"})
            .set_description_localizations({locales.Locale.TR: "bir"})
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
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
            nsfw=True,
        )

    @pytest.mark.asyncio
    async def test_create_with_guild(self):
        builder = (
            special_endpoints.SlashCommandBuilder("we are number", "one")
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
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
            nsfw=True,
        )


class TestContextMenuBuilder:
    def test_build_with_optional_data(self):
        builder = (
            special_endpoints.ContextMenuCommandBuilder(commands.CommandType.USER, "we are number")
            .set_id(3412312)
            .set_name_localizations({locales.Locale.TR: "merhaba"})
            .set_default_member_permissions(permissions.Permissions.ADMINISTRATOR)
            .set_is_nsfw(True)
            .set_integration_types([applications.ApplicationIntegrationType.GUILD_INSTALL])
            .set_context_types([applications.ApplicationContextType.GUILD])
        )

        result = builder.build(mock.Mock())

        assert result == {
            "name": "we are number",
            "type": 2,
            "nsfw": True,
            "default_member_permissions": 8,
            "id": "3412312",
            "name_localizations": {locales.Locale.TR: "merhaba"},
            "contexts": [applications.ApplicationIntegrationType.GUILD_INSTALL.value],
            "integration_types": [applications.ApplicationContextType.GUILD.value],
        }

    def test_build_without_optional_data(self):
        builder = special_endpoints.ContextMenuCommandBuilder(commands.CommandType.MESSAGE, "nameeeee")

        result = builder.build(mock.Mock())

        assert result == {"type": 3, "name": "nameeeee", "name_localizations": {}}

    @pytest.mark.asyncio
    async def test_create(self):
        builder = (
            special_endpoints.ContextMenuCommandBuilder(commands.CommandType.USER, "we are number")
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
            .set_name_localizations({"meow": "nyan"})
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
            nsfw=True,
        )

    @pytest.mark.asyncio
    async def test_create_with_guild(self):
        builder = (
            special_endpoints.ContextMenuCommandBuilder(commands.CommandType.USER, "we are number")
            .set_default_member_permissions(permissions.Permissions.BAN_MEMBERS)
            .set_name_localizations({"en-ghibli": "meow"})
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
    class ButtonBuilder(special_endpoints._ButtonBuilder):
        @property
        def style(self) -> components.ButtonStyle:
            return components.ButtonStyle.DANGER

    @pytest.fixture
    def button(self):
        return Test_ButtonBuilder.ButtonBuilder(id=5855932, emoji=543123, label="a lebel", is_disabled=True)

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

    def test_build(self, button):
        payload, attachments = button.build()

        assert payload == {
            "id": 5855932,
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.DANGER,
            "emoji": {"id": "543123"},
            "label": "a lebel",
            "disabled": True,
        }

        assert attachments == []

    @pytest.mark.parametrize("emoji", [123321, emojis.CustomEmoji(id=123321, name="", is_animated=True)])
    def test_build_with_custom_emoji(self, emoji: typing.Union[int, emojis.Emoji]):
        button = Test_ButtonBuilder.ButtonBuilder(emoji=emoji)

        payload, attachments = button.build()

        assert payload == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.DANGER,
            "emoji": {"id": "123321"},
            "disabled": False,
        }

        assert attachments == []

    def test_build_without_optional_fields(self):
        button = Test_ButtonBuilder.ButtonBuilder()

        payload, attachments = button.build()

        assert payload == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.DANGER,
            "disabled": False,
        }

        assert attachments == []


class TestLinkButtonBuilder:
    def test_url_property(self):
        button = special_endpoints.LinkButtonBuilder(url="hihihihi", label="no u", is_disabled=True)

        assert button.url == "hihihihi"

    def test_build(self):
        button = special_endpoints.LinkButtonBuilder(
            id=5855932, url="hihihihi", label="no u", emoji="emoji_name", is_disabled=True
        )

        payload, attachments = button.build()

        assert payload == {
            "id": 5855932,
            "style": components.ButtonStyle.LINK,
            "type": components.ComponentType.BUTTON,
            "disabled": True,
            "emoji": {"name": "emoji_name"},
            "label": "no u",
            "url": "hihihihi",
        }
        assert attachments == []


class TestInteractiveButtonBuilder:
    def test_custom_id_property(self):
        button = special_endpoints.InteractiveButtonBuilder(
            style=components.ButtonStyle.DANGER, custom_id="oogie"
        ).set_custom_id("eeeeee")

        assert button.custom_id == "eeeeee"

    def test_build(self):
        button = special_endpoints.InteractiveButtonBuilder(
            id=5855932,
            style=components.ButtonStyle.PRIMARY,
            label="no u",
            emoji="emoji_name",
            is_disabled=True,
            custom_id="oogie",
        )

        payload, attachments = button.build()

        assert payload == {
            "id": 5855932,
            "style": components.ButtonStyle.PRIMARY,
            "type": components.ComponentType.BUTTON,
            "custom_id": "oogie",
            "disabled": True,
            "emoji": {"name": "emoji_name"},
            "label": "no u",
        }
        assert attachments == []


class TestSelectOptionBuilder:
    @pytest.fixture
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
    @pytest.fixture
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
            id=5855932,
            custom_id="45234fsdf",
            type=components.ComponentType.USER_SELECT_MENU,
            placeholder="meep",
            min_values=5,
            max_values=23,
            is_disabled=True,
        )

        payload, attachments = menu.build()

        assert payload == {
            "id": 5855932,
            "type": components.ComponentType.USER_SELECT_MENU,
            "custom_id": "45234fsdf",
            "placeholder": "meep",
            "disabled": True,
            "min_values": 5,
            "max_values": 23,
        }

        assert attachments == []

    def test_build_without_optional_fields(self):
        menu = special_endpoints.SelectMenuBuilder(custom_id="o2o2o2", type=components.ComponentType.ROLE_SELECT_MENU)

        payload, attachments = menu.build()

        assert payload == {
            "type": components.ComponentType.ROLE_SELECT_MENU,
            "custom_id": "o2o2o2",
            "disabled": False,
            "min_values": 0,
            "max_values": 1,
        }

        assert attachments == []


class TestTextSelectMenuBuilder:
    @pytest.fixture
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
            id=5855932,
            custom_id="o2o2o2",
            placeholder="hi",
            min_values=22,
            max_values=53,
            is_disabled=True,
            options=[special_endpoints.SelectOptionBuilder("meow", "vault")],
        )

        payload, attachments = menu.build()

        assert payload == {
            "id": 5855932,
            "type": components.ComponentType.TEXT_SELECT_MENU,
            "custom_id": "o2o2o2",
            "placeholder": "hi",
            "min_values": 22,
            "max_values": 53,
            "disabled": True,
            "options": [{"label": "meow", "value": "vault", "default": False}],
        }

        assert attachments == []

    def test_build_without_optional_fields(self):
        menu = special_endpoints.TextSelectMenuBuilder(custom_id="fds  qw")

        payload, attachments = menu.build()

        assert payload == {
            "type": components.ComponentType.TEXT_SELECT_MENU,
            "custom_id": "fds  qw",
            "min_values": 0,
            "max_values": 1,
            "disabled": False,
            "options": [],
        }

        assert attachments == []


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
            id=5855932,
            custom_id="o2o2o2",
            placeholder="hi",
            min_values=22,
            max_values=53,
            is_disabled=True,
            channel_types=[channels.ChannelType.GUILD_CATEGORY],
        )

        payload, attachments = menu.build()

        assert payload == {
            "id": 5855932,
            "type": components.ComponentType.CHANNEL_SELECT_MENU,
            "custom_id": "o2o2o2",
            "placeholder": "hi",
            "min_values": 22,
            "max_values": 53,
            "disabled": True,
            "channel_types": [channels.ChannelType.GUILD_CATEGORY],
        }

        assert attachments == []

    def test_build_without_optional_fields(self):
        menu = special_endpoints.ChannelSelectMenuBuilder(custom_id="42312312")

        payload, attachments = menu.build()

        assert payload == {
            "type": components.ComponentType.CHANNEL_SELECT_MENU,
            "custom_id": "42312312",
            "min_values": 0,
            "max_values": 1,
            "disabled": False,
            "channel_types": [],
        }

        assert attachments == []


class TestTextInput:
    @pytest.fixture
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

        payload, attachments = text_input.build()

        assert payload == {
            "type": components.ComponentType.TEXT_INPUT,
            "style": 1,
            "custom_id": "o2o2o2",
            "label": "label",
            "required": True,
            "min_length": 0,
            "max_length": 4000,
        }

        assert attachments == []

    def test_build(self):
        text_input = special_endpoints.TextInputBuilder(
            id=5855932,
            custom_id="o2o2o2",
            label="label",
            placeholder="placeholder",
            value="value",
            required=False,
            min_length=10,
            max_length=250,
        )

        payload, attachments = text_input.build()

        assert payload == {
            "id": 5855932,
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

        assert attachments == []


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
        mock_component_1 = mock.Mock(
            special_endpoints.InteractiveButtonBuilder,
            build=mock.Mock(return_value=(mock.Mock(type=components.ComponentType.BUTTON), ())),
        )
        mock_component_2 = mock.Mock(
            special_endpoints.InteractiveButtonBuilder,
            build=mock.Mock(return_value=(mock.Mock(type=components.ComponentType.BUTTON), ())),
        )

        row = special_endpoints.MessageActionRowBuilder(id=5855932, components=[mock_component_1, mock_component_2])

        payload, attachments = row.build()

        assert payload == {
            "type": components.ComponentType.ACTION_ROW,
            "id": 5855932,
            "components": [mock_component_1.build.return_value[0], mock_component_2.build.return_value[0]],
        }
        mock_component_1.build.assert_called_once_with()
        mock_component_2.build.assert_called_once_with()

        assert attachments == []


class TestSectionComponentBuilder:
    def test_type_property(self):
        section = special_endpoints.SectionComponentBuilder(accessory=mock.Mock())

        assert section.type is components.ComponentType.SECTION

    def test_add_component(self):
        section = special_endpoints.SectionComponentBuilder(accessory=mock.Mock())

        assert section.components == []

        text_display = special_endpoints.TextDisplayComponentBuilder(content="test content")

        section.add_component(text_display)

        assert section.components == [text_display]

    def test_add_text_display(self):
        section = special_endpoints.SectionComponentBuilder(accessory=mock.Mock())

        assert section.components == []

        section.add_text_display("test content")

        assert len(section.components) == 1

        assert section.components[0].content == "test content"

    def test_build(self):
        accessory = special_endpoints.ThumbnailComponentBuilder(
            id=2193485, media="some-test-file.png", description="a cool image", spoiler=False
        )

        section = special_endpoints.SectionComponentBuilder(id=5855932, accessory=accessory)
        section.add_text_display("A display?", id=4893723)
        section.add_text_display("Yes, a display.", id=9018345)

        payload, attachments = section.build()

        assert payload == {
            "type": components.ComponentType.SECTION,
            "id": 5855932,
            "accessory": {
                "type": components.ComponentType.THUMBNAIL,
                "id": 2193485,
                "media": {"url": "attachment://some-test-file.png"},
                "description": "a cool image",
                "spoiler": False,
            },
            "components": [
                {"type": components.ComponentType.TEXT_DISPLAY, "id": 4893723, "content": "A display?"},
                {"type": components.ComponentType.TEXT_DISPLAY, "id": 9018345, "content": "Yes, a display."},
            ],
        }
        assert attachments == [files.ensure_resource("some-test-file.png")]

    def test_build_without_optional_fields(self):
        section = special_endpoints.SectionComponentBuilder(
            accessory=special_endpoints.ThumbnailComponentBuilder(
                media="some-test-file.png", description="a cool image", spoiler=False
            )
        )

        payload, attachments = section.build()

        assert payload == {
            "type": components.ComponentType.SECTION,
            "accessory": {
                "type": components.ComponentType.THUMBNAIL,
                "media": {"url": "attachment://some-test-file.png"},
                "description": "a cool image",
                "spoiler": False,
            },
            "components": [],
        }
        assert attachments == [files.ensure_resource("some-test-file.png")]


class TestTextDisplayComponentBuilder:
    def test_type_property(self):
        text_display = special_endpoints.TextDisplayComponentBuilder(content="A display?")

        assert text_display.type is components.ComponentType.TEXT_DISPLAY

    def test_build(self):
        text_display = special_endpoints.TextDisplayComponentBuilder(id=5855932, content="A display?")

        payload, attachments = text_display.build()

        assert payload == {"type": components.ComponentType.TEXT_DISPLAY, "id": 5855932, "content": "A display?"}

        assert attachments == ()


class TestThumbnailComponentBuilder:
    def test_type_property(self):
        thumbnail = special_endpoints.ThumbnailComponentBuilder(media=mock.Mock())

        assert thumbnail.type is components.ComponentType.THUMBNAIL

    def test_build(self):
        thumbnail = special_endpoints.ThumbnailComponentBuilder(
            id=5855932, media="some-test-file.png", description="a cool image", spoiler=False
        )

        payload, attachments = thumbnail.build()

        assert payload == {
            "type": components.ComponentType.THUMBNAIL,
            "id": 5855932,
            "media": {"url": "attachment://some-test-file.png"},
            "description": "a cool image",
            "spoiler": False,
        }

        assert attachments == (files.ensure_resource("some-test-file.png"),)

    def test_build_without_optional_fields(self):
        thumbnail = special_endpoints.ThumbnailComponentBuilder(media="some-test-file.png")

        payload, attachments = thumbnail.build()

        assert payload == {
            "type": components.ComponentType.THUMBNAIL,
            "media": {"url": "attachment://some-test-file.png"},
            "spoiler": False,
        }

        assert attachments == (files.ensure_resource("some-test-file.png"),)


class TestMediaGalleryComponentBuilder:
    def test_type_property(self):
        media_gallery = special_endpoints.MediaGalleryComponentBuilder()

        assert media_gallery.type is components.ComponentType.MEDIA_GALLERY

    def test_add_item(self):
        media_gallery = special_endpoints.MediaGalleryComponentBuilder()

        assert media_gallery.items == []

        media_gallery_item = special_endpoints.MediaGalleryItemBuilder(
            media="some-test-file.png", description="Some description", spoiler=False
        )

        media_gallery.add_item(media_gallery_item)

        assert media_gallery.items == [media_gallery_item]

    def test_add_media_gallery_item(self):
        media_gallery = special_endpoints.MediaGalleryComponentBuilder()

        assert media_gallery.items == []

        media_gallery.add_media_gallery_item("some-test-file.png", description="Some description", spoiler=False)

        assert len(media_gallery.items) == 1

        assert media_gallery.items[0].media == "some-test-file.png"
        assert media_gallery.items[0].description == "Some description"
        assert media_gallery.items[0].is_spoiler is False

    def test_build(self):
        media_gallery = special_endpoints.MediaGalleryComponentBuilder(id=5855932)

        media_gallery.add_media_gallery_item("some-test-file.png", description="Some description", spoiler=False)

        media_gallery.add_media_gallery_item("some-test-file2.png", description="Some description 2", spoiler=True)

        payload, attachments = media_gallery.build()

        assert payload == {
            "type": components.ComponentType.MEDIA_GALLERY,
            "id": 5855932,
            "items": [
                {
                    "media": {"url": "attachment://some-test-file.png"},
                    "description": "Some description",
                    "spoiler": False,
                },
                {
                    "media": {"url": "attachment://some-test-file2.png"},
                    "description": "Some description 2",
                    "spoiler": True,
                },
            ],
        }

        assert attachments == [
            files.ensure_resource("some-test-file.png"),
            files.ensure_resource("some-test-file2.png"),
        ]

    def test_build_without_optional_fields(self):
        media_gallery = special_endpoints.MediaGalleryComponentBuilder()

        payload, attachments = media_gallery.build()

        assert payload == {"type": components.ComponentType.MEDIA_GALLERY, "items": []}

        assert attachments == []


class TestMediaGalleryItemBuilder:
    def test_build(self):
        media_gallery_item = special_endpoints.MediaGalleryItemBuilder(
            media="some-test-file.png", description="Some description", spoiler=False
        )

        payload, attachments = media_gallery_item.build()

        assert payload == {
            "media": {"url": "attachment://some-test-file.png"},
            "description": "Some description",
            "spoiler": False,
        }
        assert attachments == (files.ensure_resource("attachment://some-test-file.png"),)

    def test_build_without_optional_fields(self):
        media_gallery_item = special_endpoints.MediaGalleryItemBuilder(media="some-test-file.png")

        payload, attachments = media_gallery_item.build()

        assert payload == {"media": {"url": "attachment://some-test-file.png"}, "spoiler": False}
        assert attachments == (files.ensure_resource("some-test-file.png"),)


class TestSeparatorComponentBuilder:
    def test_type_property(self):
        separator = special_endpoints.SeparatorComponentBuilder()

        assert separator.type is components.ComponentType.SEPARATOR

    def test_build(self):
        separator = special_endpoints.SeparatorComponentBuilder(
            id=5855932, spacing=components.SpacingType.SMALL, divider=True
        )

        payload, attachments = separator.build()

        assert payload == {
            "type": components.ComponentType.SEPARATOR,
            "id": 5855932,
            "spacing": components.SpacingType.SMALL,
            "divider": True,
        }
        assert attachments == ()

    def test_build_without_optional_fields(self):
        separator = special_endpoints.SeparatorComponentBuilder()

        payload, attachments = separator.build()

        assert payload == {"type": components.ComponentType.SEPARATOR}
        assert attachments == ()


class TestFileComponentBuilder:
    def test_type_property(self):
        file = special_endpoints.FileComponentBuilder(file=mock.Mock())

        assert file.type is components.ComponentType.FILE

    def test_build(self):
        file = special_endpoints.FileComponentBuilder(
            id=5855932, file="https://example.com/some-test-file.png", spoiler=True
        )

        payload, attachments = file.build()

        assert payload == {
            "type": components.ComponentType.FILE,
            "id": 5855932,
            "file": {"url": "https://example.com/some-test-file.png"},
            "spoiler": True,
        }
        assert attachments == (files.ensure_resource("https://example.com/some-test-file.png"),)

    def test_build_without_optional_fields(self):
        file = special_endpoints.FileComponentBuilder(file="some-test-file.png")

        payload, attachments = file.build()

        assert payload == {
            "type": components.ComponentType.FILE,
            "file": {"url": "attachment://some-test-file.png"},
            "spoiler": False,
        }
        assert attachments == (files.ensure_resource("some-test-file.png"),)


class TestMessageContainerBuilder:
    def test_type_property(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.type is components.ComponentType.CONTAINER

    def test_add_component(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.components == []

        component = special_endpoints.SeparatorComponentBuilder()

        container.add_component(component)

        assert container.components == [component]

    def test_add_action_row(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.components == []

        button = special_endpoints.InteractiveButtonBuilder(
            style=components.ButtonStyle.DANGER, custom_id="button", label="test button"
        )

        container.add_action_row([button])

        assert len(container.components) == 1

        component = container.components[0]

        assert isinstance(component, special_endpoints.MessageActionRowBuilder)

        assert component.components == [button]

    def test_add_text_display(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.components == []

        container.add_text_display("A text display!")

        assert len(container.components) == 1

        component = container.components[0]

        assert isinstance(component, special_endpoints.TextDisplayComponentBuilder)

        assert component.content == "A text display!"

    def test_add_media_gallery(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.components == []

        media_gallery_item = special_endpoints.MediaGalleryItemBuilder(
            media="some-test-file.png", description="Some description", spoiler=False
        )
        container.add_media_gallery([media_gallery_item])

        assert len(container.components) == 1
        component = container.components[0]
        assert isinstance(component, special_endpoints.MediaGalleryComponentBuilder)
        assert component.items == [media_gallery_item]

    def test_add_separator(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.components == []

        container.add_separator(spacing=components.SpacingType.LARGE, divider=False)

        assert len(container.components) == 1

        component = container.components[0]

        assert isinstance(component, special_endpoints.SeparatorComponentBuilder)

        assert component.spacing == components.SpacingType.LARGE
        assert component.divider is False

    def test_add_file(self):
        container = special_endpoints.ContainerComponentBuilder()

        assert container.components == []

        container.add_file(file="some-test-file.png", spoiler=True)

        assert len(container.components) == 1
        component = container.components[0]
        assert isinstance(component, special_endpoints.FileComponentBuilder)
        assert component.file == "some-test-file.png"
        assert component.is_spoiler is True

    def test_build(self):
        accent_color = colors.Color.from_hex_code("#FFB123")
        mock_button = mock.Mock(
            special_endpoints.InteractiveButtonBuilder,
            build=mock.Mock(return_value=(mock.Mock(type=components.ComponentType.BUTTON), ())),
        )
        media_gallery_item = special_endpoints.MediaGalleryItemBuilder(
            media="some-test-file.png", description="Some description", spoiler=False
        )

        container = special_endpoints.ContainerComponentBuilder(id=5855932, accent_color=accent_color, spoiler=True)
        container.add_action_row([mock_button], id=3204958)
        container.add_text_display("A text display!", id=8944352)
        container.add_media_gallery([media_gallery_item], id=1098573)
        container.add_separator(spacing=components.SpacingType.LARGE, divider=False, id=9542323)
        container.add_file(file="file.txt", spoiler=True, id=2339534)

        payload, attachments = container.build()

        assert payload == {
            "type": components.ComponentType.CONTAINER,
            "id": 5855932,
            "accent_color": accent_color,
            "spoiler": True,
            "components": [
                {
                    "type": components.ComponentType.ACTION_ROW,
                    "id": 3204958,
                    "components": [mock_button.build.return_value[0]],
                },
                {"type": components.ComponentType.TEXT_DISPLAY, "id": 8944352, "content": "A text display!"},
                {
                    "type": components.ComponentType.MEDIA_GALLERY,
                    "id": 1098573,
                    "items": [
                        {
                            "media": {"url": "attachment://some-test-file.png"},
                            "description": "Some description",
                            "spoiler": False,
                        }
                    ],
                },
                {
                    "type": components.ComponentType.SEPARATOR,
                    "id": 9542323,
                    "spacing": components.SpacingType.LARGE,
                    "divider": False,
                },
                {
                    "type": components.ComponentType.FILE,
                    "id": 2339534,
                    "file": {"url": "attachment://file.txt"},
                    "spoiler": True,
                },
            ],
        }

        mock_button.build.assert_called_once_with()

        assert attachments == [files.ensure_resource("some-test-file.png"), files.ensure_resource("file.txt")]

    def test_build_without_optional_fields(self):
        container = special_endpoints.ContainerComponentBuilder(accent_color=None)

        payload, attachments = container.build()

        assert payload == {
            "type": components.ComponentType.CONTAINER,
            "accent_color": None,
            "spoiler": False,
            "components": [],
        }

        assert attachments == []

    def test_build_without_undefined_fields(self):
        container = special_endpoints.ContainerComponentBuilder()

        payload, attachments = container.build()

        assert payload == {"type": components.ComponentType.CONTAINER, "spoiler": False, "components": []}
        assert attachments == []


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
        mock_component_1 = mock.Mock(
            special_endpoints.InteractiveButtonBuilder,
            build=mock.Mock(return_value=(mock.Mock(type=components.ComponentType.TEXT_INPUT), ())),
        )
        mock_component_2 = mock.Mock(
            special_endpoints.InteractiveButtonBuilder,
            build=mock.Mock(return_value=(mock.Mock(type=components.ComponentType.TEXT_INPUT), ())),
        )

        row = special_endpoints.ModalActionRowBuilder(id=5855932, components=[mock_component_1, mock_component_2])

        payload, attachments = row.build()

        assert payload == {
            "type": components.ComponentType.ACTION_ROW,
            "id": 5855932,
            "components": [mock_component_1.build.return_value[0], mock_component_2.build.return_value[0]],
        }

        mock_component_1.build.assert_called_once_with()
        mock_component_2.build.assert_called_once_with()

        assert attachments == []


class TestPollBuilder:
    def test_add_answer(self):
        poll_builder = special_endpoints.PollBuilder(question_text="A cool question", allow_multiselect=False)

        assert poll_builder.answers == []

        poll_builder.add_answer(text="Beanos", emoji=emojis.UnicodeEmoji("👌"))

        assert len(poll_builder.answers) == 1

        assert poll_builder.answers[0].text == "Beanos"
        assert poll_builder.answers[0].emoji == emojis.UnicodeEmoji("👌")

    def test_build(self):
        poll_builder = special_endpoints.PollBuilder(
            question_text="question_text",
            answers=[
                special_endpoints.PollAnswerBuilder(
                    text="answer_1_text",
                    emoji=emojis.CustomEmoji(id=snowflakes.Snowflake(456), name="question_emoji", is_animated=False),
                ),
                special_endpoints.PollAnswerBuilder(text="answer_2_text"),
                special_endpoints.PollAnswerBuilder(emoji=emojis.UnicodeEmoji("👀")),
            ],
            duration=9,
            allow_multiselect=True,
            layout_type=polls.PollLayoutType.DEFAULT,
        )

        assert poll_builder.build() == {
            "question": {"text": "question_text"},
            "answers": [
                {"poll_media": {"text": "answer_1_text", "emoji": {"id": "456"}}},
                {"poll_media": {"text": "answer_2_text"}},
                {"poll_media": {"emoji": {"name": "👀"}}},
            ],
            "duration": 9,
            "allow_multiselect": True,
            "layout_type": polls.PollLayoutType.DEFAULT,
        }

    def test_build_without_optional_fields(self):
        poll_builder = special_endpoints.PollBuilder(question_text="question_text", allow_multiselect=True)

        assert poll_builder.build() == {"question": {"text": "question_text"}, "answers": [], "allow_multiselect": True}


class TestPollAnswerBuilder:
    def test_build(self):
        poll_answer = special_endpoints.PollAnswerBuilder(
            text="answer_1_text",
            emoji=emojis.CustomEmoji(id=snowflakes.Snowflake(456), name="question_emoji", is_animated=False),
        )

        assert poll_answer.build() == {"poll_media": {"text": "answer_1_text", "emoji": {"id": "456"}}}


class TestAutoModBlockMessageActionBuilder:
    def test_type_property(self):
        block_message_action = special_endpoints.AutoModBlockMessageActionBuilder(custom_message="beanos")

        assert block_message_action.type == auto_mod.AutoModActionType.BLOCK_MESSAGE
        assert block_message_action.custom_message == "beanos"

    def test_build(self):
        block_message_action = special_endpoints.AutoModBlockMessageActionBuilder(custom_message="hello world!")

        assert block_message_action.build() == {
            "type": auto_mod.AutoModActionType.BLOCK_MESSAGE,
            "metadata": {"custom_message": "hello world!"},
        }


class TestAutoModSendAlertMessageActionBuilder:
    def test_type_property(self):
        send_alert_message_action = special_endpoints.AutoModSendAlertMessageActionBuilder(
            channel_id=snowflakes.Snowflake(123)
        )

        assert send_alert_message_action.type == auto_mod.AutoModActionType.SEND_ALERT_MESSAGE
        assert send_alert_message_action.channel_id == snowflakes.Snowflake(123)

    def test_build(self):
        send_alert_message_action = special_endpoints.AutoModSendAlertMessageActionBuilder(
            channel_id=snowflakes.Snowflake(456)
        )

        assert send_alert_message_action.build() == {
            "type": auto_mod.AutoModActionType.SEND_ALERT_MESSAGE,
            "metadata": {"channel_id": 456},
        }


class TestAutoModTimeoutActionBuilder:
    def test_type_property(self):
        timeout_action = special_endpoints.AutoModTimeoutActionBuilder(duration_seconds=3)

        assert timeout_action.type == auto_mod.AutoModActionType.TIMEOUT
        assert timeout_action.duration_seconds == 3

    def test_build(self):
        timeout_action = special_endpoints.AutoModTimeoutActionBuilder(duration_seconds=5)

        assert timeout_action.build() == {
            "type": auto_mod.AutoModActionType.TIMEOUT,
            "metadata": {"duration_seconds": 5},
        }


class TestAutoModBlockMemberInteractionActionBuilder:
    def test_type_property(self):
        block_member_interaction_action = special_endpoints.AutoModBlockMemberInteractionActionBuilder()

        assert block_member_interaction_action.type == auto_mod.AutoModActionType.BLOCK_MEMBER_INTERACTION

    def test_build(self):
        block_member_interaction_action = special_endpoints.AutoModBlockMemberInteractionActionBuilder()

        assert block_member_interaction_action.build() == {
            "type": auto_mod.AutoModActionType.BLOCK_MEMBER_INTERACTION,
            "metadata": {},
        }


class TestAutoModKeywordTriggerBuilder:
    def test_type_property(self):
        keyword_trigger = special_endpoints.AutoModKeywordTriggerBuilder(
            keyword_filter=["keyword", "filter"], regex_patterns=["regex", "patterns"], allow_list=["allow", "list"]
        )

        assert keyword_trigger.type == auto_mod.AutoModTriggerType.KEYWORD
        assert keyword_trigger.keyword_filter == ["keyword", "filter"]
        assert keyword_trigger.regex_patterns == ["regex", "patterns"]
        assert keyword_trigger.allow_list == ["allow", "list"]

    def test_build(self):
        keyword_trigger = special_endpoints.AutoModKeywordTriggerBuilder(
            keyword_filter=["keyword", "filter"], regex_patterns=["regex", "patterns"], allow_list=["allow", "list"]
        )

        assert keyword_trigger.build() == {
            "keyword_filter": ["keyword", "filter"],
            "regex_patterns": ["regex", "patterns"],
            "allow_list": ["allow", "list"],
        }


class TestAutoModSpamTriggerBuilder:
    def test_type_property(self):
        spam_trigger = special_endpoints.AutoModSpamTriggerBuilder()

        assert spam_trigger.type == auto_mod.AutoModTriggerType.SPAM

    def test_build(self):
        spam_trigger = special_endpoints.AutoModSpamTriggerBuilder()

        assert spam_trigger.build() == {}


class TestAutoModKeywordPresetTriggerBuilder:
    def test_type_property(self):
        keyword_preset_trigger = special_endpoints.AutoModKeywordPresetTriggerBuilder(
            presets=[auto_mod.AutoModKeywordPresetType.PROFANITY, auto_mod.AutoModKeywordPresetType.SLURS],
            allow_list=["allow", "list"],
        )

        assert keyword_preset_trigger.type == auto_mod.AutoModTriggerType.KEYWORD_PRESET
        assert keyword_preset_trigger.presets == [
            auto_mod.AutoModKeywordPresetType.PROFANITY,
            auto_mod.AutoModKeywordPresetType.SLURS,
        ]
        assert keyword_preset_trigger.allow_list == ["allow", "list"]

    def test_build(self):
        keyword_preset_trigger = special_endpoints.AutoModKeywordPresetTriggerBuilder(
            presets=[auto_mod.AutoModKeywordPresetType.PROFANITY, auto_mod.AutoModKeywordPresetType.SLURS],
            allow_list=["allow", "list"],
        )

        assert keyword_preset_trigger.build() == {"presets": [1, 3], "allow_list": ["allow", "list"]}


class TestAutoModMentionSpamTriggerBuilder:
    def test_type_property(self):
        mention_spam_trigger = special_endpoints.AutoModMentionSpamTriggerBuilder(
            mention_total_limit=3, mention_raid_protection_enabled=True
        )

        assert mention_spam_trigger.type == auto_mod.AutoModTriggerType.MENTION_SPAM
        assert mention_spam_trigger.mention_total_limit == 3
        assert mention_spam_trigger.mention_raid_protection_enabled is True

    def test_build(self):
        mention_spam_trigger = special_endpoints.AutoModMentionSpamTriggerBuilder(
            mention_total_limit=5, mention_raid_protection_enabled=False
        )

        assert mention_spam_trigger.build() == {"mention_total_limit": 5, "mention_raid_protection_enabled": False}


class TestAutoModMemberProfileTriggerBuilder:
    def test_type_property(self):
        member_profile_trigger = special_endpoints.AutoModMemberProfileTriggerBuilder(
            keyword_filter=["keyword", "filter"], regex_patterns=["regex", "patterns"], allow_list=["allow", "list"]
        )

        assert member_profile_trigger.type == auto_mod.AutoModTriggerType.MEMBER_PROFILE
        assert member_profile_trigger.keyword_filter == ["keyword", "filter"]
        assert member_profile_trigger.regex_patterns == ["regex", "patterns"]
        assert member_profile_trigger.allow_list == ["allow", "list"]

    def test_build(self):
        member_profile_trigger = special_endpoints.AutoModMemberProfileTriggerBuilder(
            keyword_filter=["keyword", "filter"], regex_patterns=["regex", "patterns"], allow_list=["allow", "list"]
        )

        assert member_profile_trigger.build() == {
            "keyword_filter": ["keyword", "filter"],
            "regex_patterns": ["regex", "patterns"],
            "allow_list": ["allow", "list"],
        }

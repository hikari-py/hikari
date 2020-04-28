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
import mock
import pytest

from hikari.internal import helpers
from hikari import guilds
from hikari import users
from tests.hikari import _helpers


@pytest.mark.parametrize(
    ("kwargs", "expected_result"),
    [
        (
            {"mentions_everyone": True, "user_mentions": True, "role_mentions": True},
            {"parse": ["everyone", "users", "roles"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": False, "role_mentions": False},
            {"parse": [], "users": [], "roles": []},
        ),
        (
            {"mentions_everyone": True, "user_mentions": ["1123123"], "role_mentions": True},
            {"parse": ["everyone", "roles"], "users": ["1123123"]},
        ),
        (
            {"mentions_everyone": True, "user_mentions": True, "role_mentions": ["1231123"]},
            {"parse": ["everyone", "users"], "roles": ["1231123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": ["1123123"], "role_mentions": True},
            {"parse": ["roles"], "users": ["1123123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": True, "role_mentions": ["1231123"]},
            {"parse": ["users"], "roles": ["1231123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": ["1123123"], "role_mentions": False},
            {"parse": [], "roles": [], "users": ["1123123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": False, "role_mentions": ["1231123"]},
            {"parse": [], "roles": ["1231123"], "users": []},
        ),
        (
            {"mentions_everyone": False, "user_mentions": ["22222"], "role_mentions": ["1231123"]},
            {"parse": [], "users": ["22222"], "roles": ["1231123"]},
        ),
        (
            {"mentions_everyone": True, "user_mentions": ["22222"], "role_mentions": ["1231123"]},
            {"parse": ["everyone"], "users": ["22222"], "roles": ["1231123"]},
        ),
    ],
)
def test_generate_allowed_mentions(kwargs, expected_result):
    assert helpers.generate_allowed_mentions(**kwargs) == expected_result


@_helpers.parametrize_valid_id_formats_for_models("role", 3, guilds.GuildRole)
def test_generate_allowed_mentions_removes_duplicate_role_ids(role):
    result = helpers.generate_allowed_mentions(
        role_mentions=["1", "2", "1", "3", "5", "7", "2", role], user_mentions=True, mentions_everyone=True
    )
    assert result == {"roles": ["1", "2", "3", "5", "7"], "parse": ["everyone", "users"]}


@_helpers.parametrize_valid_id_formats_for_models("user", 3, users.User)
def test_generate_allowed_mentions_removes_duplicate_user_ids(user):
    result = helpers.generate_allowed_mentions(
        role_mentions=True, user_mentions=["1", "2", "1", "3", "5", "7", "2", user], mentions_everyone=True
    )
    assert result == {"users": ["1", "2", "3", "5", "7"], "parse": ["everyone", "roles"]}


@_helpers.parametrize_valid_id_formats_for_models("role", 190007233919057920, guilds.GuildRole)
def test_generate_allowed_mentions_handles_all_role_formats(role):
    result = helpers.generate_allowed_mentions(role_mentions=[role], user_mentions=True, mentions_everyone=True)
    assert result == {"roles": ["190007233919057920"], "parse": ["everyone", "users"]}


@_helpers.parametrize_valid_id_formats_for_models("user", 190007233919057920, users.User)
def test_generate_allowed_mentions_handles_all_user_formats(user):
    result = helpers.generate_allowed_mentions(role_mentions=True, user_mentions=[user], mentions_everyone=True)
    assert result == {"users": ["190007233919057920"], "parse": ["everyone", "roles"]}


@_helpers.assert_raises(type_=ValueError)
def test_generate_allowed_mentions_raises_error_on_too_many_roles():
    helpers.generate_allowed_mentions(user_mentions=False, role_mentions=list(range(101)), mentions_everyone=False)


@_helpers.assert_raises(type_=ValueError)
def test_generate_allowed_mentions_raises_error_on_too_many_users():
    helpers.generate_allowed_mentions(user_mentions=list(range(101)), role_mentions=False, mentions_everyone=False)


@pytest.mark.asyncio
async def test_pagination_handler_handles_empty_resource():
    mock_deserialize = mock.MagicMock()
    mock_request = mock.AsyncMock(side_effect=[[]])
    async for _ in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start="123123123",
        maximum_limit=100,
        limit=42,
    ):
        assert False, "Async generator shouldn't have yielded anything."
    mock_request.assert_called_once_with(
        limit=42, before="123123123",
    )
    mock_deserialize.assert_not_called()


@pytest.mark.asyncio
async def test_pagination_handler_ends_without_limit_with_start():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start="123123123",
        maximum_limit=100,
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls([mock.call(limit=100, before="123123123"), mock.call(limit=100, before="20202020"),],)
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
    )


@pytest.mark.asyncio
async def test_pagination_handler_before_pagination():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    async for _ in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start="9223372036854775807",
        maximum_limit=100,
        limit=None,
    ):
        break
    mock_request.assert_called_once_with(limit=100, before="9223372036854775807")


@pytest.mark.asyncio
async def test_pagination_handler_after_pagination():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    async for _ in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="after",
        request=mock_request,
        reversing=False,
        start="0",
        limit=None,
        maximum_limit=1000,
    ):
        break
    mock_request.assert_called_once_with(limit=1000, after="0")


@pytest.mark.asyncio
async def test_pagination_handler_ends_without_limit_without_start():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start="9223372036854775807",
        maximum_limit=100,
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [mock.call(limit=100, before="9223372036854775807"), mock.call(limit=100, before="20202020")],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
    )


@pytest.mark.asyncio
async def test_pagination_handler_tracks_ends_when_hits_limit():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start="9223372036854775807",
        maximum_limit=100,
        limit=2,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_called_once_with(limit=2, before="9223372036854775807")
    mock_deserialize.assert_has_calls([mock.call({"id": "312312312"}), mock.call({"id": "31231231"})])


@pytest.mark.asyncio
async def test_pagination_handler_tracks_ends_when_limit_set_but_exhausts_requested_data():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start="9223372036854775807",
        maximum_limit=100,
        limit=42,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [mock.call(limit=42, before="9223372036854775807"), mock.call(limit=39, before="20202020"),],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "312312312"}), mock.call({"id": "31231231"}), mock.call({"id": "20202020"})]
    )


@pytest.mark.asyncio
async def test_pagination_handler_reverses_data_when_reverse_is_true():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start="9223372036854775807",
        maximum_limit=100,
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [mock.call(limit=100, before="9223372036854775807"), mock.call(limit=100, before="20202020"),],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
    )


@pytest.mark.asyncio
async def test_pagination_handler_id_getter():
    mock_payloads = [{"id": "312312312"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(user=mock.MagicMock(__int__=lambda x: 20202020))]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in helpers.pagination_handler(
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start="9223372036854775807",
        id_getter=lambda entity: str(int(entity.user)),
        maximum_limit=100,
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [mock.call(limit=100, before="9223372036854775807"), mock.call(limit=100, before="20202020"),],
    )
    mock_deserialize.assert_has_calls([mock.call({"id": "312312312"}), mock.call({"id": "20202020"})])

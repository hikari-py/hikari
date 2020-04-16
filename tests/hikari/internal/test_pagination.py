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
import pytest
import mock

from hikari.internal import pagination


@pytest.mark.asyncio
async def test__pagination_handler_ends_handles_empty_resource():
    mock_deserialize = mock.MagicMock()
    mock_request = mock.AsyncMock(side_effect=[[]])
    async for _ in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start="123123123",
        limit=42,
    ):
        assert False, "Async generator shouldn't have yielded anything."
    mock_request.assert_called_once_with(
        limit=42, before="123123123", random_kwarg="test",
    )
    mock_deserialize.assert_not_called()


@pytest.mark.asyncio
async def test__pagination_handler_ends_without_limit_with_start():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start="123123123",
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [
            mock.call(limit=100, before="123123123", random_kwarg="test"),
            mock.call(limit=100, before="20202020", random_kwarg="test"),
        ],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
    )


@pytest.mark.asyncio
async def test__pagination_handler_ends_without_limit_without_start():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start=None,
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [
            mock.call(limit=100, before=..., random_kwarg="test"),
            mock.call(limit=100, before="20202020", random_kwarg="test"),
        ],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
    )


@pytest.mark.asyncio
async def test__pagination_handler_tracks_ends_when_hits_limit():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start=None,
        limit=2,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_called_once_with(limit=2, before=..., random_kwarg="test")
    mock_deserialize.assert_has_calls([mock.call({"id": "312312312"}), mock.call({"id": "31231231"})])


@pytest.mark.asyncio
async def test__pagination_handler_tracks_ends_when_limit_set_but_exhausts_requested_data():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start=None,
        limit=42,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [
            mock.call(limit=42, before=..., random_kwarg="test"),
            mock.call(limit=39, before="20202020", random_kwarg="test"),
        ],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "312312312"}), mock.call({"id": "31231231"}), mock.call({"id": "20202020"})]
    )


@pytest.mark.asyncio
async def test__pagination_handler_reverses_data_when_reverse_is_true():
    mock_payloads = [{"id": "312312312"}, {"id": "31231231"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock(id=20202020)]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start=None,
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [
            mock.call(limit=100, before=..., random_kwarg="test"),
            mock.call(limit=100, before="20202020", random_kwarg="test"),
        ],
    )
    mock_deserialize.assert_has_calls(
        [mock.call({"id": "20202020"}), mock.call({"id": "31231231"}), mock.call({"id": "312312312"})]
    )


@pytest.mark.asyncio
async def test__pagination_handler_id_getter():
    mock_payloads = [{"id": "312312312"}, {"id": "20202020"}]
    mock_models = [mock.MagicMock(), mock.MagicMock(user=mock.MagicMock(__int__=lambda x: 20202020))]
    mock_deserialize = mock.MagicMock(side_effect=mock_models)
    mock_request = mock.AsyncMock(side_effect=[mock_payloads, []])
    results = []
    async for result in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=False,
        start=None,
        id_getter=lambda entity: str(int(entity.user)),
        limit=None,
    ):
        results.append(result)
    assert results == mock_models
    mock_request.assert_has_calls(
        [
            mock.call(limit=100, before=..., random_kwarg="test"),
            mock.call(limit=100, before="20202020", random_kwarg="test"),
        ],
    )
    mock_deserialize.assert_has_calls([mock.call({"id": "312312312"}), mock.call({"id": "20202020"})])


@pytest.mark.asyncio
async def test__pagination_handler_handles_no_initial_data():
    mock_deserialize = mock.MagicMock()
    mock_request = mock.AsyncMock(side_effect=[[]])
    async for _ in pagination.pagination_handler(
        random_kwarg="test",
        deserializer=mock_deserialize,
        direction="before",
        request=mock_request,
        reversing=True,
        start=None,
        limit=None,
    ):
        assert False, "Async generator shouldn't have yielded anything."
    mock_request.assert_called_once_with(
        limit=100, before=..., random_kwarg="test",
    )
    mock_deserialize.assert_not_called()

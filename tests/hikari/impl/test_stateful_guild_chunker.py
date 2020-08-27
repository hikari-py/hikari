# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import contextlib
import copy
import time

import mock
import pytest

from hikari import guilds
from hikari import intents
from hikari import snowflakes
from hikari import undefined
from hikari.events import shard_events
from hikari.impl import bot
from hikari.impl import shard
from hikari.impl import stateful_guild_chunker
from hikari.utilities import attr_extensions
from tests.hikari import hikari_test_helpers


@pytest.fixture()
def mock_app():
    app = mock.Mock(bot.BotApp)
    app.shards = {
        0: mock.Mock(shard.GatewayShardImpl, request_guild_members=mock.AsyncMock()),
        1: mock.Mock(shard.GatewayShardImpl, request_guild_members=mock.AsyncMock()),
        2: mock.Mock(shard.GatewayShardImpl, request_guild_members=mock.AsyncMock()),
        3: mock.Mock(shard.GatewayShardImpl, request_guild_members=mock.AsyncMock()),
    }
    app.shard_count = len(app.shards)
    return app


@pytest.mark.parametrize(("guild_id", "expected_id"), [])  # FIXME: add cases
def test__get_shard_id(mock_app, guild_id, expected_id):
    assert stateful_guild_chunker._get_shard_id(mock_app, guild_id) == expected_id


def test__random_nonce():
    result = stateful_guild_chunker._random_nonce()
    assert isinstance(result, str)
    assert len(result) == 28


class TestChunkStream:
    def test__listener(self):
        ...

    def test___anext__(self):
        ...

    def test_open_for_active_stream(self):
        ...

    def test_open_for_inactive_stream(self):
        ...


class TestTrackedChunks:
    def test___copy___when_missing_chunks_is_not_none(self):
        obj = hikari_test_helpers.stub_class(
            stateful_guild_chunker._TrackedChunks, missing_chunks=[5, 6, 7, 8, 9], not_found=[2, 4, 6, 7, 8]
        )
        new_obj = hikari_test_helpers.stub_class(stateful_guild_chunker._TrackedChunks)

        with mock.patch.object(attr_extensions, "copy_attrs", return_value=new_obj):
            result = copy.copy(obj)
            attr_extensions.copy_attrs.assert_called_once_with(obj)

        assert result is new_obj
        assert result.missing_chunks == obj.missing_chunks
        assert result.missing_chunks is not obj.missing_chunks
        assert result.not_found == obj.not_found
        assert result.not_found is not obj.not_found

    def test___copy___when_missing_chunks_is_none(self):
        obj = hikari_test_helpers.stub_class(
            stateful_guild_chunker._TrackedChunks, missing_chunks=None, not_found=[2, 4, 6, 7, 8]
        )
        new_obj = hikari_test_helpers.stub_class(stateful_guild_chunker._TrackedChunks)

        with mock.patch.object(attr_extensions, "copy_attrs", return_value=new_obj):
            result = copy.copy(obj)
            attr_extensions.copy_attrs.assert_called_once_with(obj)

        assert result.missing_chunks is None

    def test_is_complete_when_complete(self):
        obj = hikari_test_helpers.mock_class_namespace(
            stateful_guild_chunker._TrackedChunks, received_chunks=mock.PropertyMock(return_value=42), init=False
        )()
        obj.chunk_count = 42
        assert obj.is_complete is True

    def test_is_complete_when_timed_out(self):
        obj = hikari_test_helpers.mock_class_namespace(
            stateful_guild_chunker._TrackedChunks, received_chunks=mock.PropertyMock(return_value=42), init=False
        )()
        obj.chunk_count = 83
        obj.last_received = 3123452134

        with mock.patch.object(
            time, "monotonic_ns", return_value=obj.last_received + stateful_guild_chunker.EXPIRY_TIME + 50
        ):
            assert obj.is_complete is True
            time.monotonic_ns.assert_called_once()

    def test_is_complete_when_not_timed_out(self):
        obj = hikari_test_helpers.mock_class_namespace(
            stateful_guild_chunker._TrackedChunks, received_chunks=mock.PropertyMock(return_value=42), init=False
        )()
        obj.chunk_count = 83
        obj.last_received = 3123452134

        with mock.patch.object(
            time, "monotonic_ns", return_value=obj.last_received + (stateful_guild_chunker.EXPIRY_TIME / 2)
        ):
            assert obj.is_complete is False
            time.monotonic_ns.assert_called_once()

    def test_is_complete_when_not_yet_received(self):
        obj = hikari_test_helpers.mock_class_namespace(
            stateful_guild_chunker._TrackedChunks, received_chunks=mock.PropertyMock(return_value=42), init=False
        )()
        obj.chunk_count = 84
        obj.last_received = None

        assert obj.is_complete is False

    def test_received_chunks_when_no_chunks_received_yet(self):
        obj = hikari_test_helpers.stub_class(
            stateful_guild_chunker._TrackedChunks, chunk_count=None, missing_chunks=None
        )
        assert obj.received_chunks == 0

    def test_received_chunks(self):
        obj = hikari_test_helpers.stub_class(
            stateful_guild_chunker._TrackedChunks,
            chunk_count=25,
            missing_chunks=[15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
        )
        assert obj.received_chunks == 14


class TestStatefulGuildChunkerImpl:
    @pytest.fixture()
    def mock_chunker(self, mock_app):
        return stateful_guild_chunker.StatefulGuildChunkerImpl(mock_app)

    def test__default_include_presences_when_include_presences_already_set(self, mock_chunker):
        assert mock_chunker._default_include_presences(54234, True) is True

    def test__default_include_presences_default_when_intents_is_none(self, mock_chunker, mock_app):
        mock_app.shards[0].intents = None
        assert mock_chunker._default_include_presences(54234, undefined.UNDEFINED) is True

    def test__default_include_presences_default_when_declaring_presences_intents(self, mock_chunker, mock_app):
        mock_app.shards[1].intents = intents.Intents.GUILD_PRESENCES | intents.Intents.GUILD_MESSAGES
        assert mock_chunker._default_include_presences(655288690192416778, undefined.UNDEFINED) is True

    def test__default_include_presences_default_when_not_declaring_presences_intents(self, mock_chunker, mock_app):
        mock_app.shards[1].intents = intents.Intents.GUILD_MEMBERS | intents.Intents.GUILD_MESSAGES
        assert mock_chunker._default_include_presences(574921006817476608, undefined.UNDEFINED) is False

    def test_fetch_members_for_guild(self):
        ...

    def test_get_chunk_status_for_invalid_nonce(self):
        ...

    def test_get_chunk_status_for_unknown_shard(self):
        ...

    def test_get_chunk_status_for_unknown_nonce(self):
        ...

    def test_get_chunk_status_for_known_nonce(self):
        ...

    def test_list_chunk_statuses_for_shard_for_known_shard(self):
        ...

    def test_list_chunk_statuses_for_shard_for_unknown_shard(self):
        ...

    def test_list_chunk_statuses_for_guild_for_unknown_shard(self):
        ...

    def test_list_chunk_statuses_for_guild_for_known_shard(self):
        ...

    @pytest.mark.asyncio
    def test_on_chunk_event_for_unknown_shard(self):
        ...

    @pytest.mark.asyncio
    def test_on_chunk_event_for_unknown_nonce(self):
        ...

    @pytest.mark.asyncio
    def test_on_chunk_event_when_initial_tracking_information_not_set(self):
        ...

    @pytest.mark.asyncio
    def test_on_chunk_event_when_initial_tracking_information_set(self):
        ...

    @pytest.mark.asyncio
    async def test_request_guild_members_when_shard_not_previously_tracked_without_optionals(self, mock_chunker, mock_app):
        mock_app.shards[2].intents= intents.Intents.GUILD_MESSAGES

        with mock.patch.object(stateful_guild_chunker, "_random_nonce", return_value="NonceNonceNonceNonce"):
            result = await mock_chunker.request_guild_members(
                745181921625243730,
            )

            stateful_guild_chunker._random_nonce.assert_called_once()

        assert result == "2.NonceNonceNonceNonce"
        assert len(mock_chunker._tracked[2]) == 1
        assert mock_chunker._tracked[2]["2.NonceNonceNonceNonce"].guild_id == snowflakes.Snowflake(745181921625243730)
        assert mock_chunker._tracked[2]["2.NonceNonceNonceNonce"].nonce == "2.NonceNonceNonceNonce"
        mock_app.shards[2].request_guild_members.assert_called_once_with(
            guild=snowflakes.Snowflake(745181921625243730),
            include_presences=False,
            limit=0,
            nonce="2.NonceNonceNonceNonce",
            query="",
            users=undefined.UNDEFINED
        )

    @pytest.mark.parametrize(
        ("guild"),
        [hikari_test_helpers.stub_class(guilds.GatewayGuild, id=snowflakes.Snowflake(43123)), 43123, "43123", snowflakes.Snowflake(43123)]
    )
    @pytest.mark.asyncio
    async def test_request_guild_members_when_shard_previously_tracked_with_optionals(self, mock_chunker, mock_app, guild):
        mock_chunker._tracked[0] = {"randomNonce": object()}

        with mock.patch.object(stateful_guild_chunker, "_random_nonce", return_value="AvEryCrYpToGraPhIcNoNcE"):
            result = await mock_chunker.request_guild_members(
                guild,
                include_presences=True,
                limit=53,
                query="Kiss",
                users=[snowflakes.Snowflake(1235432)]
            )

            stateful_guild_chunker._random_nonce.assert_called_once()

        assert result == "0.AvEryCrYpToGraPhIcNoNcE"
        assert len(mock_chunker._tracked[0]) == 2
        assert mock_chunker._tracked[0]["0.AvEryCrYpToGraPhIcNoNcE"].guild_id == snowflakes.Snowflake(43123)
        assert mock_chunker._tracked[0]["0.AvEryCrYpToGraPhIcNoNcE"].nonce == "0.AvEryCrYpToGraPhIcNoNcE"
        mock_app.shards[0].request_guild_members.assert_called_once_with(
            guild=snowflakes.Snowflake(43123),
            include_presences=True,
            limit=53,
            nonce="0.AvEryCrYpToGraPhIcNoNcE",
            query="Kiss",
            users=[snowflakes.Snowflake(1235432)]
        )



    @pytest.mark.asyncio
    async def test_close(self, mock_chunker):
        assert await mock_chunker.close() is None

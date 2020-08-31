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

import pytest

from hikari.impl import stateless_guild_chunker


class TestStatelessGuildChunkerImpl:
    @pytest.fixture()
    def component(self):
        return stateless_guild_chunker.StatelessGuildChunkerImpl()

    @pytest.mark.asyncio
    async def test_fetch_members_for_guild_returns_empty_streamer(self, component):
        async with component.fetch_members_for_guild(31234, timeout=None) as streamer:
            assert await streamer == []

    @pytest.mark.asyncio
    async def test_get_request_status(self, component):
        assert await component.get_request_status("ofkfkf") is None

    @pytest.mark.asyncio
    async def test_list_requests_for_shard(self, component):
        assert await component.list_requests_for_shard(4) == ()

    @pytest.mark.asyncio
    async def test_list_requests_for_guild(self, component):
        assert await component.list_requests_for_guild(53421134123) == ()

    @pytest.mark.asyncio
    async def test_consume_chunk_event(self, component):
        with pytest.raises(NotImplementedError):
            assert await component.consume_chunk_event(object())

    @pytest.mark.asyncio
    async def test_request_guild_chunk_raises_NotImplementedError(self, component):
        with pytest.raises(NotImplementedError):
            await component.request_guild_members(object())

    @pytest.mark.asyncio
    async def test_close(self, component):
        assert await component.close() is None

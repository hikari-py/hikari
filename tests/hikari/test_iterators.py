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
import pytest

from hikari import iterators
from tests.hikari import hikari_test_helpers


class TestLazyIterator:
    @pytest.fixture
    def lazy_iterator(self):
        return hikari_test_helpers.mock_class_namespace(iterators.LazyIterator)()

    def test_asynchronous_only(self, lazy_iterator):
        with pytest.raises(TypeError, match="is async-only, did you mean 'async for' or `anext`?"):
            next(lazy_iterator)

    @pytest.mark.asyncio
    async def test_flatten(self):
        iterator = iterators.FlatLazyIterator([[123, 321, 4352, 123], [], [12343123, 4234432], [543123123]])

        assert await iterator.flatten() == [123, 321, 4352, 123, 12343123, 4234432, 543123123]

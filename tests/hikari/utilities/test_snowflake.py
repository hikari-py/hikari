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
import datetime

import pytest

from hikari.utilities import snowflake


@pytest.fixture()
def raw_id():
    return 537_340_989_808_050_216


@pytest.fixture()
def neko_snowflake(raw_id):
    return snowflake.Snowflake(raw_id)


class TestSnowflake:
    def test_created_at(self, neko_snowflake):
        assert neko_snowflake.created_at == datetime.datetime(
            2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc
        )

    def test_increment(self, neko_snowflake):
        assert neko_snowflake.increment == 40

    def test_internal_process_id(self, neko_snowflake):
        assert neko_snowflake.internal_process_id == 0

    def test_internal_worker_id(self, neko_snowflake):
        assert neko_snowflake.internal_worker_id == 2

    def test_hash(self, neko_snowflake, raw_id):
        assert hash(neko_snowflake) == raw_id

    def test_int_cast(self, neko_snowflake, raw_id):
        assert int(neko_snowflake) == raw_id

    def test_str_cast(self, neko_snowflake, raw_id):
        assert str(neko_snowflake) == str(raw_id)

    def test_repr_cast(self, neko_snowflake, raw_id):
        assert repr(neko_snowflake) == repr(raw_id)

    def test_eq(self, neko_snowflake, raw_id):
        assert neko_snowflake == raw_id
        assert neko_snowflake == snowflake.Snowflake(raw_id)
        assert str(raw_id) != neko_snowflake

    def test_lt(self, neko_snowflake, raw_id):
        assert neko_snowflake < raw_id + 1

    def test_deserialize(self, neko_snowflake, raw_id):
        assert neko_snowflake == snowflake.Snowflake(raw_id)

    def test_from_datetime(self):
        result = snowflake.Snowflake.from_datetime(
            datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        )
        assert result == 537340989807788032
        assert isinstance(result, snowflake.Snowflake)

    def test_min(self):
        sf = snowflake.Snowflake.min()
        assert sf == 0
        assert snowflake.Snowflake.min() is sf

    def test_max(self):
        sf = snowflake.Snowflake.max()
        assert sf == (1 << 63) - 1
        assert snowflake.Snowflake.max() is sf


class TestUnique:
    @pytest.fixture
    def neko_unique(self, neko_snowflake):
        class NekoUnique(snowflake.Unique):
            id = neko_snowflake

        return NekoUnique()

    def test_created_at(self, neko_unique):
        assert neko_unique.created_at == datetime.datetime(
            2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc
        )

    def test__hash__(self, neko_unique, raw_id):
        assert hash(neko_unique) == raw_id

    def test__eq__(self, neko_snowflake, raw_id):
        class NekoUnique(snowflake.Unique):
            id = neko_snowflake

        class NekoUnique2(snowflake.Unique):
            id = neko_snowflake

        unique1 = NekoUnique()
        unique2 = NekoUnique()

        assert unique1 == unique2
        assert unique1 != NekoUnique2()
        assert unique1 != raw_id

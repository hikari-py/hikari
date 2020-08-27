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
import asyncio
import datetime

import pytest

from hikari.utilities import mapping


class TestMRUMutableMapping:
    def test___init___raises_value_error_on_invalid_expiry(self):
        with pytest.raises(ValueError):
            mapping.MRUMutableMapping(datetime.timedelta(seconds=0))

        with pytest.raises(ValueError):
            mapping.MRUMutableMapping(datetime.timedelta(seconds=-50))

    def test___delitem__(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=100))
        mock_map.update({"ok": "no", "ayanami": "rei qt"})
        del mock_map["ok"]
        assert mock_map == {"ayanami": "rei qt"}

    @pytest.mark.asyncio
    async def test___delitem___garbage_collection(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=0.2))
        mock_map.update({"nyaa": "see", "awwo": "awoo2"})
        await asyncio.sleep(0.1)
        assert mock_map == {"nyaa": "see", "awwo": "awoo2"}
        mock_map.update({"ayanami": "shinji", "rei": "aww"})
        assert mock_map == {"nyaa": "see", "awwo": "awoo2", "ayanami": "shinji", "rei": "aww"}
        await asyncio.sleep(0.15)
        del mock_map["ayanami"]
        assert mock_map == {"rei": "aww"}

    def test___getitem___for_valid_entry(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=100))
        mock_map["OK"] = 42
        mock_map["blam"] = 8
        assert mock_map["OK"] == 42

    def test___getitem___for_unknown_entry(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=100))
        mock_map["blam"] = 8

        with pytest.raises(KeyError):
            assert not mock_map["OK"]

    def test___iter__(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=100))
        mock_map.update({"o": "k", "k": "o", "awoo": "blam", "hikari": "rei"})
        assert list(mock_map) == ["o", "k", "awoo", "hikari"]

    def test___len__(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=100))
        mock_map.update({"o": "k", "boop": "bop", "k": "o", "awoo": "blam", "rei": "cute", "hikari": "rei"})
        assert len(mock_map) == 6

    def test___setitem__(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=100))
        mock_map["blat"] = 42
        assert mock_map == {"blat": 42}

    @pytest.mark.asyncio
    async def test___setitem___garbage_collection(self):
        mock_map = mapping.MRUMutableMapping(datetime.timedelta(seconds=0.25))
        mock_map.update({"OK": "no", "blam": "booga"})
        await asyncio.sleep(0.1)
        assert mock_map == {"OK": "no", "blam": "booga"}
        mock_map.update({"ayanami": "rei", "owo": "awoo"})
        assert mock_map == {"OK": "no", "blam": "booga", "ayanami": "rei", "owo": "awoo"}
        await asyncio.sleep(0.2)
        mock_map.update({"nyaa": "qt"})
        assert mock_map == {"ayanami": "rei", "owo": "awoo", "nyaa": "qt"}


class TestCMRIMutableMapping:
    def test___delitem___for_existing_entry(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        mock_map["Ok"] = 42
        del mock_map["Ok"]
        assert "Ok" not in mock_map

    def test___delitem___for_non_existing_entry(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        with pytest.raises(KeyError):
            del mock_map["Blam"]

    def test___getitem___for_existing_entry(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        mock_map["blat"] = 42
        assert mock_map["blat"] == 42

    def test___getitem___for_non_existing_entry(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        with pytest.raises(KeyError):
            assert mock_map["CIA"]

    def test___iter___(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        mock_map.update({"OK": "blam", "blaaa": "neoeo", "neon": "genesis", "evangelion": None})
        assert list(mock_map) == ["OK", "blaaa", "neon", "evangelion"]

    def test___len___(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        mock_map.update({"ooga": "blam", "blaaa": "neoeo", "the": "boys", "neon": "genesis", "evangelion": None})
        assert len(mock_map) == 5

    def test___setitem___when_limit_not_reached(self):
        mock_map = mapping.CMRIMutableMapping(limit=50)
        mock_map["OK"] = 523
        mock_map["blam"] = 512387
        mock_map.update({"bll": "no", "ieiei": "lslsl"})
        assert mock_map == {"OK": 523, "blam": 512387, "bll": "no", "ieiei": "lslsl"}

    def test___setitem___when_limit_reached(self):
        mock_map = mapping.CMRIMutableMapping(limit=4)
        mock_map.update({"bll": "no", "ieiei": "lslsl", "pacify": "me", "qt": "pie"})
        mock_map["eva"] = "Rei"
        mock_map.update({"shinji": "ikari"})
        assert mock_map == {"pacify": "me", "qt": "pie", "eva": "Rei", "shinji": "ikari"}


def test_get_index_or_slice_with_index_within_range():
    result = mapping.get_index_or_slice({"i": "e", "n": "o", "b": "a", "hikari": "Rei", "p": "a", "o": "o"}, 3)
    assert result == "Rei"


def test_get_index_or_slice_with_index_outside_range():
    with pytest.raises(IndexError):
        assert not mapping.get_index_or_slice({"i": "e", "n": "o", "b": "a", "hikari": "noa"}, 77)


def test_get_index_or_slice_with_slice():
    test_map = {"o": "b", "b": "o", "a": "m", "arara": "blam", "oof": "no", "rika": "may"}
    assert mapping.get_index_or_slice(test_map, slice(1, 5, 2)) == ("o", "blam")


def test_get_index_or_slice_with_invalid_type():
    with pytest.raises(TypeError):
        assert mapping.get_index_or_slice({}, object())

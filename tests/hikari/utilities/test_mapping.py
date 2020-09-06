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
import time

import pytest

from hikari.utilities import mapping
from tests.hikari import hikari_test_helpers


class TestDictionaryCollection:
    def test___init___with_source(self):
        mock_map = mapping.DictionaryCollection({"o": "NO", "bye": "blam", "foo": "bar"})
        assert mock_map == {"o": "NO", "bye": "blam", "foo": "bar"}

    def test_copy(self):
        mock_map = mapping.DictionaryCollection({"foo": "bar", "crash": "balloon"})
        result = mock_map.copy()

        assert result == {"foo": "bar", "crash": "balloon"}
        assert isinstance(result, mapping.DictionaryCollection)
        assert result is not mock_map

    def test_freeze(self):
        mock_map = mapping.DictionaryCollection({"hikari": "shinji", "gendo": "san"})
        result = mock_map.freeze()

        assert result == {"hikari": "shinji", "gendo": "san"}
        assert isinstance(result, dict)

    def test___delitem__(self):
        mock_map = mapping.DictionaryCollection({"hikari": "shinji", "gendo": "san", "screwed": "up"})
        del mock_map["hikari"]

        assert mock_map == {"gendo": "san", "screwed": "up"}

    def test___getitem__(self):
        mock_map = mapping.DictionaryCollection({"curiosity": "rover", "ok": "bye"})
        assert mock_map["ok"] == "bye"

    def test____iter__(self):
        mock_map = mapping.DictionaryCollection({"curiosity": "rover", "cat": "bag", "ok": "bye"})
        assert list(mock_map) == ["curiosity", "cat", "ok"]

    def test___len__(self):
        mock_map = mapping.DictionaryCollection({"hmm": "blam", "cat": "bag", "ok": "bye"})
        assert len(mock_map) == 3

    def test___setitem__(self):
        mock_map = mapping.DictionaryCollection({"hmm": "forearm", "cat": "bag", "ok": "bye"})
        mock_map["bye"] = 4

        assert mock_map == {"hmm": "forearm", "cat": "bag", "ok": "bye", "bye": 4}


class TestFrozenMRIMapping:
    def test___init__(self):
        mock_map = mapping._FrozenMRIMapping({"foo": (0.432, "bar"), "blam": (0.111, "okok")})
        assert mock_map == {"foo": "bar", "blam": "okok"}

    def test___getitem__(self):
        mock_map = mapping._FrozenMRIMapping({"blam": (0.432, "bar"), "obar": (0.111, "okok")})
        assert mock_map["obar"] == "okok"

    def test___iter__(self):
        mock_map = mapping._FrozenMRIMapping({"bye": (0.33, "bye"), "111": (0.2, "222"), "45949": (0.5, "020202")})
        assert list(mock_map) == ["bye", "111", "45949"]

    def test___len__(self):
        mock_map = mapping._FrozenMRIMapping({"wsw": (0.3, "3"), "fdsa": (0.55, "ewqwe"), "45949": (0.23, "fsasd")})
        assert len(mock_map) == 3

    def test___delitem__(self):
        mock_map = mapping._FrozenMRIMapping({"rororo": (0.55, "bye bye"), "raw": (0.999, "ywywyw")})
        del mock_map["raw"]
        assert mock_map == {"rororo": "bye bye"}

    def test___setitem__(self):
        mock_map = mapping._FrozenMRIMapping({"rororo": (0.55, "bye 3231"), "2121": (0.999, "4321")})
        mock_map["foo bar"] = 42

        assert mock_map == {"rororo": "bye 3231", "2121": "4321", "foo bar": 42}


class TestMRIMutableMapping:
    def test___init___with_source(self):
        raw_map = {
            "not_in": (time.perf_counter() - 50, "goodbye"),
            "ok": (time.perf_counter() + 30, "no"),
            "blam": (time.perf_counter() + 20, "bye"),
        }
        mocK_map = mapping.MRIMutableMapping(raw_map, expiry=datetime.timedelta(seconds=42))

        assert mocK_map == {"blam": "bye", "ok": "no"}

    def test___init___raises_value_error_on_invalid_expiry(self):
        with pytest.raises(ValueError, match="expiry time must be greater than 0 microseconds."):
            mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=0))

        with pytest.raises(ValueError, match="expiry time must be greater than 0 microseconds."):
            mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=-50))

    def test_copy(self):
        raw_map = {
            "floom": (0.4312, "buebue"),
            "bash": (0.65234, "bunny_time"),
        }
        mock_map = mapping.MRIMutableMapping(raw_map, expiry=datetime.timedelta(seconds=4523412))
        result = mock_map.copy()

        assert result is not mock_map
        assert isinstance(result, mapping.MRIMutableMapping)
        assert result == {"floom": "buebue", "bash": "bunny_time"}

    def test_freeze(self):
        raw_map = {"bash": (0.523423, "gtuutueu"), "blam": (0.4332, "poke"), "owowo": (0.323, "no you")}
        mock_map = mapping.MRIMutableMapping(raw_map, expiry=datetime.timedelta(seconds=6523423))
        result = mock_map.freeze()

        assert result == {"bash": "gtuutueu", "blam": "poke", "owowo": "no you"}
        assert isinstance(result, mapping._FrozenMRIMapping)

    def test___delitem__(self):
        mock_map = mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=100))
        mock_map.update({"ok": "no", "ayanami": "rei qt"})
        del mock_map["ok"]
        assert mock_map == {"ayanami": "rei qt"}

    @pytest.mark.asyncio
    async def test___delitem___garbage_collection(self):
        mock_map = mapping.MRIMutableMapping(
            expiry=datetime.timedelta(seconds=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 3)
        )
        mock_map.update({"nyaa": "see", "awwo": "awoo2"})
        await asyncio.sleep(hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 2)
        assert mock_map == {"nyaa": "see", "awwo": "awoo2"}
        mock_map.update({"ayanami": "shinji", "rei": "aww"})
        assert mock_map == {"nyaa": "see", "awwo": "awoo2", "ayanami": "shinji", "rei": "aww"}
        await asyncio.sleep(hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 2)
        del mock_map["ayanami"]
        assert mock_map == {"rei": "aww"}

    def test___getitem___for_valid_entry(self):
        mock_map = mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=100))
        mock_map["OK"] = 42
        mock_map["blam"] = 8
        assert mock_map["OK"] == 42

    def test___getitem___for_unknown_entry(self):
        mock_map = mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=100))
        mock_map["blam"] = 8

        with pytest.raises(KeyError):
            mock_map["OK"]

    def test___iter__(self):
        mock_map = mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=100))
        mock_map.update({"o": "k", "k": "o", "awoo": "blam", "hikari": "rei"})
        assert list(mock_map) == ["o", "k", "awoo", "hikari"]

    def test___len__(self):
        mock_map = mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=100))
        mock_map.update({"o": "k", "boop": "bop", "k": "o", "awoo": "blam", "rei": "cute", "hikari": "rei"})
        assert len(mock_map) == 6

    def test___setitem__(self):
        mock_map = mapping.MRIMutableMapping(expiry=datetime.timedelta(seconds=100))
        mock_map["blat"] = 42
        assert mock_map == {"blat": 42}

    def test___setitem___removes_old_entry_instead_of_replacing(self):
        mock_map = mapping.MRIMutableMapping(
            {
                "ok": (time.perf_counter() + 50, "no"),
                "bar": (time.perf_counter() + 60, "bat"),
                "foo": (time.perf_counter() + 70, "blam"),
            },
            expiry=datetime.timedelta(seconds=100),
        )
        mock_map["ok"] = "foo"
        assert list(mock_map.items())[2] == ("ok", "foo")

    # TODO: fix this so that it is not flaky.
    # https://travis-ci.org/github/nekokatt/hikari/jobs/724494888#L797
    @pytest.mark.skip("flaky test, might fail on Windows runners.")
    @pytest.mark.asyncio
    async def test___setitem___garbage_collection(self):
        mock_map = mapping.MRIMutableMapping(
            expiry=datetime.timedelta(seconds=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 3)
        )
        mock_map.update({"OK": "no", "blam": "booga"})
        await asyncio.sleep(hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 2)
        assert mock_map == {"OK": "no", "blam": "booga"}
        mock_map.update({"ayanami": "rei", "owo": "awoo"})
        assert mock_map == {"OK": "no", "blam": "booga", "ayanami": "rei", "owo": "awoo"}
        await asyncio.sleep(hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 2)
        mock_map.update({"nyaa": "qt"})
        assert mock_map == {"ayanami": "rei", "owo": "awoo", "nyaa": "qt"}


class TestCMRIMutableMapping:
    def test___init___with_source(self):
        raw_map = {"voo": "doo", "blam": "blast", "foo": "bye"}
        mock_map = mapping.CMRIMutableMapping(raw_map, limit=2)
        assert mock_map == {"blam": "blast", "foo": "bye"}

    def test_copy(self):
        mock_map = mapping.CMRIMutableMapping({"o": "n", "b": "a", "a": "v"}, limit=42)
        result = mock_map.copy()

        assert result is not mock_map
        assert isinstance(result, mapping.CMRIMutableMapping)
        assert result == {"o": "n", "b": "a", "a": "v"}

    def test_freeze(self):
        mock_map = mapping.CMRIMutableMapping({"o": "no", "good": "bye"}, limit=5)
        result = mock_map.freeze()

        assert isinstance(result, dict)
        assert result == {"o": "no", "good": "bye"}

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
            mock_map["CIA"]

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
        mapping.get_index_or_slice({"i": "e", "n": "o", "b": "a", "hikari": "noa"}, 77)


def test_get_index_or_slice_with_slice():
    test_map = {"o": "b", "b": "o", "a": "m", "arara": "blam", "oof": "no", "rika": "may"}
    assert mapping.get_index_or_slice(test_map, slice(1, 5, 2)) == ("o", "blam")


def test_get_index_or_slice_with_invalid_type():
    with pytest.raises(TypeError):
        mapping.get_index_or_slice({}, object())

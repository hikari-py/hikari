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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import io
import pathlib
import contextlib
import typing

import mock
import pytest

from hikari import files
from tests.hikari import _helpers


class TestFile:
    @pytest.fixture
    def stub_file(self):
        class StubFile(files.File):
            def __init__(self):
                pass

        return StubFile()

    @pytest.mark.parametrize(
        ("input_name", "input_data", "expected_name", "expected_data", "expected_path"),
        [
            ("path/to/test.txt", None, "test.txt", None, "path/to/test.txt"),
            ("test", memoryview(b"test_data"), "test", b"test_data", None),
            ("test", io.BytesIO(b"test_data"), "test", b"test_data", None),
            ("test", pathlib.Path("test_path"), "test", None, "test_path"),
            (pathlib.Path("test"), None, "test", None, "test"),
            ("test", b"test_data", "test", b"test_data", None),
            ("test", bytearray("test_data", "utf-8"), "test", b"test_data", None),
        ],
    )
    def test__init__(self, input_name, input_data, expected_name, expected_data, expected_path):
        file_obj = files.File(input_name, input_data)

        assert file_obj.name == expected_name
        assert file_obj._data == expected_data
        assert file_obj._path == expected_path

    @_helpers.assert_raises(type_=TypeError)
    def test__init__when_invalid_type_provided(self):
        file_obj = files.File("any name", True)

    @pytest.mark.asyncio
    async def test__aiter___when_path_is_not_None_and_data_is_None(self, event_loop, stub_file):
        stub_file._path = "test"
        stub_file._data = None
        stub_file._executor = None

        with mock.patch("builtins.open", mock.mock_open(read_data=b"test")) as mock_open:
            data = b""
            async for chunk in stub_file:
                data += chunk

            mock.call("test", "rb") in mock_open.mock_calls  # File open
            mock.call().__exit__(None, None, None) in mock_open.mock_calls  # File close
            assert data == b"test"

    @pytest.mark.asyncio
    async def test__aiter___when_data_isinstance_IOBase(self, event_loop, stub_file):
        stub_file._path = None
        stub_file._data = io.BytesIO(b"test")
        stub_file._executor = None

        data = b""
        async for chunk in stub_file:
            data += chunk

        assert data == b"test"

    @pytest.mark.asyncio
    async def test__aiter___when_data_isinstance_AsyncIterable(self, stub_file):
        class AsyncIterable(typing.AsyncIterable):
            async def __aiter__(self):
                yield b"te"
                yield b"st"

        stub_file._path = None
        stub_file._data = AsyncIterable()
        stub_file._executor = None

        data = b""
        async for chunk in stub_file:
            data += chunk

        assert data == b"test"

    @pytest.mark.asyncio
    async def test__aiter___when_data_isinstance_bytes(self, stub_file):
        stub_file._path = None
        stub_file._data = b"test"
        stub_file._executor = None

        data = b""
        async for chunk in stub_file:
            data += chunk

        assert data == b"test"

    @pytest.mark.asyncio
    async def test__aiter___when_data_isinstance_Iterable(self, stub_file):
        stub_file._path = None
        stub_file._data = [b"te", b"st"]
        stub_file._executor = None

        data = b""
        async for chunk in stub_file:
            data += chunk

        assert data == b"test"

    @_helpers.assert_raises(type_=TypeError)
    @pytest.mark.asyncio
    async def test__aiter___when_invalid_type(self, stub_file):
        stub_file._path = None
        stub_file._data = True
        stub_file._executor = None

        async for chunk in stub_file:
            pass

    @pytest.mark.asyncio
    async def test_read_all(self, stub_file):
        stub_file._path = None
        stub_file._data = b"test"
        stub_file._executor = None

        data = await stub_file.read_all()

        assert data == b"test"

    @pytest.mark.asyncio
    async def test__read_path(self, stub_file):
        stub_file._path = "test"

        with mock.patch("builtins.open", mock.mock_open(read_data=b"test")) as mock_open:
            data = stub_file._read_path()

            mock_open.assert_called_once_with("test", "rb")
            assert data == b"test"

    @pytest.mark.asyncio
    async def test__read_lines(self, stub_file):
        stub_file._data = io.BytesIO(bytearray("test\ntest\ntest", "utf-8"))

        data = stub_file._read_lines()

        assert data == b"test\ntest\ntest"

    @_helpers.assert_raises(type_=TypeError)
    @pytest.mark.asyncio
    async def test__read_lines_when_invalid_type(self, stub_file):
        stub_file._data = io.StringIO("this should error")

        stub_file._read_lines()

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
import concurrent.futures
import io
import os
import random
import tempfile
import uuid

import aiohttp
import mock
import pytest

from hikari import errors
from hikari.models import files
from tests.hikari import _helpers


@pytest.mark.asyncio
class TestBaseStream:
    async def test_read(self):
        class Impl(files.BaseStream):
            async def __aiter__(self):
                yield b"foo"
                yield b" "
                yield b"bar"
                yield b" "
                yield b"baz"
                yield b" "
                yield b"bork"

            @property
            def filename(self) -> str:
                return "poof"

        i = Impl()

        assert await i.read() == b"foo bar baz bork"

    def test_repr(self):
        class Impl(files.BaseStream):
            @property
            def filename(self) -> str:
                return "poofs.gpg"

            async def __aiter__(self):
                yield b""

        i = Impl()

        assert repr(i) == "Impl(filename='poofs.gpg')"


@pytest.mark.asyncio
class TestByteStream:
    async def test_filename(self):
        stream = files.ByteStream("foo.txt", b"(.) (.)")
        assert stream.filename == "foo.txt"

    @pytest.mark.parametrize(
        "chunks",
        [
            (b"foo", b"bar"),
            (bytearray(b"foo"), bytearray(b"bar")),
            (memoryview(b"foo"), memoryview(b"bar")),
            ("foo", "bar"),
            ("foo", b"bar"),
        ],
    )
    async def test_async_gen_function(self, chunks):
        async def generator():
            for chunk in chunks:
                yield chunk

        stream = files.ByteStream("foo.txt", generator)

        assert await stream.read() == b"foobar"

    @pytest.mark.parametrize(
        "chunks",
        [
            (b"foo", b"bar"),
            (bytearray(b"foo"), bytearray(b"bar")),
            (memoryview(b"foo"), memoryview(b"bar")),
            ("foo", "bar"),
            ("foo", b"bar"),
        ],
    )
    async def test_async_gen(self, chunks):
        async def generator():
            for chunk in chunks:
                yield chunk

        stream = files.ByteStream("foo.txt", generator)

        assert await stream.read() == b"foobar"

    @pytest.mark.parametrize(
        "chunks",
        [
            (b"foo", b"bar"),
            (bytearray(b"foo"), bytearray(b"bar")),
            (memoryview(b"foo"), memoryview(b"bar")),
            ("foo", "bar"),
            ("foo", b"bar"),
        ],
    )
    async def test_generator_async_iterable(self, chunks):
        class AsyncIterable:
            async def __aiter__(self):
                for chunk in chunks:
                    yield chunk

        stream = files.ByteStream("foo.txt", AsyncIterable())

        assert await stream.read() == b"foobar"

    @pytest.mark.parametrize(
        "chunks",
        [
            (b"foo", b"bar"),
            (bytearray(b"foo"), bytearray(b"bar")),
            (memoryview(b"foo"), memoryview(b"bar")),
            ("foo", "bar"),
            ("foo", b"bar"),
        ],
    )
    async def test_delegating_async_iterable(self, chunks):
        async def delegated_to():
            for chunk in chunks:
                yield chunk

        class AsyncIterable:
            def __aiter__(self):
                return delegated_to()

        stream = files.ByteStream("foo.txt", AsyncIterable())

        assert await stream.read() == b"foobar"

    @pytest.mark.parametrize(
        "chunks",
        [
            (b"foo", b"bar"),
            (bytearray(b"foo"), bytearray(b"bar")),
            (memoryview(b"foo"), memoryview(b"bar")),
            ("foo", "bar"),
            ("foo", b"bar"),
        ],
    )
    async def test_generator_async_iterator(self, chunks):
        class AsyncIterator:
            def __init__(self):
                self.i = 0

            async def __anext__(self):
                if self.i < len(chunks):
                    chunk = chunks[self.i]
                    self.i += 1
                    return chunk
                raise StopAsyncIteration()

        stream = files.ByteStream("foo.txt", AsyncIterator())

        assert await stream.read() == b"foobar"

    async def test_BytesIO(self):
        stream = files.ByteStream("foo.txt", io.BytesIO(b"foobar"))
        assert await stream.read() == b"foobar"

    async def test_StringIO(self):
        stream = files.ByteStream("foo.txt", io.StringIO("foobar"))
        assert await stream.read() == b"foobar"

    async def test_bytes(self):
        stream = files.ByteStream("foo.txt", b"foobar")
        assert await stream.read() == b"foobar"

    async def test_bytearray(self):
        stream = files.ByteStream("foo.txt", bytearray(b"foobar"))
        assert await stream.read() == b"foobar"

    async def test_memoryview(self):
        stream = files.ByteStream("foo.txt", memoryview(b"foobar"))
        assert await stream.read() == b"foobar"

    async def test_str(self):
        stream = files.ByteStream("foo.txt", "foobar")
        assert await stream.read() == b"foobar"

    async def test_large_BytesIO_chunks_in_sections(self):
        data = bytearray(random.getrandbits(8) for _ in range(1 * 1024 * 1024))
        data_file = io.BytesIO(data)
        data_stream = files.ByteStream("large_data_file.bin", data_file)

        i = 0
        async for chunk in data_stream:
            expected_slice = data[i * files.MAGIC_NUMBER : (i + 1) * files.MAGIC_NUMBER]
            assert chunk == expected_slice, f"failed on slice #{i}"
            i += 1

    @_helpers.assert_raises(type_=TypeError)
    def test_bad_type(self):
        files.ByteStream("foo", 3.14)

    @_helpers.assert_raises(type_=TypeError)
    async def test_bad_chunk(self):
        async def chunker():
            yield 3.14

        await files.ByteStream("foo", chunker()).read()


@pytest.mark.asyncio
class TestWebResource:
    # This is slow, generate once per class only.
    @pytest.fixture(scope="class")
    def random_bytes(self):
        return bytes(bytearray(random.getrandbits(8) for _ in range(1 * 1024 * 1024)))

    @pytest.fixture
    def stub_content(self, random_bytes):
        class ContentIterator:
            def __init__(self):
                self.raw_content = random_bytes

            async def __aiter__(self):
                # Pretend to send 1KiB chunks in response.
                for i in range(0, len(self.raw_content), 1024):
                    yield self.raw_content[i : i + 1024]

        return ContentIterator()

    @pytest.fixture
    def stub_response(self, stub_content):
        class StubResponse:
            def __init__(self):
                self.status = 200
                self.content = stub_content
                self.headers = {"x-whatever": "bleh"}
                self.real_url = "https://some-websi.te"

            async def read(self):
                return self.content.raw_content

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        return StubResponse()

    @pytest.fixture
    def mock_request(self, stub_response):
        with mock.patch.object(aiohttp, "request", new=mock.MagicMock(return_value=stub_response)) as request:
            yield request

    async def test_filename(self):
        stream = files.WebResourceStream("cat.png", "http://http.cat")
        assert stream.filename == "cat.png"

    async def test_happy_path_reads_data_in_chunks(self, stub_content, stub_response, mock_request):
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        i = 0
        async for chunk in stream:
            assert chunk == stub_content.raw_content[i * 1024 : (i + 1) * 1024]
            i += 1

        assert i > 0, "no data yielded :("

        mock_request.assert_called_once_with("GET", "https://some-websi.te")

    @_helpers.assert_raises(type_=errors.BadRequest)
    async def test_400(self, stub_content, stub_response, mock_request):
        stub_response.status = 400
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"

    @_helpers.assert_raises(type_=errors.Unauthorized)
    async def test_401(self, stub_content, stub_response, mock_request):
        stub_response.status = 401
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"

    @_helpers.assert_raises(type_=errors.Forbidden)
    async def test_403(self, stub_content, stub_response, mock_request):
        stub_response.status = 403
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"

    @_helpers.assert_raises(type_=errors.NotFound)
    async def test_404(self, stub_content, stub_response, mock_request):
        stub_response.status = 404
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"

    @pytest.mark.parametrize("status", [402, 405, 406, 408, 415, 429])
    @_helpers.assert_raises(type_=errors.ClientHTTPErrorResponse)
    async def test_4xx(self, stub_content, stub_response, mock_request, status):
        stub_response.status = status
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"

    @pytest.mark.parametrize("status", [500, 501, 502, 503, 504])
    @_helpers.assert_raises(type_=errors.ServerHTTPErrorResponse)
    async def test_5xx(self, stub_content, stub_response, mock_request, status):
        stub_response.status = status
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"

    @pytest.mark.parametrize("status", [100, 101, 102, 300, 301, 302, 303])
    @_helpers.assert_raises(type_=errors.HTTPErrorResponse)
    async def test_random_status_codes(self, stub_content, stub_response, mock_request, status):
        stub_response.status = status
        stream = files.WebResourceStream("cat.png", "https://some-websi.te")

        async for _ in stream:
            assert False, "expected error by now"


@pytest.mark.asyncio
class TestFileStream:
    # slow, again.
    @pytest.fixture(scope="class")
    def random_bytes(self):
        return bytes(bytearray(random.getrandbits(8) for _ in range(5 * 1024 * 1024)))

    @pytest.fixture
    def threadpool_executor(self):
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        yield executor
        executor.shutdown(wait=True)

    @pytest.fixture
    def processpool_executor(self):
        executor = concurrent.futures.ProcessPoolExecutor(max_workers=5)
        yield executor
        executor.shutdown(wait=True)

    @pytest.fixture(scope="class")
    def dummy_file(self, random_bytes):
        with tempfile.TemporaryDirectory() as directory:
            file = os.path.join(directory, str(uuid.uuid4()))

            with open(file, "wb") as fp:
                fp.write(random_bytes)

            yield file

    async def test_filename(self):
        stream = files.FileStream("cat.png", "/root/cat.png")
        assert stream.filename == "cat.png"

    async def test_read_no_executor(self, random_bytes, dummy_file):
        stream = files.FileStream("xxx", dummy_file)

        start = 0
        async for chunk in stream:
            end = start + len(chunk)
            assert chunk == random_bytes[start:end]
            start = end

        assert start == len(random_bytes)

    async def test_read_in_threadpool(self, random_bytes, dummy_file, threadpool_executor):
        stream = files.FileStream("xxx", dummy_file, executor=threadpool_executor)

        start = 0
        async for chunk in stream:
            end = start + len(chunk)
            assert chunk == random_bytes[start:end]
            start = end

        assert start == len(random_bytes)

    @_helpers.skip_if_no_sem_open
    async def test_read_in_processpool(self, random_bytes, dummy_file, processpool_executor):
        stream = files.FileStream("xxx", dummy_file, executor=processpool_executor)

        start = 0
        async for chunk in stream:
            end = start + len(chunk)
            assert chunk == random_bytes[start:end]
            start = end

        assert start == len(random_bytes)

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

import asyncio
import base64
import concurrent.futures
import pathlib
import random
import tempfile

import aiohttp
import mock
import pytest

from hikari import files
from hikari import messages
from tests.hikari import hikari_test_helpers


class TestAsyncReaderContextManager:
    @pytest.fixture()
    def reader(self):
        return hikari_test_helpers.mock_class_namespace(files.AsyncReaderContextManager)

    def test___enter__(self, reader):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            reader().__enter__()

    def test___exit__(self, reader):
        try:
            reader().__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)


class Test_ThreadedFileReaderContextManagerImpl:
    @pytest.mark.asyncio()
    async def test_enter_dunder_method_when_already_open(self):
        manager = files._ThreadedFileReaderContextManagerImpl(mock.Mock(), "ea", pathlib.Path("ea"))
        manager.file = mock.Mock()
        with pytest.raises(RuntimeError, match="File is already open"):
            await manager.__aenter__()

    @pytest.mark.asyncio()
    async def test_exit_dunder_method_when_not_open(self):
        manager = files._ThreadedFileReaderContextManagerImpl(mock.Mock(), "ea", pathlib.Path("ea"))

        with pytest.raises(RuntimeError, match="File isn't open"):
            await manager.__aexit__(None, None, None)

    @pytest.mark.asyncio()
    async def test_context_manager(self):
        executor = concurrent.futures.ThreadPoolExecutor()
        mock_data = b"meeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" * 50

        # A try, finally is used to delete the file rather than relying on delete=True behaviour
        # as on Windows the file cannot be accessed by other processes if delete is True.
        file = tempfile.NamedTemporaryFile("wb", delete=False)
        path = pathlib.Path(file.name)
        try:
            with file:
                file.write(mock_data)

            context_manager = files._ThreadedFileReaderContextManagerImpl(executor, "meow.txt", path)

            async with context_manager as reader:
                data = await reader.read()

                assert reader.filename == "meow.txt"
                assert reader.path == path
                assert reader.executor is executor
                assert data == mock_data

        finally:
            path.unlink()

    @mock.patch.object(pathlib.Path, "expanduser", side_effect=RuntimeError)
    @pytest.mark.asyncio()
    async def test_context_manager_when_expandname_raises_runtime_error(self, expanduser: mock.Mock):
        # We can't mock patch stuff in other processes easily (if at all) so
        # for this test we have to cheat and use a thread pool executor.
        executor = concurrent.futures.ThreadPoolExecutor()

        # A try, finally is used to delete the file rather than relying on delete=True behaviour
        # as on Windows the file cannot be accessed by other processes if delete is True.
        with tempfile.NamedTemporaryFile(delete=False) as file:
            pass

        path = pathlib.Path(file.name)
        try:
            context_manager = files._ThreadedFileReaderContextManagerImpl(executor, "filename.txt", path)

            async with context_manager as reader:
                assert reader.path == path

            expanduser.assert_called_once_with()

        finally:
            path.unlink()

    @pytest.mark.asyncio()
    async def test_context_manager_for_unknown_file(self):
        executor = concurrent.futures.ThreadPoolExecutor()
        path = pathlib.Path(base64.urlsafe_b64encode(random.getrandbits(512).to_bytes(64, "little")).decode())
        context_manager = files._ThreadedFileReaderContextManagerImpl(executor, "ea.txt", path)

        with pytest.raises(FileNotFoundError):  # noqa:  PT012 - raises block should contain a single statement
            async with context_manager:
                ...

    @pytest.mark.asyncio()
    async def test_test_context_manager_when_target_is_dir(self):
        executor = concurrent.futures.ThreadPoolExecutor()

        with tempfile.TemporaryDirectory() as name:
            path = pathlib.Path(name)
            context_manager = files._ThreadedFileReaderContextManagerImpl(executor, "meow.txt", path)

            with pytest.raises(IsADirectoryError):  # noqa:  PT012 - raises block should contain a single statement
                async with context_manager:
                    ...


class Test_MultiProcessingFileReaderContextManagerImpl:
    @pytest.mark.asyncio()
    async def test_context_manager(self):
        executor = concurrent.futures.ProcessPoolExecutor()
        mock_data = b"kon'nichiwa i am yellow and blue da be meow da bayeet" * 50

        # A try, finally is used to delete the file rather than relying on delete=True behaviour
        # as on Windows the file cannot be accessed by other processes if delete is True.
        file = tempfile.NamedTemporaryFile("wb", delete=False)
        path = pathlib.Path(file.name)
        try:
            with file:
                file.write(mock_data)

            context_manager = files._MultiProcessingFileReaderContextManagerImpl(executor, "filename.txt", path)

            async with context_manager as reader:
                data = await reader.read()

                assert reader.filename == "filename.txt"
                assert reader.path == path
                assert reader.executor is executor
                assert data == mock_data

        finally:
            path.unlink()

    @mock.patch.object(pathlib.Path, "expanduser", side_effect=RuntimeError)
    @pytest.mark.asyncio()
    async def test_context_manager_when_expandname_raises_runtime_error(self, expanduser: mock.Mock):
        # We can't mock patch stuff in other processes easily (if at all) so
        # for this test we have to cheat and use a thread pool executor.
        executor = concurrent.futures.ThreadPoolExecutor()

        with tempfile.NamedTemporaryFile() as file:
            path = pathlib.Path(file.name)
            context_manager = files._MultiProcessingFileReaderContextManagerImpl(executor, "filename.txt", path)

            async with context_manager as reader:
                assert reader.path == path

        expanduser.assert_called_once_with()

    @pytest.mark.asyncio()
    async def test_context_manager_for_unknown_file(self):
        executor = concurrent.futures.ProcessPoolExecutor()
        path = pathlib.Path(base64.urlsafe_b64encode(random.getrandbits(512).to_bytes(64, "little")).decode())
        context_manager = files._MultiProcessingFileReaderContextManagerImpl(executor, "ea.txt", path)

        with pytest.raises(FileNotFoundError):  # noqa:  PT012 - raises block should contain a single statement
            async with context_manager:
                ...

    @pytest.mark.asyncio()
    async def test_test_context_manager_when_target_is_dir(self):
        executor = concurrent.futures.ProcessPoolExecutor()

        with tempfile.TemporaryDirectory() as name:
            path = pathlib.Path(name)
            context_manager = files._MultiProcessingFileReaderContextManagerImpl(executor, "meow.txt", path)

            with pytest.raises(IsADirectoryError):  # noqa:  PT012 - raises block should contain a single statement
                async with context_manager:
                    ...


class TestResource:
    @pytest.fixture()
    def data(self):
        return b"line1\nline2\nline3\n"

    @pytest.fixture()
    def attachment(self, data):
        return messages.Attachment(
            id=123,
            filename="file.txt",
            media_type="text",
            height=None,
            width=None,
            proxy_url="htt",
            size=len(b"line1\nline2\nline3\n"),
            url="https://rick.roll",
            is_ephemeral=False,
        )

    async def create_stream(self):
        # https://github.com/aio-libs/aiohttp/blob/master/tests/test_streams.py#L26
        loop = asyncio.get_event_loop()
        protocol = mock.Mock(_reading_paused=False)
        stream = aiohttp.streams.StreamReader(protocol, 2**16, loop=loop)
        stream.feed_data(b"line1\nline2\nline3\n")
        stream.feed_eof()
        return stream

    async def create_reader(self):
        return files.WebReader(
            stream=await self.create_stream(),
            url="https://rick.roll",
            status=200,
            reason="None",
            filename="file.txt",
            charset=None,
            mimetype="your mum",
            size=len(b"line1\nline2\nline3\n"),
            head_only=False,
        )

    @pytest.mark.asyncio()
    async def test_resource_read(self, attachment: messages.Attachment, data: bytes):
        with mock.patch.object(files._WebReaderAsyncReaderContextManagerImpl, "__aenter__") as mock_aenter:
            mock_aenter.return_value = await self.create_reader()

            # Mocking the previous object throws an error here
            # so we just want to avoid it.
            try:
                assert await attachment.read() == data
            except AttributeError as exc:
                if str(exc) != "'NotImplementedType' object has no attribute '__aexit__'":
                    raise exc

    @pytest.mark.asyncio()
    async def test_resource_save(self, attachment: messages.Attachment, data: bytes):
        with mock.patch.object(files._WebReaderAsyncReaderContextManagerImpl, "__aenter__") as mock_aenter:
            mock_aenter.return_value = await self.create_reader()

            # A try, finally is used to delete the file rather than relying on delete=True behaviour
            # as on Windows the file cannot be accessed by other processes if delete is True.
            try:
                file = tempfile.NamedTemporaryFile("wb", delete=False)
                path = pathlib.Path(file.name)

                with file:
                    # Mocking the previous object throws an error here
                    # so we just want to avoid it.
                    try:
                        await attachment.save(path=path)
                    except AttributeError as exc:
                        if str(exc) != "'NotImplementedType' object has no attribute '__aexit__'":
                            raise exc

                    with open(path, "rb") as f:
                        assert f.read() == data
            finally:
                path.unlink()

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
import pathlib

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


def test__open_path():
    expanded_path = mock.Mock()
    path = mock.Mock(expanduser=mock.Mock(return_value=expanded_path))

    assert files._open_path(path) is expanded_path.open.return_value

    expanded_path.open.assert_called_once_with("rb")


class TestThreadedFileReaderContextManagerImpl:
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
        mock_file = mock.Mock()
        executor = object()
        path = pathlib.Path("test/path/")

        loop = mock.Mock(run_in_executor=mock.AsyncMock(side_effect=[mock_file, None]))

        context_manager = files._ThreadedFileReaderContextManagerImpl(executor, "meow.txt", path)

        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            async with context_manager as reader:
                assert context_manager.file is mock_file

                assert reader.filename == "meow.txt"
                assert reader._executor is executor

                loop.run_in_executor.assert_called_once_with(executor, files._open_path, path)
                loop.run_in_executor.reset_mock()

        loop.run_in_executor.assert_called_once_with(executor, mock_file.close)
        assert context_manager.file is None


# class TestResource:
#     @pytest.fixture()
#     def data(self):
#         return b"line1\nline2\nline3\n"

#     @pytest.fixture()
#     def attachment(self, data: bytes):
#         return messages.Attachment(
#             id=123,
#             filename="file.txt",
#             media_type="text",
#             height=None,
#             width=None,
#             proxy_url="htt",
#             size=len(b"line1\nline2\nline3\n"),
#             url="https://rick.roll",
#             is_ephemeral=False,
#         )

#     async def create_stream(self):
#         # https://github.com/aio-libs/aiohttp/blob/master/tests/test_streams.py#L26
#         loop = asyncio.get_event_loop()
#         protocol = mock.Mock(_reading_paused=False)
#         stream = aiohttp.streams.StreamReader(protocol, 2**16, loop=loop)
#         stream.feed_data(b"line1\nline2\nline3\n")
#         stream.feed_eof()
#         return stream

#     async def create_reader(self):
#         return files.WebReader(
#             stream=await self.create_stream(),
#             url="https://rick.roll",
#             status=200,
#             reason="None",
#             filename="file.txt",
#             charset=None,
#             mimetype="your mum",
#             size=len(b"line1\nline2\nline3\n"),
#             head_only=False,
#         )

#     @pytest.mark.asyncio()
#     async def test_resource_read(self, attachment: messages.Attachment, data: bytes):
#         with mock.patch.object(files._WebReaderAsyncReaderContextManagerImpl, "__aenter__") as mock_aenter:
#             mock_aenter.return_value = await self.create_reader()

#             # Mocking the previous object throws an error here
#             # so we just want to avoid it.
#             try:
#                 assert await attachment.read() == data
#             except AttributeError as exc:
#                 if str(exc) != "'NotImplementedType' object has no attribute '__aexit__'":
#                     raise

#     @pytest.mark.asyncio()
#     async def test_resource_save(self, attachment: messages.Attachment, data: bytes):
#         with mock.patch.object(files._WebReaderAsyncReaderContextManagerImpl, "__aenter__") as mock_aenter:
#             mock_aenter.return_value = await self.create_reader()

#             # A try, finally is used to delete the file rather than relying on delete=True behaviour
#             # as on Windows the file cannot be accessed by other processes if delete is True.
#             try:
#                 file = tempfile.NamedTemporaryFile("wb", delete=True)
#                 path = pathlib.Path(file.name)

#                 with file:
#                     # Mocking the previous object throws an error here
#                     # so we just want to avoid it.
#                     try:
#                         await attachment.save(path=path)
#                     except AttributeError as exc:
#                         if str(exc) != "'NotImplementedType' object has no attribute '__aexit__'":
#                             raise

#                     with open(path, "rb") as f:
#                         assert f.read() == data
#             finally:
#                 path.unlink()


class TestResource:
    @pytest.fixture()
    def resource(self):
        class MockReader:
            data = iter(("never", "gonna", "give", "you", "up"))

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args, **kwargs):
                return

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self.data)
                except StopIteration:
                    raise StopAsyncIteration from None

        class ResourceImpl(files.Resource):
            stream = mock.Mock(return_value=MockReader())
            url = "https://myspace.com/rickastley/lyrics.txt"
            filename = "lyrics.txt"

        return ResourceImpl()

    @pytest.mark.asyncio()
    async def test_save(self, resource):
        executor = object()
        path = pathlib.Path("rickroll/lyrics.txt")
        file_open = hikari_test_helpers.AsyncContextManagerMock()
        file_open.write = mock.Mock()
        loop = mock.Mock(run_in_executor=mock.Mock(side_effect=[file_open, None]))

        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            await resource.save(path, executor=executor, force=True)

        file_open.assert_used_once()
        assert loop.run_in_executor.call_count == 6
        loop.run_in_executor.assert_has_calls(
            [
                mock.call(executor, resource._open, path, True),
                mock.call(executor, path.write, "never"),
                mock.call(executor, path.write, "gonna"),
                mock.call(executor, path.write, "give"),
                mock.call(executor, path.write, "you"),
                mock.call(executor, path.write, "up"),
            ]
        )

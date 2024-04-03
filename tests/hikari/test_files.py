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
import shutil

import mock
import pytest

from hikari import files
from tests.hikari import hikari_test_helpers


class TestURL:
    def test_default_filename(self):
        url = files.URL("https://i.ytimg.com/vi_webp/dQw4w9WgXcQ/maxresdefault.webp")

        assert url.filename == "maxresdefault.webp"

    def test_set_filename(self):
        url = files.URL("https://i.ytimg.com/vi_webp/dQw4w9WgXcQ/maxresdefault.webp", "yeltsakir.webp")

        assert url.filename == "yeltsakir.webp"


class TestAsyncReaderContextManager:
    @pytest.fixture
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


def test__open_read_path():
    expanded_path = mock.Mock()
    path = mock.Mock(expanduser=mock.Mock(return_value=expanded_path))

    assert files._open_read_path(path) is expanded_path.open.return_value

    expanded_path.open.assert_called_once_with("rb")


class TestThreadedFileReaderContextManagerImpl:
    @pytest.mark.asyncio
    async def test_enter_dunder_method_when_already_open(self):
        manager = files._ThreadedFileReaderContextManagerImpl(mock.Mock(), "ea", pathlib.Path("ea"))
        manager.file = mock.Mock()
        with pytest.raises(RuntimeError, match="File is already open"):
            await manager.__aenter__()

    @pytest.mark.asyncio
    async def test_exit_dunder_method_when_not_open(self):
        manager = files._ThreadedFileReaderContextManagerImpl(mock.Mock(), "ea", pathlib.Path("ea"))

        with pytest.raises(RuntimeError, match="File isn't open"):
            await manager.__aexit__(None, None, None)

    @pytest.mark.asyncio
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

                loop.run_in_executor.assert_called_once_with(executor, files._open_read_path, path)
                loop.run_in_executor.reset_mock()

        loop.run_in_executor.assert_called_once_with(executor, mock_file.close)
        assert context_manager.file is None


class TestToWritePath:
    def test_when_dir(self):
        mock_path = mock.Mock(is_dir=mock.Mock(return_value=True))
        joinpath = mock_path.joinpath.return_value = mock.Mock(exists=mock.Mock(return_value=False))

        with mock.patch.object(files, "ensure_path", return_value=mock_path) as ensure_path:
            assert files._to_write_path("test_path", "some_filename.png", False) is joinpath.expanduser.return_value

        mock_path.joinpath.assert_called_once_with("some_filename.png")
        ensure_path.assert_called_once_with("test_path")

    def test_when_exists_but_not_force(self):
        mock_path = mock.Mock(is_dir=mock.Mock(return_value=False), exists=mock.Mock(return_value=True))

        with mock.patch.object(files, "ensure_path", return_value=mock_path) as ensure_path:
            with pytest.raises(FileExistsError):
                files._to_write_path("test_path", "some_filename.png", False)

        ensure_path.assert_called_once_with("test_path")

    def test_when_exists_but_force(self):
        mock_path = mock.Mock(is_dir=mock.Mock(return_value=False), exists=mock.Mock(return_value=True))

        with mock.patch.object(files, "ensure_path", return_value=mock_path) as ensure_path:
            assert files._to_write_path("test_path", "some_filename.png", True) is mock_path.expanduser.return_value

        ensure_path.assert_called_once_with("test_path")


def test_open_write_path():
    with mock.patch.object(files, "_to_write_path") as to_write_path:
        assert (
            files._open_write_path("path", "some_filename.png", False) is to_write_path.return_value.open.return_value
        )

    to_write_path.assert_called_once_with("path", "some_filename.png", False)
    to_write_path.return_value.open.assert_called_once_with("wb")


class TestResource:
    @pytest.fixture
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

    @pytest.mark.asyncio
    async def test_save(self, resource):
        executor = object()
        file_open = mock.Mock()
        file_open.write = mock.Mock()
        loop = mock.Mock(run_in_executor=mock.AsyncMock(side_effect=[file_open, None, None, None, None, None, None]))

        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            await resource.save("rickroll/lyrics.txt", executor=executor, force=True)

        assert loop.run_in_executor.call_count == 7
        loop.run_in_executor.assert_has_calls(
            [
                mock.call(executor, files._open_write_path, "rickroll/lyrics.txt", "lyrics.txt", True),
                mock.call(executor, file_open.write, "never"),
                mock.call(executor, file_open.write, "gonna"),
                mock.call(executor, file_open.write, "give"),
                mock.call(executor, file_open.write, "you"),
                mock.call(executor, file_open.write, "up"),
                mock.call(executor, file_open.close),
            ]
        )


def test_copy_to_path():
    with mock.patch.object(files, "_to_write_path") as to_write_path:
        with mock.patch.object(shutil, "copy2") as copy2:
            files._copy_to_path("original_path", "path", "some_filename.png", False)

    to_write_path.assert_called_once_with("path", "some_filename.png", False)
    copy2.assert_called_once_with("original_path", to_write_path.return_value)


class TestFile:
    @pytest.fixture
    def file_obj(self):
        return files.File("one/path/something.txt")

    @pytest.mark.asyncio
    async def test_save(self, file_obj):
        mock_executor = object()
        loop = mock.Mock(run_in_executor=mock.AsyncMock())

        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            with mock.patch.object(files.Resource, "save") as super_save:
                await file_obj.save("some_path/", executor=mock_executor, force=True)

        super_save.assert_not_called()
        loop.run_in_executor.assert_awaited_once_with(
            mock_executor,
            files._copy_to_path,
            pathlib.Path("one/path/something.txt"),
            "some_path/",
            "something.txt",
            True,
        )


def test_write_bytes():
    with mock.patch.object(files, "_to_write_path") as to_write_path:
        files._write_bytes("path", "some_filename.png", False, b"some bytes")

    to_write_path.assert_called_once_with("path", "some_filename.png", False)
    to_write_path.return_value.write_bytes.assert_called_once_with(b"some bytes")


class TestBytes:
    @pytest.fixture
    def bytes_obj(self):
        return files.Bytes(b"some data", "something.txt")

    @pytest.mark.parametrize("data_type", [bytes, bytearray, memoryview])
    @pytest.mark.asyncio
    async def test_save(self, bytes_obj, data_type):
        bytes_obj.data = mock.Mock(data_type)
        mock_executor = object()
        loop = mock.Mock(run_in_executor=mock.AsyncMock())

        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            with mock.patch.object(files.Resource, "save") as super_save:
                await bytes_obj.save("some_path/", executor=mock_executor, force=True)

        super_save.assert_not_called()
        loop.run_in_executor.assert_awaited_once_with(
            mock_executor, files._write_bytes, "some_path/", "something.txt", True, bytes_obj.data
        )

    @pytest.mark.asyncio
    async def test_save_when_data_is_not_bytes(self, bytes_obj):
        bytes_obj.data = object()
        mock_executor = object()

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            with mock.patch.object(files.Resource, "save") as super_save:
                await bytes_obj.save("some_path/", executor=mock_executor, force=True)

        super_save.assert_called_once_with("some_path/", executor=mock_executor, force=True)
        get_running_loop.return_value.run_in_executor.assert_not_called()

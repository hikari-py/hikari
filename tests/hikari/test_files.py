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

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

import base64
import concurrent.futures
import pathlib
import random
import tempfile

import mock
import pytest

from hikari import files
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


class Test_FileAsyncReaderContextManagerImpl:
    @pytest.mark.asyncio()
    async def test_context_manager(self):
        mock_reader = mock.Mock(executor=concurrent.futures.ThreadPoolExecutor())
        context_manager = files._FileAsyncReaderContextManagerImpl(mock_reader)

        with tempfile.NamedTemporaryFile() as file:
            mock_reader.path = pathlib.Path(file.name)

            async with context_manager as reader:
                assert reader is mock_reader

    @pytest.mark.asyncio()
    async def test_context_manager_for_unknown_file(self):
        mock_reader = mock.Mock(executor=concurrent.futures.ThreadPoolExecutor())
        context_manager = files._FileAsyncReaderContextManagerImpl(mock_reader)

        mock_reader.path = pathlib.Path(
            base64.urlsafe_b64encode(random.getrandbits(512).to_bytes(64, "little")).decode()
        )

        with pytest.raises(FileNotFoundError):  # noqa:  PT012 - raises block should contain a single statement
            async with context_manager:
                ...

    @pytest.mark.asyncio()
    async def test_test_context_manager_when_target_is_dir(self):
        mock_reader = mock.Mock(executor=concurrent.futures.ThreadPoolExecutor())
        context_manager = files._FileAsyncReaderContextManagerImpl(mock_reader)

        with tempfile.TemporaryDirectory() as name:
            mock_reader.path = pathlib.Path(name)

            with pytest.raises(IsADirectoryError):  # noqa:  PT012 - raises block should contain a single statement
                async with context_manager:
                    ...

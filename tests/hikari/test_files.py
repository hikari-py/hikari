# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

import pathlib

import mock
import pytest

from hikari import files
from tests.hikari import hikari_test_helpers


class TestEnsurePath:
    def test_when_doesnt_exists(self):
        mock_path = mock.Mock(exists=mock.Mock(return_value=False))

        with mock.patch.object(pathlib, "Path", return_value=mock_path) as pathlib_path:
            with pytest.raises(FileNotFoundError):
                files.ensure_path("cats.py")

        pathlib_path.assert_called_once_with("cats.py")

    def test_when_is_dir(self):
        mock_path = mock.Mock(exists=mock.Mock(return_value=True), is_dir=mock.Mock(return_value=True))

        with mock.patch.object(pathlib, "Path", return_value=mock_path) as pathlib_path:
            with pytest.raises(IsADirectoryError):
                files.ensure_path("cats.py")

        pathlib_path.assert_called_once_with("cats.py")

    def test_ensure_path(self):
        mock_path = mock.Mock(exists=mock.Mock(return_value=True), is_dir=mock.Mock(return_value=False))

        with mock.patch.object(pathlib, "Path", return_value=mock_path) as pathlib_path:
            assert files.ensure_path("cats.py") is mock_path

        pathlib_path.assert_called_once_with("cats.py")


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

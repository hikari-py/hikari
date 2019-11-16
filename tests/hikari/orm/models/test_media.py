#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import asynctest
import pytest

from hikari.internal_utilities import io_helpers
from hikari.orm.models import media
from tests.hikari import _helpers
from tests.hikari.orm.testdata import *


@pytest.fixture
@fixture_test_data(raw("avatar.jpeg.b64"))
def test_avatar_data_uri(test_data):
    return test_data.rstrip()


@pytest.mark.model
class TestAvatar:
    def test_Avatar_compress_then_decompress_gives_same_data(self, test_avatar_data_uri):
        avatar = media.Avatar.from_data_uri_scheme(test_avatar_data_uri)
        new_uri = avatar.to_data_uri()
        assert test_avatar_data_uri == new_uri

    def test_Avatar_get_file_types(self, test_avatar_data_uri):
        guesses = media.Avatar.from_data_uri_scheme(test_avatar_data_uri).get_file_types()
        assert ".jpg" in guesses
        assert ".jpeg" in guesses

    def test_Avatar_to_file_objects(self, test_avatar_data_uri):
        avatar = media.Avatar.from_data_uri_scheme(test_avatar_data_uri)
        assert hasattr(avatar.to_file_object(), "read")

    def test_Avatar_len(self, test_avatar_data_uri):
        assert len(test_avatar_data_uri) > len(media.Avatar.from_data_uri_scheme(test_avatar_data_uri))

    def test_invalid_Avatar_uri_scheme(self):
        try:
            media.Avatar.from_data_uri_scheme("potato")
            assert False, "No TypeError raised"
        except TypeError:
            pass


@pytest.mark.model
class TestAttachment:
    def test_Attachment_when_not_an_image(self):
        attachment = media.Attachment(
            {
                "id": "123456",
                "filename": "doggo.mov",
                "url": "bork.com",
                "proxy_url": "we-are-watching-you.nsa.bork.com",
                "size": 69,
            }
        )

        assert attachment.id == 123456
        assert attachment.filename == "doggo.mov"
        assert attachment.url == "bork.com"
        assert attachment.proxy_url == "we-are-watching-you.nsa.bork.com"
        assert attachment.size == 69
        assert attachment.width is None
        assert attachment.height is None

    def test_Attachment_when_an_image(self):
        attachment = media.Attachment(
            {
                "id": "123456",
                "filename": "doggo.png",
                "url": "bork.com",
                "proxy_url": "we-are-watching-you.nsa.bork.com",
                "size": 69,
                "width": 1920,
                "height": 1080,
            }
        )

        assert attachment.id == 123456
        assert attachment.filename == "doggo.png"
        assert attachment.url == "bork.com"
        assert attachment.proxy_url == "we-are-watching-you.nsa.bork.com"
        assert attachment.size == 69
        assert attachment.width == 1920
        assert attachment.height == 1080

    @pytest.mark.asyncio
    async def test_Attachment_save(self):
        chunks = 1000
        i = 0

        async def _readany():
            nonlocal i
            i += 1
            while i < chunks:
                yield bytes(i)
                i += 1
            else:
                yield None

        iter = _readany()

        async def readany():
            return await iter.__anext__()

        async def __aenter__(self):
            return self

        async def __aexit__(self, ex_t, ex, ex_tb):
            ...

        aiofiles_obj = asynctest.MagicMock()
        aiofiles_obj.write = asynctest.CoroutineMock()
        aiohttp_resp_obj = asynctest.MagicMock()
        aiohttp_resp_obj.content = asynctest.MagicMock()
        aiohttp_resp_obj.content.readany = asynctest.CoroutineMock(wraps=readany)
        aiofiles_obj.__aenter__ = __aenter__
        aiohttp_resp_obj.__aenter__ = __aenter__
        aiofiles_obj.__aexit__ = __aexit__
        aiohttp_resp_obj.__aexit__ = __aexit__

        with _helpers.mock_patch("aiofiles.open", return_value=aiofiles_obj) as aiofiles_open:
            with _helpers.mock_patch("aiohttp.request", return_value=aiohttp_resp_obj) as aiohttp_request:
                attachment = media.Attachment(
                    {
                        "id": "123456",
                        "filename": "doggo.png",
                        "url": "bork.com",
                        "proxy_url": "we-are-watching-you.nsa.bork.com",
                        "size": 69,
                        "width": 1920,
                        "height": 1080,
                    }
                )

                fake_file = "test.file"
                await attachment.save(fake_file)

                aiohttp_request.assert_called_once_with("get", attachment.url)
                aiofiles_open.assert_called_once_with(fake_file, "wb", executor=None, loop=None)
                assert aiofiles_obj.write.await_count == chunks
                assert aiohttp_resp_obj.content.readany.await_count == chunks
                assert i == chunks

    @pytest.mark.asyncio
    async def test_Attachment_read(self):
        async def __aenter__(self):
            return self

        async def __aexit__(self, ex_t, ex, ex_tb):
            ...

        expected_result = object()

        aiohttp_resp_obj = asynctest.MagicMock()
        aiohttp_resp_obj.read = asynctest.CoroutineMock(return_value=expected_result)
        aiohttp_resp_obj.raise_for_status = asynctest.MagicMock()
        aiohttp_resp_obj.__aenter__ = __aenter__
        aiohttp_resp_obj.__aexit__ = __aexit__

        with _helpers.mock_patch("aiohttp.request", return_value=aiohttp_resp_obj) as aiohttp_request:
            attachment = media.Attachment(
                {
                    "id": "123456",
                    "filename": "doggo.png",
                    "url": "bork.com",
                    "proxy_url": "we-are-watching-you.nsa.bork.com",
                    "size": 69,
                    "width": 1920,
                    "height": 1080,
                }
            )

            actual_result = await attachment.read()

            aiohttp_request.assert_called_once_with("get", attachment.url)
            aiohttp_resp_obj.raise_for_status.assert_called_once()
            aiohttp_resp_obj.read.assert_awaited_once()
            assert actual_result is expected_result


@pytest.mark.model
@pytest.mark.asyncio
async def test_InMemoryFile_open():
    file = media.InMemoryFile("foo", "this is data")

    class ContextManager:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with _helpers.mock_patch(io_helpers.make_resource_seekable, return_value=ContextManager()) as mrs:
        async with file.open() as fp:
            assert isinstance(fp, ContextManager)
        mrs.assert_called_once_with("this is data")


@pytest.mark.model
@pytest.mark.asyncio
async def test_File_open():
    class ContextManager:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with _helpers.mock_patch("aiofiles.open", return_value=ContextManager()) as aiofiles_open:
        file = media.File("foo")

        async with file.open() as fp:
            assert isinstance(fp, ContextManager)

        aiofiles_open.assert_called_once_with("foo")


@pytest.mark.model
@pytest.mark.parametrize("file", [media.File("foo",), media.InMemoryFile("foo", "foo")])
def test_hash_File(file):
    assert hash(file) == hash(file.name)

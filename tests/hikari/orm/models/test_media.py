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
import asyncmock as mock
import pytest

from hikari.internal_utilities import storage
from hikari.orm.models import media
from tests.hikari import _helpers


@pytest.fixture
def test_image_data_uri():
    return (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAE0lEQVR42mP8/5+hngENMNJAEAD4tAx3yVEBjwAA"
        "AABJRU5ErkJggg=="
    )


@pytest.fixture
def test_image_data():
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\x00\x00\x00\x05\x08\x06\x00\x00\x00\x8do&\xe5\x00\x00\x00"
        b"\x13IDATx\xdac\xfc\xff\x9f\xa1\x9e\x01\r0\xd2@\x10\x00\xf8\xb4\x0cw\xc9Q\x01\x8f\x00\x00\x00\x00IEND\xaeB`"
        b"\x82"
    )


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
        chunks = 100
        aiofiles_obj = mock.AsyncMock()
        aiofiles_obj.write = mock.AsyncMock()
        aiohttp_resp_obj = mock.AsyncMock()
        aiohttp_resp_obj.raise_for_status = mock.MagicMock()
        aiohttp_resp_obj.content = mock.MagicMock()
        aiohttp_resp_obj.content.readany = mock.AsyncMock(side_effect=[*(bytes(i) for i in range(chunks)), None])

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
                assert aiofiles_obj.write.call_count == chunks + 1
                assert aiohttp_resp_obj.content.readany.call_count == chunks + 1

    @pytest.mark.asyncio
    async def test_Attachment_read(self):
        expected_result = object()

        aiohttp_resp_obj = mock.AsyncMock()
        aiohttp_resp_obj.read = mock.AsyncMock(return_value=expected_result)
        aiohttp_resp_obj.raise_for_status = mock.MagicMock()

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
            aiohttp_resp_obj.read.assert_called_once()
            assert actual_result is expected_result

    @pytest.mark.model
    def test_Attachment___repr__(self):
        assert repr(
            _helpers.mock_model(media.Attachment, id=42, filename="foo", size=69, __repr__=media.Attachment.__repr__)
        )


@pytest.mark.model
@pytest.mark.asyncio
async def test_InMemoryFile_open():
    file = media.InMemoryFile("foo", "this is data")

    class ContextManager:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with _helpers.mock_patch(storage.make_resource_seekable, return_value=ContextManager()) as mrs:
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
@pytest.mark.parametrize("file", [media.File("foo"), media.InMemoryFile("foo", "bar")])
def test_hash_File(file):
    assert hash(file) == hash(file.name)

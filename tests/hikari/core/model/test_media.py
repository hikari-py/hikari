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

import pytest

from hikari.core.model import media

from tests.hikari.core.testdata import *


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
    def test_Attachment_from_dict_when_not_an_image(self):
        attachment = media.Attachment.from_dict(
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

    def test_Attachment_from_dict_when_an_image(self):
        attachment = media.Attachment.from_dict(
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

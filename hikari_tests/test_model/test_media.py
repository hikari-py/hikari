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

from hikari.model import media
from .testdata import *


@pytest.fixture
@with_test_data(raw("avatar.jpeg.b64"))
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

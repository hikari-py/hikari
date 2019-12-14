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
import pytest

from hikari.internal_utilities import media_transformations


@pytest.mark.parametrize(
    ["img_bytes", "expect"],
    [
        (b"\211PNG\r\n\032\n", "data:image/png;base64,iVBORw0KGgo="),
        (b"      Exif", "data:image/jpeg;base64,ICAgICAgRXhpZg=="),
        (b"      JFIF", "data:image/jpeg;base64,ICAgICAgSkZJRg=="),
        (b"GIF87a", "data:image/gif;base64,R0lGODdh"),
        (b"GIF89a", "data:image/gif;base64,R0lGODlh"),
        (b"RIFF    WEBP", "data:image/webp;base64,UklGRiAgICBXRUJQ"),
    ],
)
def test_image_bytes_to_image_data_img_types(img_bytes, expect):
    assert media_transformations.image_bytes_to_image_data(img_bytes) == expect


def test_image_bytes_to_image_data_when_None_returns_None():
    assert media_transformations.image_bytes_to_image_data(None) == None


def test_image_bytes_to_image_data_when_unsuported_image_type_raises_value_error():
    try:
        media_transformations.image_bytes_to_image_data(b"")
        assert False
    except ValueError:
        assert True

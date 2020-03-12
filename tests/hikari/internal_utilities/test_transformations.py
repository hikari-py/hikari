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
import dataclasses
import typing

import cymock as mock
import pytest

from hikari.internal_utilities import transformations


@pytest.mark.parametrize(
    ["value", "cast", "expect"],
    [
        ("22", int, 22),
        (None, int, None),
        ("22", lambda a: float(a) / 10 + 7, 9.2),
        (None, lambda a: float(a) / 10 + 7, None),
    ],
)
def test_nullable_cast(value, cast, expect):
    assert transformations.nullable_cast(value, cast) == expect


@pytest.mark.parametrize(
    ["value", "cast", "default", "expect"],
    [
        ("hello", int, "dead", "dead"),
        ("22", int, "dead", 22),
        ("22", lambda n: n + 4, ..., ...),
        (22, lambda n: n + 4, ..., 26),
    ],
)
def test_try_cast(value, cast, default, expect):
    assert transformations.try_cast(value, cast, default) == expect


def test_put_if_specified_when_specified():
    d = {}
    transformations.put_if_specified(d, "foo", 69)
    transformations.put_if_specified(d, "bar", "hi")
    transformations.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    transformations.put_if_specified(d, "bar", ...)
    assert d == {}


def test_put_if_specified_when_type_after_passed():
    d = {}
    transformations.put_if_specified(d, "foo", 69, str)
    transformations.put_if_specified(d, "bar", "69", int)
    assert d == {"foo": "69", "bar": 69}


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
    assert transformations.image_bytes_to_image_data(img_bytes) == expect


def test_image_bytes_to_image_data_when_None_returns_None():
    assert transformations.image_bytes_to_image_data(None) is None


def test_image_bytes_to_image_data_when_unsuported_image_type_raises_value_error():
    try:
        transformations.image_bytes_to_image_data(b"")
        assert False
    except ValueError:
        assert True

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

from hikari.utilities import files
from hikari.utilities import cdn


def test_generate_cdn_url():
    url = cdn.generate_cdn_url("not", "a", "path", format_="neko", size=16)
    assert url == files.URL("https://cdn.discordapp.com/not/a/path.neko?size=16")


def test_generate_cdn_url_with_size_set_to_none():
    url = cdn.generate_cdn_url("not", "a", "path", format_="neko", size=None)
    assert url == files.URL("https://cdn.discordapp.com/not/a/path.neko")


def test_generate_cdn_url_with_invalid_size_out_of_limits():
    with pytest.raises(ValueError):
        cdn.generate_cdn_url("not", "a", "path", format_="neko", size=11)


def test_generate_cdn_url_with_invalid_size_now_power_of_two():
    with pytest.raises(ValueError):
        cdn.generate_cdn_url("not", "a", "path", format_="neko", size=111)


def test_get_default_avatar_index():
    assert cdn.get_default_avatar_index("1234") == 4


def test_get_default_avatar_url():
    assert cdn.get_default_avatar_url("1234") == files.URL("https://cdn.discordapp.com/embed/avatars/4.png")

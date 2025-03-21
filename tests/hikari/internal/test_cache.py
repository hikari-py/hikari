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
from __future__ import annotations

import copy

import mock

from hikari import snowflakes
from hikari import stickers
from hikari.internal import cache


class TestStickerData:
    def test_from_entity(self) -> None:
        mock_user = object()
        mock_sticker = stickers.GuildSticker(
            id=snowflakes.Snowflake(69420),
            name="lulzor",
            format_type=123,
            description="Fake sticker",
            guild_id=snowflakes.Snowflake(42069),
            is_available=True,
            tag="some tag",
            user=None,
        )

        data = cache.GuildStickerData.build_from_entity(mock_sticker, user=mock_user)

        assert data.id is mock_sticker.id
        assert data.name is mock_sticker.name
        assert data.format_type is mock_sticker.format_type
        assert data.description is mock_sticker.description
        assert data.guild_id is mock_sticker.guild_id
        assert data.is_available is mock_sticker.is_available
        assert data.tag is mock_sticker.tag
        assert data.user is mock_user

    def test_from_entity_when_user_not_passed(self) -> None:
        mock_user = object()
        mock_sticker = mock_sticker = stickers.GuildSticker(
            id=snowflakes.Snowflake(69420),
            name="lulzor",
            format_type=123,
            description="Fake sticker",
            guild_id=snowflakes.Snowflake(42069),
            is_available=True,
            tag="some tag",
            user=mock_user,
        )

        with mock.patch.object(copy, "copy") as mock_copy:
            with mock.patch.object(cache, "RefCell") as refcell:
                data = cache.GuildStickerData.build_from_entity(mock_sticker)

        assert data.user is refcell.return_value
        mock_copy.assert_called_once_with(mock_user)
        refcell.assert_called_once_with(mock_copy.return_value)

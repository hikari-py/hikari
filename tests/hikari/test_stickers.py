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
import mock
import pytest

from hikari import snowflakes
from hikari import stickers
from hikari import urls
from hikari.internal import routes


class TestStickerPack:
    @pytest.fixture
    def model(self):
        return stickers.StickerPack(
            id=123,
            name="testing",
            description="testing description",
            cover_sticker_id=snowflakes.Snowflake(6541234),
            stickers=[],
            sku_id=123,
            banner_asset_id=snowflakes.Snowflake(541231),
        )

    def test_banner_url(self, model):
        banner = object()

        with mock.patch.object(stickers.StickerPack, "make_banner_url", return_value=banner):
            assert model.banner_url is banner

    def test_make_banner_url(self, model):
        with mock.patch.object(
            routes, "CDN_STICKER_PACK_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext="url", size=512) == "file"

        route.compile_to_file.assert_called_once_with(urls.CDN_URL, hash=541231, size=512, file_format="url")

    def test_make_banner_url_when_no_banner_asset(self, model):
        model.banner_asset_id = None

        assert model.make_banner_url(ext="url", size=512) is None


class TestPartialSticker:
    @pytest.fixture
    def model(self):
        return stickers.PartialSticker(id=123, name="testing", format_type="some")

    def test_image_url(self, model):
        model.format_type = stickers.StickerFormatType.PNG

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.image_url == "file"

        route.compile_to_file.assert_called_once_with(urls.CDN_URL, sticker_id=123, file_format="png")

    def test_image_url_when_LOTTIE(self, model):
        model.format_type = stickers.StickerFormatType.LOTTIE

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.image_url == "file"

        route.compile_to_file.assert_called_once_with(urls.CDN_URL, sticker_id=123, file_format="json")

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

    def test_make_banner_url_format_set_to_deprecated_ext_argument_if_provided(self, model):
        with mock.patch.object(
            routes, "CDN_STICKER_PACK_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, hash=541231, size=4096, file_format="JPEG", lossless=True
        )

    def test_banner_url(self, model):
        banner = object()

        with mock.patch.object(stickers.StickerPack, "make_banner_url", return_value=banner):
            assert model.banner_url is banner

    def test_make_banner_url(self, model):
        with mock.patch.object(
            routes, "CDN_STICKER_PACK_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(file_format="URL", size=512) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, hash=541231, size=512, file_format="URL", lossless=True
        )

    def test_make_banner_url_when_no_banner_asset(self, model):
        model.banner_asset_id = None

        assert model.make_banner_url(file_format="URL", size=512) is None


class TestPartialSticker:
    @pytest.fixture
    def model(self):
        return stickers.PartialSticker(id=123, name="testing", format_type="some")

    def test_make_url_uses_CDN_when_LOTTIE(self, model):
        model.format_type = stickers.StickerFormatType.LOTTIE

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url() == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, sticker_id=123, file_format="LOTTIE", size=4096, lossless=True
        )

    def test_make_url_uses_MEDIA_PROXY_when_not_LOTTIE(self, model):
        model.format_type = stickers.StickerFormatType.GIF

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url() == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, sticker_id=123, file_format="GIF", size=4096, lossless=True
        )

    def test_make_url_raises_TypeError_when_GIF_sticker_requested_as_APNG(self, model):
        model.format_type = stickers.StickerFormatType.GIF

        with pytest.raises(TypeError):
            model.make_url(file_format="APNG")

    def test_make_url_raises_TypeError_when_APNG_sticker_requested_as_AWEBP_or_GIF(self, model):
        model.format_type = stickers.StickerFormatType.APNG

        with pytest.raises(TypeError):
            model.make_url(file_format="AWEBP")

        with pytest.raises(TypeError):
            model.make_url(file_format="GIF")

    def test_make_url_raises_TypeError_when_PNG_sticker_requested_as_animated_format(self, model):
        model.format_type = stickers.StickerFormatType.PNG

        with pytest.raises(TypeError):
            model.make_url(file_format="APNG")

        with pytest.raises(TypeError):
            model.make_url(file_format="AWEBP")

        with pytest.raises(TypeError):
            model.make_url(file_format="GIF")

    def test_make_url_raises_TypeError_when_LOTTIE_sticker_requested_as_non_LOTTIE_format(self, model):
        model.format_type = stickers.StickerFormatType.LOTTIE

        with pytest.raises(TypeError):
            model.make_url(file_format="PNG")

    def test_make_url_raises_TypeError_when_non_LOTTIE_sticker_requested_as_LOTTIE(self, model):
        model.format_type = stickers.StickerFormatType.PNG

        with pytest.raises(TypeError):
            model.make_url(file_format="LOTTIE")

    def test_make_url_applies_correct_settings_for_APNG(self, model):
        model.format_type = stickers.StickerFormatType.APNG

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url(file_format="PNG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, sticker_id=123, file_format="PNG", size=4096, lossless=True
        )

    def test_make_url_applies_correct_settings_for_AWEBP(self, model):
        model.format_type = stickers.StickerFormatType.GIF

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url(file_format="AWEBP") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, sticker_id=123, file_format="AWEBP", size=4096, lossless=True
        )

    def test_make_url_applies_correct_settings_for_WEBP_lossless(self, model):
        model.format_type = stickers.StickerFormatType.PNG

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url(file_format="WEBP", lossless=True) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, sticker_id=123, file_format="WEBP", size=4096, lossless=True
        )

    def test_make_url_applies_correct_settings_for_WEBP_lossy(self, model):
        model.format_type = stickers.StickerFormatType.PNG

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url(file_format="WEBP", lossless=False) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, sticker_id=123, file_format="WEBP", size=4096, lossless=False
        )

    def test_make_url_applies_no_extra_settings_for_non_special_formats(self, model):
        model.format_type = stickers.StickerFormatType.PNG

        with mock.patch.object(
            routes, "CDN_STICKER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_url(file_format="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, sticker_id=123, file_format="JPEG", size=4096, lossless=True
        )

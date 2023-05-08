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

from hikari import files
from hikari import presences
from hikari import snowflakes
from hikari import urls
from hikari.impl import gateway_bot
from hikari.internal import routes


@pytest.fixture()
def mock_app():
    return mock.Mock(spec_set=gateway_bot.GatewayBot)


class TestActivityAssets:
    def test_large_image_url_property(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=None, small_text=None
        )

        with mock.patch.object(presences.ActivityAssets, "make_large_image_url") as make_large_image_url:
            result = asset.large_image_url

        assert result is make_large_image_url.return_value
        make_large_image_url.assert_called_once_with()

    def test_large_image_url_property_when_runtime_error(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=None, small_text=None
        )

        with mock.patch.object(
            presences.ActivityAssets, "make_large_image_url", side_effect=RuntimeError
        ) as make_large_image_url:
            result = asset.large_image_url

        assert result is None
        make_large_image_url.assert_called_once_with()

    def test_make_large_image_url(self):
        asset = presences.ActivityAssets(
            application_id=45123123, large_image="541sdfasdasd", large_text=None, small_image=None, small_text=None
        )

        with mock.patch.object(routes, "CDN_APPLICATION_ASSET") as route:
            assert asset.make_large_image_url(ext="fa", size=3121) is route.compile_to_file.return_value

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=45123123, hash="541sdfasdasd", size=3121, file_format="fa"
        )

    def test_make_large_image_url_when_no_hash(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=None, small_text=None
        )

        assert asset.make_large_image_url() is None

    @pytest.mark.parametrize(
        ("asset_hash", "expected"), [("mp:541sdfasdasd", "https://media.discordapp.net/541sdfasdasd")]
    )
    def test_make_large_image_url_when_dynamic_url(self, asset_hash: str, expected: str):
        asset = presences.ActivityAssets(
            application_id=None, large_image=asset_hash, large_text=None, small_image=None, small_text=None
        )

        assert asset.make_large_image_url() == files.URL(expected)

    def test_make_large_image_url_when_unknown_dynamic_url(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image="uwu:nou", large_text=None, small_image=None, small_text=None
        )

        with pytest.raises(RuntimeError, match="Unknown asset type"):
            asset.make_large_image_url()

    def test_small_image_url_property(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=None, small_text=None
        )

        with mock.patch.object(presences.ActivityAssets, "make_small_image_url") as make_small_image_url:
            result = asset.small_image_url

        assert result is make_small_image_url.return_value
        make_small_image_url.assert_called_once_with()

    def test_small_image_url_property_when_runtime_error(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=None, small_text=None
        )

        with mock.patch.object(
            presences.ActivityAssets, "make_small_image_url", side_effect=RuntimeError
        ) as make_small_image_url:
            result = asset.small_image_url

        assert result is None
        make_small_image_url.assert_called_once_with()

    def test_make_small_image_url(self):
        asset = presences.ActivityAssets(
            application_id=123321, large_image=None, large_text=None, small_image="aseqwsdas", small_text=None
        )

        with mock.patch.object(routes, "CDN_APPLICATION_ASSET") as route:
            assert asset.make_small_image_url(ext="eat", size=123312) is route.compile_to_file.return_value

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123321, hash="aseqwsdas", size=123312, file_format="eat"
        )

    def test_make_small_image_url_when_no_hash(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=None, small_text=None
        )

        assert asset.make_small_image_url() is None

    @pytest.mark.parametrize(("asset_hash", "expected"), [("mp:4123fdssdf", "https://media.discordapp.net/4123fdssdf")])
    def test_make_small_image_url_when_dynamic_url(self, asset_hash: str, expected: str):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image=asset_hash, small_text=None
        )

        assert asset.make_small_image_url() == files.URL(expected)

    def test_make_small_image_url_when_unknown_dynamic_url(self):
        asset = presences.ActivityAssets(
            application_id=None, large_image=None, large_text=None, small_image="meow:nyaa", small_text=None
        )

        with pytest.raises(RuntimeError, match="Unknown asset type"):
            asset.make_small_image_url()


class TestActivity:
    def test_str_operator(self):
        activity = presences.Activity(name="something", type=presences.ActivityType(1))
        assert str(activity) == "something"


class TestMemberPresence:
    @pytest.fixture()
    def model(self, mock_app):
        return presences.MemberPresence(
            app=mock_app,
            user_id=snowflakes.Snowflake(432),
            guild_id=snowflakes.Snowflake(234),
            visible_status=presences.Status.ONLINE,
            activities=mock.Mock(presences.RichActivity),
            client_status=mock.Mock(presences.ClientStatus),
        )

    @pytest.mark.asyncio()
    async def test_fetch_user(self, model):
        model.app.rest.fetch_user = mock.AsyncMock()

        assert await model.fetch_user() is model.app.rest.fetch_user.return_value
        model.app.rest.fetch_user.assert_awaited_once_with(432)

    @pytest.mark.asyncio()
    async def test_fetch_member(self, model):
        model.app.rest.fetch_member = mock.AsyncMock()

        assert await model.fetch_member() is model.app.rest.fetch_member.return_value
        model.app.rest.fetch_member.assert_awaited_once_with(234, 432)

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

from hikari import invites
from hikari import urls
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


class TestInviteCode:
    def test_str_operator(self):
        mock_invite = hikari_test_helpers.mock_class_namespace(
            invites.InviteCode, code=mock.PropertyMock(return_value="hikari")
        )()
        assert str(mock_invite) == "https://discord.gg/hikari"


class TestInviteGuild:
    @pytest.fixture
    def model(self):
        return invites.InviteGuild(
            app=mock.Mock(),
            id=123321,
            icon_hash="hi",
            name="bye",
            features=[],
            splash_hash="4o4o4o",
            banner_hash="fofoof",
            description="fkkfkf",
            verification_level=1,
            vanity_url_code=None,
            welcome_screen=None,
            nsfw_level=2,
        )

    def test_splash_url(self, model: invites.InviteGuild):
        splash = object()

        with mock.patch.object(invites.InviteGuild, "make_splash_url", return_value=splash):
            assert model.splash_url is splash

    def test_make_splash_url_when_hash(self, model: invites.InviteGuild):
        model.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_splash_url(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123321, hash="18dnf8dfbakfdh", size=2, file_format="url"
        )

    def test_make_splash_url_when_no_hash(self, model: invites.InviteGuild):
        model.splash_hash = None
        assert model.make_splash_url(ext="png", size=1024) is None

    def test_banner_url(self, model: invites.InviteGuild):
        banner = object()

        with mock.patch.object(invites.InviteGuild, "make_banner_url", return_value=banner):
            assert model.banner_url is banner

    def test_make_banner_url_when_hash(self, model: invites.InviteGuild):
        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext="url", size=512) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123321, hash="fofoof", size=512, file_format="url"
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_for_gif(self, model: invites.InviteGuild):
        model.banner_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=model.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="gif"
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_not_for_gif(self, model: invites.InviteGuild):
        model.banner_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=model.id, hash=model.banner_hash, size=4096, file_format="png"
        )

    def test_make_banner_url_when_no_hash(self, model: invites.InviteGuild):
        model.banner_hash = None
        assert model.make_banner_url(ext="png", size=2048) is None


class TestInviteWithMetadata:
    def test_uses_left(self):
        mock_invite = hikari_test_helpers.mock_class_namespace(
            invites.InviteWithMetadata, init_=False, max_uses=123, uses=55
        )()

        assert mock_invite.uses_left == 68

    def test_uses_left_when_none(self):
        mock_invite = hikari_test_helpers.mock_class_namespace(invites.InviteWithMetadata, init_=False, max_uses=None)()

        assert mock_invite.uses_left is None

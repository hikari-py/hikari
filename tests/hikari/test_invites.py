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

import datetime

import mock
import pytest

from hikari import guilds
from hikari import invites
from hikari import snowflakes
from hikari import urls
from hikari.internal import routes


class TestInviteCode:
    class MockInviteCode(invites.InviteCode):
        def __init__(self):
            self._code = "hikari"

        @property
        def code(self) -> str:
            return self._code

    @pytest.fixture
    def invite_code(self) -> invites.InviteCode:
        return TestInviteCode.MockInviteCode()

    def test_str_operator(self, invite_code: invites.InviteCode):
        assert str(invite_code) == "https://discord.gg/hikari"


class TestInviteGuild:
    @pytest.fixture
    def model(self) -> invites.InviteGuild:
        return invites.InviteGuild(
            app=mock.Mock(),
            id=snowflakes.Snowflake(123321),
            icon_hash="hi",
            name="bye",
            features=[],
            splash_hash="4o4o4o",
            banner_hash="fofoof",
            description="fkkfkf",
            verification_level=1,
            vanity_url_code=None,
            welcome_screen=None,
            nsfw_level=guilds.GuildNSFWLevel.SAFE,
        )

    def test_make_splash_url_format_set_to_deprecated_ext_argument_if_provided(self, model: invites.InviteGuild):
        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_splash_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123321, hash="4o4o4o", size=4096, file_format="JPEG", lossless=True
        )

    def test_splash_url(self, model: invites.InviteGuild):
        splash = mock.Mock()

        with mock.patch.object(invites.InviteGuild, "make_splash_url", return_value=splash):
            assert model.splash_url is splash

    def test_make_splash_url_when_hash(self, model: invites.InviteGuild):
        model.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_splash_url(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123321, hash="18dnf8dfbakfdh", size=2, file_format="URL", lossless=True
        )

    def test_make_splash_url_when_no_hash(self, model: invites.InviteGuild):
        model.splash_hash = None
        assert model.make_splash_url(ext="png", size=1024) is None

    def test_make_banner_url_format_set_to_deprecated_ext_argument_if_provided(self, model: invites.InviteGuild):
        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123321, hash="fofoof", size=4096, file_format="JPEG", lossless=True
        )

    def test_banner_url(self, model: invites.InviteGuild):
        banner = mock.Mock()

        with mock.patch.object(invites.InviteGuild, "make_banner_url", return_value=banner):
            assert model.banner_url is banner

    def test_make_banner_url_when_hash(self, model: invites.InviteGuild):
        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext="url", size=512) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123321, hash="fofoof", size=512, file_format="URL", lossless=True
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_for_gif(self, model: invites.InviteGuild):
        model.banner_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=model.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="GIF", lossless=True
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_not_for_gif(self, model: invites.InviteGuild):
        model.banner_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=model.id, hash=model.banner_hash, size=4096, file_format="PNG", lossless=True
        )

    def test_make_banner_url_when_no_hash(self, model: invites.InviteGuild):
        model.banner_hash = None
        assert model.make_banner_url(ext="png", size=2048) is None


class TestInviteWithMetadata:
    @pytest.fixture
    def invite_with_metadata(self):
        return invites.InviteWithMetadata(
            app=mock.Mock(),
            code="invite_code",
            guild=mock.Mock(),
            guild_id=snowflakes.Snowflake(12345),
            channel=mock.Mock(),
            channel_id=snowflakes.Snowflake(54321),
            inviter=mock.Mock(),
            target_type=invites.TargetType.EMBEDDED_APPLICATION,
            target_user=mock.Mock(),
            target_application=mock.Mock(),
            approximate_active_member_count=3,
            expires_at=datetime.datetime.fromtimestamp(3000),
            approximate_member_count=10,
            uses=55,
            max_uses=123,
            max_age=datetime.timedelta(3),
            is_temporary=True,
            created_at=datetime.datetime.fromtimestamp(2000),
        )

    def test_uses_left(self, invite_with_metadata: invites.InviteWithMetadata):
        assert invite_with_metadata.uses_left == 68

    def test_uses_left_when_none(self, invite_with_metadata: invites.InviteWithMetadata):
        invite_with_metadata.max_uses = None

        assert invite_with_metadata.uses_left is None

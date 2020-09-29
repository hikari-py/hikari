# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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

from hikari import guilds
from hikari import urls
from hikari import users
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


def test_GuildExplicitContentFilterLevel_str_operator():
    level = guilds.GuildExplicitContentFilterLevel(1)
    assert str(level) == "MEMBERS_WITHOUT_ROLES"


def test_GuildFeature_str_operator():
    feature = guilds.GuildFeature("ANIMATED_ICON")
    assert str(feature) == "ANIMATED_ICON"


def test_GuildMessageNotificationsLevel_str_operator():
    level = guilds.GuildMessageNotificationsLevel(1)
    assert str(level) == "ONLY_MENTIONS"


def test_GuildMFALevel_str_operator():
    level = guilds.GuildMFALevel(1)
    assert str(level) == "ELEVATED"


def test_GuildPremiumTier_str_operator():
    level = guilds.GuildPremiumTier(1)
    assert str(level) == "TIER_1"


def test_GuildSystemChannelFlag_str_operator():
    flag = guilds.GuildSystemChannelFlag(1 << 0)
    assert str(flag) == "SUPPRESS_USER_JOIN"


def test_GuildVerificationLevel_str_operator():
    level = guilds.GuildVerificationLevel(0)
    assert str(level) == "NONE"


def test_PartialRole_str_operator():
    mock_role = mock.Mock(guilds.Role)
    mock_role.name = "The Big Cool"
    assert guilds.PartialRole.__str__(mock_role) == "The Big Cool"


def test_IntegrationAccount_str_operator():
    mock_account = mock.Mock(guilds.IntegrationAccount)
    mock_account.name = "your mother"
    assert guilds.IntegrationAccount.__str__(mock_account) == "your mother"


def test_PartialIntegration_str_operator():
    mock_integration = mock.Mock(guilds.PartialIntegration)
    mock_integration.name = "not an integration"
    assert guilds.PartialIntegration.__str__(mock_integration) == "not an integration"


def test_Role_colour_property():
    role_obj = hikari_test_helpers.mock_entire_class_namespace(guilds.Role, color="color")
    assert role_obj.colour == "color"


class TestMember:
    @pytest.fixture()
    def obj(self):
        return hikari_test_helpers.mock_entire_class_namespace(
            guilds.Member,
            user=mock.Mock(
                users.User,
                id=123,
                username="davfsa",
                discriminator="0001",
                avatar_url="avatar",
                avatar_hash="a_12asfdjk1213",
                default_avatar_url="default avatar",
                format_avatar=mock.Mock(return_value="formated avatar"),
                is_bot=False,
                is_system=True,
                flags="flags",
                mention="<@123>",
                __str__=mock.Mock(return_value="davfsa#0001"),
            ),
            nickname="davb",
            guild_id=456,
        )

    def test_str_operator(self, obj):
        assert guilds.Member.__str__(obj) == "davfsa#0001"

    def test_id_property(self, obj):
        assert obj.id == 123

    def test_id_setter_property(self, obj):
        with pytest.raises(TypeError):
            obj.id = 456

    def test_username_property(self, obj):
        assert obj.username == "davfsa"

    def test_discriminator_property(self, obj):
        assert obj.discriminator == "0001"

    def test_avatar_hash_property(self, obj):
        assert obj.avatar_hash == "a_12asfdjk1213"

    def test_is_bot_property(self, obj):
        assert obj.is_bot is False

    def test_is_system_property(self, obj):
        assert obj.is_system is True

    def test_flags_property(self, obj):
        assert obj.flags == "flags"

    def test_avatar_url_property(self, obj):
        assert obj.avatar_url == "avatar"

    def test_format_avatar(self, obj):
        assert obj.format_avatar(ext="png", size=1) == "formated avatar"
        obj.user.format_avatar.assert_called_once_with(ext="png", size=1)

    def test_default_avatar_property(self, obj):
        assert obj.default_avatar_url == "default avatar"

    def test_display_name_property_when_nickname(self, obj):
        assert obj.display_name == "davb"

    def test_display_name_property_when_no_nickname(self, obj):
        obj.nickname = None
        assert obj.display_name == "davfsa"

    def test_mention_property_when_nickname(self, obj):
        assert obj.mention == "<@!123>"

    def test_mention_property_when_no_nickname(self, obj):
        obj.nickname = None
        assert obj.mention == "<@123>"

    def test_top_role_when_empty_cache(self, obj):
        obj.app.cache.get_roles_view_for_guild.return_value = {}

        assert obj.top_role is None

        obj.app.cache.get_roles_view_for_guild.assert_called_once_with(456)

    def test_top_role_when_role_ids_not_in_cache(self, obj):
        role1 = mock.Mock(id=123, position=2)
        role2 = mock.Mock(id=456, position=1)
        mock_cache_view = {123: role1, 456: role2}
        obj.app.cache.get_roles_view_for_guild.return_value = mock_cache_view
        obj.role_ids = [321, 654]

        assert obj.top_role is None

        obj.app.cache.get_roles_view_for_guild.assert_called_once_with(456)

    def test_top_role(self, obj):
        role1 = mock.Mock(id=321, position=2)
        role2 = mock.Mock(id=654, position=1)
        mock_cache_view = {321: role1, 654: role2}
        obj.app.cache.get_roles_view_for_guild.return_value = mock_cache_view
        obj.role_ids = [321, 654]

        assert obj.top_role is role1

        obj.app.cache.get_roles_view_for_guild.assert_called_once_with(456)


class TestPartialGuild:
    @pytest.fixture()
    def obj(self):
        return hikari_test_helpers.mock_entire_class_namespace(
            guilds.PartialGuild, name="hikari", id=1234567890, app=mock.Mock(shard_count=4), icon_hash=None
        )

    def test_str_operator(self, obj):
        assert str(obj) == "hikari"

    def test_shard_id_property(self, obj):
        assert obj.shard_id == 2

    @pytest.mark.parametrize("error", [TypeError, AttributeError, NameError])
    def test_shard_id_property_when_error(self, error, obj):
        obj.app.shard_count = mock.Mock(spec_set=int, side_effect=error)

        assert obj.shard_id is None

    def test_icon_url(self, obj):
        icon = object()

        with mock.patch.object(guilds.PartialGuild, "format_icon", return_value=icon):
            assert obj.icon_url is icon

    def test_format_icon_when_no_hash(self, obj):
        obj.icon_hash = None

        assert obj.format_icon(ext="png", size=2) is None

    def test_format_icon_when_format_is_None_and_avatar_hash_is_for_gif(self, obj):
        obj.icon_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_icon(ext=None, size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=1234567890,
            hash="a_18dnf8dfbakfdh",
            size=2,
            file_format="gif",
        )

    def test_format_icon_when_format_is_None_and_avatar_hash_is_not_for_gif(self, obj):
        obj.icon_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_icon(ext=None, size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=1234567890,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="png",
        )

    def test_format_icon_with_all_args(self, obj):
        obj.icon_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_icon(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=1234567890,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )


class TestGuildPreview:
    @pytest.fixture()
    def obj(self):
        return hikari_test_helpers.mock_entire_class_namespace(
            guilds.GuildPreview, id=123, splash_hash=None, discovery_splash_hash=None
        )

    def test_splash_url(self, obj):
        splash = object()

        with mock.patch.object(guilds.GuildPreview, "format_splash", return_value=splash):
            assert obj.splash_url is splash

    def test_format_splash_when_hash(self, obj):
        obj.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_splash(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )

    def test_format_splash_when_no_hash(self, obj):
        assert obj.format_splash(ext="png", size=2) is None

    def test_discovery_splash_url(self, obj):
        discovery_splash = object()

        with mock.patch.object(guilds.GuildPreview, "format_discovery_splash", return_value=discovery_splash):
            assert obj.discovery_splash_url is discovery_splash

    def test_format_discovery_splash_when_hash(self, obj):
        obj.discovery_splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_DISCOVERY_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_discovery_splash(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )

    def test_format_discovery_splash_when_no_hash(self, obj):
        assert obj.format_discovery_splash(ext="png", size=2) is None


class TestGuild:
    @pytest.fixture()
    def obj(self):
        class StubGuild(guilds.Guild):
            emojis = None
            get_emoji = None
            get_role = None
            roles = None

        return hikari_test_helpers.mock_entire_class_namespace(
            StubGuild, id=123, splash_hash=None, discovery_splash_hash=None, banner_hash=None
        )

    def test_splash_url(self, obj):
        splash = object()

        with mock.patch.object(guilds.Guild, "format_splash", return_value=splash):
            assert obj.splash_url is splash

    def test_format_splash_when_hash(self, obj):
        obj.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_splash(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )

    def test_format_splash_when_no_hash(self, obj):
        assert obj.format_splash(ext="png", size=2) is None

    def test_discovery_splash_url(self, obj):
        discovery_splash = object()

        with mock.patch.object(guilds.Guild, "format_discovery_splash", return_value=discovery_splash):
            assert obj.discovery_splash_url is discovery_splash

    def test_format_discovery_splash_when_hash(self, obj):
        obj.discovery_splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_DISCOVERY_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_discovery_splash(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )

    def test_format_discovery_splash_when_no_hash(self, obj):
        assert obj.format_discovery_splash(ext="png", size=2) is None

    def test_banner_url(self, obj):
        banner = object()

        with mock.patch.object(guilds.Guild, "format_banner", return_value=banner):
            assert obj.banner_url is banner

    def test_format_banner_when_hash(self, obj):
        obj.banner_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_banner(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )

    def test_format_banner_when_no_hash(self, obj):
        assert obj.format_banner(ext="png", size=2) is None

# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
import datetime

import mock
import pytest

from hikari import colors
from hikari import guilds
from hikari import permissions
from hikari import snowflakes
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.impl import bot
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


@pytest.fixture()
def mock_app():
    return mock.Mock(spec_set=bot.BotApp)


class TestPartialRole:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.PartialRole(
            app=mock_app,
            id=snowflakes.Snowflake(1106913972),
            name="The Big Cool",
        )

    def test_str_operator(self, model):
        assert str(model) == "The Big Cool"


def test_PartialApplication_str_operator():
    mock_application = mock.Mock(guilds.PartialApplication)
    mock_application.name = "beans"
    assert guilds.PartialApplication.__str__(mock_application) == "beans"


class TestPartialApplication:
    @pytest.fixture()
    def model(self):
        return hikari_test_helpers.mock_class_namespace(
            guilds.PartialApplication,
            init_=False,
            slots_=False,
            id=123,
            icon_hash="ahashicon",
        )()

    def test_icon_url_property(self, model):
        model.make_icon_url = mock.Mock(return_value="url")

        assert model.icon_url == "url"

        model.make_icon_url.assert_called_once_with()

    def test_make_icon_url_when_hash_is_None(self, model):
        model.icon_hash = None

        with mock.patch.object(
            routes, "CDN_APPLICATION_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_make_icon_url_when_hash_is_not_None(self, model):
        with mock.patch.object(
            routes, "CDN_APPLICATION_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="ahashicon", size=1, file_format="jpeg"
        )


class TestIntegrationAccount:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.IntegrationAccount(id="foo", name="bar")

    def test_str_operator(self, model):
        assert str(model) == "bar"


class TestPartialIntegration:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.PartialIntegration(
            account=mock.Mock(return_value=guilds.IntegrationAccount),
            id=snowflakes.Snowflake(69420),
            name="nice",
            type="illegal",
        )

    def test_str_operator(self, model):
        assert str(model) == "nice"


class TestRole:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.Role(
            app=mock_app,
            id=snowflakes.Snowflake(979899100),
            name="@everyone",
            color=colors.Color(0x1A2B3C),
            guild_id=snowflakes.Snowflake(112233),
            is_hoisted=False,
            is_managed=False,
            is_mentionable=True,
            permissions=permissions.Permissions.CONNECT,
            position=12,
            bot_id=None,
            integration_id=None,
            is_premium_subscriber_role=False,
        )

    def test_colour_property(self, model):
        assert model.colour == colors.Color(0x1A2B3C)


class TestMember:
    @pytest.fixture()
    def mock_user(self):
        return mock.Mock(spec_set=users.User, id=snowflakes.Snowflake(123))

    @pytest.fixture()
    def model(self, mock_user):
        return guilds.Member(
            guild_id=snowflakes.Snowflake(456),
            is_deaf=True,
            is_mute=True,
            is_pending=False,
            joined_at=datetime.datetime.now().astimezone(),
            nickname="davb",
            premium_since=None,
            role_ids=[
                snowflakes.Snowflake(456),
                snowflakes.Snowflake(1234),
            ],
            user=mock_user,
        )

    def test_str_operator(self, model, mock_user):
        assert str(model) == str(mock_user)

    def test_app_property(self, model, mock_user):
        assert model.app is mock_user.app

    def test_id_property(self, model, mock_user):
        assert model.id is mock_user.id

    def test_id_setter_property(self, model):
        with pytest.raises(TypeError):
            model.id = 456

    def test_username_property(self, model, mock_user):
        assert model.username is mock_user.username

    def test_discriminator_property(self, model, mock_user):
        assert model.discriminator is mock_user.discriminator

    def test_avatar_hash_property(self, model, mock_user):
        assert model.avatar_hash is mock_user.avatar_hash

    def test_is_bot_property(self, model, mock_user):
        assert model.is_bot is mock_user.is_bot

    def test_is_system_property(self, model, mock_user):
        assert model.is_system is mock_user.is_system

    def test_flags_property(self, model, mock_user):
        assert model.flags is mock_user.flags

    def test_avatar_url_property(self, model, mock_user):
        assert model.avatar_url is mock_user.avatar_url

    def test_make_avatar_url(self, model, mock_user):
        result = model.make_avatar_url(ext="png", size=4096)
        mock_user.make_avatar_url.assert_called_once_with(ext="png", size=4096)
        assert result is mock_user.make_avatar_url.return_value

    @pytest.mark.asyncio
    async def test_fetch_dm_channel(self, model, mock_user):
        mock_user.fetch_dm_channel = mock.AsyncMock()
        result = await model.fetch_dm_channel()
        mock_user.fetch_dm_channel.assert_awaited_once_with()
        assert result is mock_user.fetch_dm_channel.return_value

    @pytest.mark.asyncio
    async def test_fetch_self(self, model):
        model.user.app.rest.fetch_member = mock.AsyncMock()

        assert await model.fetch_self() is model.user.app.rest.fetch_member.return_value

        model.user.app.rest.fetch_member.assert_awaited_once_with(456, 123)

    @pytest.mark.asyncio
    async def test_ban(self, model):
        model.app.rest.ban_user = mock.AsyncMock()

        await model.ban(delete_message_days=10, reason="bored")

        model.app.rest.ban_user.assert_awaited_once_with(456, 123, delete_message_days=10, reason="bored")

    def test_default_avatar_url_property(self, model, mock_user):
        assert model.default_avatar_url is mock_user.default_avatar_url

    def test_display_name_property_when_nickname(self, model):
        assert model.display_name == "davb"

    def test_display_name_property_when_no_nickname(self, model, mock_user):
        model.nickname = None
        assert model.display_name is mock_user.username

    def test_mention_property_when_nickname(self, model):
        assert model.mention == "<@!123>"

    def test_mention_property_when_no_nickname(self, model, mock_user):
        model.nickname = None
        assert model.mention == mock_user.mention

    def test_roles(self, model):
        role1 = mock.Mock(id=321, position=2)
        role2 = mock.Mock(id=654, position=1)
        mock_cache_view = {321: role1, 654: role2}
        model.user.app.cache.get_roles_view_for_guild.return_value = mock_cache_view
        model.role_ids = [321, 654]

        assert model.roles == [role1, role2]

        model.user.app.cache.get_roles_view_for_guild.assert_called_once_with(456)

    def test_roles_when_role_ids_not_in_cache(self, model):
        role1 = mock.Mock(id=123, position=2)
        role2 = mock.Mock(id=456, position=1)
        mock_cache_view = {123: role1, 456: role2}
        model.user.app.cache.get_roles_view_for_guild.return_value = mock_cache_view
        model.role_ids = [321, 456]

        assert model.roles == [role2]

        model.user.app.cache.get_roles_view_for_guild.assert_called_once_with(456)

    def test_roles_when_empty_cache(self, model):
        model.user.app.cache.get_roles_view_for_guild.return_value = {}

        assert model.roles == []

        model.user.app.cache.get_roles_view_for_guild.assert_called_once_with(456)

    def test_roles_when_no_cache_trait(self, model):
        model.user.app = object()

        assert model.roles == []

    def test_top_role(self, model):
        role1 = mock.Mock(id=321, position=2)
        role2 = mock.Mock(id=654, position=1)

        with mock.patch.object(guilds.Member, "roles", new=[role1, role2]):
            assert model.top_role is role1

    def test_top_role_when_roles_is_empty(self, model):
        with mock.patch.object(guilds.Member, "roles", new=[]):
            assert model.top_role is None

    def test_presence(self, model):
        assert model.presence is model.user.app.cache.get_presence.return_value
        model.user.app.cache.get_presence.assert_called_once_with(456, 123)

    def test_presence_when_no_cache_trait(self, model):
        model.user.app = object()
        assert model.presence is None


class TestPartialGuild:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.PartialGuild(
            app=mock_app,
            id=snowflakes.Snowflake(90210),
            icon_hash="yeet",
            name="hikari",
        )

    def test_str_operator(self, model):
        assert str(model) == "hikari"

    def test_shard_id_property(self, model):
        model.app.shard_count = 4
        assert model.shard_id == 0

    def test_shard_id_when_not_shard_aware(self, model):
        model.app = object()

        assert model.shard_id is None

    def test_icon_url(self, model):
        icon = object()

        with mock.patch.object(guilds.PartialGuild, "make_icon_url", return_value=icon):
            assert model.icon_url is icon

    def test_make_icon_url_when_no_hash(self, model):
        model.icon_hash = None

        assert model.make_icon_url(ext="png", size=2048) is None

    def test_make_icon_url_when_format_is_None_and_avatar_hash_is_for_gif(self, model):
        model.icon_hash = "a_yeet"

        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext=None, size=1024) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=90210,
            hash="a_yeet",
            size=1024,
            file_format="gif",
        )

    def test_make_icon_url_when_format_is_None_and_avatar_hash_is_not_for_gif(self, model):
        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=90210,
            hash="yeet",
            size=4096,
            file_format="png",
        )

    def test_make_icon_url_with_all_args(self, model):
        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="url", size=2048) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=90210,
            hash="yeet",
            size=2048,
            file_format="url",
        )

    @pytest.mark.asyncio
    async def test_kick(self, model):
        model.app.rest.kick_user = mock.AsyncMock()
        await model.kick(4321, reason="Go away!")

        model.app.rest.kick_user.assert_awaited_once_with(90210, 4321, reason="Go away!")

    @pytest.mark.asyncio
    async def test_ban(self, model):
        model.app.rest.ban_user = mock.AsyncMock()
        await model.ban(4321, delete_message_days=10, reason="Go away!")

        model.app.rest.ban_user.assert_awaited_once_with(90210, 4321, delete_message_days=10, reason="Go away!")

    @pytest.mark.asyncio
    async def test_unban(self, model):
        model.app.rest.unban_user = mock.AsyncMock()
        await model.unban(4321, reason="Comeback!!")

        model.app.rest.unban_user.assert_awaited_once_with(90210, 4321, reason="Comeback!!")

    @pytest.mark.asyncio
    async def test_edit(self, model):
        model.app.rest.edit_guild = mock.AsyncMock()
        edited_guild = await model.edit(
            name="chad server",
            verification_level=guilds.GuildVerificationLevel.LOW,
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ALL_MESSAGES,
            explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.DISABLED,
            owner=6996,
            afk_timeout=400,
            preferred_locale="us-en",
            reason="beep boop",
        )

        model.app.rest.edit_guild.assert_awaited_once_with(
            90210,
            name="chad server",
            verification_level=guilds.GuildVerificationLevel.LOW,
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ALL_MESSAGES,
            explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.DISABLED,
            afk_channel=undefined.UNDEFINED,
            afk_timeout=400,
            icon=undefined.UNDEFINED,
            owner=6996,
            splash=undefined.UNDEFINED,
            banner=undefined.UNDEFINED,
            system_channel=undefined.UNDEFINED,
            rules_channel=undefined.UNDEFINED,
            public_updates_channel=undefined.UNDEFINED,
            preferred_locale="us-en",
            reason="beep boop",
        )

        assert edited_guild is model.app.rest.edit_guild.return_value

    @pytest.mark.asyncio
    async def test_fetch_emojis(self, model):
        model.app.rest.fetch_guild_emojis = mock.AsyncMock()

        emojis = await model.fetch_emojis()

        model.app.rest.fetch_guild_emojis.assert_awaited_once_with(model.id)
        assert emojis is model.app.rest.fetch_guild_emojis.return_value

    @pytest.mark.asyncio
    async def test_fetch_emoji(self, model):
        model.app.rest.fetch_emoji = mock.AsyncMock()

        emoji = await model.fetch_emoji(349)

        model.app.rest.fetch_emoji.assert_awaited_once_with(model.id, 349)
        assert emoji is model.app.rest.fetch_emoji.return_value

    @pytest.mark.asyncio
    async def test_create_category(self, model):
        model.app.rest.create_guild_category = mock.AsyncMock()

        category = await model.create_category("very cool category", position=2)

        model.app.rest.create_guild_category.assert_awaited_once_with(
            90210,
            "very cool category",
            position=2,
            permission_overwrites=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert category is model.app.rest.create_guild_category.return_value

    @pytest.mark.asyncio
    async def test_create_text_channel(self, model):
        model.app.rest.create_guild_text_channel = mock.AsyncMock()

        text_channel = await model.create_text_channel(
            "cool text channel", position=3, nsfw=False, rate_limit_per_user=30
        )

        model.app.rest.create_guild_text_channel.assert_awaited_once_with(
            90210,
            "cool text channel",
            position=3,
            topic=undefined.UNDEFINED,
            nsfw=False,
            rate_limit_per_user=30,
            permission_overwrites=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert text_channel is model.app.rest.create_guild_text_channel.return_value

    @pytest.mark.asyncio
    async def test_create_news_channel(self, model):
        model.app.rest.create_guild_news_channel = mock.AsyncMock()

        news_channel = await model.create_news_channel(
            "cool news channel", position=1, nsfw=False, rate_limit_per_user=420
        )

        model.app.rest.create_guild_news_channel.assert_awaited_once_with(
            90210,
            "cool news channel",
            position=1,
            topic=undefined.UNDEFINED,
            nsfw=False,
            rate_limit_per_user=420,
            permission_overwrites=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert news_channel is model.app.rest.create_guild_news_channel.return_value

    @pytest.mark.asyncio
    async def test_create_voice_channel(self, model):
        model.app.rest.create_guild_voice_channel = mock.AsyncMock()

        voice_channel = await model.create_voice_channel(
            "cool voice channel", position=1, bitrate=3200, video_quality_mode=2
        )

        model.app.rest.create_guild_voice_channel.assert_awaited_once_with(
            90210,
            "cool voice channel",
            position=1,
            user_limit=undefined.UNDEFINED,
            bitrate=3200,
            video_quality_mode=2,
            permission_overwrites=undefined.UNDEFINED,
            region=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert voice_channel is model.app.rest.create_guild_voice_channel.return_value

    @pytest.mark.asyncio
    async def test_create_stage_channel(self, model):
        model.app.rest.create_guild_stage_channel = mock.AsyncMock()

        stage_channel = await model.create_stage_channel("cool stage channel", position=1, bitrate=3200, user_limit=100)

        model.app.rest.create_guild_stage_channel.assert_awaited_once_with(
            90210,
            "cool stage channel",
            position=1,
            user_limit=100,
            bitrate=3200,
            permission_overwrites=undefined.UNDEFINED,
            region=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert stage_channel is model.app.rest.create_guild_stage_channel.return_value

    @pytest.mark.asyncio
    async def test_delete_channel(self, model):
        model.app.rest.delete_channel = mock.AsyncMock()

        deleted_channel = await model.delete_channel(1288820)

        model.app.rest.delete_channel.assert_awaited_once_with(1288820)
        assert deleted_channel is model.app.rest.delete_channel.return_value

    @pytest.mark.asyncio
    async def test_delete_category(self, model):
        model.app.rest.delete_channel = mock.AsyncMock()

        deleted_category = await model.delete_category(2828001)

        model.app.rest.delete_channel.assert_awaited_once_with(2828001)
        assert deleted_category is model.app.rest.delete_channel.return_value


class TestGuildPreview:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.GuildPreview(
            app=mock_app,
            features=["huge super secret nsfw channel"],
            id=snowflakes.Snowflake(123),
            icon_hash="dis is mah icon hash",
            name="DAPI",
            splash_hash="dis is also mah splash hash",
            discovery_splash_hash=None,
            emojis={},
            approximate_active_member_count=12,
            approximate_member_count=999_283_252_124_633,
            description="the place for quality shitposting!",
        )

    def test_splash_url(self, model):
        splash = object()

        with mock.patch.object(guilds.GuildPreview, "make_splash_url", return_value=splash):
            assert model.splash_url is splash

    def test_make_splash_url_when_hash(self, model):
        model.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_splash_url(ext="url", size=1024) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=1024,
            file_format="url",
        )

    def test_make_splash_url_when_no_hash(self, model):
        model.splash_hash = None
        assert model.make_splash_url(ext="png", size=512) is None

    def test_discovery_splash_url(self, model):
        discovery_splash = object()

        with mock.patch.object(guilds.GuildPreview, "make_discovery_splash_url", return_value=discovery_splash):
            assert model.discovery_splash_url is discovery_splash

    def test_make_discovery_splash_url_when_hash(self, model):
        model.discovery_splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_DISCOVERY_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_discovery_splash_url(ext="url", size=2048) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2048,
            file_format="url",
        )

    def test_make_discovery_splash_url_when_no_hash(self, model):
        model.discovery_splash_hash = None
        assert model.make_discovery_splash_url(ext="png", size=4096) is None


class TestGuild:
    @pytest.fixture()
    def model(self, mock_app):
        return hikari_test_helpers.mock_class_namespace(guilds.Guild)(
            app=mock_app,
            is_nsfw=False,
            id=snowflakes.Snowflake(123),
            splash_hash="splash_hash",
            discovery_splash_hash="discovery_splash_hash",
            banner_hash="banner_hash",
            icon_hash="icon_hash",
            features=[guilds.GuildFeature.ANIMATED_ICON],
            name="some guild",
            application_id=snowflakes.Snowflake(9876),
            afk_channel_id=snowflakes.Snowflake(1234),
            afk_timeout=datetime.timedelta(seconds=60),
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
            description=None,
            explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
            is_widget_enabled=False,
            max_video_channel_users=10,
            mfa_level=guilds.GuildMFALevel.NONE,
            owner_id=snowflakes.Snowflake(1111),
            preferred_locale="en-GB",
            premium_subscription_count=12,
            premium_tier=guilds.GuildPremiumTier.TIER_3,
            public_updates_channel_id=snowflakes.Snowflake(99699),
            rules_channel_id=snowflakes.Snowflake(123445),
            system_channel_id=snowflakes.Snowflake(123888),
            vanity_url_code="yeet",
            verification_level=guilds.GuildVerificationLevel.VERY_HIGH,
            widget_channel_id=snowflakes.Snowflake(192729),
            system_channel_flags=guilds.GuildSystemChannelFlag.SUPPRESS_PREMIUM_SUBSCRIPTION,
        )

    def test_splash_url(self, model):
        splash = object()

        with mock.patch.object(guilds.Guild, "make_splash_url", return_value=splash):
            assert model.splash_url is splash

    def test_make_splash_url_when_hash(self, model):
        model.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_splash_url(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=2,
            file_format="url",
        )

    def test_make_splash_url_when_no_hash(self, model):
        model.splash_hash = None
        assert model.make_splash_url(ext="png", size=1024) is None

    def test_discovery_splash_url(self, model):
        discovery_splash = object()

        with mock.patch.object(guilds.Guild, "make_discovery_splash_url", return_value=discovery_splash):
            assert model.discovery_splash_url is discovery_splash

    def test_make_discovery_splash_url_when_hash(self, model):
        model.discovery_splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_DISCOVERY_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_discovery_splash_url(ext="url", size=1024) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="18dnf8dfbakfdh",
            size=1024,
            file_format="url",
        )

    def test_make_discovery_splash_url_when_no_hash(self, model):
        model.discovery_splash_hash = None
        assert model.make_discovery_splash_url(ext="png", size=2048) is None

    def test_banner_url(self, model):
        banner = object()

        with mock.patch.object(guilds.Guild, "make_banner_url", return_value=banner):
            assert model.banner_url is banner

    def test_make_banner_url_when_hash(self, model):
        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_banner_url(ext="url", size=512) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=123,
            hash="banner_hash",
            size=512,
            file_format="url",
        )

    def test_make_banner_url_when_no_hash(self, model):
        model.banner_hash = None
        assert model.make_banner_url(ext="png", size=2048) is None
    
    @pytest.mark.asyncio
    async def test_fetch_owner(self, model):
        model.app.rest.fetch_member = mock.AsyncMock()

        owner = await model.fetch_owner()

        model.app.rest.fetch_member.assert_awaited_once_with(123, 1111)
        assert owner is model.app.rest.fetch_member.return_value
    
    @pytest.mark.asyncio
    async def test_fetch_widget_channel(self, model):
        model.app.rest.fetch_channel = mock.AsyncMock()

        widget_channel = await model.fetch_widget_channel()

        assert widget_channel is model.app.rest.fetch_channel.return_value
        model.app.rest.fetch_channel.assert_awaited_once_with(192729)
    
        model.widget_channel_id = None

        widget_none_case = await model.fetch_widget_channel()
        assert None is widget_none_case
    
    @pytest.mark.asyncio
    async def test_fetch_rules_channel(self, model):
        model.app.rest.fetch_channel = mock.AsyncMock()

        rules_channel = await model.fetch_rules_channel()

        assert rules_channel is model.app.rest.fetch_channel.return_value
        model.app.rest.fetch_channel.assert_awaited_once_with(123445)

        model.rules_channel_id = None

        rules_none_case = await model.fetch_rules_channel()
        assert None is rules_none_case

    @pytest.mark.asyncio
    async def test_fetch_system_channel(self, model):
        model.app.rest.fetch_channel = mock.AsyncMock()

        system_channel = await model.fetch_system_channel()

        assert system_channel is model.app.rest.fetch_channel.return_value
        model.app.rest.fetch_channel.assert_awaited_once_with(123888)

        model.system_channel_id = None

        system_none_case = await model.fetch_system_channel()
        assert None is system_none_case

    @pytest.mark.asyncio
    async def test_fetch_public_updates_channel(self, model):
        model.app.rest.fetch_channel = mock.AsyncMock()

        public_updates_channel = await model.fetch_public_updates_channel()

        assert public_updates_channel is model.app.rest.fetch_channel.return_value
        model.app.rest.fetch_channel.assert_awaited_once_with(99699)

        model.public_updates_channel_id = None

        public_updates_none_case = await model.fetch_public_updates_channel()
        assert None is public_updates_none_case

    @pytest.mark.asyncio
    async def test_fetch_afk_channel(self, model):
        model.app.rest.fetch_channel = mock.AsyncMock()

        afk_channel = await model.fetch_afk_channel()

        assert afk_channel is model.app.rest.fetch_channel.return_value
        model.app.rest.fetch_channel.assert_awaited_once_with(1234)

        model.afk_channel_id = None

        afk_none_case = await model.fetch_afk_channel()
        assert None is afk_none_case

class TestRestGuild:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.RESTGuild(
            app=mock_app,
            id=snowflakes.Snowflake(123),
            splash_hash="splash_hash",
            discovery_splash_hash="discovery_splash_hash",
            banner_hash="banner_hash",
            icon_hash="icon_hash",
            features=[guilds.GuildFeature.ANIMATED_ICON],
            name="some guild",
            application_id=snowflakes.Snowflake(9876),
            afk_channel_id=snowflakes.Snowflake(1234),
            afk_timeout=datetime.timedelta(seconds=60),
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
            description=None,
            explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
            is_widget_enabled=False,
            max_video_channel_users=10,
            mfa_level=guilds.GuildMFALevel.NONE,
            owner_id=snowflakes.Snowflake(1111),
            preferred_locale="en-GB",
            premium_subscription_count=12,
            is_nsfw=True,
            premium_tier=guilds.GuildPremiumTier.TIER_3,
            public_updates_channel_id=None,
            rules_channel_id=None,
            system_channel_id=None,
            vanity_url_code="yeet",
            verification_level=guilds.GuildVerificationLevel.VERY_HIGH,
            widget_channel_id=None,
            system_channel_flags=guilds.GuildSystemChannelFlag.SUPPRESS_PREMIUM_SUBSCRIPTION,
            emojis={},
            roles={},
            approximate_active_member_count=1000,
            approximate_member_count=100,
            max_presences=100,
            max_members=100,
        )

    def test_get_emoji(self, model):
        emoji = object()
        model._emojis = {snowflakes.Snowflake(123): emoji}

        assert model.get_emoji(123) is emoji

    def test_get_role(self, model):
        role = object()
        model._roles = {snowflakes.Snowflake(123): role}

        assert model.get_role(123) is role


class TestGatewayGuild:
    @pytest.fixture()
    def model(self, mock_app):
        return guilds.GatewayGuild(
            app=mock_app,
            is_nsfw=True,
            id=snowflakes.Snowflake(123),
            splash_hash="splash_hash",
            discovery_splash_hash="discovery_splash_hash",
            banner_hash="banner_hash",
            icon_hash="icon_hash",
            features=[guilds.GuildFeature.ANIMATED_ICON],
            name="some guild",
            application_id=snowflakes.Snowflake(9876),
            afk_channel_id=snowflakes.Snowflake(1234),
            afk_timeout=datetime.timedelta(seconds=60),
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
            description=None,
            explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
            is_widget_enabled=False,
            max_video_channel_users=10,
            mfa_level=guilds.GuildMFALevel.NONE,
            owner_id=snowflakes.Snowflake(1111),
            preferred_locale="en-GB",
            premium_subscription_count=12,
            premium_tier=guilds.GuildPremiumTier.TIER_3,
            public_updates_channel_id=None,
            rules_channel_id=None,
            system_channel_id=None,
            vanity_url_code="yeet",
            verification_level=guilds.GuildVerificationLevel.VERY_HIGH,
            widget_channel_id=None,
            system_channel_flags=guilds.GuildSystemChannelFlag.SUPPRESS_PREMIUM_SUBSCRIPTION,
            is_large=True,
            joined_at=None,
            member_count=1,
        )

    def test_channels(self, model):
        assert model.channels is model.app.cache.get_guild_channels_view_for_guild.return_value
        model.app.cache.get_guild_channels_view_for_guild.assert_called_once_with(123)

    def test_channels_when_no_cache_trait(self, model):
        model.app = object()
        assert model.channels == {}

    def test_emojis(self, model):
        assert model.emojis is model.app.cache.get_emojis_view_for_guild.return_value
        model.app.cache.get_emojis_view_for_guild.assert_called_once_with(123)

    def test_emojis_when_no_cache_trait(self, model):
        model.app = object()
        assert model.emojis == {}

    def test_members(self, model):
        assert model.members is model.app.cache.get_members_view_for_guild.return_value
        model.app.cache.get_members_view_for_guild.assert_called_once_with(123)

    def test_members_when_no_cache_trait(self, model):
        model.app = object()
        assert model.members == {}

    def test_presences(self, model):
        assert model.presences is model.app.cache.get_presences_view_for_guild.return_value
        model.app.cache.get_presences_view_for_guild.assert_called_once_with(123)

    def test_presences_when_no_cache_trait(self, model):
        model.app = object()
        assert model.presences == {}

    def test_roles(self, model):
        assert model.roles is model.app.cache.get_roles_view_for_guild.return_value
        model.app.cache.get_roles_view_for_guild.assert_called_once_with(123)

    def test_roles_when_no_cache_trait(self, model):
        model.app = object()
        assert model.roles == {}

    def test_voice_states(self, model):
        assert model.voice_states is model.app.cache.get_voice_states_view_for_guild.return_value
        model.app.cache.get_voice_states_view_for_guild.assert_called_once_with(123)

    def test_voice_states_when_no_cache_trait(self, model):
        model.app = object()
        assert model.voice_states == {}

    def test_get_channel(self, model):
        assert model.get_channel(456) is model.app.cache.get_guild_channel.return_value
        model.app.cache.get_guild_channel.assert_called_once_with(456)

    def test_get_channel_when_no_cache_trait(self, model):
        model.app = object()
        assert model.get_channel(456) is None

    def test_get_emoji(self, model):
        assert model.get_emoji(456) is model.app.cache.get_emoji.return_value
        model.app.cache.get_emoji.assert_called_once_with(456)

    def test_get_emoji_when_no_cache_trait(self, model):
        model.app = object()
        assert model.get_emoji(456) is None

    def test_get_member(self, model):
        assert model.get_member(456) is model.app.cache.get_member.return_value
        model.app.cache.get_member.assert_called_once_with(123, 456)

    def test_get_member_when_no_cache_trait(self, model):
        model.app = object()
        assert model.get_member(456) is None

    def test_get_presence(self, model):
        assert model.get_presence(456) is model.app.cache.get_presence.return_value
        model.app.cache.get_presence.assert_called_once_with(123, 456)

    def test_get_presence_when_no_cache_trait(self, model):
        model.app = object()
        assert model.get_presence(456) is None

    def test_get_role(self, model):
        assert model.get_role(456) is model.app.cache.get_role.return_value
        model.app.cache.get_role.assert_called_once_with(456)

    def test_get_role_when_no_cache_trait(self, model):
        model.app = object()
        assert model.get_role(456) is None

    def test_get_voice_state(self, model):
        assert model.get_voice_state(456) is model.app.cache.get_voice_state.return_value
        model.app.cache.get_voice_state.assert_called_once_with(123, 456)

    def test_get_voice_state_when_no_cache_trait(self, model):
        model.app = object()
        assert model.get_voice_state(456) is None

    def test_get_my_member_when_not_shardaware(self, model):
        model.app = object()
        assert model.get_my_member() is None

    def test_get_my_member_when_no_me(self, model):
        model.app.me = None
        assert model.get_my_member() is None

    def test_get_my_member(self, model):
        model.app.me = mock.Mock(id=123)

        with mock.patch.object(guilds.GatewayGuild, "get_member") as get_member:
            assert model.get_my_member() is get_member.return_value

        get_member.assert_called_once_with(123)

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

from hikari import colors
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.internal import routes


class TestPartialUser:
    class MockedPartialUser(users.PartialUser):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._id = snowflakes.Snowflake(12)
            self._avatar_hash = "avatar_hash"
            self._banner_hash = "banner_hash"
            self._accent_color = colors.Color.from_hex_code("FFB123")
            self._discriminator = "discriminator"
            self._username = "username"
            self._global_name = "global_name"
            self._display_name = "display_name"
            self._avatar_decoration = users.AvatarDecoration(
                asset_hash="avatar_decoration_asset_hash", sku_id=snowflakes.Snowflake(999), expires_at=None
            )
            self._is_bot = False
            self._is_system = False
            self._flags = users.UserFlag.NONE
            self._mention = "mention"
            self._primary_guild = users.PrimaryGuild(
                identity_guild_id=snowflakes.Snowflake(1234), identity_enabled=True, tag="HKRI", badge_hash="1234"
            )

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def id(self) -> snowflakes.Snowflake:
            return self._id

        @property
        def avatar_hash(self) -> undefined.UndefinedNoneOr[str]:
            return self._avatar_hash

        @property
        def banner_hash(self) -> undefined.UndefinedNoneOr[str]:
            return self._banner_hash

        @property
        def accent_color(self) -> undefined.UndefinedNoneOr[colors.Color]:
            return self._accent_color

        @property
        def discriminator(self) -> undefined.UndefinedOr[str]:
            return self._discriminator

        @property
        def username(self) -> undefined.UndefinedOr[str]:
            return self._username

        @property
        def global_name(self) -> undefined.UndefinedNoneOr[str]:
            return self._global_name

        @property
        def display_name(self) -> undefined.UndefinedNoneOr[str]:
            return self._display_name

        @property
        def avatar_decoration(self) -> users.AvatarDecoration | None:
            return self._avatar_decoration

        @property
        def is_bot(self) -> undefined.UndefinedOr[bool]:
            return self._is_bot

        @property
        def is_system(self) -> undefined.UndefinedOr[bool]:
            return self._is_system

        @property
        def flags(self) -> undefined.UndefinedOr[users.UserFlag]:
            return self._flags

        @property
        def mention(self) -> str:
            return self._mention

        @property
        def primary_guild(self) -> users.PrimaryGuild | None:
            return self._primary_guild

    @pytest.fixture
    def partial_user(self, hikari_app: traits.RESTAware) -> users.PartialUser:
        # ABC, so must be stubbed.
        return TestPartialUser.MockedPartialUser(hikari_app)

    def test_accent_colour_alias_property(self, partial_user: users.PartialUser):
        with mock.patch.object(partial_user, "_accent_color", mock.Mock):
            assert partial_user.accent_colour is partial_user.accent_color

    @pytest.mark.asyncio
    async def test_fetch_self(self, partial_user: users.PartialUser):
        with (
            mock.patch.object(partial_user, "_id", snowflakes.Snowflake(123)),
            mock.patch.object(partial_user.app.rest, "fetch_user", new_callable=mock.AsyncMock) as patched_fetch_user,
        ):
            assert await partial_user.fetch_self() is patched_fetch_user.return_value
            patched_fetch_user.assert_awaited_once_with(user=123)

    @pytest.mark.asyncio
    async def test_send_uses_cached_id(self, partial_user: users.PartialUser):
        embed = mock.Mock()
        embeds = [mock.Mock()]
        attachment = mock.Mock()
        attachments = [mock.Mock(), mock.Mock()]
        component = mock.Mock()
        components = [mock.Mock(), mock.Mock()]
        user_mentions = [mock.Mock(), mock.Mock()]
        role_mentions = [mock.Mock(), mock.Mock()]
        reply = mock.Mock()
        mentions_reply = mock.Mock()

        # partial_user.fetch_dm_channel = mock.AsyncMock()

        with (
            mock.patch.object(partial_user, "fetch_dm_channel", new=mock.AsyncMock()) as patched_fetch_dm_channel,
            mock.patch.object(
                partial_user, "_app", mock.Mock(spec=traits.CacheAware, rest=mock.AsyncMock())
            ) as patched_app,
            mock.patch.object(patched_app.cache, "get_dm_channel_id") as patched_get_dm_channel_id,
            mock.patch.object(patched_app.rest, "create_message") as patched_create_message,
        ):
            returned = await partial_user.send(
                content="test",
                embed=embed,
                embeds=embeds,
                attachment=attachment,
                attachments=attachments,
                component=component,
                components=components,
                tts=True,
                reply=reply,
                reply_must_exist=False,
                mentions_everyone=False,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                mentions_reply=mentions_reply,
                flags=34123342,
            )

            assert returned is patched_create_message.return_value

            patched_get_dm_channel_id.assert_called_once_with(12)
            patched_fetch_dm_channel.assert_not_called()
            patched_create_message.assert_awaited_once_with(
                channel=patched_get_dm_channel_id.return_value,
                content="test",
                embed=embed,
                embeds=embeds,
                attachment=attachment,
                attachments=attachments,
                component=component,
                components=components,
                tts=True,
                mentions_everyone=False,
                reply_must_exist=False,
                reply=reply,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                mentions_reply=mentions_reply,
                flags=34123342,
            )

    @pytest.mark.asyncio
    async def test_send_when_not_cached(self, partial_user: users.PartialUser):
        with (
            mock.patch.object(
                partial_user, "_app", mock.Mock(spec=traits.CacheAware, rest=mock.AsyncMock())
            ) as patched_app,
            mock.patch.object(
                patched_app.cache, "get_dm_channel_id", new=mock.Mock(return_value=None)
            ) as patched_get_dm_channel_id,
            mock.patch.object(patched_app.rest, "create_message") as patched_create_message,
            mock.patch.object(partial_user, "fetch_dm_channel", new=mock.AsyncMock()) as patched_fetch_dm_channel,
        ):
            returned = await partial_user.send()

            assert returned is patched_create_message.return_value

            patched_get_dm_channel_id.assert_called_once_with(12)
            patched_fetch_dm_channel.assert_awaited_once()
            patched_create_message.assert_awaited_once_with(
                channel=patched_fetch_dm_channel.return_value.id,
                content=undefined.UNDEFINED,
                embed=undefined.UNDEFINED,
                embeds=undefined.UNDEFINED,
                attachment=undefined.UNDEFINED,
                attachments=undefined.UNDEFINED,
                component=undefined.UNDEFINED,
                components=undefined.UNDEFINED,
                tts=undefined.UNDEFINED,
                mentions_everyone=undefined.UNDEFINED,
                reply=undefined.UNDEFINED,
                reply_must_exist=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
                mentions_reply=undefined.UNDEFINED,
                flags=undefined.UNDEFINED,
            )

    @pytest.mark.asyncio
    async def test_send_when_not_cache_aware(self, partial_user: users.PartialUser):
        with (
            mock.patch.object(partial_user, "_id", snowflakes.Snowflake(522234)),
            mock.patch.object(
                partial_user, "fetch_dm_channel", new_callable=mock.AsyncMock
            ) as patched_fetch_dm_channel,
            mock.patch.object(
                partial_user.app.rest, "create_message", new_callable=mock.AsyncMock
            ) as patched_create_message,
        ):
            returned = await partial_user.send()

            assert returned is patched_create_message.return_value

            patched_fetch_dm_channel.assert_awaited_once()
            patched_create_message.assert_awaited_once_with(
                channel=patched_fetch_dm_channel.return_value.id,
                content=undefined.UNDEFINED,
                embed=undefined.UNDEFINED,
                embeds=undefined.UNDEFINED,
                attachment=undefined.UNDEFINED,
                attachments=undefined.UNDEFINED,
                component=undefined.UNDEFINED,
                components=undefined.UNDEFINED,
                tts=undefined.UNDEFINED,
                mentions_everyone=undefined.UNDEFINED,
                reply=undefined.UNDEFINED,
                reply_must_exist=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
                mentions_reply=undefined.UNDEFINED,
                flags=undefined.UNDEFINED,
            )

    @pytest.mark.asyncio
    async def test_fetch_dm_channel(self, partial_user: users.PartialUser):
        with (
            mock.patch.object(partial_user, "_id", snowflakes.Snowflake(123)),
            mock.patch.object(
                partial_user.app.rest, "create_dm_channel", new_callable=mock.AsyncMock
            ) as patched_create_dm_channel,
        ):
            assert await partial_user.fetch_dm_channel() == patched_create_dm_channel.return_value

            patched_create_dm_channel.assert_awaited_once_with(123)


class TestUser:
    class MockedUser(users.User):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._id = snowflakes.Snowflake(12)
            self._avatar_hash = "avatar_hash"
            self._banner_hash = "banner_hash"
            self._accent_color = colors.Color.from_hex_code("FFB123")
            self._discriminator = "discriminator"
            self._username = "username"
            self._global_name = "global_name"
            self._global_name = "global_name"
            self._display_name = "display_name"
            self._avatar_decoration = users.AvatarDecoration(
                asset_hash="avatar_decoration_asset_hash", sku_id=snowflakes.Snowflake(999), expires_at=None
            )
            self._is_bot = False
            self._is_system = False
            self._flags = users.UserFlag.NONE
            self._mention = "mention"
            self._primary_guild = users.PrimaryGuild(
                identity_guild_id=snowflakes.Snowflake(123), identity_enabled=True, tag="HKRI", badge_hash="amogus"
            )

        @property
        def app(self) -> traits.RESTAware:
            return self._app

        @property
        def id(self) -> snowflakes.Snowflake:
            return self._id

        @property
        def avatar_hash(self) -> str:
            return self._avatar_hash

        @property
        def banner_hash(self) -> str:
            return self._banner_hash

        @property
        def accent_color(self) -> colors.Color:
            return self._accent_color

        @property
        def discriminator(self) -> str:
            return self._discriminator

        @property
        def username(self) -> str:
            return self._username

        @property
        def global_name(self) -> str:
            return self._global_name

        @property
        def display_name(self) -> str:
            return "display_name"

        @property
        def avatar_decoration(self) -> users.AvatarDecoration | None:
            return self._avatar_decoration

        @property
        def is_bot(self) -> bool:
            return self._is_bot

        @property
        def is_system(self) -> bool:
            return self._is_system

        @property
        def flags(self) -> users.UserFlag:
            return self._flags

        @property
        def mention(self) -> str:
            return self._mention

        @property
        def primary_guild(self) -> users.PrimaryGuild | None:
            return self._primary_guild

    @pytest.fixture
    def user(self, hikari_app: traits.RESTAware) -> users.User:
        # ABC, so must be stubbed.
        return TestUser.MockedUser(hikari_app)

    def test_accent_colour_alias_property(self, user: users.User):
        assert user.accent_colour is user.accent_color

    def test_avatar_decoration_property(self, user: users.User):
        with mock.patch.object(users.AvatarDecoration, "make_url") as make_url:
            assert user.avatar_decoration is not None
            assert user.avatar_decoration.url is make_url.return_value

    def test_avatar_decoration_make_url_with_all_args(self, user: users.User):
        with mock.patch.object(
            routes, "CDN_AVATAR_DECORATION", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert user.avatar_decoration is not None
            assert user.avatar_decoration.make_url(size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.MEDIA_PROXY_URL, hash=user.avatar_decoration.asset_hash, size=4096, file_format="PNG", lossless=True
        )

    def test_make_avatar_url_format_set_to_deprecated_ext_argument_if_provided(self, user: users.User):
        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert user.make_avatar_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=12, hash="avatar_hash", size=4096, file_format="JPEG", lossless=True
        )

    def test_avatar_url_property(self, user: users.User):
        with mock.patch.object(users.User, "make_avatar_url") as make_avatar_url:
            assert user.avatar_url is make_avatar_url.return_value

    def test_make_avatar_url_when_no_hash(self, user: users.User):
        with mock.patch.object(user, "_avatar_hash", None):
            assert user.make_avatar_url(file_format="PNG", size=1024) is None

    def test_make_avatar_url_when_format_is_None_and_avatar_hash_is_for_gif(self, user: users.User):
        with (
            mock.patch.object(user, "_avatar_hash", "a_18dnf8dfbakfdh"),
            mock.patch.object(
                routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
            ) as route,
        ):
            assert user.make_avatar_url(file_format="GIF", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=user.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="GIF", lossless=True
        )

    def test_make_avatar_url_when_format_is_None_and_avatar_hash_is_not_for_gif(self, user: users.User):
        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert user.make_avatar_url(file_format="PNG", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=user.id, hash=user.avatar_hash, size=4096, file_format="PNG", lossless=True
        )

    def test_make_avatar_url_with_all_args(self, user: users.User):
        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert user.make_avatar_url(file_format="JPG", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=user.id, hash=user.avatar_hash, size=4096, file_format="JPG", lossless=True
        )

    def test_display_avatar_url_when_avatar_url(self, user: users.User):
        with mock.patch.object(users.User, "make_avatar_url") as mock_make_avatar_url:
            assert user.display_avatar_url is mock_make_avatar_url.return_value

    def test_display_avatar_url_when_no_avatar_url(self, user: users.User):
        with (
            mock.patch.object(users.User, "make_avatar_url", return_value=None),
            mock.patch.object(users.User, "default_avatar_url") as mock_default_avatar_url,
        ):
            assert user.display_avatar_url is mock_default_avatar_url

    def test_display_banner_url_when_banner_url(self, user: users.User):
        with mock.patch.object(users.User, "make_banner_url") as mock_make_banner_url:
            assert user.display_banner_url is mock_make_banner_url.return_value

    def test_display_banner_url_when_no_banner_url(self, user: users.User):
        with mock.patch.object(users.User, "make_banner_url", return_value=None):
            assert user.display_banner_url is None

    def test_default_avatar(self, user: users.User):
        with (
            mock.patch.object(user, "_id", 377812572784820226),
            mock.patch.object(user, "_discriminator", "1234"),
            mock.patch.object(routes, "CDN_DEFAULT_USER_AVATAR") as patched_route,
            mock.patch.object(
                patched_route, "compile_to_file", new=mock.Mock(return_value="file")
            ) as patched_compile_to_file,
        ):
            assert user.default_avatar_url == "file"

        patched_compile_to_file.assert_called_once_with(urls.CDN_URL, style=4, file_format="PNG")

    def test_default_avatar_for_migrated_users(self, user: users.User):
        with (
            mock.patch.object(user, "_id", 377812572784820226),
            mock.patch.object(user, "_discriminator", "0"),
            mock.patch.object(routes, "CDN_DEFAULT_USER_AVATAR") as patched_route,
            mock.patch.object(
                patched_route, "compile_to_file", new=mock.Mock(return_value="file")
            ) as patched_compile_to_file,
        ):
            assert user.default_avatar_url == "file"

        patched_compile_to_file.assert_called_once_with(urls.CDN_URL, style=0, file_format="PNG")

    def test_make_banner_url_format_set_to_deprecated_ext_argument_if_provided(self, user: users.User):
        with mock.patch.object(
            routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert user.make_banner_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=12, hash="banner_hash", size=4096, file_format="JPEG", lossless=True
        )

    def test_banner_url_property(self, user: users.User):
        with mock.patch.object(users.User, "make_banner_url") as make_banner_url:
            assert user.banner_url is make_banner_url.return_value

    def test_make_banner_url_when_no_hash(self, user: users.User):
        with mock.patch.object(user, "_banner_hash", None), mock.patch.object(routes, "CDN_USER_BANNER"):
            assert user.make_banner_url(file_format="JPG", size=4096) is None

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_for_gif(self, user: users.User):
        with (
            mock.patch.object(user, "_banner_hash", "a_18dnf8dfbakfdh"),
            mock.patch.object(
                routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
            ) as route,
        ):
            assert user.make_banner_url(file_format="GIF", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=user.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="GIF", lossless=True
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_not_for_gif(self, user: users.User):
        with (
            mock.patch.object(user, "_banner_hash", "banner_hash"),
            mock.patch.object(
                routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
            ) as route,
        ):
            assert user.make_banner_url(file_format="PNG", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=user.id, hash=user.banner_hash, size=4096, file_format="PNG", lossless=True
        )

    def test_make_banner_url_with_all_args(self, user: users.User):
        with (
            mock.patch.object(user, "_banner_hash", "banner_hash"),
            mock.patch.object(
                routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
            ) as route,
        ):
            assert user.make_banner_url(file_format="PNG", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=user.id, hash=user.banner_hash, size=4096, file_format="PNG", lossless=True
        )


class TestPartialUserImpl:
    @pytest.fixture
    def partial_user(self) -> users.PartialUserImpl:
        return users.PartialUserImpl(
            id=snowflakes.Snowflake(123),
            app=mock.Mock(),
            discriminator="8637",
            username="thomm.o",
            global_name=None,
            avatar_decoration=None,
            avatar_hash=None,
            banner_hash=None,
            accent_color=None,
            is_bot=False,
            is_system=False,
            flags=users.UserFlag.DISCORD_EMPLOYEE,
            primary_guild=None,
        )

    def test_str_operator(self, partial_user: users.PartialUserImpl):
        assert str(partial_user) == "thomm.o#8637"

    def test_str_operator_when_partial(self, partial_user: users.PartialUserImpl):
        partial_user.username = undefined.UNDEFINED
        assert str(partial_user) == "Partial user ID 123"

    def test_mention_property(self, partial_user: users.PartialUserImpl):
        assert partial_user.mention == "<@123>"

    def test_display_name_property_when_global_name(self, partial_user: users.PartialUserImpl):
        partial_user.global_name = "Thommo"
        assert partial_user.display_name == partial_user.global_name

    def test_display_name_property_when_no_global_name(self, partial_user: users.PartialUserImpl):
        partial_user.global_name = None
        assert partial_user.display_name == partial_user.username

    @pytest.mark.asyncio
    async def test_fetch_self(self, partial_user: users.PartialUserImpl):
        user = mock.Mock()
        partial_user.app.rest.fetch_user = mock.AsyncMock(return_value=user)
        assert await partial_user.fetch_self() is user
        partial_user.app.rest.fetch_user.assert_awaited_once_with(user=123)


@pytest.mark.asyncio
class TestOwnUser:
    @pytest.fixture
    def own_user(self) -> users.OwnUser:
        return users.OwnUser(
            id=snowflakes.Snowflake(12345),
            app=mock.Mock(),
            discriminator="1234",
            username="foobar",
            global_name=None,
            avatar_decoration=None,
            avatar_hash="69420",
            banner_hash="42069",
            accent_color=colors.Color(123456),
            is_bot=False,
            is_system=False,
            flags=users.UserFlag.PARTNERED_SERVER_OWNER,
            is_mfa_enabled=True,
            locale="en-GB",
            is_verified=False,
            email="someone@example.com",
            premium_type=None,
            primary_guild=None,
        )

    async def test_fetch_self(self, own_user: users.OwnUser):
        user = mock.Mock()
        own_user.app.rest.fetch_my_user = mock.AsyncMock(return_value=user)
        assert await own_user.fetch_self() is user
        own_user.app.rest.fetch_my_user.assert_awaited_once_with()

    async def test_fetch_dm_channel(self, own_user: users.OwnUser):
        with pytest.raises(TypeError, match=r"Unable to fetch your own DM channel"):
            await own_user.fetch_dm_channel()

    async def test_send(self, own_user: users.OwnUser):
        with pytest.raises(TypeError, match=r"Unable to send a DM to yourself"):
            await own_user.send()


class TestPrimaryGuild:
    @pytest.fixture
    def primary_guild(self) -> users.PrimaryGuild:
        return users.PrimaryGuild(
            identity_guild_id=snowflakes.Snowflake(1234), identity_enabled=True, tag="HKRI", badge_hash="abcd1234"
        )

    def test_make_url(self, primary_guild: users.PrimaryGuild):
        with mock.patch.object(
            routes, "CDN_PRIMARY_GUILD_BADGE", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert primary_guild.make_url() == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=1234, hash="abcd1234", size=4096, file_format="PNG", lossless=True
        )

    def test_make_url_with_all_args(self, primary_guild: users.PrimaryGuild):
        with mock.patch.object(
            routes, "CDN_PRIMARY_GUILD_BADGE", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert primary_guild.make_url(file_format="WEBP", size=280, lossless=False) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=1234, hash="abcd1234", size=280, file_format="WEBP", lossless=False
        )

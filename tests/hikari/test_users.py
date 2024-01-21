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
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


class TestPartialUser:
    @pytest.fixture()
    def obj(self):
        # ABC, so must be stubbed.
        return hikari_test_helpers.mock_class_namespace(users.PartialUser, slots_=False)()

    def test_accent_colour_alias_property(self, obj):
        obj.accent_color = object()

        assert obj.accent_colour is obj.accent_color

    @pytest.mark.asyncio()
    async def test_fetch_self(self, obj):
        obj.id = 123
        obj.app = mock.AsyncMock()

        assert await obj.fetch_self() is obj.app.rest.fetch_user.return_value
        obj.app.rest.fetch_user.assert_awaited_once_with(user=123)

    @pytest.mark.asyncio()
    async def test_send_uses_cached_id(self, obj):
        obj.id = 4123123
        embed = object()
        embeds = [object()]
        attachment = object()
        attachments = [object(), object()]
        component = object()
        components = [object(), object()]
        user_mentions = [object(), object()]
        role_mentions = [object(), object()]
        reply = object()
        mentions_reply = object()

        obj.app = mock.Mock(spec=traits.CacheAware, rest=mock.AsyncMock())
        obj.fetch_dm_channel = mock.AsyncMock()

        returned = await obj.send(
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

        assert returned is obj.app.rest.create_message.return_value

        obj.app.cache.get_dm_channel_id.assert_called_once_with(4123123)
        obj.fetch_dm_channel.assert_not_called()
        obj.app.rest.create_message.assert_awaited_once_with(
            channel=obj.app.cache.get_dm_channel_id.return_value,
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

    @pytest.mark.asyncio()
    async def test_send_when_not_cached(self, obj):
        obj.id = 522234
        obj.app = mock.Mock(spec=traits.CacheAware, rest=mock.AsyncMock())
        obj.app.cache.get_dm_channel_id = mock.Mock(return_value=None)
        obj.fetch_dm_channel = mock.AsyncMock()

        returned = await obj.send()

        assert returned is obj.app.rest.create_message.return_value

        obj.app.cache.get_dm_channel_id.assert_called_once_with(522234)
        obj.fetch_dm_channel.assert_awaited_once()
        obj.app.rest.create_message.assert_awaited_once_with(
            channel=obj.fetch_dm_channel.return_value.id,
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

    @pytest.mark.asyncio()
    async def test_send_when_not_cache_aware(self, obj):
        obj.id = 522234
        obj.app = mock.Mock(spec=traits.RESTAware, rest=mock.AsyncMock())
        obj.fetch_dm_channel = mock.AsyncMock()

        returned = await obj.send()

        assert returned is obj.app.rest.create_message.return_value

        obj.fetch_dm_channel.assert_awaited_once()
        obj.app.rest.create_message.assert_awaited_once_with(
            channel=obj.fetch_dm_channel.return_value.id,
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

    @pytest.mark.asyncio()
    async def test_fetch_dm_channel(self, obj):
        obj.id = 123
        obj.app = mock.Mock()
        obj.app.rest.create_dm_channel = mock.AsyncMock()

        assert await obj.fetch_dm_channel() == obj.app.rest.create_dm_channel.return_value

        obj.app.rest.create_dm_channel.assert_awaited_once_with(123)


class TestUser:
    @pytest.fixture()
    def obj(self):
        # ABC, so must be stubbed.
        return hikari_test_helpers.mock_class_namespace(users.User, slots_=False)()

    def test_accent_colour_alias_property(self, obj):
        obj.accent_color = object()

        assert obj.accent_colour is obj.accent_color

    def test_avatar_url_property(self, obj):
        with mock.patch.object(users.User, "make_avatar_url") as make_avatar_url:
            assert obj.avatar_url is make_avatar_url.return_value

    def test_make_avatar_url_when_no_hash(self, obj):
        obj.avatar_hash = None
        assert obj.make_avatar_url(ext="png", size=1024) is None

    def test_make_avatar_url_when_format_is_None_and_avatar_hash_is_for_gif(self, obj):
        obj.avatar_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.make_avatar_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=obj.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="gif"
        )

    def test_make_avatar_url_when_format_is_None_and_avatar_hash_is_not_for_gif(self, obj):
        obj.avatar_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.make_avatar_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=obj.id, hash=obj.avatar_hash, size=4096, file_format="png"
        )

    def test_make_avatar_url_with_all_args(self, obj):
        obj.avatar_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.make_avatar_url(ext="url", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=obj.id, hash=obj.avatar_hash, size=4096, file_format="url"
        )

    def test_display_avatar_url_when_avatar_url(self, obj):
        with mock.patch.object(users.User, "make_avatar_url") as mock_make_avatar_url:
            assert obj.display_avatar_url is mock_make_avatar_url.return_value

    def test_display_avatar_url_when_no_avatar_url(self, obj):
        with mock.patch.object(users.User, "make_avatar_url", return_value=None):
            with mock.patch.object(users.User, "default_avatar_url") as mock_default_avatar_url:
                assert obj.display_avatar_url is mock_default_avatar_url

    def test_default_avatar(self, obj):
        obj.avatar_hash = "18dnf8dfbakfdh"
        obj.discriminator = "1234"

        with mock.patch.object(
            routes, "CDN_DEFAULT_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.default_avatar_url == "file"

        route.compile_to_file.assert_called_once_with(urls.CDN_URL, style=4, file_format="png")

    def test_default_avatar_for_migrated_users(self, obj):
        obj.id = 377812572784820226
        obj.avatar_hash = "18dnf8dfbakfdh"
        obj.discriminator = "0"

        with mock.patch.object(
            routes, "CDN_DEFAULT_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.default_avatar_url == "file"

        route.compile_to_file.assert_called_once_with(urls.CDN_URL, style=0, file_format="png")

    def test_banner_url_property(self, obj):
        with mock.patch.object(users.User, "make_banner_url") as make_banner_url:
            assert obj.banner_url is make_banner_url.return_value

    def test_make_banner_url_when_no_hash(self, obj):
        obj.banner_hash = None

        with mock.patch.object(routes, "CDN_USER_BANNER") as route:
            assert obj.make_banner_url(ext=None, size=4096) is None

        route.compile_to_file.assert_not_called()

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_for_gif(self, obj):
        obj.banner_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=obj.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="gif"
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_not_for_gif(self, obj):
        obj.banner_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=obj.id, hash=obj.banner_hash, size=4096, file_format="png"
        )

    def test_make_banner_url_with_all_args(self, obj):
        obj.banner_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.make_banner_url(ext="url", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, user_id=obj.id, hash=obj.banner_hash, size=4096, file_format="url"
        )


class TestPartialUserImpl:
    @pytest.fixture()
    def obj(self):
        return users.PartialUserImpl(
            id=snowflakes.Snowflake(123),
            app=mock.Mock(),
            discriminator="8637",
            username="thomm.o",
            global_name=None,
            avatar_hash=None,
            banner_hash=None,
            accent_color=None,
            is_bot=False,
            is_system=False,
            flags=users.UserFlag.DISCORD_EMPLOYEE,
        )

    def test_str_operator(self, obj):
        assert str(obj) == "thomm.o#8637"

    def test_str_operator_when_partial(self, obj):
        obj.username = undefined.UNDEFINED
        assert str(obj) == "Partial user ID 123"

    def test_mention_property(self, obj):
        assert obj.mention == "<@123>"

    @pytest.mark.asyncio()
    async def test_fetch_self(self, obj):
        user = object()
        obj.app.rest.fetch_user = mock.AsyncMock(return_value=user)
        assert await obj.fetch_self() is user
        obj.app.rest.fetch_user.assert_awaited_once_with(user=123)


@pytest.mark.asyncio()
class TestOwnUser:
    @pytest.fixture()
    def obj(self):
        return users.OwnUser(
            id=snowflakes.Snowflake(12345),
            app=mock.Mock(),
            discriminator="1234",
            username="foobar",
            global_name=None,
            avatar_hash="69420",
            banner_hash="42069",
            accent_color=123456,
            is_bot=False,
            is_system=False,
            flags=users.UserFlag.PARTNERED_SERVER_OWNER,
            is_mfa_enabled=True,
            locale="en-GB",
            is_verified=False,
            email="someone@example.com",
            premium_type=None,
        )

    async def test_fetch_self(self, obj):
        user = object()
        obj.app.rest.fetch_my_user = mock.AsyncMock(return_value=user)
        assert await obj.fetch_self() is user
        obj.app.rest.fetch_my_user.assert_awaited_once_with()

    async def test_fetch_dm_channel(self, obj):
        with pytest.raises(TypeError, match=r"Unable to fetch your own DM channel"):
            await obj.fetch_dm_channel()

    async def test_send(self, obj):
        with pytest.raises(TypeError, match=r"Unable to send a DM to yourself"):
            await obj.send()

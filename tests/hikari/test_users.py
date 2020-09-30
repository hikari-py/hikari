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

from hikari import undefined
from hikari import urls
from hikari import users
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


def test_UserFlag_str_operator():
    flag = users.UserFlag(1 << 17)
    assert str(flag) == "EARLY_VERIFIED_DEVELOPER"


def test_PremiumType_str_operator():
    premium_type = users.PremiumType(1)
    assert str(premium_type) == "NITRO_CLASSIC"


class TestUser:
    @pytest.fixture()
    def obj(self):
        return hikari_test_helpers.mock_class_namespace(users.User, slots=False)()

    def test_avatar_url_when_hash(self, obj):
        avatar = object()

        with mock.patch.object(users.User, "format_avatar", return_value=avatar):
            assert obj.avatar_url is avatar

    def test_avatar_url_when_no_hash(self, obj):
        with mock.patch.object(users.User, "format_avatar", return_value=None):
            assert obj.avatar_url is None

    def test_format_avatar_when_no_hash(self, obj):
        obj.avatar_hash = None
        assert obj.format_avatar(ext="png", size=1024) is None

    def test_format_avatar_when_format_is_None_and_avatar_hash_is_for_gif(self, obj):
        obj.avatar_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_avatar(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            user_id=obj.id,
            hash="a_18dnf8dfbakfdh",
            size=4096,
            file_format="gif",
        )

    def test_format_avatar_when_format_is_None_and_avatar_hash_is_not_for_gif(self, obj):
        obj.avatar_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_avatar(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            user_id=obj.id,
            hash=obj.avatar_hash,
            size=4096,
            file_format="png",
        )

    def test_format_avatar_with_all_args(self, obj):
        obj.avatar_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.format_avatar(ext="url", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            user_id=obj.id,
            hash=obj.avatar_hash,
            size=4096,
            file_format="url",
        )

    def test_default_avatar(self, obj):
        obj.avatar_hash = "18dnf8dfbakfdh"
        obj.discriminator = "1234"

        with mock.patch.object(
            routes, "CDN_DEFAULT_USER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert obj.default_avatar == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            discriminator=4,
            file_format="png",
        )


class TestPartialUserImpl:
    @pytest.fixture()
    def obj(self):
        return hikari_test_helpers.stub_class(
            users.PartialUserImpl, id=123, username="thomm.o", discriminator="8637", app=mock.Mock()
        )

    def test_str_operator(self, obj):
        assert str(obj) == "thomm.o#8637"

    def test_str_operator_when_partial(self, obj):
        obj.username = undefined.UNDEFINED
        assert str(obj) == "Partial user ID 123"

    def test_mention_property(self, obj):
        assert obj.mention == "<@123>"

    @pytest.mark.asyncio
    async def test_fetch_self(self, obj):
        user = object()
        obj.app.rest.fetch_user = mock.AsyncMock(return_value=user)
        assert await obj.fetch_self() is user
        obj.app.rest.fetch_user.assert_awaited_once_with(user=123)


@pytest.mark.asyncio
class TestOwnUser:
    @pytest.fixture()
    def obj(self):
        return hikari_test_helpers.stub_class(users.OwnUser, app=mock.Mock())

    async def test_fetch_self(self, obj):
        user = object()
        obj.app.rest.fetch_my_user = mock.AsyncMock(return_value=user)
        assert await obj.fetch_self() is user
        obj.app.rest.fetch_my_user.assert_awaited_once_with()

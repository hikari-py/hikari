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

from hikari import presences
from hikari import snowflakes
from hikari.impl import bot


@pytest.fixture()
def mock_app():
    return mock.Mock(spec_set=bot.GatewayBot)


class TestActivityAssets:
    def test_large_image_url_property(self):
        raise NotImplementedError

    def test_large_image_url_property_when_runtime_error(self):
        raise NotImplementedError

    def test_make_large_image_url(self):
        raise NotImplementedError

    def test_make_large_image_url_when_dynamic_url(self):
        raise NotImplementedError

    def test_small_image_url_property(self):
        raise NotImplementedError

    def test_small_image_url_property_when_runtime_error(self):
        raise NotImplementedError

    def test_make_small_image_url(self):
        raise NotImplementedError

    def test_make_small_image_url_when_dynamic_url(self):
        raise NotImplementedError


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

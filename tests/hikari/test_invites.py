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

from hikari import invites
from tests.hikari import hikari_test_helpers


class TestInviteCode:
    def test_str_operator(self):
        mock_invite = hikari_test_helpers.mock_class_namespace(
            invites.InviteCode, code=mock.PropertyMock(return_value="hikari")
        )()
        assert str(mock_invite) == "https://discord.gg/hikari"


class TestInviteWithMetadata:
    def test_uses_left(self):
        mock_invite = hikari_test_helpers.mock_class_namespace(
            invites.InviteWithMetadata, init_=False, max_uses=123, uses=55
        )()

        assert mock_invite.uses_left == 68

    def test_uses_left_when_none(self):
        mock_invite = hikari_test_helpers.mock_class_namespace(invites.InviteWithMetadata, init_=False, max_uses=None)()

        assert mock_invite.uses_left is None

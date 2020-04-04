#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import cymock as mock
import pytest

from hikari import emojis
from hikari import users
from tests.hikari import _helpers


class TestUnicodeEmoji:
    def test_deserialize(self):
        emoji_obj = emojis.UnicodeEmoji.deserialize({"name": "🤷"})

        assert emoji_obj.name == "🤷"


class TestUnknownEmoji:
    def test_deserialize(self):
        emoji_obj = emojis.UnknownEmoji.deserialize({"id": "1234", "name": "test", "animated": True})

        assert emoji_obj.id == 1234
        assert emoji_obj.name == "test"
        assert emoji_obj.is_animated is True


class TestGuildEmoji:
    def test_deserialize(self):
        mock_user = mock.MagicMock(users.User)

        test_user_payload = {"id": "123456", "username": "hikari", "discriminator": "0000", "avatar": None}
        with _helpers.patch_marshal_attr(
            emojis.GuildEmoji, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            emoji_obj = emojis.GuildEmoji.deserialize(
                {
                    "id": "12345",
                    "name": "testing",
                    "animated": False,
                    "roles": ["123", "456"],
                    "user": test_user_payload,
                    "require_colons": True,
                    "managed": False,
                }
            )
            patched_user_deserializer.assert_called_once_with(test_user_payload)

        assert emoji_obj.id == 12345
        assert emoji_obj.name == "testing"
        assert emoji_obj.is_animated is False
        assert emoji_obj.role_ids == {123, 456}
        assert emoji_obj.user == mock_user
        assert emoji_obj.is_colons_required is True
        assert emoji_obj.is_managed is False


@pytest.mark.parametrize(
    ["payload", "expected_type"],
    [({"name": "🤷"}, emojis.UnicodeEmoji), ({"id": "1234", "name": "test"}, emojis.UnknownEmoji)],
)
def test_deserialize_reaction_emoji_returns_expected_type(payload, expected_type):
    assert isinstance(emojis.deserialize_reaction_emoji(payload), expected_type)

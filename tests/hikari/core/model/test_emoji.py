#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
from unittest import mock

import pytest

from hikari.core.model import emoji
from hikari.core.model import model_cache


@pytest.mark.model
class TestEmoji:
    def test_Emoji_from_dict(self):
        test_state = mock.MagicMock(state_set=model_cache.AbstractModelCache)

        user_dict = {
            "username": "Luigi",
            "discriminator": "0002",
            "id": "96008815106887111",
            "avatar": "5500909a3274e1812beb4e8de6631111",
        }

        emj = emoji.Emoji.from_dict(
            test_state,
            {
                "id": "1234567",
                "name": "peepohappy",
                "roles": [{"id": 999}, {"id": 888}, {"id": 777}],
                "user": user_dict,
                "require_colons": True,
                "managed": False,
                "animated": False,
            },
            12345
        )

        assert emj.id == 1234567
        assert emj.name == "peepohappy"
        assert len(emj._role_ids) == 3
        assert emj.require_colons is True
        assert emj.managed is False
        assert emj.animated is False
        assert emj._guild_id == 12345
        test_state.parse_user.assert_called_with(user_dict)

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

from hikari.core.model import reaction
from hikari.core.model import model_state


@pytest.mark.model
class TestReaction:
    def test_Reaction_from_dict(self):
        test_state = mock.MagicMock(state_set=model_state.AbstractModelState)

        emoji_dict = {
            "id": "41771983429993937",
            "name": "LUL",
            "roles": ["41771983429993000", "41771983429993111"],
            "user": {
                "username": "Luigi",
                "discriminator": "0002",
                "id": "96008815106887111",
                "avatar": "5500909a3274e1812beb4e8de6631111"
            },
            "require_colons": True,
            "managed": False,
            "animated": False
        }

        re = reaction.Reaction.from_dict(
            test_state,
            {
                "count": 420,
                "me": True,
                "emoji": emoji_dict
            }
        )

        assert re.count == 420
        assert re.me is True
        test_state.parse_emoji.assert_called_with(emoji_dict)

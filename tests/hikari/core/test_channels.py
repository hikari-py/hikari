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
import pytest

from hikari.core import channels


@pytest.fixture()
def test_partial_channel_payload():
    return {"id": "561884984214814750", "name": "general", "type": 0}


class TestPartialChannel:
    def test_deserialize(self, test_partial_channel_payload):
        partial_channel_obj = channels.PartialChannel.deserialize(test_partial_channel_payload)
        assert partial_channel_obj.id == 561884984214814750
        assert partial_channel_obj.name == "general"
        assert partial_channel_obj.type is channels.ChannelType.GUILD_TEXT

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
import pytest

from hikari.model import channel


@pytest.mark.model
class TestChannel:
    def test_type(self):
        class Dummy(channel.Channel):
            @staticmethod
            def from_dict(payload, state):
                pass

        d = Dummy(NotImplemented, 123)
        assert d.type == Dummy

    @pytest.mark.xfail
    def test_GuildTextChannel_from_dict(self):
        raise NotImplementedError

    @pytest.mark.xfail
    def test_DMChannel_from_dict(self):
        raise NotImplementedError

    @pytest.mark.xfail
    def test_GuildVoiceChannel_from_dict(self):
        raise NotImplementedError

    @pytest.mark.xfail
    def test_GroupDMChannel_from_dict(self):
        raise NotImplementedError

    def test_GuildCategory_from_dict(self):
        gc = channel.GuildCategory.from_dict({
            "id": "123456",
            "guild_id": "54321",
            "position": 69,
            "permission_overwrites": [],
            "name": "dank category",
        }, NotImplemented)

        assert gc.name == "dank category"
        assert gc.position == 69
        assert gc.guild_id == 54321
        assert gc.id == 123456
        assert gc.permission_overwrites == []

    @pytest.mark.xfail
    def test_GuildNewsChannel_from_dict(self):
        raise NotImplementedError

    @pytest.mark.xfail
    def test_GuildStoreChannel_from_dict(self):
        raise NotImplementedError

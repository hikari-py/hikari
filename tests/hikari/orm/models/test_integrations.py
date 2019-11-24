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
import datetime
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import integrations


@pytest.mark.model
def test_PartialIntegration():
    partial_integration_obj = integrations.PartialIntegration({"id": "53242", "name": "OwO", "type": "twitch",})
    assert partial_integration_obj.id == 53242
    assert partial_integration_obj.name == "OwO"
    assert partial_integration_obj.type == "twitch"


@pytest.mark.model
class TestIntegration:
    def test_Integration(self):
        test_state = mock.MagicMock(state_set=state_registry.IStateRegistry)
        test_fabric = fabric.Fabric(None, test_state)

        user_dict = {
            "username": "Luigi",
            "discriminator": "0002",
            "id": "96008815106887111",
            "avatar": "5500909a3274e1812beb4e8de6631111",
        }

        account_dict = {"id": "123456789", "name": "lasagna"}

        integration_obj = integrations.Integration(
            test_fabric,
            {
                "id": "1234567",
                "name": "peepohappy",
                "type": "twitch",
                "enabled": True,
                "syncing": False,
                "role_id": "69696969",
                "expire_behavior": 2,
                "expire_grace_period": 420,
                "user": user_dict,
                "account": account_dict,
                "synced_at": "2016-03-31T19:15:39.954000+00:00",
            },
        )

        assert integration_obj.id == 1234567
        assert integration_obj.name == "peepohappy"
        assert integration_obj.type == "twitch"
        assert integration_obj.enabled is True
        assert integration_obj.syncing is False
        assert integration_obj._role_id == 69696969
        assert integration_obj.expire_grace_period == 420
        assert integration_obj.synced_at == datetime.datetime(
            2016, 3, 31, 19, 15, 39, 954000, tzinfo=datetime.timezone.utc
        )
        test_state.parse_user.assert_called_with(user_dict)


@pytest.mark.model
class TestIntegrationAccount:
    def test_IntegrationAccount(self):
        test_state = mock.MagicMock(state_set=state_registry.IStateRegistry)
        test_fabric = fabric.Fabric(None, test_state)

        inteacc = integrations.IntegrationAccount(test_fabric, {"id": "1234567", "name": "memes"})

        assert inteacc.id == 1234567
        assert inteacc.name == "memes"

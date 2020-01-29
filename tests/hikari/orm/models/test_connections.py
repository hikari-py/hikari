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
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm.models import connections
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture()
def mock_state_registry():
    return mock.create_autospec(base_registry.BaseRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model()
def test_Connection(fabric_obj):
    connection_obj = connections.Connection(
        fabric_obj,
        {
            "type": "twitter",
            "id": "12was12",
            "name": "Robin_Williams",
            "visibility": 0,
            "revoked": True,
            "friend_sync": False,
            "show_activity": True,
            "verified": True,
        },
    )
    assert connection_obj.type == "twitter"
    assert connection_obj.id == "12was12"
    assert connection_obj.name == "Robin_Williams"
    assert connection_obj.visibility is connections.ConnectionVisibility.NONE
    assert connection_obj.is_revoked is True
    assert connection_obj.is_friend_synced is False
    assert connection_obj.is_showing_activity is True
    assert connection_obj.is_verified is True


@pytest.mark.model
def test_Connection___repr__():
    assert repr(
        _helpers.mock_model(
            connections.Connection, type="asdfmovies", id=42, name="ObamaCare", __repr__=connections.Connection.__repr__
        )
    )

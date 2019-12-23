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
from hikari.orm import state_registry
from hikari.orm.models import webhooks
from tests.hikari import _helpers


@pytest.fixture()
def webhook_user():
    return {
        "username": "Luigi",
        "discriminator": "0002",
        "id": "96008815106887111",
        "avatar": "5500909a3274e1812beb4e8de6631111",
    }


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.BaseStateRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model
class TestWebhookUser:
    def test_parse(self, webhook_user):
        obj = webhooks.WebhookUser(webhook_user)
        assert obj.id == 96008815106887111
        assert obj.avatar_hash == "5500909a3274e1812beb4e8de6631111"
        assert obj.discriminator == 2
        assert obj.username == "Luigi"

    def test_is_bot(self, webhook_user):
        obj = webhooks.WebhookUser(webhook_user)
        assert obj.is_bot


@pytest.mark.model
class TestWebhook:
    def test_parse_webhook(self, fabric_obj, webhook_user):
        wh = webhooks.Webhook(
            fabric_obj,
            {
                "name": "test webhook",
                "channel_id": "199737254929760256",
                "token": "3d89bb7572e0fb30d8128367b3b1b44fecd1726de135cbe28a41f8b2f777c372ba2939e72279b94526ff5d1bd4358d65cf11",
                "avatar": None,
                "guild_id": "199737254929760256",
                "id": "223704706495545344",
                "type": 1,
                "user": webhook_user,
            },
        )

        assert wh.name == "test webhook"
        assert wh.channel_id == 199737254929760256
        assert (
            wh.token
            == "3d89bb7572e0fb30d8128367b3b1b44fecd1726de135cbe28a41f8b2f777c372ba2939e72279b94526ff5d1bd4358d65cf11"
        )
        assert wh.avatar_hash is None
        assert wh.guild_id == 199737254929760256
        assert wh.type is webhooks.WebhookType.INCOMING
        fabric_obj.state_registry.parse_webhook_user.assert_called_with(webhook_user)

    @pytest.mark.model
    def test_Webhook___repr__(self):
        assert repr(_helpers.mock_model(webhooks.Webhook, id=42, name="foo", __repr__=webhooks.Webhook.__repr__))

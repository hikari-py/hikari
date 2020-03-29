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

from hikari.core import users
from hikari.core import webhooks
from tests.hikari import _helpers


class TestWebhook:
    def test_deserialize(self):
        test_user_payload = {"id": "123456", "username": "hikari", "discriminator": "0000", "avatar": None}
        payload = {
            "id": "1234",
            "type": 1,
            "guild_id": "123",
            "channel_id": "456",
            "user": test_user_payload,
            "name": "hikari webhook",
            "avatar": "bb71f469c158984e265093a81b3397fb",
            "token": "ueoqrialsdfaKJLKfajslkdf",
        }
        mock_user = mock.MagicMock(users.User)

        with _helpers.patch_marshal_attr(
            webhooks.Webhook, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as mock_user_deserializer:
            webhook_obj = webhooks.Webhook.deserialize(payload)
            mock_user_deserializer.assert_called_once_with(test_user_payload)

        assert webhook_obj.id == 1234
        assert webhook_obj.type == webhooks.WebhookType.INCOMING
        assert webhook_obj.guild_id == 123
        assert webhook_obj.channel_id == 456
        assert webhook_obj.user == mock_user
        assert webhook_obj.name == "hikari webhook"
        assert webhook_obj.avatar_hash == "bb71f469c158984e265093a81b3397fb"
        assert webhook_obj.token == "ueoqrialsdfaKJLKfajslkdf"

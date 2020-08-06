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
import mock

from hikari.models import webhooks


def test_WebhookType_str_operator():
    type = webhooks.WebhookType(1)
    assert str(type) == "INCOMING"


def test_Webhook_str_operator():
    mock_webhook = mock.Mock(webhooks.Webhook)
    mock_webhook.name = "not a webhook"
    assert webhooks.Webhook.__str__(mock_webhook) == "not a webhook"


def test_Webhook_str_operator_when_name_is_None():
    mock_webhook = mock.Mock(webhooks.Webhook)
    mock_webhook.name = None
    mock_webhook.id = 987654321
    assert webhooks.Webhook.__str__(mock_webhook) == "Unnamed webhook ID 987654321"

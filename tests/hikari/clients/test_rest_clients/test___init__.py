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
import inspect

import mock
import pytest

from hikari.clients import configs
from hikari.clients import rest_clients
from hikari.net import rest


class TestRESTClient:
    @pytest.fixture()
    def mock_config(self):
        # Mocking the Configs leads to attribute errors regardless of spec set.
        return configs.RESTConfig(token="blah.blah.blah")

    def test_init(self, mock_config):
        mock_low_level_rest_clients = mock.MagicMock(rest.LowLevelRestfulClient)
        with mock.patch.object(rest, "LowLevelRestfulClient", return_value=mock_low_level_rest_clients) as patched_init:
            cli = rest_clients.RESTClient(mock_config)
            patched_init.assert_called_once_with(
                allow_redirects=mock_config.allow_redirects,
                connector=mock_config.tcp_connector,
                proxy_headers=mock_config.proxy_headers,
                proxy_auth=mock_config.proxy_auth,
                ssl_context=mock_config.ssl_context,
                verify_ssl=mock_config.verify_ssl,
                timeout=mock_config.request_timeout,
                token=f"{mock_config.token_type} {mock_config.token}",
                version=mock_config.rest_version,
            )
            assert cli._session is mock_low_level_rest_clients

    def test_inheritance(self):
        for attr, routine in (
            member
            for component in [
                rest_clients.channels_component.RESTChannelComponent,
                rest_clients.current_users_component.RESTCurrentUserComponent,
                rest_clients.gateways_component.RESTGatewayComponent,
                rest_clients.guilds_component.RESTGuildComponent,
                rest_clients.invites_component.RESTInviteComponent,
                rest_clients.oauth2_component.RESTOauth2Component,
                rest_clients.reactions_component.RESTReactionComponent,
                rest_clients.users_component.RESTUserComponent,
                rest_clients.voices_component.RESTVoiceComponent,
                rest_clients.webhooks_component.RESTWebhookComponent,
            ]
            for member in inspect.getmembers(component, inspect.isroutine)
        ):
            if not attr.startswith("__"):
                assert hasattr(rest_clients.RESTClient, attr), (
                    f"Missing {routine.__qualname__} on RestClient; the component might not be being "
                    "inherited properly or at all."
                )
                assert getattr(rest_clients.RESTClient, attr) == routine, (
                    f"Mismatching method found on RestClient; expected {routine.__qualname__} but got "
                    f"{getattr(rest_clients.RESTClient, attr).__qualname__}. `{attr}` is most likely being declared on"
                    "multiple components."
                )

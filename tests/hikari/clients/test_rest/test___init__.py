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

from hikari.clients import components
from hikari.clients import configs
from hikari.clients import rest as high_level_rest
from hikari.net import rest as low_level_rest


class TestRESTClient:
    def test_init(self):
        mock_config = configs.RESTConfig(token="blah.blah.blah", trust_env=True)
        mock_components = mock.MagicMock(components.Components, config=mock_config)
        mock_low_level_rest_clients = mock.MagicMock(low_level_rest.REST)
        with mock.patch.object(low_level_rest, "REST", return_value=mock_low_level_rest_clients) as patched_init:
            client = high_level_rest.RESTClient(mock_components)
            patched_init.assert_called_once_with(
                allow_redirects=mock_config.allow_redirects,
                base_url=mock_config.rest_url,
                connector=mock_config.tcp_connector,
                debug=False,
                proxy_headers=mock_config.proxy_headers,
                proxy_auth=mock_config.proxy_auth,
                ssl_context=mock_config.ssl_context,
                verify_ssl=mock_config.verify_ssl,
                timeout=mock_config.request_timeout,
                token=f"{mock_config.token_type} {mock_config.token}",
                trust_env=True,
                version=mock_config.rest_version,
            )
            assert client._session is mock_low_level_rest_clients
            assert client._components is mock_components

    def test_inheritance(self):
        for attr, routine in (
            member
            for component in [
                high_level_rest.channel.RESTChannelComponent,
                high_level_rest.me.RESTCurrentUserComponent,
                high_level_rest.gateway.RESTGatewayComponent,
                high_level_rest.guild.RESTGuildComponent,
                high_level_rest.invite.RESTInviteComponent,
                high_level_rest.oauth2.RESTOAuth2Component,
                high_level_rest.react.RESTReactionComponent,
                high_level_rest.user.RESTUserComponent,
                high_level_rest.voice.RESTVoiceComponent,
                high_level_rest.webhook.RESTWebhookComponent,
            ]
            for member in inspect.getmembers(component, inspect.isroutine)
        ):
            if not attr.startswith("__"):
                assert hasattr(high_level_rest.RESTClient, attr), (
                    f"Missing {routine.__qualname__} on RestClient; the component might not be being "
                    "inherited properly or at all."
                )
                assert getattr(high_level_rest.RESTClient, attr) == routine, (
                    f"Mismatching method found on RestClient; expected {routine.__qualname__} but got "
                    f"{getattr(high_level_rest.RESTClient, attr).__qualname__}. `{attr}` is most likely being declared on"
                    "multiple components."
                )

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

from hikari import http_settings
from hikari.net import rest as high_level_rest
from hikari import application
from hikari.net.rest import channel
from hikari.net.rest import gateway
from hikari.net.rest import guild
from hikari.net.rest import invite
from hikari.net.rest import me
from hikari.net.rest import oauth2
from hikari.net.rest import react
from hikari.net.rest import session as low_level_rest
from hikari.net.rest import user
from hikari.net.rest import voice
from hikari.net.rest import webhook


class TestRESTClient:
    @pytest.mark.parametrize(
        ["token", "token_type", "expected_token"],
        [
            ("foobar.baz.bork", None, None),
            ("foobar.baz.bork", "Bot", "Bot foobar.baz.bork"),
            ("foobar.baz.bork", "Bearer", "Bearer foobar.baz.bork"),
        ],
    )
    def test_init(self, token, token_type, expected_token):
        mock_config = http_settings.RESTConfig(token=token, token_type=token_type, trust_env=True)
        mock_app = mock.MagicMock(application.Application, config=mock_config)
        mock_low_level_rest_clients = mock.MagicMock(low_level_rest.RESTSession)
        with mock.patch.object(low_level_rest, "RESTSession", return_value=mock_low_level_rest_clients) as patched_init:
            client = high_level_rest.RESTClient(mock_app)
            patched_init.assert_called_once_with(
                allow_redirects=mock_config._allow_redirects,
                base_url=mock_config.rest_url,
                connector=mock_config.tcp_connector,
                debug=False,
                proxy_headers=mock_config._proxy_headers,
                proxy_auth=mock_config._proxy_auth,
                ssl_context=mock_config._ssl_context,
                verify_ssl=mock_config._verify_ssl,
                timeout=mock_config.request_timeout,
                token=expected_token,
                trust_env=True,
                version=mock_config.rest_version,
            )
            assert client._session is mock_low_level_rest_clients
            assert client._app is mock_app

    def test_inheritance(self):
        for attr, routine in (
            member
            for component in [
                channel.RESTChannelComponent,
                me.RESTCurrentUserComponent,
                gateway.RESTGatewayComponent,
                guild.RESTGuildComponent,
                invite.RESTInviteComponent,
                oauth2.RESTOAuth2Component,
                react.RESTReactionComponent,
                user.RESTUserComponent,
                voice.RESTVoiceComponent,
                webhook.RESTWebhookComponent,
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
                    "multiple application."
                )

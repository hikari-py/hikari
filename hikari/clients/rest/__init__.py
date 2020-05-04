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
"""Marshall wrappings for the REST implementation in `hikari.net.rest`.

This provides an object-oriented interface for interacting with discord's REST
API.
"""

from __future__ import annotations

__all__ = ["RESTClient"]

import typing

from hikari.clients.rest import channel
from hikari.clients.rest import gateway
from hikari.clients.rest import guild
from hikari.clients.rest import invite
from hikari.clients.rest import me
from hikari.clients.rest import oauth2
from hikari.clients.rest import react
from hikari.clients.rest import user
from hikari.clients.rest import voice
from hikari.clients.rest import webhook
from hikari.net import rest as low_level_rest

if typing.TYPE_CHECKING:
    from hikari.clients import components as _components


class RESTClient(
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
):
    """
    A marshalling object-oriented REST API client.

    This client bridges the basic REST API exposed by
    `hikari.net.rest.REST` and wraps it in a unit of processing that can handle
    handle parsing API objects into Hikari entity objects.

    Parameters
    ----------
    components : hikari.clients.components.Components
        The client components that this rest client should be bound by.
        Includes the rest config.

    !!! note
        For all endpoints where a `reason` argument is provided, this may be a
        string inclusively between `0` and `512` characters length, with any
        additional characters being cut off.
    """

    def __init__(self, components: _components.Components) -> None:
        token = None
        if components.config.token_type is not None:
            token = f"{components.config.token_type} {components.config.token}"
        super().__init__(
            components,
            low_level_rest.REST(
                allow_redirects=components.config.allow_redirects,
                base_url=components.config.rest_url,
                connector=components.config.tcp_connector,
                debug=components.config.debug,
                proxy_headers=components.config.proxy_headers,
                proxy_auth=components.config.proxy_auth,
                ssl_context=components.config.ssl_context,
                verify_ssl=components.config.verify_ssl,
                timeout=components.config.request_timeout,
                token=token,
                trust_env=components.config.trust_env,
                version=components.config.rest_version,
            ),
        )

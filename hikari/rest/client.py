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
"""Marshall wrappings for the RESTSession implementation in `hikari.net.rest`.

This provides an object-oriented interface for interacting with discord's RESTSession
API.
"""

from __future__ import annotations

__all__ = ["RESTClient"]

import typing

from . import channel
from . import gateway
from . import guild
from . import invite
from . import me
from . import oauth2
from . import react
from . import session
from . import user
from . import voice
from . import webhook

if typing.TYPE_CHECKING:
    from hikari.components import application


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
    A marshalling object-oriented RESTSession API client.

    This client bridges the basic RESTSession API exposed by
    `hikari.net.rest.RESTSession` and wraps it in a unit of processing that can handle
    handle parsing API objects into Hikari entity objects.

    Parameters
    ----------
    app : hikari.clients.application.Application
        The client application that this rest client should be bound by.
        Includes the rest config.

    !!! note
        For all endpoints where a `reason` argument is provided, this may be a
        string inclusively between `0` and `512` characters length, with any
        additional characters being cut off.
    """

    def __init__(self, app: application.Application) -> None:
        token = None
        if app.config.token_type is not None:
            token = f"{app.config.token_type} {app.config.token}"
        super().__init__(
            app,
            session.RESTSession(
                allow_redirects=app.config.allow_redirects,
                base_url=app.config.rest_url,
                connector=app.config.tcp_connector,
                debug=app.config.debug,
                proxy_headers=app.config.proxy_headers,
                proxy_auth=app.config.proxy_auth,
                ssl_context=app.config.ssl_context,
                verify_ssl=app.config.verify_ssl,
                timeout=app.config.request_timeout,
                token=token,
                trust_env=app.config.trust_env,
                version=app.config.rest_version,
            ),
        )

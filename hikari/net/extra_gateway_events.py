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
"""
Events the gateway implementation will provide special implementations for that are noteworthy.
"""
#: Fired when the connection has completed the initial handshake. This is triggered before the gateway has finished
#: loading all guilds. The Discord API refers to this as a `READY` event, however, to prevent confusion for bot
#: creators, this is referred to as `CONNECT` instead.
#:
#: Note:
#:    This is fired when the initial handshake has completed, but guilds will not yet have become available.
#:    Implementations should track the guilds that become available as they become available to determine when
#:    the full initialization has completed.
#:
#: Args:
#:    gateway:
#:        the gateway object that is connected.
#:    payload:
#:        a ready event as described by https://discordapp.com/developers/docs/topics/gateway#ready-ready-event-fields
CONNECT = "connect"

#: Fired when a gateway connection closes due to some connection error or if requested by Discord's servers.
#:
#: Args:
#:     gateway:
#:         the gateway instance that sent this signal.
#:     code:
#:         the integer closure code given by the gateway.
#:     reason:
#:         the optional string reason for the closure given by the gateway.
DISCONNECT = "disconnect"

#: Fired if an INVALID_SESSION payload is sent.
#:
#: |selfHealing|
#:
#: Args:
#:     gateway:
#:         the gateway instance that sent this signal.
#:     can_resume:
#:         `True` if we expect the connection to be resumed (that is, it disconnects and reconnects without the initial
#:         identification handshake and parsing of guild information). If `False`, the connection will be restarted as
#:         if a fresh connection from scratch, which will take longer.
INVALID_SESSION = "invalid_session"

#: Fired if the gateway requested we reconnect.
#:
#: |selfHealing|
#:
#: Args:
#:     gateway:
#:         the gateway instance that sent this signal.
RECONNECT = "reconnect"

#: Fired if a connection was successfully resumed.
#:
#: Args:
#:     gateway:
#:         the gateway instance that sent this signal.
RESUME = "resume"

#: Fired if the gateway is told to shutdown by your code. The gateway will not automatically restart in this case.
#:
#: Args:
#:     gateway:
#:         the gateway instance that sent this signal.
SHUTDOWN = "shutdown"

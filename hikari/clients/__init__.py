#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""The models API for interacting with Discord directly."""

from hikari.clients import app_config
from hikari.clients import bot_client
from hikari.clients import gateway_client
from hikari.clients import gateway_config
from hikari.clients import http_client
from hikari.clients import http_config
from hikari.clients import protocol_config
from hikari.clients import websocket_client

from hikari.clients.app_config import *
from hikari.clients.bot_client import *
from hikari.clients.gateway_client import *
from hikari.clients.gateway_config import *
from hikari.clients.http_client import *
from hikari.clients.http_config import *
from hikari.clients.protocol_config import *
from hikari.clients.shard_client import *
from hikari.clients.websocket_client import *


__all__ = [
    *app_config.__all__,
    *bot_client.__all__,
    *gateway_client.__all__,
    *gateway_config.__all__,
    *http_client.__all__,
    *http_config.__all__,
    *protocol_config.__all__,
    *shard_client.__all__,
    *websocket_client.__all__,
]

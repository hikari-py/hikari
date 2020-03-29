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
"""The core API for interacting with Discord directly."""

from hikari.core.clients import app_config
from hikari.core.clients import bot_client
from hikari.core.clients import gateway_client
from hikari.core.clients import gateway_config
from hikari.core.clients import http_client
from hikari.core.clients import http_config
from hikari.core.clients import protocol_config
from hikari.core.clients import shard_client

from hikari.core.clients.app_config import *
from hikari.core.clients.bot_client import *
from hikari.core.clients.gateway_client import *
from hikari.core.clients.gateway_config import *
from hikari.core.clients.http_client import *
from hikari.core.clients.http_config import *
from hikari.core.clients.protocol_config import *
from hikari.core.clients.shard_client import *


__all__ = [
    *app_config.__all__,
    *bot_client.__all__,
    *gateway_client.__all__,
    *gateway_config.__all__,
    *http_client.__all__,
    *http_config.__all__,
    *protocol_config.__all__,
    *shard_client.__all__,
]

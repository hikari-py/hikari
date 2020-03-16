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
"""Network components for the Hikari Discord API.

These components describe the low level parts of Hikari. No model classes exist
for these; the majority of communication is done via JSON arrays and objects.
"""
from hikari.net import base_http_client
from hikari.net import codes
from hikari.net import gateway
from hikari.net import http_client
from hikari.net import ratelimits
from hikari.net import routes
from hikari.net import user_agent
from hikari.net import versions

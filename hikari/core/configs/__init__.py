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
"""Configuration data objects. These structure the settings a user can
initialise their application with, and optionally support being read
in from an external source, such as a JSON file, using the marshalling
functionality included in this library.
"""

from hikari.core.configs import app
from hikari.core.configs import gateway
from hikari.core.configs import http
from hikari.core.configs import protocol

from hikari.core.configs.app import *
from hikari.core.configs.gateway import *
from hikari.core.configs.http import *
from hikari.core.configs.protocol import *

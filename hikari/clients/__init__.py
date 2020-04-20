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

from hikari.clients import bot
from hikari.clients import configs
from hikari.clients import rest
from hikari.clients import runnable
from hikari.clients.bot import *
from hikari.clients.configs import *
from hikari.clients.rest import *
from hikari.clients.runnable import *
from hikari.clients.shards import *

__all__ = [
    *bot.__all__,
    *configs.__all__,
    *rest.__all__,
    *shards.__all__,
    *runnable.__all__,
]

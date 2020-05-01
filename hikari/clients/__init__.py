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

from __future__ import annotations

from hikari.clients import bot_base
from hikari.clients import components
from hikari.clients import configs
from hikari.clients import rest
from hikari.clients import runnable
from hikari.clients import shard_states
from hikari.clients import shards
from hikari.clients import stateless
from hikari.clients.bot_base import *
from hikari.clients.components import *
from hikari.clients.configs import *
from hikari.clients.rest import *
from hikari.clients.runnable import *
from hikari.clients.shard_states import *
from hikari.clients.shards import *
from hikari.clients.stateless import *

__all__ = [
    *bot_base.__all__,
    *components.__all__,
    *configs.__all__,
    *rest.__all__,
    *shard_states.__all__,
    *shards.__all__,
    *runnable.__all__,
    *stateless.__all__,
]

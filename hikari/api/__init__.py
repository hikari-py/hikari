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
"""Interfaces for components that make up Hikari applications.

These are provided to uncouple specific implementation details from each
implementation, thus allowing custom solutions to be engineered such as bots
relying on a distributed event bus or cache.
"""
from __future__ import annotations

from hikari.api.app import *
from hikari.api.cache import *
from hikari.api.component import *
from hikari.api.entity_factory import *
from hikari.api.event_consumer import *
from hikari.api.event_dispatcher import *

__all__ = (
    app.__all__
    + cache.__all__
    + component.__all__
    + entity_factory.__all__
    + event_consumer.__all__
    + event_dispatcher.__all__
)

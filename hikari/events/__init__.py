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
"""Components and entities that are used to describe Discord gateway events."""

from __future__ import annotations

from hikari.events import bases
from hikari.events import channels
from hikari.events import guilds
from hikari.events import messages
from hikari.events import other
from hikari.events.bases import *
from hikari.events.channels import *
from hikari.events.guilds import *
from hikari.events.messages import *
from hikari.events.other import *

__all__ = [
    *bases.__all__,
    *channels.__all__,
    *guilds.__all__,
    *messages.__all__,
    *other.__all__,
]

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

# Do I need this? It still resolves without adding these in...?
from hikari.core import channels
from hikari.core import clients
from hikari.core import entities
from hikari.core import events
from hikari.core import gateway_entities
from hikari.core import guilds
from hikari.core import invites
from hikari.core import messages
from hikari.core import oauth2
from hikari.core import permissions
from hikari.core import snowflakes
from hikari.core import users
from hikari.core import webhooks

# Import everything into this namespace.
from hikari.core.channels import *
from hikari.core.clients import *
from hikari.core.colors import *
from hikari.core.colours import *
from hikari.core.embeds import *
from hikari.core.emojis import *
from hikari.core.entities import *
from hikari.core.events import *
from hikari.core.gateway_entities import *
from hikari.core.guilds import *
from hikari.core.invites import *
from hikari.core.messages import *
from hikari.core.oauth2 import *
from hikari.core.permissions import *
from hikari.core.snowflakes import *
from hikari.core.users import *
from hikari.core.voices import *
from hikari.core.webhooks import *

__all__ = [
    *channels.__all__,
    *clients.__all__,
    *entities.__all__,
    *events.__all__,
    *gateway_entities.__all__,
    *guilds.__all__,
    *invites.__all__,
    *messages.__all__,
    *oauth2.__all__,
    *permissions.__all__,
    *snowflakes.__all__,
    *users.__all__,
    *webhooks.__all__,
]

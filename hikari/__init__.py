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
"""Hikari's models framework for writing Discord bots in Python."""
from hikari import audit_logs
from hikari import channels
from hikari import clients
from hikari import colors
from hikari import colours
from hikari import embeds
from hikari import emojis
from hikari import entities
from hikari import errors
from hikari import events
from hikari import gateway_entities
from hikari import guilds
from hikari import invites
from hikari import messages
from hikari import net
from hikari import oauth2
from hikari import permissions
from hikari import snowflakes
from hikari import state
from hikari import users
from hikari import voices
from hikari import webhooks
from hikari._about import __author__
from hikari._about import __copyright__
from hikari._about import __email__
from hikari._about import __license__
from hikari._about import __url__
from hikari._about import __version__
from hikari.audit_logs import *
from hikari.channels import *
from hikari.clients import *
from hikari.colors import *
from hikari.colours import *
from hikari.embeds import *
from hikari.emojis import *
from hikari.entities import *
from hikari.events import *
from hikari.gateway_entities import *
from hikari.guilds import *
from hikari.invites import *
from hikari.messages import *
from hikari.net import *
from hikari.oauth2 import *
from hikari.permissions import *
from hikari.snowflakes import *
from hikari.state import *
from hikari.users import *
from hikari.voices import *
from hikari.webhooks import *

# Import everything into this namespace.

__all__ = [
    *audit_logs.__all__,
    *channels.__all__,
    *clients.__all__,
    *colors.__all__,
    *colours.__all__,
    *embeds.__all__,
    *emojis.__all__,
    *entities.__all__,
    *events.__all__,
    *gateway_entities.__all__,
    *guilds.__all__,
    *invites.__all__,
    *messages.__all__,
    *net.__all__,
    *oauth2.__all__,
    *permissions.__all__,
    *snowflakes.__all__,
    *state.__all__,
    *users.__all__,
    *voices.__all__,
    *webhooks.__all__,
]

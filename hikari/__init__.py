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

from __future__ import annotations

from hikari import applications
from hikari import audit_logs
from hikari import bases
from hikari import channels
from hikari import clients
from hikari import colors
from hikari import colours
from hikari import embeds
from hikari import emojis
from hikari import errors
from hikari import events
from hikari import files
from hikari import gateway_entities
from hikari import guilds
from hikari import intents
from hikari import invites
from hikari import messages
from hikari import net
from hikari import permissions
from hikari import state
from hikari import users
from hikari import voices
from hikari import webhooks
from hikari._about import __author__
from hikari._about import __ci__
from hikari._about import __copyright__
from hikari._about import __discord_invite__
from hikari._about import __docs__
from hikari._about import __email__
from hikari._about import __issue_tracker__
from hikari._about import __license__
from hikari._about import __url__
from hikari._about import __version__
from hikari.applications import *
from hikari.audit_logs import *
from hikari.bases import *
from hikari.channels import *
from hikari.clients import *
from hikari.colors import *
from hikari.colours import *
from hikari.embeds import *
from hikari.emojis import *
from hikari.events import *
from hikari.files import *
from hikari.gateway_entities import *
from hikari.guilds import *
from hikari.intents import *
from hikari.invites import *
from hikari.messages import *
from hikari.permissions import *
from hikari.unset import *
from hikari.users import *
from hikari.voices import *
from hikari.webhooks import *

# Adding everything to `__all__` pollutes the top level index in our documentation, therefore this is left empty.
__all__ = []

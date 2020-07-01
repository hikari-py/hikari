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
"""Data classes representing Discord entities."""

from __future__ import annotations

# noinspection PyUnresolvedReferences
import typing

from hikari.models import applications
from hikari.models import audit_logs
from hikari.models import channels
from hikari.models import colors
from hikari.models import colours
from hikari.models import embeds
from hikari.models import emojis
from hikari.models import gateway
from hikari.models import guilds
from hikari.models import intents
from hikari.models import invites
from hikari.models import messages
from hikari.models import permissions
from hikari.models import presences
from hikari.models import users
from hikari.models import voices
from hikari.models import webhooks

from hikari.models.applications import *
from hikari.models.audit_logs import *
from hikari.models.channels import *
from hikari.models.colors import *
from hikari.models.colours import *
from hikari.models.embeds import *
from hikari.models.emojis import *
from hikari.models.gateway import *
from hikari.models.guilds import *
from hikari.models.intents import *
from hikari.models.invites import *
from hikari.models.messages import *
from hikari.models.permissions import *
from hikari.models.presences import *
from hikari.models.users import *
from hikari.models.voices import *
from hikari.models.webhooks import *

__all__: typing.Final[typing.List[str]] = (
    applications.__all__
    + audit_logs.__all__
    + channels.__all__
    + colors.__all__
    + colours.__all__
    + embeds.__all__
    + emojis.__all__
    + gateway.__all__
    + guilds.__all__
    + intents.__all__
    + invites.__all__
    + messages.__all__
    + permissions.__all__
    + presences.__all__
    + users.__all__
    + voices.__all__
    + webhooks.__all__
)

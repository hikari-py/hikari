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
"""
Hikari's core framework for writing Discord bots in Python.
"""
from __future__ import annotations

from hikari._about import __author__, __copyright__, __email__, __license__, __version__, __url__

from hikari import net
from hikari import orm
from hikari import errors

from hikari.errors import *

from hikari.net.codes import *
from hikari.net.errors import *
from hikari.net.gateway import *
from hikari.net.http_client import *
from hikari.net.status_info_client import *
from hikari.net.versions import *

from hikari.orm.gateway.chunk_mode import *
from hikari.orm.gateway.event_types import *

from hikari.orm.models.applications import *
from hikari.orm.models.audit_logs import *
from hikari.orm.models.channels import *
from hikari.orm.models.colors import *
from hikari.orm.models.colours import *
from hikari.orm.models.connections import *
from hikari.orm.models.embeds import *
from hikari.orm.models.emojis import *
from hikari.orm.models.guilds import *
from hikari.orm.models.integrations import *
from hikari.orm.models.invites import *
from hikari.orm.models.media import *
from hikari.orm.models.members import *
from hikari.orm.models.messages import *
from hikari.orm.models.overwrites import *
from hikari.orm.models.permissions import *
from hikari.orm.models.presences import *
from hikari.orm.models.reactions import *
from hikari.orm.models.roles import *
from hikari.orm.models.teams import *
from hikari.orm.models.users import *
from hikari.orm.models.voices import *
from hikari.orm.models.webhooks import *

from hikari.orm.client import *
from hikari.orm.client_options import *

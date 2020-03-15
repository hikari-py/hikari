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
from . import channels
from . import entities
from . import events
from . import gateway_bot
from . import guilds
from . import invites
from . import messages
from . import oauth2
from . import permissions
from . import snowflakes
from . import users

from .channels import *
from .entities import *
from .events import *
from .gateway_bot import *
from .guilds import *
from .invites import *
from .messages import *
from .oauth2 import *
from .permissions import *
from .snowflakes import *
from .users import *

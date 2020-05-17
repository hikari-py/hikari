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
"""Marshall classes used for describing discord entities."""

from __future__ import annotations

from .applications import *
from .audit_logs import *
from .bases import *
from .channels import *
from .colors import *
from .colours import *
from .embeds import *
from .emojis import *
from .files import *
from .gateway import *
from .guilds import *
from .intents import *
from .invites import *
from .messages import *
from .permissions import *
from .unset import *
from .users import *
from .voices import *
from .webhooks import *

__all__ = (
    applications.__all__
    + audit_logs.__all__
    + bases.__all__
    + channels.__all__
    + colors.__all__
    + colours.__all__
    + embeds.__all__
    + emojis.__all__
    + files.__all__
    + gateway.__all__
    + guilds.__all__
    + intents.__all__
    + invites.__all__
    + messages.__all__
    + permissions.__all__
    + unset.__all__
    + users.__all__
    + voices.__all__
    + webhooks.__all__
)

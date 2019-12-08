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

from hikari.orm import events
from hikari.orm import state_registry
from . import commands
from . import errors
from . import net
from . import orm


__author__ = "Nekokatt"
__contributors__ = {"FasterSpeeding", "LunarCoffee", "raatty", "Tmpod", "Zach", "thomm.o", "rock500", "davfsa"}
__copyright__ = f"© 2019-2020 Nekokatt"
__license__ = "LGPLv3"
__version__ = "0.0.59"
__url__ = "https://gitlab.com/nekokatt/hikari"

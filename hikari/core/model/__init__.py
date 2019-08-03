#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
All models used in Hikari's public API.
"""
import builtins as _builtins

from .base import *
from .channel import *
from .color import *
from .embed import *
from .emoji import *
from .guild import *
from .integration import *
from .invite import *
from .media import *
from .message import *
from .overwrite import *
from .permission import *
from .reaction import *
from .role import *
from .server_debug import *
from .service_status import *
from .user import *
from .voice import *
from .webhook import *

# Easier than keeping these lists up to date with several dozen classes...
_builtins = dir(_builtins)
__all__ = [m for m in globals() if not m.startswith("_") and m not in _builtins]
del _builtins

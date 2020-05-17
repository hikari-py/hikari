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

from ._about import __author__
from ._about import __ci__
from ._about import __copyright__
from ._about import __discord_invite__
from ._about import __docs__
from ._about import __email__
from ._about import __issue_tracker__
from ._about import __license__
from ._about import __url__
from ._about import __version__
from .configs import *
from .events import *
from .errors import *
from .gateway import *
from .models import *
from .rest import *
from .stateful import *
from .stateless import *

__all__ = []

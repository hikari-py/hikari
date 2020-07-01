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
"""A sane Python framework for writing modern Discord bots.

To get started, you will want to initialize an instance of `Bot` for writing
a bot, or `RESTClientFactory` if you only need to use the REST API.
"""

from __future__ import annotations

# noinspection PyUnresolvedReferences
import typing

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

# We need these imported explicitly for the __all__ to be visible due to
# Python's weird import visibility system.
from hikari import config
from hikari import events
from hikari import errors
from hikari import models
from hikari.utilities import files as _files
from hikari.utilities import iterators as _iterators
from hikari.utilities import snowflake as _snowflake
from hikari.utilities import spel as _spel
from hikari.utilities import undefined as _undefined

from hikari.config import *
from hikari.events import *
from hikari.errors import *
from hikari.models import *
from hikari.utilities.files import *
from hikari.utilities.iterators import *
from hikari.utilities.snowflake import *
from hikari.utilities.spel import *
from hikari.utilities.undefined import *

from hikari.impl.bot import BotAppImpl as Bot
from hikari.impl.rest_app import RESTAppFactoryImpl as RESTClientFactory

_presorted_all = (
    config.__all__
    + events.__all__
    + errors.__all__
    + models.__all__
    + _files.__all__
    + _iterators.__all__
    + _snowflake.__all__
    + _spel.__all__
    + _undefined.__all__
)

__all__: typing.Final[typing.List[str]] = [
    # This may seem a bit dirty, but I have added an edge case to the documentation
    # logic to *ignore* the sorting member rules for the root `hikari` module
    # (this file) specifically. This way, we can force `Bot` and `RESTClientFactory`
    # to the top of the list.
    "Bot",
    "RESTClientFactory",
    *sorted(_presorted_all),
]

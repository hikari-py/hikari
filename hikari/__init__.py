# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""A sane Python framework for writing modern Discord bots.

To get started, you will want to initialize an instance of `Bot`
(an alias for `hikari.impl.bot.BotAppImpl`) for writing a bot, or `REST` (an
alias for `hikari.impl.rest.RESTAppFactoryImpl`) if you only need to use
the REST API.
"""

# We need these imported explicitly for the __all__ to be visible due to
# Python's weird import visibility system.
from hikari import config
from hikari import errors
from hikari import events
from hikari import models
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
from hikari.config import *
from hikari.errors import *
from hikari.events import *
from hikari.impl.bot import BotAppImpl as Bot
from hikari.impl.rest import RESTAppFactoryImpl as REST
from hikari.models import *
from hikari.utilities.files import File
from hikari.utilities.files import LazyByteIteratorish
from hikari.utilities.files import Pathish
from hikari.utilities.files import Rawish
from hikari.utilities.files import Resourceish
from hikari.utilities.snowflake import SearchableSnowflakeish
from hikari.utilities.snowflake import SearchableSnowflakeishOr
from hikari.utilities.snowflake import Snowflake
from hikari.utilities.snowflake import Snowflakeish
from hikari.utilities.snowflake import SnowflakeishOr
from hikari.utilities.snowflake import Unique
from hikari.utilities.undefined import UNDEFINED
from hikari.utilities.undefined import UndefinedNoneOr
from hikari.utilities.undefined import UndefinedOr

_presorted_all = [
    "File",
    "Pathish",
    "Rawish",
    "LazyByteIteratorish",
    "Resourceish",
    "Snowflake",
    "Snowflakeish",
    "SnowflakeishOr",
    "SearchableSnowflakeish",
    "SearchableSnowflakeishOr",
    "Unique",
    "UNDEFINED",
    "UndefinedOr",
    "UndefinedNoneOr",
    *config.__all__,
    *events.__all__,
    *errors.__all__,
    *models.__all__,
]

# This may seem a bit dirty, but I have added an edge case to the documentation
# logic to *ignore* the sorting member rules for the root `hikari` module
# (this file) specifically. This way, we can force `Bot` and `RESTClientFactory`
# to the top of the list.
__all__ = ["Bot", "REST", *sorted(_presorted_all)]

del _presorted_all

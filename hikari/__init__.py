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
(an alias for `hikari.impl.bot.BotApp`) for writing a bot, or `REST` (an
alias for `hikari.impl.rest.RESTApp`) if you only need to use
the REST API.
"""

from __future__ import annotations

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
from hikari.impl.bot import BotApp as Bot
from hikari.impl.rest import RESTApp as REST
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

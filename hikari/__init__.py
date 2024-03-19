# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

To get started, you will want to initialize an instance of [`hikari.impl.gateway_bot.GatewayBot`][]
for writing a gateway based bot, [`hikari.impl.rest_bot.RESTBot`][] for a REST based bot,
or [`hikari.impl.rest.RESTApp`][] if you only need to use the REST API.
"""

from __future__ import annotations

from hikari import api
from hikari import applications
from hikari import events
from hikari import files
from hikari import impl
from hikari import interactions
from hikari import snowflakes
from hikari import undefined
from hikari._about import __author__
from hikari._about import __ci__
from hikari._about import __copyright__
from hikari._about import __coverage__
from hikari._about import __discord_invite__
from hikari._about import __docs__
from hikari._about import __email__
from hikari._about import __git_sha1__
from hikari._about import __issue_tracker__
from hikari._about import __license__
from hikari._about import __maintainer__
from hikari._about import __url__
from hikari._about import __version__
from hikari.applications import Application
from hikari.applications import ApplicationFlags
from hikari.applications import ApplicationRoleConnectionMetadataRecord
from hikari.applications import ApplicationRoleConnectionMetadataRecordType
from hikari.applications import AuthorizationApplication
from hikari.applications import AuthorizationInformation
from hikari.applications import ConnectionVisibility
from hikari.applications import OAuth2AuthorizationToken
from hikari.applications import OAuth2ImplicitToken
from hikari.applications import OAuth2Scope
from hikari.applications import OwnApplicationRoleConnection
from hikari.applications import OwnConnection
from hikari.applications import OwnGuild
from hikari.applications import PartialOAuth2Token
from hikari.applications import Team
from hikari.applications import TeamMember
from hikari.applications import TeamMembershipState
from hikari.applications import TokenType
from hikari.audit_logs import *
from hikari.channels import *
from hikari.colors import *
from hikari.colours import *
from hikari.commands import *
from hikari.components import *
from hikari.embeds import *
from hikari.emojis import *
from hikari.errors import *
from hikari.events.base_events import Event
from hikari.events.base_events import ExceptionEvent
from hikari.events.channel_events import *
from hikari.events.guild_events import *
from hikari.events.interaction_events import *
from hikari.events.lifetime_events import *
from hikari.events.member_events import *
from hikari.events.message_events import *
from hikari.events.reaction_events import *
from hikari.events.role_events import *
from hikari.events.scheduled_events import *
from hikari.events.shard_events import *
from hikari.events.typing_events import *
from hikari.events.user_events import *
from hikari.events.voice_events import *
from hikari.files import URL
from hikari.files import Bytes
from hikari.files import File
from hikari.files import LazyByteIteratorish
from hikari.files import Pathish
from hikari.files import Rawish
from hikari.files import Resourceish
from hikari.guilds import *
from hikari.impl import ClientCredentialsStrategy
from hikari.impl import GatewayBot
from hikari.impl import RESTApp
from hikari.impl import RESTBot
from hikari.intents import *
from hikari.interactions.base_interactions import *
from hikari.interactions.command_interactions import *
from hikari.interactions.component_interactions import *
from hikari.interactions.modal_interactions import *
from hikari.invites import *
from hikari.iterators import *
from hikari.locales import *
from hikari.messages import *
from hikari.permissions import *
from hikari.presences import *
from hikari.scheduled_events import *
from hikari.sessions import *
from hikari.snowflakes import SearchableSnowflakeish
from hikari.snowflakes import SearchableSnowflakeishOr
from hikari.snowflakes import Snowflake
from hikari.snowflakes import Snowflakeish
from hikari.snowflakes import SnowflakeishOr
from hikari.snowflakes import SnowflakeishSequence
from hikari.snowflakes import Unique
from hikari.stickers import *
from hikari.templates import *
from hikari.traits import *
from hikari.undefined import UNDEFINED
from hikari.undefined import UndefinedNoneOr
from hikari.undefined import UndefinedOr
from hikari.undefined import UndefinedType
from hikari.users import *
from hikari.voices import *
from hikari.webhooks import *

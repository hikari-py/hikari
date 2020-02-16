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

from hikari import errors
from hikari import net
from hikari import orm
from hikari._about import __author__, __copyright__, __email__, __license__, __version__, __url__

# Errors
from hikari.net.errors import BadRequestHTTPError
from hikari.net.errors import ClientHTTPError
from hikari.net.errors import ForbiddenHTTPError
from hikari.net.errors import GatewayClientClosedError
from hikari.net.errors import GatewayConnectionClosedError
from hikari.net.errors import GatewayError
from hikari.net.errors import GatewayInvalidSessionError
from hikari.net.errors import GatewayInvalidTokenError
from hikari.net.errors import GatewayMustReconnectError
from hikari.net.errors import GatewayNeedsShardingError
from hikari.net.errors import GatewayZombiedError
from hikari.net.errors import HTTPError
from hikari.net.errors import NotFoundHTTPError
from hikari.net.errors import ServerHTTPError
from hikari.net.errors import UnauthorizedHTTPError

# Gateway
from hikari.net.gateway import GatewayClient

# HTTP Client
from hikari.net.http_client import HTTPClient

# API versions
from hikari.net.versions import GatewayVersion
from hikari.net.versions import HTTPAPIVersion
from hikari.orm import client

# Bot client
from hikari.orm.client import Client

# Fabric
from hikari.orm.fabric import Fabric

# HTTP Adapter
from hikari.orm.http.http_adapter_impl import HTTPAdapterImpl

# Models
from hikari.orm.models.applications import Application
from hikari.orm.models.audit_logs import AuditLog
from hikari.orm.models.audit_logs import AuditLogChange
from hikari.orm.models.audit_logs import AuditLogEntry
from hikari.orm.models.audit_logs import AuditLogEntryCountInfo
from hikari.orm.models.audit_logs import BaseAuditLogEntryInfo
from hikari.orm.models.audit_logs import ChannelOverwriteAuditLogEntryInfo
from hikari.orm.models.audit_logs import MemberMoveAuditLogEntryInfo
from hikari.orm.models.audit_logs import MemberPruneAuditLogEntryInfo
from hikari.orm.models.audit_logs import MessageDeleteAuditLogEntryInfo
from hikari.orm.models.audit_logs import MessagePinAuditLogEntryInfo
from hikari.orm.models.channels import Channel
from hikari.orm.models.channels import DMChannel
from hikari.orm.models.channels import GroupDMChannel
from hikari.orm.models.channels import GuildAnnouncementChannel
from hikari.orm.models.channels import GuildCategory
from hikari.orm.models.channels import GuildChannel
from hikari.orm.models.channels import GuildStoreChannel
from hikari.orm.models.channels import GuildTextChannel
from hikari.orm.models.channels import GuildVoiceChannel
from hikari.orm.models.channels import PartialChannel
from hikari.orm.models.channels import TextChannel
from hikari.orm.models.colors import Color
from hikari.orm.models.colours import Colour
from hikari.orm.models.connections import Connection
from hikari.orm.models.embeds import Embed
from hikari.orm.models.emojis import Emoji
from hikari.orm.models.emojis import GuildEmoji
from hikari.orm.models.emojis import UnicodeEmoji
from hikari.orm.models.emojis import UnknownEmoji
from hikari.orm.models.gateway_bot import GatewayBot
from hikari.orm.models.gateway_bot import SessionStartLimit
from hikari.orm.models.guilds import Guild
from hikari.orm.models.guilds import GuildEmbed
from hikari.orm.models.guilds import PartialGuild
from hikari.orm.models.integrations import Integration
from hikari.orm.models.integrations import IntegrationAccount
from hikari.orm.models.integrations import PartialIntegration
from hikari.orm.models.invites import Invite
from hikari.orm.models.invites import InviteWithMetadata
from hikari.orm.models.invites import VanityURL
from hikari.orm.models.media import AbstractFile
from hikari.orm.models.media import Attachment
from hikari.orm.models.media import File
from hikari.orm.models.media import InMemoryFile
from hikari.orm.models.members import Member
from hikari.orm.models.messages import Message
from hikari.orm.models.messages import MessageActivity
from hikari.orm.models.messages import MessageApplication
from hikari.orm.models.messages import MessageCrosspost
from hikari.orm.models.overwrites import Overwrite
from hikari.orm.models.permissions import Permission
from hikari.orm.models.presences import Activity
from hikari.orm.models.presences import ActivityAssets
from hikari.orm.models.presences import ActivityParty
from hikari.orm.models.presences import ActivityTimestamps
from hikari.orm.models.presences import ActivityType
from hikari.orm.models.presences import MemberPresence
from hikari.orm.models.presences import Presence
from hikari.orm.models.presences import RichActivity
from hikari.orm.models.presences import Status
from hikari.orm.models.reactions import Reaction
from hikari.orm.models.roles import PartialRole
from hikari.orm.models.roles import Role
from hikari.orm.models.teams import Team
from hikari.orm.models.teams import TeamMember
from hikari.orm.models.users import BaseUser
from hikari.orm.models.users import OAuth2User
from hikari.orm.models.users import User
from hikari.orm.models.voices import VoiceRegion
from hikari.orm.models.voices import VoiceServer
from hikari.orm.models.voices import VoiceState
from hikari.orm.models.webhooks import Webhook
from hikari.orm.models.webhooks import WebhookUser

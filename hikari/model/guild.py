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
Guild models.
"""
from __future__ import annotations

__all__ = ()

import datetime
import enum
import typing

from hikari.model import base
from hikari.model import channel
from hikari.model import emoji
from hikari.model import permission
from hikari.model import role
from hikari.model import user
from hikari.model import voice

from hikari.utils import dateutils
from hikari.utils import transform


@base.dataclass()
class Guild(base.SnowflakeMixin):
    # We leave out widget and embed information as there isn't documentation to distinguish what each of them are for,
    # as they seem to overlap.
    # We omit:
    #    owner - we can infer this from the owner ID
    #    embed_enabled
    #    embed_channel_id
    #    widget_enabled
    #    widget_channel_id
    #    permissions - we can get this with a REST call if needed later.

    __slots__ = (
        "id",
        "_afk_channel_id",  # diff name to payload
        "_owner_id",  # diff name to payload
        "_voice_region_id",  # diff name to payload
        "_system_channel_id",  # diff name to payload
        "creator_application_id",  # imply if this is none that the guild is not bot-made.
        "name",
        "icon_hash",  # diff name to payload
        "splash_hash",  # diff name to payload
        "afk_timeout",
        "verification_level",
        "message_notification_level",  # diff name to payload
        "explicit_content_filter_level",  # diff name to payload
        "roles",
        "emojis",
        "features",
        "member_count",
        "mfa_level",
        "joined_at",
        "large",
        "unavailable",
        "voice_states",  # TODO: add guild_id key in.
        "members",
        "channels",
        "max_members",
        "vanity_url_code",
        "description",
        "banner_hash",  # diff name to payload
        "premium_tier",
        "premium_subscription_count",
        "system_channel_flags",  # not documented...
    )

    #: The guild ID.
    id: int
    #: Voice Channel ID for AFK users.
    _afk_channel_id: typing.Optional[int]
    #: The ID of the user who owns the guild.
    _owner_id: int
    #: The ID of the voice region for this guild.
    _voice_region_id: int
    #: System channel ID, if set.
    _system_channel_id: typing.Optional[int]
    #: The application ID of the creator of the guild. This is always `None` unless the guild was made by a bot.
    creator_application_id: typing.Optional[int]
    #: The name of the guild.
    name: str
    #: The hash of the icon of the guild.
    icon_hash: str
    #: The hash of the splash for the guild.
    splash_hash: str
    #: Permissions for our user in the guild, minus channel overrides, if the user is in the guild.
    my_permissions: typing.Optional[permission.Permission]
    #: Timeout before a user is classed as being AFK in seconds.
    afk_timeout: int
    #: Verification level for this guild.
    verification_level: VerificationLevel
    #: Default level for message notifications in this guild.
    message_notification_level: MessageNotificationLevel
    #: Explicit content filtering level.
    explicit_content_filter_level: ExplicitContentFilterLevel
    #: Roles in this guild.
    roles: typing.List[role.Role]
    #: Emojis in this guild.
    emojis: typing.List[emoji.Emoji]
    #: Enabled features in this guild.
    features: typing.List[typing.Union[GuildFeatures, str]]
    #: Number of members.
    member_count: typing.Optional[int]
    #: MFA level for this guild.
    mfa_level: MFALevel
    #: The date/time the bot user joined this guild, if it is in the guild.
    joined_at: typing.Optional[datetime.datetime]
    #: True if the guild is considered to be large, or False if it is not. This is defined by whatever the large
    #: threshold for the gateway is set to.
    large: bool
    #: True if the guild is considered to be unavailable, or False if it is not.
    unavailable: bool
    #: Voice states of users in the guild.
    voice_states: typing.List[voice.VoiceState]
    #: Members in the guild.
    members: typing.List[user.Member]
    #: Channels in the guild.
    channels: typing.List[channel.GuildChannel]
    #: Max members allowed in the guild.
    max_members: int
    #: Code for the vanity URL.
    vanity_url_code: typing.Optional[str]
    #: Guild description
    description: typing.Optional[str]
    #: Hash code for the banner.
    banner_hash: typing.Optional[str]
    #: Premium tier.
    premium_tier: PremiumTier
    #: Number of current Nitro boosts on this server.
    premium_subscription_count: int
    #: Describes what can the system channel can do.
    system_channel_flags: typing.Optional[SystemChannelFlags]


class SystemChannelFlags(enum.IntFlag):
    """
    Defines what is enabled to be displayed in the system channel.
    """

    #: Users joining.
    USER_JOIN = 1
    #: Nitro boosting.
    PREMIUM_SUBSCRIPTION = 2


class GuildFeatures(base.NamedEnumMixin, enum.Enum):
    """
    Features that a guild can provide.
    """

    # We could have done this as a bitfield of flags but Discord hasn't done a concrete definition of what these
    # can be, I had to read other libraries to see how they handled it...
    ANIMATED_ICON = enum.auto()
    BANNER = enum.auto()
    COMMERCE = enum.auto()
    DISCOVERABLE = enum.auto()
    INVITE_SPLASH = enum.auto()
    MORE_EMOJI = enum.auto()
    NEWS = enum.auto()
    LURKABLE = enum.auto()
    PARTNERED = enum.auto()
    VANITY_URL = enum.auto()
    VERIFIED = enum.auto()
    VIP_REGIONS = enum.auto()


class MessageNotificationLevel(enum.IntEnum):
    """Setting for message notifications."""

    ALL_MESSAGES = 0
    ONLY_MENTIONS = 1


class ExplicitContentFilterLevel(enum.IntEnum):
    """Setting for the explicit content filter."""

    DISABLED = 0
    MEMBERS_WITHOUT_ROLES = 1
    ALL_MEMBERS = 2


class MFALevel(enum.IntEnum):
    """Setting multi-factor authorization level."""

    NONE = 0
    ELEVATED = 1


class VerificationLevel(enum.IntEnum):
    """Setting for user verification."""

    #: Unrestricted
    NONE = 0
    #: Must have a verified email on their account.
    LOW = 1
    #: Must have been registered on Discord for more than 5 minutes.
    MEDIUM = 2
    #: (╯°□°）╯︵ ┻━┻ - must be a member of the server for longer than 10 minutes.
    HIGH = 3
    #: ┻━┻ミヽ(ಠ益ಠ)ﾉ彡┻━┻ - must have a verified phone number.
    VERY_HIGH = 4


class PremiumTier(enum.IntEnum):
    """Tier for Discord Nitro boosting in a server."""

    NONE = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


@base.dataclass()
class Ban:
    """
    A user that was banned, along with the reason for the ban.
    """

    __slots__ = ("reason", "user")

    reason: typing.Optional[str]
    user: user.User

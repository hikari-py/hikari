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

import dataclasses
import datetime
import enum
import typing

from hikari.core.model import base
from hikari.core.model import channel
from hikari.core.model import emoji
from hikari.core.components import state_registry
from hikari.core.model import permission
from hikari.core.model import role
from hikari.core.model import user
from hikari.core.utils import date_utils, auto_repr
from hikari.core.utils import transform


@dataclasses.dataclass()
class Guild(base.Snowflake, base.Volatile):
    """
    Implementation of a Guild.
    """

    # We leave out widget and embed information as there isn't documentation to distinguish what each of them are for,
    # as they seem to overlap.
    # We omit:
    #    owner - we can infer this from the owner ID
    #    embed_enabled
    #    embed_channel_id
    #    widget_enabled
    #    widget_channel_id

    __slots__ = (
        "_state",
        "id",
        "_afk_channel_id",
        "_owner_id",
        "_voice_region",
        "_system_channel_id",
        "creator_application_id",
        "name",
        "icon_hash",
        "splash_hash",
        "afk_timeout",
        "verification_level",
        "preferred_locale",
        "message_notification_level",
        "explicit_content_filter_level",
        "roles",
        "emojis",
        "features",
        "member_count",
        "mfa_level",
        "my_permissions",
        "joined_at",
        "large",
        "unavailable",
        "members",
        "channels",
        "max_members",
        "vanity_url_code",
        "description",
        "banner_hash",
        "premium_tier",
        "premium_subscription_count",
        "system_channel_flags",  # not documented...
    )

    _state: state_registry.StateRegistry
    _afk_channel_id: typing.Optional[int]
    _owner_id: int
    _system_channel_id: typing.Optional[int]
    _voice_region: typing.Optional[str]

    #: The guild ID.
    #:
    #: :type: :class:`int`
    id: int

    #: The application ID of the creator of the guild. This is always `None` unless the guild was made by a bot.
    #:
    #: :type: :class:`int` or `None`
    creator_application_id: typing.Optional[int]

    #: The name of the guild.
    #:
    #: :type: :class:`str`
    name: str

    #: The hash of the icon of the guild.
    #:
    #: :type: :class:`str`
    icon_hash: str

    #: The hash of the splash for the guild.
    #:
    #: :type: :class:`str`
    splash_hash: str

    #: Permissions for our user in the guild, minus channel overrides, if the user is in the guild.
    #:
    #: :type: :class:`hikari.core.model.permission.Permission` or `None`
    my_permissions: typing.Optional[permission.Permission]

    #: Timeout before a user is classed as being AFK in seconds.
    #:
    #: :type: :class:`int`
    afk_timeout: int

    #: Verification level for this guild.
    #:
    #: :type: :class:`hikari.core.model.guild.GuildVerificationLevel`
    verification_level: VerificationLevel

    #: The preferred locale of the guild. This is only populated if the guild has the
    # :attr:`hikari.core.model.guild.GuildFeature`
    #:
    #: :type: :class:`str` or `None`
    preferred_locale: typing.Optional[str]

    #: Default level for message notifications in this guild.
    #:
    #: :type: :class:`hikari.core.model.guild.NotificationLevel`
    message_notification_level: NotificationLevel

    #: Explicit content filtering level.
    #:
    #: :type: :class:`hikari.core.model.guild.ExplicitContentFilterLevel`
    explicit_content_filter_level: ExplicitContentFilterLevel

    #: Roles in this guild. Maps IDs to the role object they represent.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.core.model.role.Role` objects
    roles: typing.Dict[int, role.Role]

    #: Emojis in this guild. Maps IDs to the role object they represent.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.core.model.emoji.GuildEmoji` objects
    emojis: typing.Dict[int, emoji.GuildEmoji]

    #: Enabled features in this guild.
    #:
    #: :type: :class:`set` of :class:`hikari.core.model.guild.Feature` enum values.
    features: typing.Set[Feature]

    #: Number of members. Only stored if the information is actively available.
    #:
    #: :type: :class:`int` or `None`
    member_count: typing.Optional[int]

    #: MFA level for this guild.
    #:
    #: :type: :class:`hikari.core.model.guild.MFALevel`
    mfa_level: MFALevel

    #: The date/time the bot user joined this guild, or `None` if the bot is not in this guild.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    joined_at: typing.Optional[datetime.datetime]

    #: True if the guild is considered to be large, or False if it is not. This is defined by whatever the large
    #: threshold for the gateway is set to.
    #:
    #: :type: :class:`bool`
    large: bool

    #: True if the guild is considered to be unavailable, or False if it is not.
    #:
    #: :type: :class:`bool`
    unavailable: bool

    #: Members in the guild.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.core.model.user.Member` objects
    members: typing.Dict[int, user.Member]

    #: Channels in the guild.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.core.model.channel.GuildChannel` objects
    channels: typing.Dict[int, channel.GuildChannel]

    #: Max members allowed in the guild. This is a hard limit enforced by Discord.
    #:
    #: :type: :class:`int`
    max_members: int

    #: Code for the vanity URL, if the guild has one.
    #:
    #: :type: :class:`str` or `None`
    vanity_url_code: typing.Optional[str]

    #: Guild description, if the guild has one assigned. Currently this only applies to discoverable guilds.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.core.model.role.Role` objects
    description: typing.Optional[str]

    #: Hash code for the guild banner, if it has one.
    #:
    #: :type: :class:`str` or `None`
    banner_hash: typing.Optional[str]

    #: Premium tier.
    #:
    #: :type: :class:`hikari.core.model.guild.PremiumTier`
    premium_tier: PremiumTier

    #: Number of current Nitro boosts on this guild.
    #:
    #: :type: :class:`int`
    premium_subscription_count: int

    #: Describes what can the system channel can do.
    #:
    #: :type: :class:`hikari.core.model.guild.SystemChannelFlag`
    system_channel_flags: typing.Optional[SystemChannelFlag]

    __repr__ = auto_repr.repr_of("id", "name", "unavailable", "large", "member_count")

    def __init__(self, global_state, payload):
        self.id = transform.nullable_cast(payload.get("id"), int)
        self._state = global_state
        self.update_state(payload)

    def update_state(self, payload):
        self._afk_channel_id = transform.nullable_cast(payload.get("afk_channel_id"), int)
        self._owner_id = transform.nullable_cast(payload.get("owner_id"), int)
        self._voice_region = payload.get("region")
        self._system_channel_id = transform.nullable_cast(payload.get("system_channel_id"), int)
        self.creator_application_id = transform.nullable_cast(payload.get("application_id"), int)
        self.name = payload.get("name")
        self.icon_hash = payload.get("icon")
        self.splash_hash = payload.get("splash")
        self.afk_timeout = payload.get("afk_timeout", float("inf"))
        self.verification_level = transform.try_cast(payload.get("verification_level"), VerificationLevel)
        self.preferred_locale = payload.get("preferred_locale")
        self.message_notification_level = transform.try_cast(
            payload.get("default_message_notifications"), NotificationLevel
        )
        self.explicit_content_filter_level = transform.try_cast(
            payload.get("explicit_content_filter"), ExplicitContentFilterLevel
        )
        self.roles = transform.snowflake_map(self._state.parse_role(r, self.id) for r in payload.get("roles", ()))
        self.emojis = transform.snowflake_map(self._state.parse_emoji(e, self.id) for e in payload.get("emojis", ()))
        self.features = {transform.try_cast(f, Feature.from_discord_name) for f in payload.get("features", ())}
        self.member_count = transform.nullable_cast(payload.get("member_count"), int)
        self.mfa_level = transform.try_cast(payload.get("mfa_level"), MFALevel)
        self.my_permissions = permission.Permission(payload.get("permissions", 0))
        self.joined_at = transform.nullable_cast(payload.get("joined_at"), date_utils.parse_iso_8601_datetime)
        self.large = payload.get("large", False)
        self.unavailable = payload.get("unavailable", False)
        self.members = transform.snowflake_map(self._state.parse_member(m, self.id) for m in payload.get("members", ()))
        self.channels = transform.snowflake_map(self._parse_channel(c) for c in payload.get("channels", ()))
        self.max_members = payload.get("max_members", 0)
        self.vanity_url_code = payload.get("vanity_url_code")
        self.description = payload.get("description")
        self.banner_hash = payload.get("banner")
        self.premium_tier = transform.try_cast(payload.get("premium_tier"), PremiumTier)
        self.premium_subscription_count = payload.get("premium_subscription_count", 0)
        self.system_channel_flags = transform.try_cast(payload.get("system_channel_flags"), SystemChannelFlag)

    def _parse_channel(self, channel):
        # Sometimes this key is missing...
        channel["guild_id"] = self.id
        return self._state.parse_channel(channel)


class SystemChannelFlag(enum.IntFlag):
    """
    Defines what is enabled to be displayed in the system channel.
    """

    #: Display a message about new users joining.
    USER_JOIN = 1
    #: Display a message when the guild is Nitro boosted.
    PREMIUM_SUBSCRIPTION = 2


class Feature(base.NamedEnum, enum.Enum):
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


class NotificationLevel(enum.IntEnum):
    """Setting for message notifications."""

    #: Notify users when any message is sent.
    ALL_MESSAGES = 0

    #: Only notify users when they are @mentioned.
    ONLY_MENTIONS = 1


class ExplicitContentFilterLevel(enum.IntEnum):
    """Setting for the explicit content filter."""

    #: No explicit content filter.
    DISABLED = 0

    #: Filter posts from anyone without a role.
    MEMBERS_WITHOUT_ROLES = 1

    #: Filter all posts.
    ALL_MEMBERS = 2


class MFALevel(enum.IntEnum):
    """Setting multi-factor authorization level."""

    #: No MFA requirement.
    NONE = 0

    #: MFA requirement.
    ELEVATED = 1


class VerificationLevel(enum.IntEnum):
    """Setting for user verification."""

    #: Unrestricted
    NONE = 0

    #: Must have a verified email on their account.
    LOW = 1

    #: Must have been registered on Discord for more than 5 minutes.
    MEDIUM = 2

    #: (╯°□°）╯︵ ┻━┻ - must be a member of the guild for longer than 10 minutes.
    HIGH = 3

    #: ┻━┻ミヽ(ಠ益ಠ)ﾉ彡┻━┻ - must have a verified phone number.
    VERY_HIGH = 4


class PremiumTier(enum.IntEnum):
    """Tier for Discord Nitro boosting in a guild."""

    #: No Nitro boosts.
    NONE = 0

    #: Level 1 Nitro boost.
    TIER_1 = 1

    #: Level 2 Nitro boost.
    TIER_2 = 2

    #: Level 3 Nitro boost.
    TIER_3 = 3


@dataclasses.dataclass()
class Ban:
    """
    A user that was banned, along with the reason for the ban.
    """

    __slots__ = ("reason", "user")

    #: The reason for the ban, if there is one given.
    #:
    #: :type: :class:`str` or `None`
    reason: typing.Optional[str]

    #: The user who is banned.
    #:
    #: :type: :class:`hikari.core.model.user.User`
    user: user.User

    __repr__ = auto_repr.repr_of("user", "reason")

    def __init__(self, global_state: state_registry.StateRegistry, payload: dict):
        self.reason = payload.get("reason")
        self.user = global_state.parse_user(payload.get("user"))


__all__ = [
    "Guild",
    "SystemChannelFlag",
    "Feature",
    "NotificationLevel",
    "ExplicitContentFilterLevel",
    "MFALevel",
    "VerificationLevel",
    "PremiumTier",
    "Ban",
]

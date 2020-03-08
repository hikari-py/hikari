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
Guild models.
"""
from __future__ import annotations

__all__ = [
    "PartialGuild",
    "Guild",
    "SystemChannelFlag",
    "Feature",
    "DefaultMessageNotificationsLevel",
    "ExplicitContentFilterLevel",
    "MFALevel",
    "VerificationLevel",
    "PremiumTier",
    "Ban",
    "WidgetStyle",
    "VerificationLevelLikeT",
    "WidgetStyleLikeT",
    "GuildLikeT",
    "GuildEmbed",
]

import dataclasses
import enum
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.internal_utilities import reprs
from hikari.internal_utilities import transformations
from hikari.internal_utilities import type_hints
from hikari.orm.models import bases
from hikari.orm.models import permissions

if typing.TYPE_CHECKING:
    import datetime

    from hikari.orm import fabric
    from hikari.orm.models import channels
    from hikari.orm.models import emojis
    from hikari.orm.models import members
    from hikari.orm.models import roles
    from hikari.orm.models import users
    from hikari.orm.models import voices


class PartialGuild(bases.BaseModel, bases.SnowflakeMixin):
    """
    Implementation of a partial guild object, found in places like invites.
    """

    __slots__ = (
        "id",
        "name",
        "splash_hash",
        "banner_hash",
        "description",
        "icon_hash",
        "features",
        "verification_level",
        "vanity_url_code",
    )

    #: The guild ID.
    #:
    #: :type: :class:`int`
    id: int

    #: The name of the guild.
    #:
    #: :type: :class:`str`
    name: str

    #: The hash of the splash for the guild.
    #:
    #: :type: :class:`str`
    splash_hash: str

    #: Hash code for the guild banner, if it has one.
    #:
    #: :type: :class:`str` or `None`
    banner_hash: type_hints.Nullable[str]

    #: Guild description, if the guild has one assigned. Currently this only applies to discoverable guilds.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.orm.models.roles.Role` objects
    description: type_hints.Nullable[str]

    #: The hash of the icon of the guild.
    #:
    #: :type: :class:`str`
    icon_hash: str

    #: Enabled features in this guild.
    #:
    #: :type: :class:`set` of :class:`hikari.orm.models.guilds.Feature` enum values.
    features: typing.Set[Feature]

    #: Verification level for this guild.
    #:
    #: :type: :class:`hikari.orm.models.guilds.GuildVerificationLevel`
    verification_level: VerificationLevel

    #: Code for the vanity URL, if the guild has one.
    #:
    #: :type: :class:`str` or `None`
    vanity_url_code: type_hints.Nullable[str]

    __repr__ = reprs.repr_of("id", "name")

    def __init__(self, payload: type_hints.JSONObject) -> None:
        self.id = transformations.nullable_cast(payload.get("id"), int)
        self.update_state(payload)  # lgtm [py/init-calls-subclass]

    def update_state(self, payload: type_hints.JSONObject) -> None:
        self.name = payload.get("name")
        self.icon_hash = payload.get("icon")
        self.splash_hash = payload.get("splash")
        self.verification_level = transformations.try_cast(payload.get("verification_level"), VerificationLevel)
        self.features = {
            transformations.try_cast(f, Feature.from_discord_name)
            for f in payload.get("features", containers.EMPTY_SEQUENCE)
        }
        self.vanity_url_code = payload.get("vanity_url_code")
        self.description = payload.get("description")
        self.banner_hash = payload.get("banner")


class Guild(PartialGuild, bases.BaseModelWithFabric):
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
        "_fabric",
        "shard_id",
        "afk_channel_id",
        "owner_id",
        "voice_region",
        "system_channel_id",
        "creator_application_id",
        "afk_timeout",
        "preferred_locale",
        "message_notification_level",
        "explicit_content_filter_level",
        "roles",
        "emojis",
        "member_count",
        "voice_states",
        "mfa_level",
        "my_permissions",
        "joined_at",
        "is_large",
        "is_unavailable",
        "members",
        "channels",
        "max_members",
        "premium_tier",
        "premium_subscription_count",
        "system_channel_flags",
    )

    __copy_by_ref__ = ("roles", "emojis", "members", "channels")

    #: The shard ID that this guild is being served by.
    #:
    #: If the bot is not sharded, this will be 0.
    #:
    #: :type: :class:`int`
    shard_id: int

    #: The AFK channel ID.
    #:
    #: :type: :class:`int`
    afk_channel_id: type_hints.Nullable[int]

    #: The owner's ID.
    #:
    #: :type: :class:`int`
    owner_id: int

    #: The system channel ID.
    #:
    #: :type: :class:`int`
    system_channel_id: type_hints.Nullable[int]

    #: The voice region.
    #:
    #: :type: :class:`str`
    voice_region: type_hints.Nullable[str]

    #: The application ID of the creator of the guild. This is always `None` unless the guild was made by a bot.
    #:
    #: :type: :class:`int` or `None`
    creator_application_id: type_hints.Nullable[int]

    #: Permissions for our user in the guild, minus channel overrides, if the user is in the guild.
    #:
    #: :type: :class:`hikari.orm.models.permissions.Permission` or `None`
    my_permissions: type_hints.Nullable[permissions.Permission]

    #: Timeout before a user is classed as being AFK in seconds.
    #:
    #: :type: :class:`int`
    afk_timeout: int

    #: The preferred locale of the guild. This is only populated if the guild has the
    #: :attr:`hikari.orm.models.guild.GuildFeature`
    #:
    #: :type: :class:`str` or `None`
    preferred_locale: type_hints.Nullable[str]

    #: Default level for message notifications in this guild.
    #:
    #: :type: :class:`hikari.orm.models.guilds.NotificationLevel`
    message_notification_level: DefaultMessageNotificationsLevel

    #: Explicit content filtering level.
    #:
    #: :type: :class:`hikari.orm.models.guilds.ExplicitContentFilterLevel`
    explicit_content_filter_level: ExplicitContentFilterLevel

    #: Roles in this guild. Maps IDs to the role object they represent.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.orm.models.roles.Role` objects
    roles: typing.MutableMapping[int, roles.Role]

    #: Emojis in this guild. Maps IDs to the role object they represent.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.orm.models.emojis.GuildEmoji` objects
    emojis: typing.MutableMapping[int, emojis.GuildEmoji]

    #: Number of members. Only stored if the information is actively available.
    #:
    #: :type: :class:`int` or `None`
    member_count: type_hints.Nullable[int]

    #: MFA level for this guild.
    #:
    #: :type: :class:`hikari.orm.models.guilds.MFALevel`
    mfa_level: MFALevel

    #: The date/time the bot user joined this guild, or `None` if the bot is not in this guild.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    joined_at: type_hints.Nullable[datetime.datetime]

    #: True if the guild is considered to be large, or False if it is not. This is defined by whatever the large
    #: threshold for the gateway is set to.
    #:
    #: :type: :class:`bool`
    is_large: bool

    #: True if the guild is considered to be unavailable, or False if it is not.
    #:
    #: :type: :class:`bool`
    is_unavailable: bool

    #: The active voice states in the guild, mapped by their user's id.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.models.orm.voices.VoiceState`
    voice_states: typing.MutableMapping[int, voices.VoiceState]

    #: Members in the guild.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.orm.models.members.Member` objects
    members: typing.MutableMapping[int, members.Member]

    #: Channels in the guild.
    #:
    #: :type: :class:`dict` mapping :class:`int` to :class:`hikari.orm.models.channels.GuildChannel` objects
    channels: typing.MutableMapping[int, channels.GuildChannel]

    #: Max members allowed in the guild. This is a hard limit enforced by Discord.
    #:
    #: :type: :class:`int`
    max_members: int

    #: Premium tier.
    #:
    #: :type: :class:`hikari.orm.models.guilds.PremiumTier`
    premium_tier: PremiumTier

    #: Number of current Nitro boosts on this guild.
    #:
    #: :type: :class:`int`
    premium_subscription_count: int

    #: Describes what can the system channel can do.
    #:
    #: :type: :class:`hikari.orm.models.guilds.SystemChannelFlag`
    system_channel_flags: type_hints.Nullable[SystemChannelFlag]

    __repr__ = reprs.repr_of("id", "name", "is_unavailable", "is_large", "member_count", "shard_id")

    def __init__(self, fabric_obj: fabric.Fabric, payload: type_hints.JSONObject) -> None:
        self._fabric = fabric_obj
        self.channels = {}
        self.emojis = {}
        self.members = {}
        self.roles = {}
        self.voice_states = {}
        super().__init__(payload)
        self.shard_id = transformations.guild_id_to_shard_id(self.id, self._fabric.shard_count)

    def update_state(self, payload: type_hints.JSONObject) -> None:
        super().update_state(payload)
        self.afk_channel_id = transformations.nullable_cast(payload.get("afk_channel_id"), int)
        self.owner_id = transformations.nullable_cast(payload.get("owner_id"), int)
        self.voice_region = payload.get("region")
        self.system_channel_id = transformations.nullable_cast(payload.get("system_channel_id"), int)
        self.creator_application_id = transformations.nullable_cast(payload.get("application_id"), int)
        self.afk_timeout = payload.get("afk_timeout", float("inf"))
        self.preferred_locale = payload.get("preferred_locale")
        self.message_notification_level = transformations.try_cast(
            payload.get("default_message_notifications"), DefaultMessageNotificationsLevel
        )
        self.explicit_content_filter_level = transformations.try_cast(
            payload.get("explicit_content_filter"), ExplicitContentFilterLevel
        )
        self.roles = transformations.id_map(
            self._fabric.state_registry.parse_role(r, self) for r in payload.get("roles", containers.EMPTY_SEQUENCE)
        )
        self.emojis = transformations.id_map(
            self._fabric.state_registry.parse_emoji(e, self) for e in payload.get("emojis", containers.EMPTY_SEQUENCE)
        )
        self.member_count = transformations.nullable_cast(payload.get("member_count"), int)

        voice_state_objs = (
            self._fabric.state_registry.parse_voice_state(vs, self)
            for vs in payload.get("voice_states", containers.EMPTY_SEQUENCE)
        )
        self.voice_states = {vs.user_id: vs for vs in voice_state_objs}
        self.mfa_level = transformations.try_cast(payload.get("mfa_level"), MFALevel)
        self.my_permissions = permissions.Permission(payload.get("permissions", 0))
        self.joined_at = transformations.nullable_cast(payload.get("joined_at"), dates.parse_iso_8601_ts)
        self.is_large = payload.get("large", False)
        self.is_unavailable = payload.get("unavailable", False)
        self.members = transformations.id_map(
            self._fabric.state_registry.parse_member(m, self) for m in payload.get("members", containers.EMPTY_SEQUENCE)
        )
        self.channels = transformations.id_map(
            self._fabric.state_registry.parse_channel(c, self)
            for c in payload.get("channels", containers.EMPTY_SEQUENCE)
        )
        self.max_members = payload.get("max_members", 0)
        self.premium_tier = transformations.try_cast(payload.get("premium_tier"), PremiumTier)
        self.premium_subscription_count = payload.get("premium_subscription_count", 0)
        self.system_channel_flags = transformations.try_cast(payload.get("system_channel_flags"), SystemChannelFlag)


class SystemChannelFlag(enum.IntFlag):
    """
    Defines what is enabled to be displayed in the system channel.

    Note:
        These flags are inverted so if they're set then the relevant setting has been disabled.
    """

    #: Display a message about new users joining.
    USER_JOIN = 1
    #: Display a message when the guild is Nitro boosted.
    PREMIUM_SUBSCRIPTION = 2


class Feature(bases.NamedEnumMixin, enum.Enum):
    """
    Features that a guild can provide.
    """
    #: Guild has access to set an animated guild icon.
    ANIMATED_ICON = enum.auto()
    #: Guild has access to set a guild banner image.
    BANNER = enum.auto()
    #: Guild has access to use commerce features (i.e. create store channels).
    COMMERCE = enum.auto()
    #: Guild is able to be discovered in the directory.
    DISCOVERABLE = enum.auto()
    #: Guild is able to be featured in the directory.
    FEATURABLE = enum.auto()
    #: Guild has access to set an invite splash background.
    INVITE_SPLASH = enum.auto()
    MORE_EMOJI = enum.auto()
    #: Guild has access to create news channels.
    NEWS = enum.auto()
    LURKABLE = enum.auto()
    #: Guild is partnered.
    PARTNERED = enum.auto()
    #: Guild is public, go figure.
    PUBLIC = enum.auto()
    #: Guild cannot be public. Who would have guessed?
    PUBLIC_DISABLED = enum.auto()
    #: Guild has access to set a vanity URL.
    VANITY_URL = enum.auto()
    #: Guild is verified.
    VERIFIED = enum.auto()
    #: Guild has access to set 384kbps bitrate in voice (previously VIP voice servers).
    VIP_REGIONS = enum.auto()


class DefaultMessageNotificationsLevel(bases.BestEffortEnumMixin, enum.IntEnum):
    """Setting for message notifications."""

    #: Notify users when any message is sent.
    ALL_MESSAGES = 0

    #: Only notify users when they are @mentioned.
    ONLY_MENTIONS = 1


class ExplicitContentFilterLevel(bases.BestEffortEnumMixin, enum.IntEnum):
    """Setting for the explicit content filter."""

    #: No explicit content filter.
    DISABLED = 0

    #: Filter posts from anyone without a role.
    MEMBERS_WITHOUT_ROLES = 1

    #: Filter all posts.
    ALL_MEMBERS = 2


class MFALevel(bases.BestEffortEnumMixin, enum.IntEnum):
    """Setting multi-factor authorization level."""

    #: No MFA requirement.
    NONE = 0

    #: MFA requirement.
    ELEVATED = 1


class VerificationLevel(bases.BestEffortEnumMixin, enum.IntEnum):
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


class PremiumTier(bases.BestEffortEnumMixin, enum.IntEnum):
    """Tier for Discord Nitro boosting in a guild."""

    #: No Nitro boosts.
    NONE = 0

    #: Level 1 Nitro boost.
    TIER_1 = 1

    #: Level 2 Nitro boost.
    TIER_2 = 2

    #: Level 3 Nitro boost.
    TIER_3 = 3


class Ban(bases.BaseModel):
    """
    A user that was banned, along with the reason for the ban.
    """

    __slots__ = ("reason", "user")

    #: The reason for the ban, if there is one given.
    #:
    #: :type: :class:`str` or `None`
    reason: type_hints.Nullable[str]

    #: The user who is banned.
    #:
    #: :type: :class:`hikari.orm.models.users.User`
    user: users.BaseUser

    __repr__ = reprs.repr_of("user", "reason")

    def __init__(self, fabric_obj: fabric.Fabric, payload: type_hints.JSONObject) -> None:
        self.reason = payload.get("reason")
        self.user = fabric_obj.state_registry.parse_user(payload.get("user"))


@dataclasses.dataclass()
class GuildEmbed(bases.BaseModel, bases.MarshalMixin):
    """
    Implementation of the guild embed object.
    """

    __slots__ = ("enabled", "channel_id")

    #: Whether the embed is enabled.
    #:
    #: :type: :class:`bool`
    enabled: bool

    #: The ID of the embed's target channel if set.
    #:
    #: :type: :class:`int` or `None`
    channel_id: type_hints.Nullable[int]

    __repr__ = reprs.repr_of("enabled", "channel_id")

    def __init__(self, *, enabled: bool = False, channel_id: int = None) -> None:
        self.enabled = enabled
        self.channel_id = transformations.nullable_cast(channel_id, int)


class WidgetStyle(bases.BestEffortEnumMixin, str, enum.Enum):
    """
    Valid styles of widget for a guild.
    """

    #: The default shield style. This will produce a widget PNG like this:
    #:
    #: .. image:: https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=shield
    #:     :alt: A preview of the shield style.
    SHIELD = "shield"

    #: The `banner1` style. This will produce a widget PNG like this:
    #:
    #: .. image:: https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=banner1
    #:     :alt: A preview of the banner1 style.
    BANNER_1 = "banner1"

    #: The `banner2` style. This will produce a widget PNG like this:
    #:
    #: .. image:: https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=banner2
    #:     :alt: A preview of the banner2 style.
    BANNER_2 = "banner2"

    #: The `banner3` style. This will produce a widget PNG like this:
    #:
    #: .. image:: https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=banner3
    #:     :alt: A preview of the banner3 style.
    BANNER_3 = "banner3"

    #: The `banner4` style. This will produce a widget PNG like this:
    #:
    #: .. image:: https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=banner4
    #:     :alt: A preview of the banner4 style.
    BANNER_4 = "banner4"


DefaultMessageNotificationsLevelLikeT = typing.Union[int, DefaultMessageNotificationsLevel]
ExplicitContentFilterLevelLikeT = typing.Union[int, ExplicitContentFilterLevel]
VerificationLevelLikeT = typing.Union[int, VerificationLevel]
WidgetStyleLikeT = typing.Union[str, WidgetStyle]
GuildLikeT = typing.Union[bases.RawSnowflakeT, Guild]

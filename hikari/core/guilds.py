#!/usr/bin/env python3
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
"""Components and entities that are used to describe guilds on Discord.
"""

__all__ = [
    "GuildEmoji",
    "GuildChannel",
    "GuildTextChannel",
    "GuildNewsChannel",
    "GuildStoreChannel",
    "GuildVoiceChannel",
    "GuildCategory",
    "GuildRole",
    "GuildFeature",
    "GuildSystemChannelFlag",
    "GuildMessageNotificationsLevel",
    "GuildExplicitContentFilterLevel",
    "GuildMFALevel",
    "GuildVerificationLevel",
    "GuildPremiumTier",
    "Guild",
    "GuildMember",
    "GuildMemberPresence",
    "GuildIntegration",
    "GuildMemberBan",
]

import datetime
import enum
import typing

import attr

from hikari.core import channels
from hikari.core import entities
from hikari.core import messages
from hikari.core import permissions as permissions_
from hikari.core import snowflakes
from hikari.core import users


@attr.s(slots=False)
class GuildEmoji(snowflakes.UniqueEntity, messages.Emoji):
    ...


@attr.s(slots=False)
class GuildChannel(channels.Channel):
    """The base for anything that is a guild channel."""


@attr.s(slots=False)
class GuildTextChannel(GuildChannel):
    ...


@attr.s(slots=False)
class GuildVoiceChannel(GuildChannel):
    ...


@attr.s(slots=False)
class GuildCategory(GuildChannel):
    ...


@attr.s(slots=False)
class GuildStoreChannel(GuildChannel):
    ...


@attr.s(slots=False)
class GuildNewsChannel(GuildChannel):
    ...


class GuildExplicitContentFilterLevel(enum.IntEnum):
    """Represents the explicit content filter setting for a guild."""

    #: No explicit content filter.
    DISABLED = 0

    #: Filter posts from anyone without a role.
    MEMBERS_WITHOUT_ROLES = 1

    #: Filter all posts.
    ALL_MEMBERS = 2


class GuildFeature(str, enum.Enum):
    """Features that a guild can provide."""

    #: Guild has access to set an animated guild icon.
    ANIMATED_ICON = "ANIMATED_ICON"
    #: Guild has access to set a guild banner image.
    BANNER = "BANNER"
    #: Guild has access to use commerce features (i.e. create store channels).
    COMMERCE = "COMMERCE"
    #: Guild is able to be discovered in the directory.
    DISCOVERABLE = "DISCOVERABLE"
    #: Guild is able to be featured in the directory.
    FEATURABLE = "FEATURABLE"
    #: Guild has access to set an invite splash background.
    INVITE_SPLASH = "INVITE_SPLASH"
    #: More emojis can be hosted in this guild than normal.
    MORE_EMOJI = "MORE_EMOJI"
    #: Guild has access to create news channels.
    NEWS = "NEWS"
    #: People can view channels in this guild without joining.
    LURKABLE = "LURKABLE"
    #: Guild is partnered.
    PARTNERED = "PARTNERED"
    #: Guild is public, go figure.
    PUBLIC = "PUBLIC"
    #: Guild cannot be public. Who would have guessed?
    PUBLIC_DISABLED = "PUBLIC_DISABLED"
    #: Guild has access to set a vanity URL.
    VANITY_URL = "VANITY_URL"
    #: Guild is verified.
    VERIFIED = "VERIFIED"
    #: Guild has access to set 384kbps bitrate in voice (previously
    #: VIP voice servers).
    VIP_REGIONS = "VIP_REGIONS"


class GuildMessageNotificationsLevel(enum.IntEnum):
    """Represents the default notification level for new messages in a guild."""

    #: Notify users when any message is sent.
    ALL_MESSAGES = 0

    #: Only notify users when they are @mentioned.
    ONLY_MENTIONS = 1


class GuildMFALevel(enum.IntEnum):
    """Represents the multi-factor authorization requirement for a guild."""

    #: No MFA requirement.
    NONE = 0

    #: MFA requirement.
    ELEVATED = 1


class GuildPremiumTier(enum.IntEnum):
    """Tier for Discord Nitro boosting in a guild."""

    #: No Nitro boosts.
    NONE = 0

    #: Level 1 Nitro boost.
    TIER_1 = 1

    #: Level 2 Nitro boost.
    TIER_2 = 2

    #: Level 3 Nitro boost.
    TIER_3 = 3


class GuildSystemChannelFlag(enum.IntFlag):
    """Defines which features are suppressed in the system channel."""

    #: Display a message about new users joining.
    SUPPRESS_USER_JOIN = 1
    #: Display a message when the guild is Nitro boosted.
    SUPPRESS_PREMIUM_SUBSCRIPTION = 2


class GuildVerificationLevel(enum.IntEnum):
    """Represents the level of verification a user needs to provide for their
    account before being allowed to participate in a guild."""

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


@attr.s(slots=True, auto_attribs=True)
class GuildMember(snowflakes.UniqueEntity):
    user: users.User


@attr.s(slots=True, auto_attribs=True)
class GuildMemberPresence(entities.HikariEntity):
    ...


@attr.s(slots=True)
class GuildIntegration(snowflakes.UniqueEntity):
    ...


@attr.s(slots=True)
class GuildMemberBan(entities.HikariEntity):
    ...


@attr.s(slots=True)
class GuildRole(entities.HikariEntity):
    ...


@attr.s(slots=True, auto_attribs=True)
class Guild(snowflakes.UniqueEntity):
    """A representation of a guild on Discord.

    Notes
    -----

    If a guild object is considered to be unavailable, then the state of any
    other fields other than the :attr:`is_unavailable` and :attr:`id` members
    may be ``None``, outdated, or incorrect. If a guild is unavailable, then
    the contents of any other fields should be ignored.
    """

    #: The name of the guild.
    #:
    #: :type: :class:`str`
    name: str

    #: The hash for the guild icon, if there is one.
    #:
    #: :type: :class:`str`, optional
    icon_hash: typing.Optional[str]

    #: The hash of the splash for the guild, if there is one.
    #:
    #: :type: :class:`str`, optional
    splash_hash: typing.Optional[str]

    #: The hash of the discovery splash for the guild, if there is one.
    #:
    #: :type: :class:`str`, optional
    discovery_splash: typing.Optional[str]

    #: The ID of the owner of this guild.
    #:
    #: :type: :class:`snowflakes.Snowflake`
    owner_id: snowflakes.Snowflake

    #: The guild level permissions that apply to the bot user.
    #:
    #: :type: :class:`hikari.core.permissions.Permission`
    my_permissions: permissions_.Permission

    #: The voice region for the guild.
    #:
    #: :type: :class:`str`
    region: str

    #: The ID for the channel that AFK voice users get sent to, if set for the
    #: guild.
    #:
    #: :type: :class:`snowflakes.Snowflake`, optional
    afk_channel_id: typing.Optional[snowflakes.Snowflake]

    #: How long a voice user has to be AFK for before they are classed as being
    #: AFK and are moved to the AFK channel (:attr:`afk_channel_id`).
    #:
    #: :type: :class:`datetime.timedelta`
    afk_timeout: datetime.timedelta

    # TODO: document when this is not specified.
    # FIXME: do we need a field for this, or can we infer it from the `embed_channel_id`?
    #: Defines if the guild embed is enabled or not. This information may not
    #: be present, in which case, it will be ``None`` instead.
    #:
    #: :type: :class:`bool`, optional
    is_embed_enabled: typing.Optional[bool]

    #: The channel ID that the guild embed will generate an invite to, if
    #: enabled for this guild. If not enabled, it will be ``None``.
    #:
    #: :type: :class:`snowflakes.Snowflake`, optional
    embed_channel_id: typing.Optional[snowflakes.Snowflake]

    #: The verification level required for a user to participate in this guild.
    #:
    #: :type: :class:`GuildVerificationLevel`
    verification_level: GuildVerificationLevel

    #: The default setting for message notifications in this guild.
    #:
    #: :type: :class:`GuildMessageNotificationsLevel`
    default_message_notifications: GuildMessageNotificationsLevel

    #: The setting for the explicit content filter in this guild.
    #:
    #: :type: :class:`GuildExplicitContentFilterLevel`
    explicit_content_filter: GuildExplicitContentFilterLevel

    #: The roles in this guild, represented as a mapping of ID to role object.
    #:
    #: :type: :class:`typing.Mapping` [ :class:`snowflakes.Snowflake`, :class:`GuildRole` ]
    roles: typing.Mapping[snowflakes.Snowflake, GuildRole]

    #: The emojis that this guild provides, represented as a mapping of ID to
    #: emoji object.
    #:
    #: :type: :class:`typing.Mapping` [ :class:`snowflakes.Snowflake`, :class:`GuildEmoji` ]
    emojis: typing.Mapping[snowflakes.Snowflake, GuildEmoji]

    #: A set of the features in this guild.
    #:
    #: :type: :class:`typing.Set` [ :class:`GuildFeature` ]
    features: typing.Set[GuildFeature]

    #: The required MFA level for users wishing to participate in this guild.
    #:
    #: :type: :class:`GuildMFALevel`
    mfa_level: GuildMFALevel

    #: The ID of the application that created this guild, if it was created by
    #: a bot. If not, this is always ``None``.
    #:
    #: :type: :class:`snowflakes.Snowflake`, optional
    application_id: typing.Optional[snowflakes.Snowflake]

    # TODO: document in which cases this information is not available.
    #: Describes whether the guild widget is enabled or not. If this information
    #: is not present, this will be ``None``.
    #:
    #: :type: :class:`bool`, optional
    is_widget_enabled: typing.Optional[bool]

    #: The channel ID that the widget's generated invite will send the user to,
    #: if enabled. If this information is unavailable, this will be ``None``.
    #:
    #: :type: :class:`snowflakes.Snowflake`, optional
    widget_channel_id: typing.Optional[snowflakes.Snowflake]

    #: The ID of the system channel (where welcome messages and Nitro boost
    #: messages are sent), or ``None`` if it is not enabled.
    #: :type: :class:`snowflakes.Snowflake`, optional
    system_channel_id: typing.Optional[snowflakes.Snowflake]

    #: Flags for the guild system channel to describe which notification
    #: features are suppressed.
    #:
    #: :type: :class:`GuildSystemChannelFlag`
    system_channel_flags: GuildSystemChannelFlag

    #: The ID of the channel where guilds with the :obj:`GuildFeature.PUBLIC`
    #: :attr:`features` display rules and guidelines. If the
    #: :obj:`GuildFeature.PUBLIC` feature is not defined, then this is ``None``.
    #:
    #: :type: :class:`snowflakes.Snowflake`, optional
    rules_channel_id: typing.Optional[snowflakes.Snowflake]

    #: The date and time that the bot user joined this guild.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: :type: :class:`datetime.datetime`, optional
    joined_at: typing.Optional[datetime.datetime]

    #: Whether the guild is considered to be large or not.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: The implications of a large guild are that presence information will
    #: not be sent about members who are offline or invisible.
    #:
    #: :type: :class:`bool`, optional
    is_large: typing.Optional[bool]

    #: Whether the guild is unavailable or not.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: An unavailable guild cannot be interacted with, and most information may
    #: be outdated or missing if that is the case.
    is_unavailable: typing.Optional[bool]

    #: The number of members in this guild.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: :type: :class:`int`, optional
    member_count: typing.Optional[int]

    #: A mapping of ID to the corresponding guild members in this guild.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: Additionally, any offline members may not be included here, especially
    #: if there are more members than the large threshold set for the gateway
    #: this object was send with.
    #:
    #: This information will only be updated if your shards have the correct
    #: intents set for any update events.
    #:
    #: Essentially, you should not trust the information here to be a full
    #: representation. If you need complete accurate information, you should
    #: query the members using the appropriate API call instead.
    #:
    #: :type: :class:`typing.Mapping` [ :class:`snowflakes.Snowflake`, :class:`GuildMember` ], optional
    members: typing.Optional[typing.Mapping[snowflakes.Snowflake, GuildMember]]

    #: A mapping of ID to the corresponding guild channels in this guild.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: Additionally, any channels that you lack permissions to see will not be
    #: defined here.
    #:
    #: This information will only be updated if your shards have the correct
    #: intents set for any update events.
    #:
    #: To retrieve a list of channels in any other case, you should make an
    #: appropriate API call to retrieve this information.
    #:
    #: :type: :class:`typing.Mapping` [ :class:`snowflakes.Snowflake`, :class:`GuildChannel` ], optional
    channels: typing.Optional[typing.Mapping[snowflakes.Snowflake, GuildChannel]]

    #: A mapping of member ID to the corresponding presence information for
    #: the given member, if available.
    #:
    #: This information is only available if the guild was sent via a
    #: `GUILD_CREATE` event. If the guild is received from any other place,
    #: this will always be ``None``.
    #:
    #: Additionally, any channels that you lack permissions to see will not be
    #: defined here.
    #:
    #: This information will only be updated if your shards have the correct
    #: intents set for any update events.
    #:
    #: To retrieve a list of presences in any other case, you should make an
    #: appropriate API call to retrieve this information.
    #:
    #: :type: :class:`typing.Mapping` [ :class:`snowflakes.Snowflake`, :class:`GuildMemberPresence` ], optional
    presences: typing.Optional[typing.Mapping[snowflakes.Snowflake, GuildMemberPresence]]

    #: The maximum number of presences for the guild. If this is ``None``, then
    #: the default value is used (currently 5000).
    #:
    #: :type: :class:`int`, optional
    max_presences: typing.Optional[int]

    #: The maximum number of members allowed in this guild.
    #:
    #: This information may not be present, in which case, it will be ``None``.
    #:
    #: :type: :class:`int`, optional
    max_members: typing.Optional[int]

    #: The vanity URL code for the guild's vanity URL.
    #: This is only present if :obj:`GuildFeatures.VANITY_URL` is in the
    #: :attr:`features` for this guild. If not, this will always be ``None``.
    #:
    #: :type: :class:`str`, optional
    vanity_url_code: typing.Optional[str]

    #: The guild's description.
    #:
    #: This is only present if certain :attr:`features` are set in this guild.
    #: Otherwise, this will always be ``None``. For all other purposes, it is
    #: ``None``.
    #:
    #: :type: :class:`str`, optional
    description: typing.Optional[str]

    #: The hash for the guild's banner.
    #: This is only present if the guild has :obj:`GuildFeatures.BANNER` in the
    #: :attr:`features` for this guild. For all other purposes, it is ``None``.
    #:
    #: :type: :class:`str`, optional
    banner_hash: typing.Optional[str]

    #: The premium tier for this guild.
    #:
    #: :type: :class:`GuildPremiumTier`
    premium_tier: GuildPremiumTier

    #: The number of nitro boosts that the server currently has. This
    #: information may not be present, in which case, it will be ``None``.
    #:
    #: :type: :class:`int`, optional
    premium_subscription_count: typing.Optional[int]

    #: The preferred locale to use for this guild.
    #:
    #: This appears to only be present if :obj:`GuildFeatures.PUBLIC` is in the
    #: :attr:`features` for this guild. For all other purposes, it should be
    #: considered to be ``None`` until more clarification is given by Discord.
    #:
    #: :type: :class:`str`, optional
    preferred_locale: typing.Optional[str]

    #: The channel ID of the channel where admins and moderators receive notices
    #: from Discord.
    #:
    #: This is only present if :obj:`GuildFeatures.PUBLIC` is in the
    #: :attr:`features` for this guild. For all other purposes, it should be
    #: considered to be ``None``.
    #:
    #: :type: :class:`snowflakes.Snowflake`, optional
    public_updates_channel_id: typing.Optional[snowflakes.Snowflake]

    # TODO: voice states

# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Application and entities that are used to describe guild templates on Discord."""

from __future__ import annotations

__all__: typing.List[str] = ["Template", "TemplateGuild", "TemplateRole"]

import typing

import attr

from hikari import guilds
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels as channels_
    from hikari import colors
    from hikari import permissions as permissions_
    from hikari import snowflakes
    from hikari import users


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class TemplateRole(guilds.PartialRole):
    """The partial role object attached to `Template`."""

    permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=False)
    """The guild wide permissions this role gives to the members it's attached to,

    This may be overridden by channel overwrites.
    """

    color: colors.Color = attr.field(eq=False, hash=False, repr=True)
    """The colour of this role.

    This will be applied to a member's name in chat if it's their top coloured role.
    """

    is_hoisted: bool = attr.field(eq=False, hash=False, repr=True)
    """Whether this role is hoisting the members it's attached to in the member list.

    members will be hoisted under their highest role where this is set to `builtins.True`.
    """

    is_mentionable: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether this role can be mentioned by all regardless of permissions."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class TemplateGuild(guilds.PartialGuild):
    """The partial guild object attached to `Template`."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The guild's description, if set."""

    verification_level: typing.Union[guilds.GuildVerificationLevel, int] = attr.field(eq=False, hash=False, repr=False)
    """The verification level needed for a user to participate in this guild."""

    default_message_notifications: typing.Union[guilds.GuildMessageNotificationsLevel, int] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The default setting for message notifications in this guild."""

    explicit_content_filter: typing.Union[guilds.GuildExplicitContentFilterLevel, int] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The setting for the explicit content filter in this guild."""

    preferred_locale: str = attr.field(eq=False, hash=False, repr=False)
    """The preferred locale to use for this guild.

    This can only be change if `GuildFeature.COMMUNITY` is in `Guild.features`
    for this guild and will otherwise default to `en-US`.
    """

    afk_timeout: datetime.timedelta = attr.field(eq=False, hash=False, repr=False)
    """Timeout for activity before a member is classed as AFK.

    How long a voice user has to be AFK for before they are classed as being
    AFK and are moved to the AFK channel (`Guild.afk_channel_id`).
    """

    roles: typing.Mapping[snowflakes.Snowflake, TemplateRole] = attr.field(eq=False, hash=False, repr=False)
    """The roles in the guild.

    !!! note
        `hikari.guilds.Role.id` will be a unique placeholder on all the role
        objects found attached this template guild.
    """

    channels: typing.Mapping[snowflakes.Snowflake, channels_.GuildChannel] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The channels for the guild.

    !!! note
        `hikari.channels.GuildChannel.id` will be a unique placeholder on all
        the channel objects found attached this template guild.
    """

    afk_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID for the channel that AFK voice users get sent to.

    If `builtins.None`, then no AFK channel is set up for this guild.
    """

    system_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the system channel or `builtins.None` if it is not enabled.

    Welcome messages and Nitro boost messages may be sent to this channel.
    """

    system_channel_flags: guilds.GuildSystemChannelFlag = attr.field(eq=False, hash=False, repr=False)
    """Return flags for the guild system channel.

    These are used to describe which notifications are suppressed.
    """


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Template:
    """Represents a template used for creating guilds."""

    code: str = attr.field(hash=True, repr=True)
    """The template's unique ID."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The template's name."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The template's description."""

    usage_count: int = attr.field(eq=False, hash=False, repr=True)
    """The number of times the template has been used to create a guild."""

    creator: users.User = attr.field(eq=False, hash=False, repr=False)
    """The user who created the template."""

    created_at: datetime.datetime = attr.field(eq=False, hash=False, repr=True)
    """When the template was created."""

    updated_at: datetime.datetime = attr.field(eq=False, hash=False, repr=True)
    """When the template was last synced with the source guild."""

    source_guild: TemplateGuild = attr.field(eq=False, hash=False, repr=True)
    """The partial object of the guild this template is based on."""

    is_unsynced: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether this template is missing changes from it's source guild."""

    def __str__(self) -> str:
        return f"https://discord.new/{self.code}"

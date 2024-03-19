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
"""Application and entities that are used to describe guild templates on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("Template", "TemplateGuild", "TemplateRole")

import typing

import attrs

from hikari import guilds
from hikari import undefined
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels as channels_
    from hikari import colors
    from hikari import permissions as permissions_
    from hikari import snowflakes
    from hikari import traits
    from hikari import users


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class TemplateRole(guilds.PartialRole):
    """The partial role object attached to [`hikari.templates.Template`][]."""

    permissions: permissions_.Permissions = attrs.field(eq=False, hash=False, repr=False)
    """The guild wide permissions this role gives to the members it's attached to.

    This may be overridden by channel overwrites.
    """

    color: colors.Color = attrs.field(eq=False, hash=False, repr=True)
    """The colour of this role.

    This will be applied to a member's name in chat if it's their top coloured role.
    """

    is_hoisted: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this role is hoisting the members it's attached to in the member list.

    members will be hoisted under their highest role where this is set to [`True`][].
    """

    is_mentionable: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this role can be mentioned by all regardless of permissions."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class TemplateGuild(guilds.PartialGuild):
    """The partial guild object attached to [`hikari.templates.Template`][]."""

    description: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The guild's description, if set."""

    verification_level: typing.Union[guilds.GuildVerificationLevel, int] = attrs.field(eq=False, hash=False, repr=False)
    """The verification level needed for a user to participate in this guild."""

    default_message_notifications: typing.Union[guilds.GuildMessageNotificationsLevel, int] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """The default setting for message notifications in this guild."""

    explicit_content_filter: typing.Union[guilds.GuildExplicitContentFilterLevel, int] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """The setting for the explicit content filter in this guild."""

    preferred_locale: str = attrs.field(eq=False, hash=False, repr=False)
    """The preferred locale to use for this guild.

    This can only be change if [`hikari.guilds.GuildFeature.COMMUNITY`][] is in [`hikari.guilds.Guild.features`][]
    for this guild and will otherwise default to `en-US`.
    """

    afk_timeout: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """Timeout for activity before a member is classed as AFK.

    How long a voice user has to be AFK for before they are classed as being
    AFK and are moved to the AFK channel ([`hikari.guilds.Guild.afk_channel_id`][]).
    """

    roles: typing.Mapping[snowflakes.Snowflake, TemplateRole] = attrs.field(eq=False, hash=False, repr=False)
    """The roles in the guild.

    !!! note
        [`hikari.guilds.Role.id`][] will be a unique placeholder on all the role
        objects found attached this template guild.
    """

    channels: typing.Mapping[snowflakes.Snowflake, channels_.GuildChannel] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """The channels for the guild.

    !!! note
        [`hikari.channels.GuildChannel.id`][] will be a unique placeholder on all
        the channel objects found attached this template guild.
    """

    afk_channel_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID for the channel that AFK voice users get sent to.

    If [`None`][], then no AFK channel is set up for this guild.
    """

    system_channel_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the system channel or [`None`][] if it is not enabled.

    Welcome messages and Nitro boost messages may be sent to this channel.
    """

    system_channel_flags: guilds.GuildSystemChannelFlag = attrs.field(eq=False, hash=False, repr=False)
    """Return flags for the guild system channel.

    These are used to describe which notifications are suppressed.
    """


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class Template:
    """Represents a template used for creating guilds."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    code: str = attrs.field(hash=True, repr=True)
    """The template's unique ID."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The template's name."""

    description: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The template's description."""

    usage_count: int = attrs.field(eq=False, hash=False, repr=True)
    """The number of times the template has been used to create a guild."""

    creator: users.User = attrs.field(eq=False, hash=False, repr=False)
    """The user who created the template."""

    created_at: datetime.datetime = attrs.field(eq=False, hash=False, repr=True)
    """When the template was created."""

    updated_at: datetime.datetime = attrs.field(eq=False, hash=False, repr=True)
    """When the template was last synced with the source guild."""

    source_guild: TemplateGuild = attrs.field(eq=False, hash=False, repr=True)
    """The partial object of the guild this template is based on."""

    is_unsynced: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this template is missing changes from it's source guild."""

    async def fetch_self(self) -> Template:
        """Fetch an up-to-date view of this template from the API.

        Returns
        -------
        hikari.templates.Template
            An up-to-date view of this template.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the template is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_template(self.code)

    async def edit(
        self,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> Template:
        """Modify a guild template.

        Parameters
        ----------
        name : hikari.undefined.UndefinedOr[str]
            The name to set for this template.
        description : hikari.undefined.UndefinedNoneOr[str]
            The description to set for the template.

        Returns
        -------
        hikari.templates.Template
            The object of the edited template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is longer than max_rate_limit when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.edit_template(self.source_guild, self, name=name, description=description)

    async def delete(self) -> None:
        """Delete a guild template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is longer than max_rate_limit when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.delete_template(self.source_guild, self)

    async def sync(self) -> Template:
        """Sync a guild template.

        Returns
        -------
        hikari.templates.Template
            The object of the synced template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild or are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.NotFoundError
            If the guild or template is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is longer than max_rate_limit when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.sync_guild_template(self.source_guild.id, self.code)

    async def create_guild(self, name: str, *, icon: undefined.UndefinedOr[str]) -> guilds.RESTGuild:
        """Make a guild from a template.

        !!! note
            This endpoint can only be used by bots in less than 10 guilds.

        Parameters
        ----------
        name : str
            The new guilds name.

        Other Parameters
        ----------------
        icon : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the guild icon to set.
            Must be a 1024x1024 image or can be an animated gif when the guild has the ANIMATED_ICON feature.

        Returns
        -------
        hikari.guilds.RESTGuild
            Object of the created guild.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value or if you call this as a bot that’s in more than 10 guilds.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is longer than max_rate_limit when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_guild_from_template(self, name, icon=icon)

    def __str__(self) -> str:
        return f"https://discord.new/{self.code}"

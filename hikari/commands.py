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
"""Models and enums used for application commands on Discord."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "PartialCommand",
    "ContextMenuCommand",
    "SlashCommand",
    "CommandChoice",
    "CommandOption",
    "CommandPermission",
    "CommandPermissionType",
    "CommandType",
    "GuildCommandPermissions",
    "OptionType",
)

import typing

import attrs

from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.internal import attrs_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import guilds
    from hikari import locales


class CommandType(int, enums.Enum):
    """The type of a command."""

    SLASH = 1
    """A text-based command."""

    USER = 2
    """A user-based command."""

    MESSAGE = 3
    """A message-based command."""


@typing.final
class OptionType(int, enums.Enum):
    """The type of a command option."""

    SUB_COMMAND = 1
    """Denotes a command option where the value will be a sub command."""

    SUB_COMMAND_GROUP = 2
    """Denotes a command option where the value will be a sub command group."""

    STRING = 3
    """Denotes a command option where the value will be a string."""

    INTEGER = 4
    """Denotes a command option where the value will be a int.

    This is range limited between -2^53 and 2^53.
    """

    BOOLEAN = 5
    """Denotes a command option where the value will be a bool."""

    USER = 6
    """Denotes a command option where the value will be resolved to a user."""

    CHANNEL = 7
    """Denotes a command option where the value will be resolved to a channel."""

    ROLE = 8
    """Denotes a command option where the value will be resolved to a role."""

    MENTIONABLE = 9
    """Denotes a command option where the value will be a snowflake ID."""

    FLOAT = 10
    """Denotes a command option where the value will be a float.

    This is range limited between -2^53 and 2^53.
    """

    ATTACHMENT = 11
    """Denotes a command option where the value will be an attachment."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class CommandChoice:
    """Represents the choices set for an application command's argument."""

    name: str = attrs.field(repr=True)
    """The choice's name (inclusively between 1-100 characters)."""

    name_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attrs.field(
        eq=False, factory=dict, hash=False, repr=False
    )
    """A mapping of name localizations for this command choice."""

    value: typing.Union[str, int, float] = attrs.field(repr=True)
    """Value of the choice (up to 100 characters if a string)."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class CommandOption:
    """Represents an application command's argument."""

    type: typing.Union[OptionType, int] = attrs.field(repr=True)
    """The type of command option this is."""

    name: str = attrs.field(repr=True)
    r"""The command option's name.

    !!! note
        This will match the regex `^[-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$` in Unicode mode and will be
        lowercase.
    """

    description: str = attrs.field(repr=False)
    """The command option's description.

    !!! note
        This will be inclusively between 1-100 characters in length.
    """

    is_required: bool = attrs.field(default=False, repr=False)
    """Whether this command option is required."""

    choices: typing.Optional[typing.Sequence[CommandChoice]] = attrs.field(default=None, repr=False)
    """A sequence of up to (and including) 25 choices for this command.

    This will be [`None`][] if the input values for this option aren't
    limited to specific values or if it's a subcommand or subcommand-group type
    option.
    """

    options: typing.Optional[typing.Sequence[CommandOption]] = attrs.field(default=None, repr=False)
    """Sequence of up to (and including) 25 of the options for this command option."""

    channel_types: typing.Optional[typing.Sequence[typing.Union[channels.ChannelType, int]]] = attrs.field(
        default=None, repr=False
    )
    """The channel types that this option will accept.

    If [`None`][], then all channel types will be accepted.
    """

    autocomplete: bool = attrs.field(default=False, repr=False)
    """Whether this option has autocomplete."""

    min_value: typing.Union[int, float, None] = attrs.field(default=None, repr=False)
    """The minimum value permitted (inclusive).

    This will be [`int`][] if the type of the option is [`hikari.commands.OptionType.INTEGER`][]
    and [`float`][] if the type is [`hikari.commands.OptionType.FLOAT`][].
    """

    max_value: typing.Union[int, float, None] = attrs.field(default=None, repr=False)
    """The maximum value permitted (inclusive).

    This will be [`int`][] if the type of the option is [`hikari.commands.OptionType.INTEGER`][]
    and [`float`][] if the type is [`hikari.commands.OptionType.FLOAT`][].
    """

    name_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attrs.field(
        eq=False, factory=dict, hash=False, repr=False
    )
    """A mapping of name localizations for this option."""

    description_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attrs.field(
        eq=False, factory=dict, hash=False, repr=False
    )
    """A mapping of description localizations for this option."""

    min_length: typing.Optional[int] = attrs.field(default=None, repr=False)
    """The minimum length permitted (inclusive).

    This is only valid for [`hikari.commands.OptionType.STRING`][],
    otherwise it will be [`None`][].
    """

    max_length: typing.Optional[int] = attrs.field(default=None, repr=False)
    """The maximum length permitted (inclusive).

    This is only valid for [`hikari.commands.OptionType.STRING`][],
    otherwise it will be [`None`][].
    """


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class PartialCommand(snowflakes.Unique):
    """Represents any application command on Discord."""

    app: traits.RESTAware = attrs.field(eq=False, hash=False, repr=False)
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    type: CommandType = attrs.field(hash=True, repr=True)
    """The type of a command."""

    application_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the application this command belongs to."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    r"""The command's name.

    !!! note
        This will match the regex `^[-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$` in Unicode mode and will be
        lowercase.
    """

    default_member_permissions: permissions.Permissions = attrs.field(eq=False, hash=False, repr=True)
    """Member permissions necessary to utilize this command by default.

    This excludes administrators of the guild and overwrites.
    """

    is_dm_enabled: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this command is enabled in DMs with the bot."""

    is_nsfw: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether this command is age-restricted."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """ID of the guild this command is in.

    This will be [`None`][] if this is a global command.
    """

    version: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """Auto-incrementing version identifier updated during substantial record changes."""

    name_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """A mapping of name localizations for this command."""

    async def fetch_self(self) -> PartialCommand:
        """Fetch an up-to-date version of this command object.

        Returns
        -------
        PartialCommand
            Object of the fetched command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the target command.
        hikari.errors.NotFoundError
            If the command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        command = await self.app.rest.fetch_application_command(
            self.application_id, self.id, undefined.UNDEFINED if self.guild_id is None else self.guild_id
        )
        return command

    async def edit(
        self,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[CommandOption]] = undefined.UNDEFINED,
    ) -> PartialCommand:
        """Edit this command.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[str]
            The name to set for the command. Leave as [`hikari.undefined.UNDEFINED`][]
            to not change.
        description : hikari.undefined.UndefinedOr[str]
            The description to set for the command. Leave as [`hikari.undefined.UNDEFINED`][]
            to not change.
        options : hikari.undefined.UndefinedOr[typing.Sequence[CommandOption]]
            A sequence of up to 10 options to set for this command. Leave this as
            [`hikari.undefined.UNDEFINED`][] to not change.

        Returns
        -------
        PartialCommand
            The edited command object.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the application's commands.
        hikari.errors.NotFoundError
            If the application or command isn't found.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        command = await self.app.rest.edit_application_command(
            self.application_id,
            self.id,
            undefined.UNDEFINED if self.guild_id is None else self.guild_id,
            name=name,
            description=description,
            options=options,
        )
        return command

    async def delete(self) -> None:
        """Delete this command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the application's commands.
        hikari.errors.NotFoundError
            If the application or command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.delete_application_command(
            self.application_id, self.id, undefined.UNDEFINED if self.guild_id is None else self.guild_id
        )

    async def fetch_guild_permissions(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> GuildCommandPermissions:
        """Fetch the permissions registered for this command in a specific guild.

        Parameters
        ----------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to fetch the command permissions for.

        Returns
        -------
        GuildCommandPermissions
            Object of the command permissions set for the specified command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands or guild.
        hikari.errors.NotFoundError
            If the provided application or command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_application_command_permissions(
            application=self.application_id, command=self.id, guild=guild
        )

    async def set_guild_permissions(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], permissions: typing.Sequence[CommandPermission]
    ) -> GuildCommandPermissions:
        """Set permissions for this command in a specific guild.

        !!! note
            This overwrites any previously set permissions.

        Parameters
        ----------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to set the command permissions in.
        permissions : typing.Sequence[CommandPermission]
            Sequence of up to 10 of the permission objects to set.

        Returns
        -------
        GuildCommandPermissions
            Object of the set permissions.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands or guild.
        hikari.errors.NotFoundError
            If the provided application or command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.set_application_command_permissions(
            application=self.application_id, command=self.id, guild=guild, permissions=permissions
        )


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class SlashCommand(PartialCommand):
    """Represents a slash command on Discord."""

    description: str = attrs.field(eq=False, hash=False, repr=False)
    """The command's description.

    None if this command is not a slash command.

    !!! note
        This will be inclusively between 1-100 characters in length.
    """

    description_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """A set of description localizations for this command."""

    options: typing.Optional[typing.Sequence[CommandOption]] = attrs.field(eq=False, hash=False, repr=False)
    """Sequence of up to (and including) 25 of the options for this command."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class ContextMenuCommand(PartialCommand):
    """Represents a context menu command on Discord."""


class CommandPermissionType(int, enums.Enum):
    """The type of entity a command permission targets."""

    ROLE = 1
    """A command permission which toggles access for a specific role."""

    USER = 2
    """A command permission which toggles access for a specific user."""

    CHANNEL = 3
    """A command permission which toggles access in a specific channel."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class CommandPermission:
    """Representation of a permission which enables or disables a command for a user or role."""

    id: snowflakes.Snowflake = attrs.field(converter=snowflakes.Snowflake)
    """ID of the role or user this permission changes the permission's state for.

    There are some special constants for this field:

    * If equals to `guild_id`, then it applies to all members in a guild.
    * If equals to (`guild_id` - 1), then it applies to all channels in a guild.
    """

    type: typing.Union[CommandPermissionType, int] = attrs.field(converter=CommandPermissionType)
    """The entity this permission overrides the command's state for."""

    has_access: bool = attrs.field()
    """Whether this permission marks the target entity as having access to the command."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildCommandPermissions:
    """Representation of the permissions set for a command within a guild."""

    id: snowflakes.Snowflake = attrs.field()
    """ID of the entity these permissions apply to.

    This may be the ID of a specific command or the application ID. When this is equal
    to `application_id`, the permissions apply to all commands that do not contain
    explicit overwrites.
    """

    application_id: snowflakes.Snowflake = attrs.field()
    """ID of the application the relevant command belongs to."""

    command_id: snowflakes.Snowflake = attrs.field()
    """ID of the command these permissions are for."""

    guild_id: snowflakes.Snowflake = attrs.field()
    """ID of the guild these permissions are in."""

    permissions: typing.Sequence[CommandPermission] = attrs.field()
    """Sequence of up to (and including) 100 of the command permissions set in this guild."""

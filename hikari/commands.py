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
"""Models and enums used for application commands on Discord."""
from __future__ import annotations

__all__: typing.List[str] = [
    "Command",
    "CommandChoice",
    "CommandOption",
    "CommandPermission",
    "CommandPermissionType",
    "GuildCommandPermissions",
    "OptionType",
]

import typing

import attr

from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import guilds


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


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class CommandChoice:
    """Represents the choices set for an application command's argument."""

    name: str = attr.field(repr=True)
    """The choice's name (inclusively between 1-100 characters)."""

    value: typing.Union[str, int, float] = attr.field(repr=True)
    """Value of the choice (up to 100 characters if a string)."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class CommandOption:
    """Represents an application command's argument."""

    type: typing.Union[OptionType, int] = attr.field(repr=True)
    """The type of command option this is."""

    name: str = attr.field(repr=True)
    r"""The command option's name.

    !!! note
        This will match the regex `^[\w-]{1,32}$` in Unicode mode and will be
        lowercase.
    """

    description: str = attr.field(repr=False)
    """The command option's description.

    !!! note
        This will be inclusively between 1-100 characters in length.
    """

    is_required: bool = attr.field(repr=False)
    """Whether this command """

    choices: typing.Optional[typing.Sequence[CommandChoice]] = attr.field(default=None, repr=False)
    """A sequence of up to (and including) 25 choices for this command.

    This will be `builtins.None` if the input values for this option aren't
    limited to specific values or if it's a subcommand or subcommand-group type
    option.
    """

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.field(default=None, repr=False)
    """Sequence of up to (and including) 25 of the options for this command option."""

    channel_types: typing.Optional[typing.Sequence[typing.Union[channels.ChannelType, int]]] = attr.field(
        default=None, repr=False
    )
    """The channel types that this option will accept.

    If `builtins.None`, then all channel types will be accepted.
    """

    min_value: typing.Union[int, float, None] = attr.field(default=None, repr=False)
    """The minimum value permitted (inclusive).

    This will be `builtins.int` if the type of the option is `hikari.commands.OptionType.INTEGER`
    and `builtins.float` if the type is `hikari.commands.OptionType.NUMBER`.
    """

    max_value: typing.Union[int, float, None] = attr.field(default=None, repr=False)
    """The maximum value permitted (inclusive).

    This will be `builtins.int` if the type of the option is `hikari.commands.OptionType.INTEGER`
    and `builtins.float` if the type is `hikari.commands.OptionType.NUMBER`.
    """


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Command(snowflakes.Unique):
    """Represents an application command on Discord."""

    app: traits.RESTAware = attr.field(eq=False, hash=False, repr=False)
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the application this command belongs to."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    r"""The command's name.

    !!! note
        This will match the regex `^[\w-]{1,32}$` in Unicode mode and will be
        lowercase.
    """

    description: str = attr.field(eq=False, hash=False, repr=False)
    """The command's description.

    !!! note
        This will be inclusively between 1-100 characters in length.
    """

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.field(eq=False, hash=False, repr=False)
    """Sequence of up to (and including) 25 of the options for this command."""

    default_permission: bool = attr.field(eq=False, hash=False, repr=True)
    """Whether the command is enabled by default when added to a guild.

    Defaults to `builtins.True`. This behaviour is overridden by command
    permissions.
    """

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """ID of the guild this command is in.

    This will be `builtins.None` if this is a global command.
    """

    version: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """Auto-incrementing version identifier updated during substantial record changes."""

    async def fetch_self(self) -> Command:
        """Fetch an up-to-date version of this command object.

        Returns
        -------
        Command
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
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_application_command(
            self.application_id, self.id, undefined.UNDEFINED if self.guild_id is None else self.guild_id
        )

    async def edit(
        self,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[CommandOption]] = undefined.UNDEFINED,
    ) -> Command:
        """Edit this command.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to edit a command for if this is a guild
            specific command. Leave this as `hikari.undefined.UNDEFINED` to delete
            a global command.
        name : hikari.undefined.UndefinedOr[builtins.str]
            The name to set for the command. Leave as `hikari.undefined.UNDEFINED`
            to not change.
        description : hikari.undefined.UndefinedOr[builtins.str]
            The description to set for the command. Leave as `hikari.undefined.UNDEFINED`
            to not change.
        options : hikari.undefined.UndefinedOr[typing.Sequence[CommandOption]]
            A sequence of up to 10 options to set for this command. Leave this as
            `hikari.undefined.UNDEFINED` to not change.

        Returns
        -------
        Command
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
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.edit_application_command(
            self.application_id,
            self.id,
            undefined.UNDEFINED if self.guild_id is None else self.guild_id,
            name=name,
            description=description,
            options=options,
        )

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
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
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
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
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
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.set_application_command_permissions(
            application=self.application_id, command=self.id, guild=guild, permissions=permissions
        )


class CommandPermissionType(int, enums.Enum):
    """The type of entity a command permission targets."""

    ROLE = 1
    """A command permission which toggles access for a specific role."""

    USER = 2
    """A command permission which toggles access for a specific user."""


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class CommandPermission:
    """Representation of a permission which enables or disables a command for a user or role."""

    id: snowflakes.Snowflake = attr.field(converter=snowflakes.Snowflake)
    """Id of the role or user this permission changes the permission's state for."""

    type: typing.Union[CommandPermissionType, int] = attr.field(converter=CommandPermissionType)
    """The entity this permission overrides the command's state for."""

    has_access: bool = attr.field()
    """Whether this permission marks the target entity as having access to the command."""


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class GuildCommandPermissions:
    """Representation of the permissions set for a command within a guild."""

    application_id: snowflakes.Snowflake = attr.field()
    """ID of the application the relevant command belongs to."""

    command_id: snowflakes.Snowflake = attr.field()
    """ID of the command these permissions are for."""

    guild_id: snowflakes.Snowflake = attr.field()
    """ID of the guild these permissions are in."""

    permissions: typing.Sequence[CommandPermission] = attr.field()
    """Sequence of up to (and including) 10 of the command permissions set in this guild."""

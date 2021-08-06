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
    "OptionType",
]

import typing

import attr

from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.internal import attr_extensions
from hikari.internal import enums


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
    """Denotes a command option where the value will be a int."""

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


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class CommandChoice:
    """Represents the choices set for an application command's argument."""

    name: str = attr.field(repr=True)
    """The choice's name (inclusively between 1-100 characters)."""

    value: typing.Union[str, int] = attr.field(repr=True)
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
        This will match the regex `^[a-z0-9_-]{1,32}$`.
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
        This will match the regex `^[a-z0-9_-]{1,32}$`.
    """

    description: str = attr.field(eq=False, hash=False, repr=False)
    """The command's description.

    !!! note
        This will be inclusively between 1-100 characters in length.
    """

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.field(eq=False, hash=False, repr=False)
    """Sequence of up to (and including) 25 of the options for this command."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """ID of the guild this command is in.

    This will be `builtins.None` if this is a global command.
    """

    async def fetch_self(self) -> Command:
        """Fetch an up-to-date version of this command object.

        Returns
        -------
        hikari.commands.Command
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
        options : hikari.undefined.UndefinedOr[typing.Sequence[hikari.commands.CommandOption]]
            A sequence of up to 10 options to set for this command. Leave this as
            `hikari.undefined.UNDEFINED` to not change.

        Returns
        -------
        hikari.commands.Command
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

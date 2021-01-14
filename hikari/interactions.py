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
"""Application and entities that are used to describe interactions on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "Command",
    "CommandChoice",
    "CommandInteractionData",
    "CommandInteractionOption",
    "CommandInteraction",
    "CommandOption",
    "InteractionMember",
    "InteractionResponseType",
    "InteractionType",
    "OptionType",
]

import typing

import attr

from hikari import channels
from hikari import guilds
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import webhooks
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import embeds as embeds_
    from hikari import messages
    from hikari import permissions as permissions_
    from hikari import users


@typing.final
class OptionType(int, enums.Enum):
    """The type of a command option."""

    SUB_COMMAND = 1
    """Denotes a command option where the value will be a sub command."""

    SUB_COMMAND_GROUP = 2
    """Denotes a command option where the value will be a sub command group."""

    STRING = 3
    """Denotes a command option where the value will be a string."""

    STR = STRING
    """Denotes a command option where the value will be a string."""

    INTEGER = 4
    """Denotes a command option where the value will be a int."""

    INT = INTEGER
    """Denotes a command option where the value will be a int."""

    BOOLEAN = 5
    """Denotes a command option where the value will be a bool."""

    BOOL = BOOLEAN
    """Denotes a command option where the value will be a bool."""

    # TODO: These may be changed to objects rather than IDs in the future.
    # See https://github.com/discord/discord-api-docs/issues/2490
    USER_ID = 6
    """Denotes a command option where the value will be a user ID."""

    CHANNEL_ID = 7
    """Denotes a command option where the value will be a channel ID."""

    ROLE_ID = 8
    """Denotes a command option where the value will be a role ID."""


@typing.final
class InteractionType(int, enums.Enum):
    """The type of an interaction."""

    # PING isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.
    APPLICATION_COMMAND = 2
    """An interaction triggered by a user calling an application command."""


@typing.final
class InteractionResponseType(int, enums.Enum):
    """The type of an interaction response."""

    # PONG isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.
    ACKNOWLEDGE = 2
    """A response that only acknowledges an interaction without sending a message."""

    CHANNEL_MESSAGE = 3
    """A response with a message to send in the origin channel."""

    CHANNEL_MESSAGE_WITH_SOURCE = 4
    """A response with a message to send in the origin channel.

    Unlike `InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE`, the response
    message will be accompanied by an application message from the author
    indicating that they triggered this command.
    """

    ACKNOWLEDGE_WITH_SOURCE = 5
    """A response which acknowledges an interaction without sending a message.

    Unlike `InteractionResponseType.ACKNOWLEDGE_WITH_SOURCE`, this response will
    still trigger an application message from the author indicating that they
    triggered this command.
    """


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandChoice:
    """Represents the choices set for an application command's argument."""

    name: str = attr.ib(eq=True, hash=False, repr=True)
    value: typing.Union[str, int] = attr.ib(eq=True, hash=False, repr=True)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandOption:
    """Represents an application command's argument."""

    type: typing.Union[OptionType, int] = attr.ib(eq=True, hash=False, repr=True)
    name: str = attr.ib(eq=True, hash=False, repr=True)
    description: str = attr.ib(eq=True, hash=False, repr=False)
    is_required: bool = attr.ib(eq=True, hash=False, repr=False)
    choices: typing.Optional[typing.Sequence[CommandChoice]] = attr.ib(eq=True, hash=False, repr=False)
    options: typing.Optional[typing.Sequence[CommandOption]] = attr.ib(eq=True, hash=False, repr=False)


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Command(snowflakes.Unique):
    """Represents an application command on Discord."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)

    name: str = attr.ib(eq=False, hash=False, repr=True)

    description: str = attr.ib(eq=False, hash=False, repr=False)

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.ib(eq=False, hash=False, repr=False)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteractionOption:
    """Represents the options passed for a command interaction."""

    name: str = attr.ib(eq=True, hash=False, repr=True)
    # TODO: value may be changed to include json objects in the future
    # See https://github.com/discord/discord-api-docs/issues/2490
    value: typing.Optional[typing.Sequence[typing.Union[str, int, bool]]] = attr.ib(eq=True, hash=False, repr=True)
    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.ib(eq=True, hash=False, repr=True)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteractionData(snowflakes.Unique):
    """Represents the data attached to a command interaction."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    name: str = attr.ib(eq=False, hash=False, repr=True)

    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.ib(eq=True, hash=False, repr=True)


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class InteractionMember(guilds.Member):
    """Model of the member who triggered an interaction.

    Unlike `hikari.guilds.Member`, this object comes with an extra
    `InteractionMember.permissions` field.
    """

    permissions: permissions_.Permissions = attr.ib(eq=False, hash=False, repr=False)
    """Permissions the member has in the current channel."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PartialInteraction(snowflakes.Unique):
    """The base model for all interaction models."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=False)
    """ID of the application this interaction belongs to."""

    type: typing.Union[InteractionType, int] = attr.ib(eq=False, hash=False, repr=True)
    """The type of interaction this is."""

    token: str = attr.ib(eq=False, hash=False, repr=False)
    """The interaction's token."""

    version: int = attr.ib(eq=False, hash=False, repr=True)
    # TODO: remove?


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteraction(PartialInteraction, webhooks.ExecutableWebhook):
    """Represents a command interaction on Discord."""

    data: CommandInteractionData = attr.ib(eq=False, hash=False, repr=False)
    """Command interaction data provided for this event."""

    channel_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """ID of the channel this command interaction event was triggered in."""

    # Allowing interactions in DMs is a TODO on Discord's end
    # See https://github.com/discord/discord-api-docs/issues/2490
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """ID of the guild this command interaction event was triggered in.

    This will be `builtins.None` for command interactions triggered in DMs.
    """

    # Allowing interactions in DMs is a TODO on Discord's end
    # See https://github.com/discord/discord-api-docs/issues/2490
    member: typing.Optional[InteractionMember] = attr.ib(eq=False, hash=False, repr=True)
    """The member who triggered this command interaction.

    This will be `builtins.None` for command interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    @property
    def webhook_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ExecutableWebhook>>.
        return self.application_id

    async def create_initial_response(
        self,
        response_type: InteractionResponseType,
        # TODO: more concise type
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> None:
        await self.app.rest.create_command_response(
            self.id,
            self.token,
            response_type,
            content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def edit_initial_response(
        self,
        # TODO: more concise type
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages.Message:
        return await self.app.rest.edit_command_response(
            self.token,
            content,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def fetch_initial_response(self) -> messages.Message:
        return await self.app.rest.fetch_command_response(self.token)

    async def fetch_channel(self) -> channels.GuildChannel:
        """Fetch the guild channel this was triggered in.

        Returns
        -------
        hikari.channels.GuildChannel
            The requested guild channel derived object of the channel this was
            triggered in.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGES` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.GuildChannel)
        return channel

    def get_channel(self) -> typing.Optional[channels.GuildChannel]:
        """Get the guild channel this was triggered in from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The object of the guild channel that was found in the cache or
            `builtins.None`.
        """
        if isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_guild_channel(self.channel_id)

        return None

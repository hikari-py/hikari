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
    "CommandInteractionOption",
    "CommandInteraction",
    "CommandOption",
    "InteractionChannel",
    "InteractionMember",
    "ResolvedOptionData",
    "ResponseType",
    "InteractionType",
    "OptionType",
    "PartialInteraction",
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


@typing.final
class InteractionType(int, enums.Enum):
    """The type of an interaction."""

    # PING isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.
    APPLICATION_COMMAND = 2
    """An interaction triggered by a user calling an application command."""


@typing.final
class ResponseType(int, enums.Enum):
    """The type of an interaction response."""

    # PONG isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.

    # Type 2 and 3 aren't included as they were deprecated/removed by Discord.
    SOURCED_RESPONSE = 4
    """An immediate response to an interaction."""

    DEFERRED_SOURCED_RESPONSE = 5
    """Acknowledge an interaction with the intention to edit in a response later.

    The user will see a loading state when this type is used until this
    interaction expires or a response is edited in over REST.
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

    app: traits.RESTAware = attr.ib(eq=False, hash=False, repr=False)

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)

    name: str = attr.ib(eq=False, hash=False, repr=True)

    description: str = attr.ib(eq=False, hash=False, repr=False)

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.ib(eq=False, hash=False, repr=False)

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)

    async def fetch_self(self) -> Command:
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
        return await self.app.rest.edit_application_command(
            self.application_id,
            self.id,
            undefined.UNDEFINED if self.guild_id is None else self.guild_id,
            name=name,
            description=description,
            options=options,
        )

    async def delete(self) -> None:
        await self.app.rest.delete_application_command(
            self.application_id, self.id, undefined.UNDEFINED if self.guild_id is None else self.guild_id
        )


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class InteractionChannel(channels.PartialChannel):
    """Represents partial channels returned as resolved entities on interactions."""

    permissions: permissions_.Permissions = attr.ib(eq=False, hash=False, repr=True)
    """Permissions the command's executor has in this channel."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class ResolvedOptionData:
    """Represents the entities set in a command's options."""

    users: typing.Mapping[snowflakes.Snowflake, users.User] = attr.ib(eq=True, hash=False, repr=False)
    members: typing.Mapping[snowflakes.Snowflake, InteractionMember] = attr.ib(eq=True, hash=False, repr=False)
    roles: typing.Mapping[snowflakes.Snowflake, guilds.Role] = attr.ib(eq=True, hash=False, repr=False)
    channels: typing.Mapping[snowflakes.Snowflake, InteractionChannel] = attr.ib(eq=True, hash=False, repr=False)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteractionOption:
    """Represents the options passed for a command interaction."""

    name: str = attr.ib(eq=True, hash=False, repr=True)
    type: OptionType = attr.ib(eq=True, hash=False, repr=True)
    value: typing.Optional[typing.Sequence[typing.Union[str, int, bool]]] = attr.ib(eq=True, hash=False, repr=True)
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
    """Version of the interaction system this interaction is under."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteraction(PartialInteraction, webhooks.ExecutableWebhook):
    """Represents a command interaction on Discord."""

    channel_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """ID of the channel this command interaction event was triggered in."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """ID of the guild this command interaction event was triggered in.

    This will be `builtins.None` for command interactions triggered in DMs.
    """

    member: typing.Optional[InteractionMember] = attr.ib(eq=False, hash=False, repr=True)
    """The member who triggered this command interaction.

    This will be `builtins.None` for command interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    user: users.User = attr.ib(eq=False, hash=False, repr=True)
    """The user who triggered this command interaction."""

    command_id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """ID of the command being invoked."""

    command_name: str = attr.ib(eq=False, hash=False, repr=True)
    """Name of the command being invoked."""

    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.ib(eq=True, hash=False, repr=True)
    """Parameter values provided by the user invoking this command."""

    resolved: typing.Optional[ResolvedOptionData] = attr.ib(eq=True, hash=False, repr=False)

    async def fetch_initial_response(self) -> messages.Message:
        return await self.app.rest.fetch_command_response(self.application_id, self.token)

    async def create_initial_response(
        self,
        response_type: ResponseType,
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
            self.application_id,
            self.token,
            content,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete_initial_response(self) -> None:
        await self.app.rest.delete_command_response(self.application_id, self.token)

    async def fetch_channel(self) -> channels.PartialChannel:
        """Fetch the guild channel this was triggered in.

        Returns
        -------
        hikari.channels.PartialChannel
            The requested partial channel derived object of the channel this was
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
        assert isinstance(channel, channels.PartialChannel)
        return channel

    def get_channel(self) -> typing.Optional[channels.GuildChannel]:
        """Get the guild channel this was triggered in from the cache.

        !!! note
            This will always return `builtins.None` for interactions triggered
            in a DM channel.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The object of the guild channel that was found in the cache or
            `builtins.None`.
        """
        if self.guild_id and isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_guild_channel(self.channel_id)

        return None

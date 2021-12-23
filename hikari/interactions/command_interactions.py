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
"""Models and enums used for Discord's Slash Commands interaction flow."""
from __future__ import annotations

__all__: typing.List[str] = [
    "CommandInteractionOption",
    "CommandInteraction",
    "COMMAND_RESPONSE_TYPES",
    "CommandResponseTypesT",
    "InteractionChannel",
    "ResolvedOptionData",
]

import typing

import attr

from hikari import channels
from hikari import commands
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.interactions import base_interactions
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import permissions as permissions_
    from hikari import users as users_
    from hikari.api import special_endpoints


COMMAND_RESPONSE_TYPES: typing.Final[typing.AbstractSet[CommandResponseTypesT]] = frozenset(
    [base_interactions.ResponseType.MESSAGE_CREATE, base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE]
)
"""Set of the response types which are valid for a command interaction.

This includes:

* `hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`
* `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`
"""

CommandResponseTypesT = typing.Literal[
    base_interactions.ResponseType.MESSAGE_CREATE, 4, base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, 5
]
"""Type-hint of the response types which are valid for a command interaction.

The following types are valid for this:

* `hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`/`4`
* `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`/`5`
"""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class InteractionChannel(channels.PartialChannel):
    """Represents partial channels returned as resolved entities on interactions."""

    permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=True)
    """Permissions the command's executor has in this channel."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class ResolvedOptionData:
    """Represents the resolved objects of entities referenced in a command's options."""

    users: typing.Mapping[snowflakes.Snowflake, users_.User] = attr.field(repr=False)
    """Mapping of snowflake IDs to the resolved option user objects."""

    members: typing.Mapping[snowflakes.Snowflake, base_interactions.InteractionMember] = attr.field(repr=False)
    """Mapping of snowflake IDs to the resolved option member objects."""

    roles: typing.Mapping[snowflakes.Snowflake, guilds.Role] = attr.field(repr=False)
    """Mapping of snowflake IDs to the resolved option role objects."""

    channels: typing.Mapping[snowflakes.Snowflake, InteractionChannel] = attr.field(repr=False)
    """Mapping of snowflake iDs to the resolved option partial channel objects."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class CommandInteractionOption:
    """Represents the options passed for a command interaction."""

    name: str = attr.field(repr=True)
    """Name of this option."""

    type: typing.Union[commands.OptionType, int] = attr.field(repr=True)
    """Type of this option."""

    value: typing.Union[snowflakes.Snowflake, str, int, bool, None] = attr.field(repr=True)
    """Value provided for this option.

    Either `CommandInteractionOption.value` or `CommandInteractionOption.options`
    will be provided with `value` being provided when an option is provided as a
    parameter with a value and `options` being provided when an option donates a
    subcommand or group.
    """

    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.field(repr=True)
    """Options provided for this option.

    Either `CommandInteractionOption.value` or `CommandInteractionOption.options`
    will be provided with `value` being provided when an option is provided as a
    parameter with a value and `options` being provided when an option donates a
    subcommand or group.
    """


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class CommandInteraction(base_interactions.MessageResponseMixin[CommandResponseTypesT]):
    """Represents a command interaction on Discord."""

    channel_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the channel this command interaction event was triggered in."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=True)
    """ID of the guild this command interaction event was triggered in.

    This will be `builtins.None` for command interactions triggered in DMs.
    """

    member: typing.Optional[base_interactions.InteractionMember] = attr.field(eq=False, hash=False, repr=True)
    """The member who triggered this command interaction.

    This will be `builtins.None` for command interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    user: users_.User = attr.field(eq=False, hash=False, repr=True)
    """The user who triggered this command interaction."""

    command_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the command being invoked."""

    command_name: str = attr.field(eq=False, hash=False, repr=True)
    """Name of the command being invoked."""

    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.field(eq=False, hash=False, repr=True)
    """Parameter values provided by the user invoking this command."""

    resolved: typing.Optional[ResolvedOptionData] = attr.field(eq=False, hash=False, repr=False)
    """Mappings of the objects resolved for the provided command options."""

    def build_response(self) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            `CommandInteraction.create_initial_response` should be used to set
            the interaction response message.

        Examples
        --------
        ```py
        async def handle_command_interaction(interaction: CommandInteraction) -> InteractionMessageBuilder:
            return (
                interaction
                .build_response()
                .add_embed(Embed(description="Hi there"))
                .set_content("Konnichiwa")
            )
        ```

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            Interaction message response builder object.
        """
        return self.app.rest.interaction_message_builder(base_interactions.ResponseType.MESSAGE_CREATE)

    def build_deferred_response(self) -> special_endpoints.InteractionDeferredBuilder:
        """Get a deferred message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            `CommandInteraction.create_initial_response` should be used to set
            the interaction response message.

        !!! note
            Unlike `hikari.api.special_endpoints.InteractionMessageBuilder`,
            the result of this call can be returned as is without any modifications
            being made to it.

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            Deferred interaction message response builder object.
        """
        return self.app.rest.interaction_deferred_builder(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)

    async def fetch_channel(self) -> channels.TextableChannel:
        """Fetch the guild channel this was triggered in.

        Returns
        -------
        hikari.channels.TextableChannel
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
        assert isinstance(channel, channels.TextableChannel)
        return channel

    def get_channel(self) -> typing.Optional[channels.TextableGuildChannel]:
        """Get the guild channel this was triggered in from the cache.

        !!! note
            This will always return `builtins.None` for interactions triggered
            in a DM channel.

        Returns
        -------
        typing.Optional[hikari.channels.TextableGuildChannel]
            The object of the guild channel that was found in the cache or
            `builtins.None`.
        """
        if isinstance(self.app, traits.CacheAware):
            channel = self.app.cache.get_guild_channel(self.channel_id)
            assert isinstance(channel, channels.TextableGuildChannel)
            return channel

        return None

    async def fetch_command(self) -> commands.Command:
        """Fetch the command which triggered this interaction.

        Returns
        -------
        hikari.commands.Command
            Object of this interaction's command.

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
            application=self.application_id, command=self.id, guild=self.guild_id or undefined.UNDEFINED
        )

    async def fetch_guild(self) -> typing.Optional[guilds.RESTGuild]:
        """Fetch the guild this interaction happened in.

        Returns
        -------
        typing.Optional[hikari.guilds.RESTGuild]
            Object of the guild this interaction happened in or `builtins.None`
            if this occurred within a DM channel.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
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
        if not self.guild_id:
            return None

        return await self.app.rest.fetch_guild(self.guild_id)

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the object of this interaction's guild guild from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the guild if found, else `builtins.None`.
        """
        if self.guild_id and isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_guild(self.guild_id)

        return None

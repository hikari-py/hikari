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
"""Models and enums used for Discord's Components interaction flow."""
from __future__ import annotations

__all__: typing.List[str] = ["ComponentInteraction", "COMPONENT_RESPONSE_TYPES", "ComponentResponseTypesT"]

import typing

import attr

from hikari import channels
from hikari import traits
from hikari.interactions import base_interactions

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import messages
    from hikari import snowflakes
    from hikari import users
    from hikari.api import special_endpoints


_DEFERRED_TYPES: typing.AbstractSet[_DeferredTypesT] = frozenset(
    [base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE]
)
_DeferredTypesT = typing.Literal[
    base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, 5, base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE, 6
]
_IMMEDIATE_TYPES: typing.AbstractSet[_ImmediateTypesT] = frozenset(
    [base_interactions.ResponseType.MESSAGE_CREATE, base_interactions.ResponseType.MESSAGE_UPDATE]
)
_ImmediateTypesT = typing.Literal[
    base_interactions.ResponseType.MESSAGE_CREATE, 4, base_interactions.ResponseType.MESSAGE_UPDATE, 7
]


# This type ignore accounts for a regression introduced to MyPy in v0.900
COMPONENT_RESPONSE_TYPES: typing.Final[typing.AbstractSet[ComponentResponseTypesT]] = frozenset(  # type: ignore[assignment]
    [*_DEFERRED_TYPES, *_IMMEDIATE_TYPES]
)
"""Set of the response types which are valid for a component interaction.

This includes:

* `hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`
* `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`
* `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`
* `hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`
"""

ComponentResponseTypesT = typing.Union[_ImmediateTypesT, _DeferredTypesT]
"""Type-hint of the response types which are valid for a component interaction.

The following types are valid for this:

* `hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`/`4`
* `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`/`5`
* `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`/`6`
* `hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`/`7`
"""


@attr.define(hash=True, weakref_slot=False)
class ComponentInteraction(base_interactions.MessageResponseMixin[ComponentResponseTypesT]):
    """Represents a component interaction on Discord."""

    channel_id: snowflakes.Snowflake = attr.field(eq=False)
    """ID of the channel this interaction was triggered in."""

    component_type: typing.Union[messages.ComponentType, int] = attr.field(eq=False)
    """The type of component which triggers this interaction.

    !!! note
        This will never be `ButtonStyle.LINK` as link buttons don't trigger
        interactions.
    """

    custom_id: str = attr.field(eq=False)
    """Developer defined ID of the component which triggered this interaction."""

    values: typing.Sequence[str] = attr.field(eq=False)
    """Sequence of the values which were selected for a select menu component."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False)
    """ID of the guild this interaction was triggered in.

    This will be `builtins.None` for command interactions triggered in DMs.
    """
    message: messages.Message = attr.field(eq=False, repr=False)
    """Object of the message the components for this interaction are attached to."""

    member: typing.Optional[base_interactions.InteractionMember] = attr.field(eq=False, hash=False, repr=True)
    """The member who triggered this interaction.

    This will be `builtins.None` for interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    user: users.User = attr.field(eq=False, hash=False, repr=True)
    """The user who triggered this interaction."""

    def build_response(self, type_: _ImmediateTypesT, /) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            `ComponentInteraction.create_initial_response` should be used to set
            the interaction response message.

        Parameters
        ----------
        type_ : typing.Union[builtins.int, hikari.interactions.base_interactions.ResponseType]
            The type of immediate response this should be.

            This may be one of the following:

            * `hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`
            * `hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`

        Examples
        --------
        ```py
        async def handle_component_interaction(interaction: ComponentInteraction) -> InteractionMessageBuilder:
            return (
                interaction
                .build_response(ResponseType.MESSAGE_UPDATE)
                .add_embed(Embed(description="Hi there"))
                .set_content("Konnichiwa")
            )
        ```

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            Interaction message response builder object.
        """
        if type_ not in _IMMEDIATE_TYPES:
            raise ValueError("Invalid type passed for an immediate response")

        return self.app.rest.interaction_message_builder(type_)

    def build_deferred_response(self, type_: _DeferredTypesT, /) -> special_endpoints.InteractionDeferredBuilder:
        """Get a deferred message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            `ComponentInteraction.create_initial_response` should be used to set
            the interaction response message.

        !!! note
            Unlike `hikari.api.special_endpoints.InteractionMessageBuilder`,
            the result of this call can be returned as is without any modifications
            being made to it.

        Parameters
        ----------
        type_ : typing.Union[builtins.int, hikari.interactions.base_interactions.ResponseType]
            The type of deferred response this should be.

            This may be one of the following:

            * `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`
            * `hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`

        Returns
        -------
        hikari.api.special_endpoints.InteractionDeferredBuilder
            Deferred interaction message response builder object.
        """
        if type_ not in _DEFERRED_TYPES:
            raise ValueError("Invalid type passed for a deferred response")

        return self.app.rest.interaction_deferred_builder(type_)

    async def fetch_channel(self) -> channels.TextableChannel:
        """Fetch the channel this interaction occurred in.

        Returns
        -------
        hikari.channels.TextableChannel
            The channel. This will be a _derivative_ of `hikari.channels.TextableChannel`.

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

    def get_channel(self) -> typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel, None]:
        """Get the guild channel this interaction occurred in.

        !!! note
            This will always return `builtins.None` for interactions triggered
            in a DM channel.

        Returns
        -------
        typing.Union[hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel, builtins.None]
            The object of the guild channel that was found in the cache or
            `builtins.None`.
        """
        if isinstance(self.app, traits.CacheAware):
            channel = self.app.cache.get_guild_channel(self.channel_id)
            assert isinstance(channel, (channels.GuildTextChannel, channels.GuildNewsChannel))
            return channel

        return None

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

    async def fetch_parent_message(self) -> messages.Message:
        """Fetch the message which this interaction was triggered on.

        Returns
        -------
        hikari.messages.Message
            The requested message.

        Raises
        ------
        builtins.ValueError
            If `token` is not available.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found or the webhook's message wasn't found.
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
        return await self.fetch_message(self.message.id)

    def get_parent_message(self) -> typing.Optional[messages.PartialMessage]:
        """Get the message which this interaction was triggered on from the cache.

        Returns
        -------
        typing.Optional[hikari.messages.Message]
            The object of the message found in the cache or `builtins.None`.
        """
        if isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_message(self.message.id)

        return None

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
"""Models and enums used for Discord's Modals interaction flow."""

from __future__ import annotations

__all__: typing.List[str] = ["ModalResponseTypesT", "ModalInteraction", "ModalInteraction"]

import typing

import attrs

from hikari import channels
from hikari import guilds
from hikari import messages
from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari.interactions import base_interactions
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import components as components_
    from hikari import locales
    from hikari import users as _users
    from hikari.api import special_endpoints

ModalResponseTypesT = typing.Literal[
    base_interactions.ResponseType.MESSAGE_CREATE,
    4,
    base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE,
    5,
    base_interactions.ResponseType.MESSAGE_UPDATE,
    7,
    base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE,
    6,
]
"""Type-hint of the response types which are valid for a modal interaction.

The following types are valid for this:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]/`4`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]/`5`
* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]/`7`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]/`6`
"""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class ModalInteraction(base_interactions.MessageResponseMixin[ModalResponseTypesT]):
    """Represents a modal interaction on Discord."""

    channel_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the channel this modal interaction event was triggered in."""

    custom_id: str = attrs.field(eq=False, hash=False, repr=True)
    """The custom id of the modal."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """ID of the guild this modal interaction event was triggered in.

    This will be [`None`][] for modal interactions triggered in DMs.
    """

    guild_locale: typing.Union[str, locales.Locale, None] = attrs.field(eq=False, hash=False, repr=True)
    """The preferred language of the guild this modal interaction was triggered in.

    This will be [`None`][] for modal interactions triggered in DMs.

    !!! note
        This value can usually only be changed if [`hikari.guilds.GuildFeature.COMMUNITY`][]
        is in [`hikari.guilds.Guild.features`][] for the guild and will otherwise
        default to [`hikari.locales.Locale.EN_US`][].
    """

    message: typing.Optional[messages.Message] = attrs.field(eq=False, repr=False)
    """The message whose component triggered the modal.

    This will be [`None`][] if the modal was a response to a command.
    """

    member: typing.Optional[base_interactions.InteractionMember] = attrs.field(eq=False, hash=False, repr=True)
    """The member who triggered this modal interaction.

    This will be [`None`][] for modal interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    user: _users.User = attrs.field(eq=False, hash=False, repr=True)
    """The user who triggered this modal interaction."""

    locale: str = attrs.field(eq=False, hash=False, repr=True)
    """The selected language of the user who triggered this modal interaction."""

    app_permissions: typing.Optional[permissions.Permissions] = attrs.field(eq=False, hash=False, repr=False)
    """Permissions the bot has in this interaction's channel if it's in a guild."""

    components: typing.Sequence[components_.ModalActionRowComponent] = attrs.field(eq=False, hash=False, repr=True)
    """Components in the modal."""

    async def fetch_channel(self) -> channels.TextableChannel:
        """Fetch the guild channel this interaction was triggered in.

        Returns
        -------
        hikari.channels.TextableChannel
            The requested partial channel derived object of the channel this
            interaction was triggered in.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][]
            permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.TextableChannel)
        return channel

    def get_channel(self) -> typing.Optional[channels.TextableGuildChannel]:
        """Get the guild channel this interaction was triggered in from the cache.

        !!! note
            This will always return [`None`][] for interactions triggered
            in a DM channel.

        Returns
        -------
        typing.Optional[hikari.channels.TextableGuildChannel]
            The object of the guild channel that was found in the cache or
            [`None`][].
        """
        if isinstance(self.app, traits.CacheAware):
            channel = self.app.cache.get_guild_channel(self.channel_id)
            assert channel is None or isinstance(channel, channels.TextableGuildChannel)
            return channel

        return None

    async def fetch_guild(self) -> typing.Optional[guilds.RESTGuild]:
        """Fetch the guild this interaction happened in.

        Returns
        -------
        typing.Optional[hikari.guilds.RESTGuild]
            Object of the guild this interaction happened in or [`None`][]
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        if not self.guild_id:
            return None

        return await self.app.rest.fetch_guild(self.guild_id)

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the object of the guild this interaction was triggered in from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the guild if found, else [`None`][].
        """
        if self.guild_id and isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_guild(self.guild_id)

        return None

    def build_response(self) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.modal_interactions.ModalInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        Examples
        --------
        ```py
            async def handle_modal_interaction(interaction: ModalInteraction) -> InteractionMessageBuilder:
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
            [`hikari.interactions.modal_interactions.ModalInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        !!! note
            Unlike [`hikari.api.special_endpoints.InteractionMessageBuilder`][],
            the result of this call can be returned as is without any modifications
            being made to it.

        Returns
        -------
        hikari.api.special_endpoints.InteractionDeferredBuilder
            Deferred interaction message response builder object.
        """
        return self.app.rest.interaction_deferred_builder(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)

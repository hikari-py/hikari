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
"""Base classes and enums inherited and used throughout the interactions flow."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "DEFERRED_RESPONSE_TYPES",
    "DeferredResponseTypesT",
    "InteractionMember",
    "InteractionChannel",
    "ResolvedOptionData",
    "InteractionType",
    "MessageResponseMixin",
    "MESSAGE_RESPONSE_TYPES",
    "MessageResponseTypesT",
    "PartialInteraction",
    "ModalResponseMixin",
    "ResponseType",
)

import typing

import attrs

from hikari import channels
from hikari import guilds
from hikari import snowflakes
from hikari import undefined
from hikari import webhooks
from hikari.internal import attrs_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import embeds as embeds_
    from hikari import files
    from hikari import messages
    from hikari import permissions as permissions_
    from hikari import traits
    from hikari import users
    from hikari.api import special_endpoints


_CommandResponseTypesT = typing.TypeVar("_CommandResponseTypesT", bound=int)


@typing.final
class InteractionType(int, enums.Enum):
    """The type of an interaction."""

    # PING isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.
    APPLICATION_COMMAND = 2
    """An interaction triggered by a user calling an application command."""

    MESSAGE_COMPONENT = 3
    """An interaction triggered by a user calling a message component."""

    AUTOCOMPLETE = 4
    """An interaction triggered by a user typing in a slash command option."""

    MODAL_SUBMIT = 5
    """An interaction triggered by a user submitting a modal."""


@typing.final
class ResponseType(int, enums.Enum):
    """The type of an interaction response."""

    # PONG isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.

    # Type 2 and 3 aren't included as they were deprecated/removed by Discord.
    MESSAGE_CREATE = 4
    """An immediate message response to an interaction.

    * [`hikari.interactions.base_interactions.InteractionType.APPLICATION_COMMAND`][]
    * [`hikari.interactions.base_interactions.InteractionType.MESSAGE_COMPONENT`][]
    """

    DEFERRED_MESSAGE_CREATE = 5
    """Acknowledge an interaction with the intention to edit in a message response later.

    The user will see a loading state when this type is used until this
    interaction expires or a message response is edited in over REST.

    This is valid for the following interaction types:

    * [`hikari.interactions.base_interactions.InteractionType.APPLICATION_COMMAND`][]
    * [`hikari.interactions.base_interactions.InteractionType.MESSAGE_COMPONENT`][]
    """

    DEFERRED_MESSAGE_UPDATE = 6
    """Acknowledge an interaction with the intention to edit its message later.

    This is valid for the following interaction types:

    * [`hikari.interactions.base_interactions.InteractionType.MESSAGE_COMPONENT`][]
    """

    MESSAGE_UPDATE = 7
    """An immediate interaction response with instructions on how to update its message.

    This is valid for the following interaction types:

    * [`hikari.interactions.base_interactions.InteractionType.MESSAGE_COMPONENT`][]
    """

    AUTOCOMPLETE = 8
    """Respond to an autocomplete interaction with suggested choices.

    This is valid for the following interaction types:

    * [`hikari.interactions.base_interactions.InteractionType.AUTOCOMPLETE`][]
    """

    MODAL = 9
    """An immediate interaction response with instructions to display a modal.

    This is valid for the following interaction types:

    * [`hikari.interactions.base_interactions.InteractionType.MODAL_SUBMIT`][]
    """


MESSAGE_RESPONSE_TYPES: typing.Final[typing.AbstractSet[MessageResponseTypesT]] = frozenset(
    [ResponseType.MESSAGE_CREATE, ResponseType.MESSAGE_UPDATE]
)
"""Set of the response types which are valid for message responses.

This includes the following:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]
* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]
"""

MessageResponseTypesT = typing.Literal[ResponseType.MESSAGE_CREATE, 4, ResponseType.MESSAGE_UPDATE, 7]
"""Type-hint of the response types which are valid for message responses.

The following are valid for this:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]/`4`
* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]/`7`
"""

DEFERRED_RESPONSE_TYPES: typing.Final[typing.AbstractSet[DeferredResponseTypesT]] = frozenset(
    [ResponseType.DEFERRED_MESSAGE_CREATE, ResponseType.DEFERRED_MESSAGE_UPDATE]
)
"""Set of the response types which are valid for deferred messages responses.

This includes the following:

* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]
"""

DeferredResponseTypesT = typing.Literal[
    ResponseType.DEFERRED_MESSAGE_CREATE, 5, ResponseType.DEFERRED_MESSAGE_UPDATE, 6
]
"""Type-hint of the response types which are valid for deferred messages responses.

The following are valid for this:

* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]/`5`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]/`6`
"""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class PartialInteraction(snowflakes.Unique, webhooks.ExecutableWebhook):
    """The base model for all interaction models."""

    app: traits.RESTAware = attrs.field(repr=False, eq=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attrs.field(eq=False, repr=False)
    """ID of the application this interaction belongs to."""

    type: typing.Union[InteractionType, int] = attrs.field(eq=False, repr=True)
    """The type of interaction this is."""

    token: str = attrs.field(eq=False, repr=False)
    """The interaction's token."""

    version: int = attrs.field(eq=False, repr=True)
    """Version of the interaction system this interaction is under."""

    @property
    def webhook_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ExecutableWebhook>>.
        return self.application_id


class MessageResponseMixin(PartialInteraction, typing.Generic[_CommandResponseTypesT]):
    """Mixin' class for all interaction types which can be responded to with a message."""

    __slots__: typing.Sequence[str] = ()

    async def fetch_initial_response(self) -> messages.Message:
        """Fetch the initial response of this interaction.

        Returns
        -------
        hikari.messages.Message
            Message object of the initial response.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the target interaction.
        hikari.errors.NotFoundError
            If the initial response isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_interaction_response(self.application_id, self.token)

    async def create_initial_response(
        self,
        response_type: _CommandResponseTypesT,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        flags: typing.Union[int, messages.MessageFlag, undefined.UndefinedType] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        attachment: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> None:
        """Create the initial response for this interaction.

        !!! warning
            Calling this on an interaction which already has an initial
            response will result in this raising a [`hikari.errors.NotFoundError`][].
            This includes if the REST interaction server has already responded
            to the request.

        Parameters
        ----------
        response_type : typing.Union[int, CommandResponseTypesT]
            The type of interaction response this is.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        flags : typing.Union[int, hikari.messages.MessageFlag, hikari.undefined.UndefinedType]
            If provided, the message flags this response should have.

            As of writing the only message flags which can be set here are
            [`hikari.messages.MessageFlag.EPHEMERAL`][], [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][]
            and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.

        Raises
        ------
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        TypeError
            If both `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction is not found or if the interaction's initial
            response has already been created.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long
        await self.app.rest.create_interaction_response(
            self.id,
            self.token,
            response_type,
            content,
            tts=tts,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            flags=flags,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def edit_initial_response(
        self,
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
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
        """Edit the initial response of this command interaction.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

        !!! warning
            If you specify a text `content`, `mentions_everyone`,
            `mentions_reply`, `user_mentions`, and `role_mentions` will default
            to [`False`][] as the message will be re-parsed for mentions. This will
            also occur if only one of the four are specified

            This is a limitation of Discord's design. If in doubt, specify all
            four of them each time.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedNoneOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and neither the
            `embed` or `embeds` kwargs are provided or if this is a
            [`hikari.files.Resourceish`][] and neither the `attachment` or
            `attachments` kwargs are provided, the values will be overwritten.
            This allows for simpler syntax when sending an embed or an
            attachment alone.

            Likewise, if this is a [`hikari.files.Resource`][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the attachment to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachment, if
            present, is not changed. If this is [`None`][], then the
            attachment is removed, if present. Otherwise, the new attachment
            that was provided will be attached.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the attachments to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachments, if
            present, are not changed. If this is [`None`][], then the
            attachments is removed, if present. Otherwise, the new attachments
            that were provided will be attached.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to set for this message.
            This component will replace any previously set components and passing
            [`None`][] will remove all components.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects set for
            this message. These components will replace any previously set
            components and passing [`None`][] or an empty sequence will
            remove all components.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embed that was provided will be used as the
            replacement.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the embeds to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embeds that were provided will be used as the
            replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        TypeError
            If both `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction or the message are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long
        return await self.app.rest.edit_interaction_response(
            self.application_id,
            self.token,
            content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete_initial_response(self) -> None:
        """Delete the initial response of this interaction.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction or response is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        await self.app.rest.delete_interaction_response(self.application_id, self.token)


class ModalResponseMixin(PartialInteraction):
    """Mixin' class for all interaction types which can be responded to with a modal."""

    __slots__: typing.Sequence[str] = ()

    async def create_modal_response(
        self,
        title: str,
        custom_id: str,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
    ) -> None:
        """Create a response by sending a modal.

        Parameters
        ----------
        title : str
            The title that will show up in the modal.
        custom_id : str
            Developer set custom ID used for identifying interactions with this modal.

        Other Parameters
        ----------------
        component : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A component builder to send in this modal.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A sequence of component builders to send in this modal.

        Raises
        ------
        ValueError
            If both `component` and `components` are specified or if none are specified.
        """
        await self.app.rest.create_modal_response(
            self.id, self.token, title=title, custom_id=custom_id, component=component, components=components
        )

    def build_modal_response(self, title: str, custom_id: str) -> special_endpoints.InteractionModalBuilder:
        """Create a builder for a modal interaction response.

        Parameters
        ----------
        title : str
            The title that will show up in the modal.
        custom_id : str
            Developer set custom ID used for identifying interactions with this modal.

        Returns
        -------
        hikari.api.special_endpoints.InteractionModalBuilder
            The interaction modal response builder object.
        """
        return self.app.rest.interaction_modal_builder(title=title, custom_id=custom_id)


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class InteractionMember(guilds.Member):
    """Model of the member who triggered an interaction.

    Unlike [`hikari.guilds.Member`][], this object comes with an extra
    [`hikari.interactions.base_interactions.InteractionMember.permissions`][] field.
    """

    permissions: permissions_.Permissions = attrs.field(eq=False, hash=False, repr=False)
    """Permissions the member has in the current channel."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class InteractionChannel(channels.PartialChannel):
    """Represents partial channels returned as resolved entities on interactions."""

    permissions: permissions_.Permissions = attrs.field(eq=False, hash=False, repr=True)
    """Permissions the command's executor has in this channel."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class ResolvedOptionData:
    """Represents the resolved objects of entities referenced in a command's options."""

    attachments: typing.Mapping[snowflakes.Snowflake, messages.Attachment] = attrs.field(repr=False)
    """Mapping of snowflake IDs to the attachment objects."""

    channels: typing.Mapping[snowflakes.Snowflake, InteractionChannel] = attrs.field(repr=False)
    """Mapping of snowflake IDs to the resolved option partial channel objects."""

    members: typing.Mapping[snowflakes.Snowflake, InteractionMember] = attrs.field(repr=False)
    """Mapping of snowflake IDs to the resolved option member objects."""

    messages: typing.Mapping[snowflakes.Snowflake, messages.Message] = attrs.field(repr=False)
    """Mapping of snowflake IDs to the resolved option partial message objects."""

    roles: typing.Mapping[snowflakes.Snowflake, guilds.Role] = attrs.field(repr=False)
    """Mapping of snowflake IDs to the resolved option role objects."""

    users: typing.Mapping[snowflakes.Snowflake, users.User] = attrs.field(repr=False)
    """Mapping of snowflake IDs to the resolved option user objects."""

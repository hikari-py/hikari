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
"""Base classes and enums inherited and used throughout the interactions flow."""
from __future__ import annotations

__all__: typing.List[str] = [
    "DEFERRED_RESPONSE_TYPES",
    "DeferredResponseTypesT",
    "InteractionMember",
    "InteractionType",
    "MessageResponseMixin",
    "MESSAGE_RESPONSE_TYPES",
    "MessageResponseTypesT",
    "PartialInteraction",
    "ResponseType",
]

import typing

import attr

from hikari import guilds
from hikari import snowflakes
from hikari import undefined
from hikari import webhooks
from hikari.internal import attr_extensions
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


@typing.final
class ResponseType(int, enums.Enum):
    """The type of an interaction response."""

    # PONG isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.

    # Type 2 and 3 aren't included as they were deprecated/removed by Discord.
    MESSAGE_CREATE = 4
    """An immediate message response to an interaction.

    * `InteractionType.APPLICATION_COMMAND`
    * `InteractionType.MESSAGE_COMPONENT`
    """

    DEFERRED_MESSAGE_CREATE = 5
    """Acknowledge an interaction with the intention to edit in a message response later.

    The user will see a loading state when this type is used until this
    interaction expires or a message response is edited in over REST.

    This is valid for the following interaction types:

    * `InteractionType.APPLICATION_COMMAND`
    * `InteractionType.MESSAGE_COMPONENT`
    """

    DEFERRED_MESSAGE_UPDATE = 6
    """Acknowledge an interaction with the intention to edit its message later.

    This is valid for the following interaction types:

    * `InteractionType.MESSAGE_COMPONENT`
    """

    MESSAGE_UPDATE = 7
    """An immediate interaction response with instructions on how to update its message.

    This is valid for the following interaction types:

    * `InteractionType.MESSAGE_COMPONENT`
    """


MESSAGE_RESPONSE_TYPES: typing.Final[typing.AbstractSet[MessageResponseTypesT]] = frozenset(
    [ResponseType.MESSAGE_CREATE, ResponseType.MESSAGE_UPDATE]
)
"""Set of the response types which are valid for message responses.

This includes the following:

* `ResponseType.MESSAGE_CREATE`
* `ResponseType.MESSAGE_UPDATE`
"""

MessageResponseTypesT = typing.Literal[ResponseType.MESSAGE_CREATE, 4, ResponseType.MESSAGE_UPDATE, 7]
"""Type-hint of the response types which are valid for message responses.

The following are valid for this:

* `ResponseType.MESSAGE_CREATE`/`4`
* `ResponseType.MESSAGE_UPDATE`/`7`
"""

DEFERRED_RESPONSE_TYPES: typing.Final[typing.AbstractSet[DeferredResponseTypesT]] = frozenset(
    [ResponseType.DEFERRED_MESSAGE_CREATE, ResponseType.DEFERRED_MESSAGE_UPDATE]
)
"""Set of the response types which are valid for deferred messages responses.

This includes the following:

* `ResponseType.DEFERRED_MESSAGE_CREATE`
* `ResponseType.DEFERRED_MESSAGE_UPDATE`
"""

DeferredResponseTypesT = typing.Literal[
    ResponseType.DEFERRED_MESSAGE_CREATE, 5, ResponseType.DEFERRED_MESSAGE_UPDATE, 6
]

"""Type-hint of the response types which are valid for deferred messages responses.

The following are valid for this:

* `ResponseType.DEFERRED_MESSAGE_CREATE`/`5`
* `ResponseType.DEFERRED_MESSAGE_UPDATE`/`6`
"""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialInteraction(snowflakes.Unique, webhooks.ExecutableWebhook):
    """The base model for all interaction models."""

    app: traits.RESTAware = attr.field(repr=False, eq=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.field(eq=False, repr=False)
    """ID of the application this interaction belongs to."""

    type: typing.Union[InteractionType, int] = attr.field(eq=False, repr=True)
    """The type of interaction this is."""

    token: str = attr.field(eq=False, repr=False)
    """The interaction's token."""

    version: int = attr.field(eq=False, repr=True)
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
        return await self.app.rest.fetch_interaction_response(self.application_id, self.token)

    async def create_initial_response(
        self,
        response_type: _CommandResponseTypesT,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        flags: typing.Union[int, messages.MessageFlag, undefined.UndefinedType] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
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
        """Create the initial response for this interaction.

        !!! warning
            Calling this on an interaction which already has an initial
            response will result in this raising a `hikari.errors.NotFoundError`.
            This includes if the REST interaction server has already responded
            to the request.

        Parameters
        ----------
        response_type : typing.Union[builtins.int, CommandResponseTypesT]
            The type of interaction response this is.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.
        component : hikari.undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        flags : typing.Union[builtins.int, hikari.messages.MessageFlag, hikari.undefined.UndefinedType]
            If provided, the message flags this response should have.

            As of writing the only message flag which can be set here is
            `hikari.messages.MessageFlag.EPHEMERAL`.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, and `builtins.True`, all user mentions will be detected.
            If provided, and `builtins.False`, all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, and `builtins.True`, all role mentions will be detected.
            If provided, and `builtins.False`, all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        Raises
        ------
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
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
        """  # noqa: E501 - Line too long
        await self.app.rest.create_interaction_response(
            self.id,
            self.token,
            response_type,
            content,
            tts=tts,
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
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        replace_attachments: bool = False,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages.Message:
        """Edit the initial response of this command interaction.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedNoneOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and neither the
            `embed` or `embeds` kwargs are provided or if this is a
            `hikari.files.Resourceish` and neither the `attachment` or
            `attachments` kwargs are provided, the values will be overwritten.
            This allows for simpler syntax when sending an embed or an
            attachment alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the attachment to set on the message. If
            `hikari.undefined.UNDEFINED`, the previous attachment, if
            present, is not changed. If this is `builtins.None`, then the
            attachment is removed, if present. Otherwise, the new attachment
            that was provided will be attached.
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]]
            If provided, the attachments to set on the message. If
            `hikari.undefined.UNDEFINED`, the previous attachments, if
            present, are not changed. If this is `builtins.None`, then the
            attachments is removed, if present. Otherwise, the new attachments
            that were provided will be attached.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to set for this message.
            This component will replace any previously set components and passing
            `builtins.None` will remove all components.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects set for
            this message. These components will replace any previously set
            components and passing `builtins.None` or an empty sequence will
            remove all components.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            `hikari.undefined.UNDEFINED`, the previous embed(s) are not changed.
            If this is `builtins.None` then any present embeds are removed.
            Otherwise, the new embed that was provided will be used as the
            replacement.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the embeds to set on the message. If
            `hikari.undefined.UNDEFINED`, the previous embed(s) are not changed.
            If this is `builtins.None` then any present embeds are removed.
            Otherwise, the new embeds that were provided will be used as the
            replacement.
        replace_attachments: bool
            Whether to replace the attachments with the provided ones. Defaults
            to `builtins.False`.

            Note this will also overwrite the embed attachments.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, and `builtins.True`, all user mentions will be detected.
            If provided, and `builtins.False`, all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, and `builtins.True`, all role mentions will be detected.
            If provided, and `builtins.False`, all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

        !!! warning
            If you specify one of `mentions_everyone`, `user_mentions`, or
            `role_mentions`, then all others will default to `builtins.False`,
            even if they were enabled previously.

            This is a limitation of Discord's design. If in doubt, specify all three of
            them each time.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
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
            replace_attachments=replace_attachments,
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
        await self.app.rest.delete_interaction_response(self.application_id, self.token)


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class InteractionMember(guilds.Member):
    """Model of the member who triggered an interaction.

    Unlike `hikari.guilds.Member`, this object comes with an extra
    `InteractionMember.permissions` field.
    """

    permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=False)
    """Permissions the member has in the current channel."""

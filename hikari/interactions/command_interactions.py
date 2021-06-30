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
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.interactions import base_interactions
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import commands
    from hikari import embeds as embeds_
    from hikari import files
    from hikari import guilds
    from hikari import messages
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

CommandResponseTypesT = typing.Union[
    typing.Literal[base_interactions.ResponseType.MESSAGE_CREATE],
    typing.Literal[4],
    typing.Literal[base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE],
    typing.Literal[5],
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

    value: typing.Union[str, int, bool, float, None] = attr.field(repr=True)
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
class CommandInteraction(base_interactions.PartialInteraction):
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
        response_type: CommandResponseTypesT,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        flags: typing.Union[int, messages.MessageFlag, undefined.UndefinedType] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]
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
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        replace_attachments: bool = False,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]
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
            invalid image URLs in embeds.
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
            replace_attachments=replace_attachments,
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
        return await self.app.rest.fetch_channel(self.channel_id)

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

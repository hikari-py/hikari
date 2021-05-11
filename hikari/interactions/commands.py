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
    "Command",
    "CommandChoice",
    "CommandInteractionOption",
    "CommandInteraction",
    "CommandOption",
    "InteractionChannel",
    "InteractionMember",
    "ResolvedOptionData",
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
from hikari.interactions import bases
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
        This will be inclusively between 1-32 characters in length and will
        match the regex `^[\w-]{1,32}$`.
    """

    description: str = attr.field(repr=False)
    """The command option's description.

    !!! note
        This will be inclusively between 1-100 characters in length.
    """

    is_required: bool = attr.field(repr=False)
    """Whether this command """

    choices: typing.Optional[typing.Sequence[CommandChoice]] = attr.field(repr=False)
    """A sequence of up to (and including) 25 choices for this command.

    This will be `builtins.None` if the input values for this option aren't
    limited to specific values or if it's a subcommand or subcommand-group type
    option.
    """

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.field(repr=False)
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
        This will be inclusively between 1-32 characters in length and will
        match the regex `^[\w-]{1,32}$`.
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
        hikari.interactions.commands.Command
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
        options : hikari.undefined.UndefinedOr[typing.Sequence[hikari.interactions.commands.CommandOption]]
            A sequence of up to 10 options to set for this command. Leave this as
            `hikari.undefined.UNDEFINED` to not change.

        Returns
        -------
        hikari.interactions.commands.Command
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

    users: typing.Mapping[snowflakes.Snowflake, users.User] = attr.field(repr=False)
    """Mapping of snowflake IDs to the resolved option user objects."""

    members: typing.Mapping[snowflakes.Snowflake, InteractionMember] = attr.field(repr=False)
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

    type: OptionType = attr.field(repr=True)
    """Type of this option."""

    value: typing.Optional[typing.Sequence[typing.Union[str, int, bool]]] = attr.field(repr=True)
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


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class InteractionMember(guilds.Member):
    """Model of the member who triggered an interaction.

    Unlike `hikari.guilds.Member`, this object comes with an extra
    `InteractionMember.permissions` field.
    """

    permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=False)
    """Permissions the member has in the current channel."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class CommandInteraction(bases.PartialInteraction, webhooks.ExecutableWebhook):
    """Represents a command interaction on Discord."""

    channel_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the channel this command interaction event was triggered in."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=True)
    """ID of the guild this command interaction event was triggered in.

    This will be `builtins.None` for command interactions triggered in DMs.
    """

    member: typing.Optional[InteractionMember] = attr.field(eq=False, hash=False, repr=True)
    """The member who triggered this command interaction.

    This will be `builtins.None` for command interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    user: users.User = attr.field(eq=False, hash=False, repr=True)
    """The user who triggered this command interaction."""

    command_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the command being invoked."""

    command_name: str = attr.field(eq=False, hash=False, repr=True)
    """Name of the command being invoked."""

    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.field(eq=False, hash=False, repr=True)
    """Parameter values provided by the user invoking this command."""

    resolved: typing.Optional[ResolvedOptionData] = attr.field(eq=False, hash=False, repr=False)
    """Mappings of the objects resolved for the provided command options."""

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
        return await self.app.rest.fetch_command_response(self.application_id, self.token)

    async def create_initial_response(
        self,
        response_type: bases.ResponseType,
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
        """Create the initial response for this interaction.

        !!! warning
            Calling this on an interaction which already has an initial response
            with further calls will result in this raising a
            `hikari.errors.NotFoundError`. This includes if the REST interaction
            server has already responded to the request.

        Parameters
        ----------
        response_type : hikari.interactions.bases.ResponseType
            The type of interaction response this is.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` nor
            no `embeds` kwarg is provided, then this will instead
            update the embed. This allows for simpler syntax when
            sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embeds.
        flags : typing.Union[builtins.int, hikari.messages.MessageFlag, hikari.undefined.UndefinedType]
            If provided, the message flags this response should have.

            As of writing the only message flag which can be set here is
            `hikari.messages.MessageFlag.EPHEMERAL`.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        nonce : hikari.undefined.UndefinedOr[builtins.str]
            An arbitrary identifier to associate with the message. This
            can be used to identify it later in received events. If provided,
            this must be less than 32 bytes. If not provided, then
            a null value is placed on the message instead. All users can
            see this value.
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
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
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
        """Edit the initial response of this command interaction.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedNoneOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` nor
            no `embeds` kwarg is provided, then this will instead
            update the embed. This allows for simpler syntax when
            sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the message embeds.
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

        !!! note
            There is currently no documented way to clear attachments or edit
            attachments from a previously sent message on Discord's API. To
            do this, delete the message and re-send it. This also applies
            to embed attachments.

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
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
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

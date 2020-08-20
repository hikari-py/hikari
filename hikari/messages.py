# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Application and entities that are used to describe messages on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "MessageType",
    "MessageFlag",
    "MessageActivityType",
    "Attachment",
    "Reaction",
    "MessageActivity",
    "MessageCrosspost",
    "PartialMessage",
    "Message",
]

import enum
import typing

import attr

from hikari import files
from hikari import snowflakes
from hikari import undefined
from hikari.utilities import attr_extensions
from hikari.utilities import constants
from hikari.utilities import flag

if typing.TYPE_CHECKING:
    import datetime

    from hikari import applications
    from hikari import channels
    from hikari import embeds as embeds_
    from hikari import emojis as emojis_
    from hikari import guilds
    from hikari import traits
    from hikari import users


@enum.unique
@typing.final
class MessageType(enum.IntEnum):
    """The type of a message."""

    DEFAULT = 0
    """A normal message."""

    RECIPIENT_ADD = 1
    """A message to denote a new recipient in a group."""

    RECIPIENT_REMOVE = 2
    """A message to denote that a recipient left the group."""

    CALL = 3
    """A message to denote a VoIP call."""

    CHANNEL_NAME_CHANGE = 4
    """A message to denote that the name of a channel changed."""

    CHANNEL_ICON_CHANGE = 5
    """A message to denote that the icon of a channel changed."""

    CHANNEL_PINNED_MESSAGE = 6
    """A message to denote that a message was pinned."""

    GUILD_MEMBER_JOIN = 7
    """A message to denote that a member joined the guild."""

    USER_PREMIUM_GUILD_SUBSCRIPTION = 8
    """A message to denote a Nitro subscription."""

    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1 = 9
    """A message to denote a tier 1 Nitro subscription."""

    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2 = 10
    """A message to denote a tier 2 Nitro subscription."""

    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3 = 11
    """A message to denote a tier 3 Nitro subscription."""

    CHANNEL_FOLLOW_ADD = 12
    """Channel follow add."""

    def __str__(self) -> str:
        return self.name


@enum.unique
@typing.final
class MessageFlag(flag.Flag):
    """Additional flags for message options."""

    NONE = 0
    """None"""

    CROSSPOSTED = 1 << 0
    """This message has been published to subscribed channels via channel following."""

    IS_CROSSPOST = 1 << 1
    """This message originated from a message in another channel via channel following."""

    SUPPRESS_EMBEDS = 1 << 2
    """Any embeds on this message should be omitted when serializing the message."""

    SOURCE_MESSAGE_DELETED = 1 << 3
    """The message this crosspost originated from was deleted via channel following."""

    URGENT = 1 << 4
    """This message came from the urgent message system."""


@enum.unique
@typing.final
class MessageActivityType(enum.IntEnum):
    """The type of a rich presence message activity."""

    NONE = 0
    """No activity."""

    JOIN = 1
    """Join an activity."""

    SPECTATE = 2
    """Spectating something."""

    LISTEN = 3
    """Listening to something."""

    JOIN_REQUEST = 5
    """Request to join an activity."""

    def __str__(self) -> str:
        return self.name


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class Attachment(snowflakes.Unique, files.WebResource):
    """Represents a file attached to a message.

    You can use this object in the same way as a `hikari.files.WebResource`,
    by passing it as an attached file when creating a message, etc.
    """

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    url: str = attr.ib(repr=True)
    """The source URL of file."""

    filename: str = attr.ib(repr=True)
    """The name of the file."""

    size: int = attr.ib(repr=True)
    """The size of the file in bytes."""

    proxy_url: str = attr.ib(repr=False)
    """The proxied URL of file."""

    height: typing.Optional[int] = attr.ib(repr=False)
    """The height of the image (if the file is an image)."""

    width: typing.Optional[int] = attr.ib(repr=False)
    """The width of the image (if the file is an image)."""

    def __str__(self) -> str:
        return self.filename


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Reaction:
    """Represents a reaction in a message."""

    count: int = attr.ib(eq=False, hash=False, repr=True)
    """The number of times the emoji has been used to react."""

    emoji: typing.Union[emojis_.UnicodeEmoji, emojis_.CustomEmoji] = attr.ib(eq=True, hash=True, repr=True)
    """The emoji used to react."""

    is_me: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the current user reacted using this emoji."""

    def __str__(self) -> str:
        return str(self.emoji)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class MessageActivity:
    """Represents the activity of a rich presence-enabled message."""

    type: MessageActivityType = attr.ib(repr=True)
    """The type of message activity."""

    party_id: typing.Optional[str] = attr.ib(repr=True)
    """The party ID of the message activity."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class MessageCrosspost:
    """Represents information about a cross-posted message.

    This is a message that is sent in one channel/guild and may be
    "published" to another.
    """

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    # TODO: get clarification on this! If it cannot happen, this should subclass PartialMessage too.
    id: typing.Optional[snowflakes.Snowflake] = attr.ib(repr=True)
    """The ID of the message.

    !!! warning
        This may be `builtins.None` in some cases according to the Discord API
        documentation, but the situations that cause this to occur are not
        currently documented.
    """

    channel_id: snowflakes.Snowflake = attr.ib(repr=True)
    """The ID of the channel that the message originated from."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(repr=True)
    """The ID of the guild that the message originated from.

    !!! warning
        This may be `builtins.None` in some cases according to the Discord API
        documentation, but the situations that cause this to occur are not
        currently documented.
    """


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, init=True, repr=True, eq=False, weakref_slot=False)
class PartialMessage(snowflakes.Unique):
    """A message representation containing partially populated information.

    This contains arbitrary fields that may be updated in a
    `MessageUpdateEvent`, but for all other purposes should be treated as
    being optionally specified.

    !!! warn
        All fields on this model except `channel` and `id` may be set to
        `hikari.undefined.UndefinedType` (a singleton) if we have not
        received information about their state from Discord alongside field
        nullability.
    """

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    channel_id: snowflakes.Snowflake = attr.ib(repr=True)
    """The ID of the channel that the message was sent in."""

    guild_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = attr.ib(repr=True)
    """The ID of the guild that the message was sent in."""

    author: undefined.UndefinedOr[users.User] = attr.ib(repr=True)
    """The author of this message."""

    member: undefined.UndefinedNoneOr[guilds.Member] = attr.ib(repr=False)
    """The member properties for the message's author."""

    content: undefined.UndefinedNoneOr[str] = attr.ib(repr=False)
    """The content of the message."""

    timestamp: undefined.UndefinedOr[datetime.datetime] = attr.ib(repr=False)
    """The timestamp that the message was sent at."""

    edited_timestamp: undefined.UndefinedNoneOr[datetime.datetime] = attr.ib(repr=False)
    """The timestamp that the message was last edited at.

    Will be `builtins.None` if the message wasn't ever edited, or `undefined`
    if the info is not available.
    """

    is_tts: undefined.UndefinedOr[bool] = attr.ib(repr=False)
    """Whether the message is a TTS message."""

    is_mentioning_everyone: undefined.UndefinedOr[bool] = attr.ib(repr=False)
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = attr.ib(repr=False)
    """The users the message mentions."""

    role_mentions: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = attr.ib(repr=False)
    """The roles the message mentions."""

    channel_mentions: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = attr.ib(repr=False)
    """The channels the message mentions."""

    attachments: undefined.UndefinedOr[typing.Sequence[Attachment]] = attr.ib(repr=False)
    """The message attachments."""

    embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = attr.ib(repr=False)
    """The message's embeds."""

    reactions: undefined.UndefinedOr[typing.Sequence[Reaction]] = attr.ib(repr=False)
    """The message's reactions."""

    is_pinned: undefined.UndefinedOr[bool] = attr.ib(repr=False)
    """Whether the message is pinned."""

    webhook_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = attr.ib(repr=False)
    """If the message was generated by a webhook, the webhook's ID."""

    type: undefined.UndefinedOr[MessageType] = attr.ib(repr=False)
    """The message's type."""

    activity: undefined.UndefinedNoneOr[MessageActivity] = attr.ib(repr=False)
    """The message's activity."""

    application: undefined.UndefinedNoneOr[applications.Application] = attr.ib(repr=False)
    """The message's application."""

    message_reference: undefined.UndefinedNoneOr[MessageCrosspost] = attr.ib(repr=False)
    """The message's cross-posted reference data."""

    flags: undefined.UndefinedNoneOr[MessageFlag] = attr.ib(repr=False)
    """The message's flags."""

    nonce: undefined.UndefinedNoneOr[str] = attr.ib(repr=False)
    """The message nonce.

    This is a string used for validating a message was sent.
    """

    @property
    def link(self) -> str:
        """Jump link to the message.

        Returns
        -------
        builtins.str
            The jump link to the message.
        """
        if self.guild_id is None:
            return f"{constants.BASE_URL}/channels/@me/{self.channel_id}/{self.id}"
        return f"{constants.BASE_URL}/channels/{self.guild_id}/{self.channel_id}/{self.id}"

    async def fetch_channel(self) -> channels.PartialChannel:
        """Fetch the channel this message was created in.

        Returns
        -------
        hikari.channels.PartialChannel
            The object of the channel this message belongs to.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you don't have access to the channel this message belongs to.
        hikari.errors.NotFound
            If the channel this message was created in does not exist.
        """
        return await self.app.rest.fetch_channel(self.channel_id)

    async def edit(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedOr[MessageFlag] = undefined.UNDEFINED,
    ) -> Message:
        """Edit an existing message in a given channel.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            The message content to update with. If
            `hikari.undefined.UNDEFINED`, then the content will not
            be changed. If `builtins.None`, then the content will be removed.

            Any other value will be cast to a `builtins.str` before sending.

            If this is a `hikari.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            The embed to set on the message. If
            `hikari.undefined.UNDEFINED`, the previous embed if
            present is not changed. If this is `builtins.None`, then the embed
            is removed if present. Otherwise, the new embed value that was
            provided will be used as the replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            Sanitation for `@everyone` mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, then `@everyone`/`@here` mentions
            in the message content will show up as mentioning everyone that can
            view the chat.
        user_mentions : hikari.undefined.UndefinedOr[typing.Collection[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser] or builtins.bool]
            Sanitation for user mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid user mentions will behave
            as mentions. If `builtins.False`, all valid user mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.snowflakes.Snowflake` user IDs, or
            `hikari.users.PartialUser`-derived objects.
        role_mentions : hikari.undefined.UndefinedOr[typing.Collection[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole] or builtins.bool]
            Sanitation for role mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid role mentions will behave
            as mentions. If `builtins.False`, all valid role mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.snowflakes.Snowflake` role IDs, or
            `hikari.guilds.PartialRole`-derived objects.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            Optional flags to set on the message. If
            `hikari.undefined.UNDEFINED`, then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are `NONE` and `SUPPRESS_EMBEDS`. If you
            have `MANAGE_MESSAGES` permissions, you can use this call to
            suppress embeds on another user's message.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

        !!! note
            There is currently no documented way to clear attachments or edit
            attachments from a previously sent message on Discord's API. To
            do this, `delete` the message and re-send it.

        !!! warning
            If the message was not sent by your user, the only parameter
            you may provide to this call is the `flags` parameter. Anything
            else will result in a `hikari.errors.Forbidden` being raised.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds; users in `user_mentions` not
            being mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel; if
            you try to change the contents of another user's message; or if you
            try to edit the flags on another user's message without the
            permissions to manage messages.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long
        return await self.app.rest.edit_message(
            message=self.id,
            channel=self.channel_id,
            content=content,
            embed=embed,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            flags=flags,
        )

    async def reply(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> Message:
        """Create a message in the given channel.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If specified, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If specified, the message embed.
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish],
            If specified, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]],
            If specified, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If specified, whether the message will be TTS (Text To Speech).
        nonce : hikari.undefined.UndefinedOr[builtins.str]
            If specified, a nonce that can be used for optimistic message
            sending.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If specified, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Collection[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser] or builtins.bool]
            If specified, and `builtins.True`, all mentions will be parsed.
            If specified, and `builtins.False`, no mentions will be parsed.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Collection[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole] or builtins.bool]
            If specified, and `builtins.True`, all mentions will be parsed.
            If specified, and `builtins.False`, no mentions will be parsed.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        !!! note
            Attachments can be passed as many different things, to aid in
            convenience.

            - If a `pathlib.PurePath` or `builtins.str` to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                `hikari.files.WebResource` such as
                `hikari.files.URL`,
                `hikari.messages.Attachment`,
                `hikari.emojis.Emoji`,
                `EmbedResource`, etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a `hikari.files.Bytes` is passed, or a `builtins.str`
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a `hikari.files.File`, `pathlib.PurePath` or
                `builtins.str` that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of `concurrent.futures.Executor` that is being used for
                the application (default is a thread pool which supports this
                behaviour).

        Returns
        -------
        hikari.messages.Message
            The created message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
            If both `attachment` and `attachments` are specified.

        !!! warning
            You are expected to make a connection to the gateway and identify
            once before being able to use this endpoint for a bot.
        """  # noqa: E501 - Line too long
        return await self.app.rest.create_message(
            channel=self.channel_id,
            content=content,
            embed=embed,
            attachment=attachment,
            attachments=attachments,
            nonce=nonce,
            tts=tts,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete(self) -> None:
        """Delete this message.

        Raises
        ------
        hikari.errors.NotFound
            If the channel this message was created in is not found, or if the
            message has already been deleted.
        hikari.errors.Forbidden
            If you lack the permissions to delete the message.
        """
        await self.app.rest.delete_message(self.channel_id, self.id)

    async def add_reaction(self, emoji: emojis_.Emojiish) -> None:
        r"""Add a reaction to this message.

        Parameters
        ----------
        emoji : hikari.emojis.Emojiish
            The emoji to add. This may be a unicode emoji string, the
            `name:id` of a custom emoji, or a subclass of
            `hikari.emojis.Emoji`.

            Note that if the emoji is an `hikari.emojis.CustomEmoji`
            and is not from a guild the bot user is in, then this will fail.

        Examples
        --------
        ```py
        # Using a unicode emoji.
        await message.add_reaction("👌")

        # Using a unicode emoji name.
        await message.add_reaction("\N{OK HAND SIGN}")

        # Using the `name:id` format.
        await message.add_reaction("rooAYAYA:705837374319493284")

        # Using a raw custom emoji mention (unanimated and animated)
        await message.add_reaction("<:rooAYAYA:705837374319493284>")
        await message.add_reaction("<a:rooAYAYA:705837374319493284>")

        # Using an Emoji-derived object.
        await message.add_reaction(some_emoji_object)
        ```

        Raises
        ------
        hikari.errors.BadRequest
            If the emoji is invalid, unknown, or formatted incorrectly.
        hikari.errors.Forbidden
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
        hikari.errors.NotFound
            If the channel or message is not found, or if the emoji is not
            found.

            This will also occur if you try to add an emoji from a
            guild you are not part of if no one else has previously
            reacted with the same emoji.
        """
        await self.app.rest.add_reaction(channel=self.channel_id, message=self.id, emoji=emoji)

    async def remove_reaction(
        self,
        emoji: emojis_.Emojiish,
        *,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
    ) -> None:
        r"""Remove a reaction from this message.

        Parameters
        ----------
        emoji : hikari.emojis.Emojiish
            The emoji to remove.
        user : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]
            The user of the reaction to remove. If unspecified, then the bot's
            reaction is removed instead.

        Examples
        --------
            # Using a unicode emoji and removing the bot's reaction from this
            # reaction.
            await message.remove_reaction("\N{OK HAND SIGN}")

            # Using a unicode emoji and removing a specific user from this
            # reaction.
            await message.remove_reaction("\N{OK HAND SIGN}", some_user)

            # Using a raw custom emoji mention (unanimated and animated)
            await message.remove_reaction("<:rooAYAYA:705837374319493284>", some_user)
            await message.remove_reaction("<a:rooAYAYA:705837374319493284>", some_user)

            # Using an Emoji object and removing a specific user from this
            # reaction.
            await message.remove_reaction(some_emoji_object, some_user)

        Raises
        ------
        hikari.errors.BadRequest
            If the emoji is invalid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error. If you
            remove the reaction of another user without `MANAGE_MESSAGES`, this
            will be raised.
        hikari.errors.NotFound
            If the channel or message is not found, or if the emoji is not
            found.
        """
        if user is undefined.UNDEFINED:
            await self.app.rest.delete_my_reaction(channel=self.channel_id, message=self.id, emoji=emoji)
        else:
            await self.app.rest.delete_reaction(channel=self.channel_id, message=self.id, emoji=emoji, user=user)

    async def remove_all_reactions(self, emoji: undefined.UndefinedOr[emojis_.Emojiish] = undefined.UNDEFINED) -> None:
        r"""Remove all users' reactions for a specific emoji from the message.

        Parameters
        ----------
        emoji : hikari.undefined.UndefinedOr[hikari.emojis.Emojiish]
            The emoji to remove all reactions for. If not specified, then all
            emojis are removed.

        Example
        --------
            # Using a unicode emoji and removing all 👌 reacts from the message.
            # reaction.
            await message.remove_all_reactions("\N{OK HAND SIGN}")

            # Using a raw custom emoji mention (unanimated and animated)
            await message.remove_all_reactions("<:rooAYAYA:705837374319493284>")
            await message.remove_all_reactions("<a:rooAYAYA:705837374319493284>")

            # Removing all reactions entirely.
            await message.remove_all_reactions()

        Raises
        ------
        hikari.errors.Forbidden
            If you are missing the `MANAGE_MESSAGES` permission, or the
            permission to view the channel
        hikari.errors.NotFound
            If the channel or message is not found, or if the emoji is not
            found.
        hikari.errors.BadRequest
            If the emoji is invalid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        if emoji is undefined.UNDEFINED:
            await self.app.rest.delete_all_reactions(channel=self.channel_id, message=self.id)
        else:
            await self.app.rest.delete_all_reactions_for_emoji(channel=self.channel_id, message=self.id, emoji=emoji)


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Message(PartialMessage):
    """Represents a message with all known details."""

    # These are purposely not auto attribs, but instead just specify a
    # tighter type bounds (i.e. none are allowed to be undefined.Undefined
    # in this model). We use this in cases where we know all information is
    # present. DO NOT ADD attr.ib TO ANY OF THESE, OR ENABLE auto_attribs
    # IN THIS CLASS, the latter will mess up slotting or cause layout conflicts
    # and possibly result in large amounts of unwasted memory if you get that
    # far.

    guild_id: typing.Optional[snowflakes.Snowflake]
    """The ID of the guild that the message was sent in."""

    author: users.User
    """The author of this message."""

    member: typing.Optional[guilds.Member]
    """The member properties for the message's author."""

    content: typing.Optional[str]
    """The content of the message."""

    timestamp: datetime.datetime
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Optional[datetime.datetime]
    """The timestamp that the message was last edited at.

    Will be `builtins.None` if it wasn't ever edited.
    """

    is_tts: bool
    """Whether the message is a TTS message."""

    is_mentioning_everyone: bool
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: typing.Sequence[snowflakes.Snowflake]
    """The users the message mentions."""

    role_mentions: typing.Sequence[snowflakes.Snowflake]
    """The roles the message mentions."""

    channel_mentions: typing.Sequence[snowflakes.Snowflake]
    """The channels the message mentions."""

    attachments: typing.Sequence[Attachment]
    """The message attachments."""

    embeds: typing.Sequence[embeds_.Embed]
    """The message embeds."""

    reactions: typing.Sequence[Reaction]
    """The message reactions."""

    is_pinned: bool
    """Whether the message is pinned."""

    webhook_id: typing.Optional[snowflakes.Snowflake]
    """If the message was generated by a webhook, the webhook's id."""

    type: MessageType
    """The message type."""

    activity: typing.Optional[MessageActivity]
    """The message activity."""

    application: typing.Optional[applications.Application]
    """The message application."""

    message_reference: typing.Optional[MessageCrosspost]
    """The message crossposted reference data."""

    flags: typing.Optional[MessageFlag]
    """The message flags."""

    nonce: typing.Optional[str]
    """The message nonce. This is a string used for validating a message was sent."""

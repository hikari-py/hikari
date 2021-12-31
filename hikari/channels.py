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
"""Application and entities that are used to describe both DMs and guild channels on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "ChannelType",
    "VideoQualityMode",
    "ChannelFollow",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "TextableChannel",
    "TextableGuildChannel",
    "PrivateChannel",
    "DMChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildChannel",
    "GuildTextChannel",
    "GuildNewsChannel",
    "GuildStoreChannel",
    "GuildVoiceChannel",
    "GuildStageChannel",
    "WebhookChannelT",
    "WebhookChannelTypes",
]

import typing

import attr

from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import webhooks
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import embeds as embeds_
    from hikari import files
    from hikari import guilds
    from hikari import iterators
    from hikari import messages
    from hikari import users
    from hikari import voices
    from hikari.api import special_endpoints
    from hikari.internal import time


@typing.final
class ChannelType(int, enums.Enum):
    """The known channel types that are exposed to us by the API."""

    GUILD_TEXT = 0
    """A text channel in a guild."""

    DM = 1
    """A direct channel between two users."""

    GUILD_VOICE = 2
    """A voice channel in a guild."""

    GROUP_DM = 3
    """A direct channel between multiple users."""

    GUILD_CATEGORY = 4
    """An category used for organizing channels in a guild."""

    GUILD_NEWS = 5
    """A channel that can be followed and can crosspost."""

    GUILD_STORE = 6
    """A channel that show's a game's store page."""

    GUILD_STAGE = 13
    """A few to many voice channel for hosting events."""


@typing.final
class VideoQualityMode(int, enums.Enum):
    """The camera quality of the voice chat."""

    AUTO = 1
    """Video quality will be set for optimal performance."""

    FULL = 2
    """Video quality will be set to 720p."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class ChannelFollow:
    """Relationship between a news channel and a subscriber channel.

    The subscriber channel will receive crosspost messages that correspond
    to any "broadcast" announcements that the news channel creates.
    """

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """Return the client application that models may use for procedures.

    Returns
    -------
    hikari.traits.RESTAware
        The REST-aware application object.
    """

    channel_id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """Return the channel ID of the channel being followed.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The channel ID for the channel being followed.
    """

    webhook_id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """Return the ID of the webhook for this follow.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The ID of the webhook that was created for this follow.
    """

    async def fetch_channel(self) -> typing.Union[GuildNewsChannel, GuildTextChannel]:
        """Fetch the object of the guild channel being followed.

        Returns
        -------
        typing.Union[hikari.channels.GuildNewsChannel, hikari.channels.GuildTextChannel]
            The channel being followed. While this will usually be
            `GuildNewsChannel`, if the channel's news status has been removed
            then this will be a `GuildTextChannel`

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
        assert isinstance(channel, (GuildTextChannel, GuildNewsChannel))
        return channel

    async def fetch_webhook(self) -> webhooks.ChannelFollowerWebhook:
        """Fetch the webhook attached to this follow.

        Returns
        -------
        hikari.webhooks.ChannelFollowerWebhook
            The webhook attached to this follow.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission in the guild or
            channel this follow is targeting.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
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
        webhook = await self.app.rest.fetch_webhook(self.webhook_id)
        assert isinstance(webhook, webhooks.ChannelFollowerWebhook)
        return webhook

    def get_channel(self) -> typing.Union[GuildNewsChannel, GuildTextChannel, None]:
        """Get the channel being followed from the cache.

        !!! warning
            This will always be `builtins.None` if you are not
            in the guild that this channel exists in.

        Returns
        -------
        typing.Union[hikari.channels.GuildNewsChannel, hikari.channels.GuildTextChannel, builtins.None]
            The object of the guild channel that was found in the cache or
            `builtins.None`. While this will usually be `GuildNewsChannel` or
            `builtins.None`, if the channel referenced has since lost it's news
            status then this will return a `GuildTextChannel`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(channel, (GuildNewsChannel, GuildTextChannel))
        return channel


@typing.final
class PermissionOverwriteType(int, enums.Enum):
    """The type of entity a Permission Overwrite targets."""

    ROLE = 0
    """A permission overwrite that targets all the members with a specific role."""

    MEMBER = 1
    """A permission overwrite that targets a specific guild member."""


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class PermissionOverwrite:
    """Represents permission overwrites for a channel or role in a channel.

    You may sometimes need to make instances of this object to add/edit
    permission overwrites on channels.

    Example
    -------
    Creating a permission overwrite.

    ```py
    overwrite = PermissionOverwrite(
        type=PermissionOverwriteType.MEMBER,
        allow=(
            Permissions.VIEW_CHANNEL
            | Permissions.READ_MESSAGE_HISTORY
            | Permissions.SEND_MESSAGES
        ),
        deny=(
            Permissions.MANAGE_MESSAGES
            | Permissions.SPEAK
        ),
    )
    ```
    """

    id: snowflakes.Snowflake = attr.field(converter=snowflakes.Snowflake, repr=True)
    """The ID of this entity."""

    type: typing.Union[PermissionOverwriteType, int] = attr.field(converter=PermissionOverwriteType, repr=True)
    """The type of entity this overwrite targets."""

    allow: permissions.Permissions = attr.field(
        converter=permissions.Permissions, default=permissions.Permissions.NONE, repr=True
    )
    """The permissions this overwrite allows."""

    deny: permissions.Permissions = attr.field(
        converter=permissions.Permissions, default=permissions.Permissions.NONE, repr=True
    )
    """The permissions this overwrite denies."""

    @property
    def unset(self) -> permissions.Permissions:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        return ~(self.allow | self.deny)


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialChannel(snowflakes.Unique):
    """Channel representation for cases where further detail is not provided.

    This is commonly received in HTTP API responses where full information is
    not available from Discord.
    """

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: typing.Optional[str] = attr.field(eq=False, hash=False, repr=True)
    """The channel's name. This will be missing for DM channels."""

    type: typing.Union[ChannelType, int] = attr.field(eq=False, hash=False, repr=True)
    """The channel's type."""

    def __str__(self) -> str:
        return self.name if self.name is not None else f"Unnamed {self.__class__.__name__} ID {self.id}"

    async def delete(self) -> PartialChannel:
        """Delete a channel in a guild, or close a DM.

        Returns
        -------
        hikari.channels.PartialChannel
            Object of the channel that was deleted.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
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

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.
        """
        return await self.app.rest.delete_channel(self.id)


class TextableChannel(PartialChannel):
    """Mixin class for a channel which can have text messages in it."""

    # This is a mixin, do not add slotted fields.
    __slots__: typing.Sequence[str] = ()

    # TODO: add examples to this and the REST method this invokes.
    def fetch_history(
        self,
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages.Message]:
        """Browse the message history for a given text channel.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, fetch messages before this snowflakes. If you provide
            a datetime object, it will be transformed into a snowflakes. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        after : hikari.undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, fetch messages after this snowflakes. If you provide
            a datetime object, it will be transformed into a snowflakes. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        around : hikari.undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, fetch messages around this snowflakes. If you provide
            a datetime object, it will be transformed into a snowflakes. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.messages.Message]
            A iterator to fetch the messages.

        Raises
        ------
        builtins.TypeError
            If you specify more than one of `before`, `after`, `about`.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint (other than `builtins.TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `builtins.TypeError`).
        """  # noqa: E501 - Line too long
        return self.app.rest.fetch_messages(self.id, before=before, after=after, around=around)

    async def fetch_message(self, message: snowflakes.SnowflakeishOr[messages.PartialMessage]) -> messages.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to fetch. This may be the object or the ID of an
            existing channel.

        Returns
        -------
        hikari.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGE_HISTORY` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not found in the
            given text channel.
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
        return await self.app.rest.fetch_message(self.id, message)

    async def send(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages.PartialMessage]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages.Message:
        """Create a message in this channel.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish],
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]],
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component : hikari.undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message will be TTS (Text To Speech).
        nonce : hikari.undefined.UndefinedOr[builtins.str]
            If provided, a nonce that can be used for optimistic message
            sending.
        reply : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]]
            If provided, the message to reply to.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        mentions_reply : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if not being used with `reply`.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, and `builtins.True`, all mentions will be parsed.
            If provided, and `builtins.False`, no mentions will be parsed.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, and `builtins.True`, all mentions will be parsed.
            If provided, and `builtins.False`, no mentions will be parsed.
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
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; `reply` not found or not in the same
            channel; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you lack permissions to send messages in the given channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
            If both `attachment` and `attachments` are specified.
        """  # noqa: E501 - Line too long
        return await self.app.rest.create_message(
            channel=self.id,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            tts=tts,
            reply=reply,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            mentions_reply=mentions_reply,
        )

    def trigger_typing(self) -> special_endpoints.TypingIndicator:
        """Trigger typing in a given channel.

        This returns an object that can either be `await`ed to trigger typing
        once, or used as an async context manager to keep typing until the
        block completes.

        ```py
        await channel.trigger_typing()   # type for 10s

        async with channel.trigger_typing():
            await asyncio.sleep(35)            # keep typing until this finishes
        ```

        !!! note
            Sending a message to this channel will stop the typing indicator. If
            using an `async with`, it will start up again after a few seconds.
            This is a limitation of Discord's API.

        Returns
        -------
        hikari.api.special_endpoints.TypingIndicator
            The typing indicator object.
        """
        return self.app.rest.trigger_typing(self.id)

    async def fetch_pins(self) -> typing.Sequence[messages.Message]:
        """Fetch the pinned messages in this text channel.

        Returns
        -------
        typing.Sequence[hikari.messages.Message]
            The pinned messages in this text channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGES` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
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
        return await self.app.rest.fetch_pins(self.id)

    async def pin_message(self, message: snowflakes.SnowflakeishOr[messages.PartialMessage]) -> None:
        """Pin an existing message in the text channel.

        Parameters
        ----------
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to pin. This may be the object or the ID
            of an existing message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found, or if the message does not exist in
            the given channel.
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
        return await self.app.rest.pin_message(self.id, message)

    async def unpin_message(self, message: snowflakes.SnowflakeishOr[messages.PartialMessage]) -> None:
        """Unpin a given message from the text channel.

        Parameters
        ----------
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to unpin. This may be the object or the ID of an
            existing message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` permission.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not a pinned message
            in the given channel.
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
        return await self.app.rest.unpin_message(self.id, message)

    async def delete_messages(
        self,
        messages: typing.Union[
            snowflakes.SnowflakeishOr[messages.PartialMessage],
            snowflakes.SnowflakeishIterable[messages.PartialMessage],
        ],
        /,
        *other_messages: snowflakes.SnowflakeishOr[messages.PartialMessage],
    ) -> None:
        """Bulk-delete messages from the channel.

        Parameters
        ----------
        messages : typing.Union[hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage], hikari.snowflakes.SnowflakeishIterable[hikari.messages.PartialMessage]]
            Either the object/ID of an existing message to delete or an iterable
            of the objects and/or IDs of existing messages to delete.

        Other Parameters
        ----------------
        *other_messages : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The objects and/or IDs of other existing messages to delete.

        !!! note
            This API endpoint will only be able to delete 100 messages
            at a time. For anything more than this, multiple requests will
            be executed one-after-the-other, since the rate limits for this
            endpoint do not favour more than one request per bucket.

            If one message is left over from chunking per 100 messages, or
            only one message is passed to this coroutine function, then the
            logic is expected to defer to `delete_message`. The implication
            of this is that the `delete_message` endpoint is ratelimited
            by a different bucket with different usage rates.

        !!! warning
            This endpoint is not atomic. If an error occurs midway through
            a bulk delete, you will **not** be able to revert any changes made
            up to this point.

        !!! warning
            Specifying any messages more than 14 days old will cause the call
            to fail, potentially with partial completion.

        Raises
        ------
        hikari.errors.BulkDeleteError
            An error containing the messages successfully deleted, and the
            messages that were not removed. The
            `builtins.BaseException.__cause__` of the exception will be the
            original error that terminated this process.
        """  # noqa: E501 - Line too long
        return await self.app.rest.delete_messages(self.id, messages, *other_messages)


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PrivateChannel(PartialChannel):
    """The base for anything that is a private (non-guild bound) channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class DMChannel(PrivateChannel, TextableChannel):
    """Represents a direct message text channel that is between you and another user."""

    recipient: users.User = attr.field(eq=False, hash=False, repr=False)
    """The user recipient of this DM."""

    @property
    def shard_id(self) -> typing.Literal[0]:
        """Return the shard ID for the shard."""
        return 0

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with: {self.recipient}"


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GroupDMChannel(PrivateChannel):
    """Represents a group direct message channel.

    !!! note
        This doesn't have the methods found on `TextableChannel` as bots cannot
        interact with a group DM that they own by sending or seeing messages in
        it.
    """

    owner_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """The ID of the owner of the group."""

    icon_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The CDN hash of the icon of the group, if an icon is set."""

    nicknames: typing.MutableMapping[snowflakes.Snowflake, str] = attr.field(eq=False, hash=False, repr=False)
    """A mapping of set nicknames within this group DMs to user IDs."""

    recipients: typing.Mapping[snowflakes.Snowflake, users.User] = attr.field(eq=False, hash=False, repr=False)
    """The recipients of the group DM."""

    application_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the application that created the group DM.

    If the group DM was not created by a bot, this will be `builtins.None`.
    """

    def __str__(self) -> str:
        if self.name is None:
            return f"{self.__class__.__name__} with: {', '.join(str(user) for user in self.recipients.values())}"

        return self.name

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Icon for this group DM, if set."""
        return self.make_icon_url()

    def make_icon_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon for this group, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon is present.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two between 16 and 4096 (inclusive).
        """
        if self.icon_hash is None:
            return None

        return routes.CDN_CHANNEL_ICON.compile_to_file(
            urls.CDN_URL,
            channel_id=self.id,
            hash=self.icon_hash,
            size=size,
            file_format=ext,
        )


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """The ID of the guild the channel belongs to."""

    position: int = attr.field(eq=False, hash=False, repr=False)
    """The sorting position of the channel.

    Higher numbers appear further down the channel list.
    """

    permission_overwrites: typing.Mapping[snowflakes.Snowflake, PermissionOverwrite] = attr.field(
        eq=False, hash=False, repr=False
    )
    """The permission overwrites for the channel.

    This maps the ID of the entity in the overwrite to the overwrite data.
    """

    is_nsfw: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """Whether the channel is marked as NSFW.

    !!! warning
        This will be `builtins.None` when received over the gateway in certain events
        (e.g Guild Create).
    """

    parent_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=True)
    """The ID of the parent category the channel belongs to.

    If no parent category is set for the channel, this will be `builtins.None`.
    """

    @property
    def mention(self) -> str:
        """Return a raw mention string for the guild channel.

        !!! note
            As of writing, GuildCategory channels are a special case
            for this and mentions of them will not resolve as clickable.

        Returns
        -------
        builtins.str
            The mention string to use.
        """
        return f"<#{self.id}>"

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Return the shard ID for the shard.

        This may be `builtins.None` if the shard count is not known.
        """
        if isinstance(self.app, traits.ShardAware):
            return snowflakes.calculate_shard_id(self.app, self.guild_id)

        return None

    async def fetch_guild(self) -> guilds.PartialGuild:
        """Fetch the guild linked to this channel.

        Returns
        -------
        hikari.guilds.RESTGuild
            The requested guild.

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
        return await self.app.rest.fetch_guild(self.guild_id)

    async def edit_overwrite(
        self,
        target: typing.Union[snowflakes.Snowflakeish, users.PartialUser, guilds.PartialRole, PermissionOverwrite],
        *,
        target_type: undefined.UndefinedOr[typing.Union[PermissionOverwriteType, int]] = undefined.UNDEFINED,
        allow: undefined.UndefinedOr[permissions.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a specific entity in the given guild channel.

           This creates new overwrite for the channel, if there no other overwrites present.

        Parameters
        ----------
        target : typing.Union[hikari.users.PartialUser, hikari.guilds.PartialRole, hikari.channels.PermissionOverwrite, hikari.snowflakes.Snowflakeish]
            The channel overwrite to edit. This may be the object or the ID of an
            existing overwrite.

        Other Parameters
        ----------------
        target_type : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.PermissionOverwriteType, int]]
            If provided, the type of the target to update. If unset, will attempt to get
            the type from `target`.
        allow : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new vale of all allowed permissions.
        deny : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new vale of all disallowed permissions.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        builtins.TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_PERMISSIONS` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found if it is
            a role.
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
        if target_type is undefined.UNDEFINED:
            assert not isinstance(
                target, int
            ), "Cannot determine the type of the target to update. Try specifying 'target_type' manually."
            return await self.app.rest.edit_permission_overwrites(
                self.id, target, allow=allow, deny=deny, reason=reason
            )

        return await self.app.rest.edit_permission_overwrites(
            self.id, typing.cast(int, target), target_type=target_type, allow=allow, deny=deny, reason=reason
        )

    async def remove_overwrite(
        self,
        target: snowflakes.SnowflakeishOr[
            typing.Union[PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflakes.Snowflakeish]
        ],
    ) -> None:
        """Delete a custom permission for an entity in a given guild channel.

        Parameters
        ----------
        target : typing.Union[hikari.users.PartialUser, hikari.guilds.PartialRole, hikari.channels.PermissionOverwrite, hikari.snowflakes.Snowflakeish]
            The channel overwrite to delete.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_PERMISSIONS` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found.
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
        return await self.app.rest.delete_permission_overwrite(self.id, target)

    async def edit(
        self,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[typing.Union[VideoQualityMode, int]] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[typing.Sequence[PermissionOverwrite]] = undefined.UNDEFINED,
        parent_category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> PartialChannel:
        """Edit the text channel.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[[builtins.str]
            If provided, the new name for the channel.
        position : hikari.undefined.UndefinedOr[[builtins.int]
            If provided, the new position for the channel.
        topic : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new topic for the channel.
        nsfw : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the new bitrate for the channel.
        video_quality_mode: hikari.undefined.UndefinedOr[typing.Union[hikari.channels.VideoQualityMode, builtins.int]]
            If provided, the new video quality mode for the channel.
        user_limit : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new rate limit per user in the channel.
        region : hikari.undefined.UndefinedOr[typing.Union[hikari.voices.VoiceRegion, builtins.str]]
            If provided, the voice region to set for this channel. Passing
            `builtins.None` here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            If provided, the new guild category for the channel.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.PartialChannel
            The edited channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing permissions to edit the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
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
        return await self.app.rest.edit_channel(
            self.id,
            name=name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            bitrate=bitrate,
            video_quality_mode=video_quality_mode,
            user_limit=user_limit,
            rate_limit_per_user=rate_limit_per_user,
            region=region,
            permission_overwrites=permission_overwrites,
            parent_category=parent_category,
            reason=reason,
        )


class TextableGuildChannel(GuildChannel, TextableChannel):
    """Mixin class for any guild channel which can have text messages in it."""

    # This is a mixin, do not add slotted fields.
    __slots__: typing.Sequence[str] = ()


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildCategory(GuildChannel):
    """Represents a guild category channel.

    These can contain other channels inside, and act as a method for
    organisation.
    """


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildTextChannel(TextableGuildChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    rate_limit_per_user: datetime.timedelta = attr.field(eq=False, hash=False, repr=False)
    """The delay (in seconds) between a user can send a message to this channel.

    If there is no rate limit, this will be 0 seconds.

    !!! note
        Any user that has permissions allowing `MANAGE_MESSAGES`,
        `MANAGE_CHANNEL`, `ADMINISTRATOR` will not be limited. Likewise, bots
        will not be affected by this rate limit.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.field(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be `builtins.None` in several cases; Discord does not document what
        these cases are. Trust no one!
    """


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildNewsChannel(TextableGuildChannel):
    """Represents an news channel."""

    topic: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.field(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be `builtins.None` in several cases; Discord does not document what
        these cases are. Trust no one!
    """


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel.

    These were originally used to sell games when Discord had a game store. This
    was scrapped at the end of 2019, so these may disappear from the platform
    eventually.
    """


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildVoiceChannel(GuildChannel):
    """Represents a voice channel."""

    bitrate: int = attr.field(eq=False, hash=False, repr=True)
    """The bitrate for the voice channel (in bits per second)."""

    region: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """ID of the voice region for this voice channel.

    If set to `builtins.None` then this is set to "auto" mode where the used
    region will be decided based on the first person who connects to it when
    it's empty.
    """

    user_limit: int = attr.field(eq=False, hash=False, repr=True)
    """The user limit for the voice channel.

    If this is `0`, then assume no limit.
    """

    video_quality_mode: typing.Union[VideoQualityMode, int] = attr.field(eq=False, hash=False, repr=False)
    """The video quality mode for the voice channel."""


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildStageChannel(GuildChannel):
    """Represents a stage channel."""

    bitrate: int = attr.field(eq=False, hash=False, repr=True)
    """The bitrate for the stage channel (in bits per second)."""

    region: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """ID of the voice region for this stage channel.

    If set to `builtins.None` then this is set to "auto" mode where the used
    region will be decided based on the first person who connects to it when
    it's empty.
    """

    user_limit: int = attr.field(eq=False, hash=False, repr=True)
    """The user limit for the stage channel.

    If this is `0`, then assume no limit.
    """


WebhookChannelT = typing.Union[GuildTextChannel, GuildNewsChannel]
"""Union of the channel types which incoming and follower webhooks can be attached to.

The following types are in this:

* `GuildTextChannel`
* `GuildNewsChannel`
"""

WebhookChannelTypes: typing.Tuple[typing.Type[GuildTextChannel], typing.Type[GuildNewsChannel]] = (
    GuildTextChannel,
    GuildNewsChannel,
)
"""Tuple of the channel types which are valid for `WebhookChannelT`.

This includes:

* `GuildTextChannel`
* `GuildNewsChannel`
"""

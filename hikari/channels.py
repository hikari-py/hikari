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
"""Application and entities that are used to describe both DMs and guild channels on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ChannelType",
    "ChannelFlag",
    "VideoQualityMode",
    "ChannelFollow",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "PermissibleGuildChannel",
    "TextableChannel",
    "TextableGuildChannel",
    "PrivateChannel",
    "DMChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildChannel",
    "GuildTextChannel",
    "GuildThreadChannel",
    "GuildNewsChannel",
    "GuildNewsThread",
    "GuildPrivateThread",
    "GuildPublicThread",
    "ForumSortOrderType",
    "ForumLayoutType",
    "ForumTag",
    "GuildForumChannel",
    "GuildVoiceChannel",
    "GuildStageChannel",
    "WebhookChannelT",
    "WebhookChannelTypes",
    "ThreadMember",
)

import typing

import attrs

from hikari import emojis
from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import webhooks
from hikari.internal import attrs_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import embeds as embeds_
    from hikari import files
    from hikari import guilds
    from hikari import iterators
    from hikari import messages as messages_
    from hikari import stickers as stickers_
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

    GUILD_NEWS_THREAD = 10
    """A temporary sub-channel within a [`hikari.channels.ChannelType.GUILD_NEWS`][] channel."""

    GUILD_PUBLIC_THREAD = 11
    """A temporary sub-channel within a [`hikari.channels.ChannelType.GUILD_TEXT`][] channel."""

    GUILD_PRIVATE_THREAD = 12
    """A temporary sub-channel with restricted access.

    Like [`hikari.channels.ChannelType.GUILD_PUBLIC_THREAD`][], these exist within
    [`hikari.channels.ChannelType.GUILD_TEXT`][] channels but can only be accessed by members who
    are invited to them or have [`hikari.permissions.Permissions.MANAGE_THREADS`][] permission.
    """

    GUILD_STAGE = 13
    """A few to many voice channel for hosting events."""

    GUILD_FORUM = 15
    """A channel consisting of a collection of public guild threads."""


@typing.final
class ChannelFlag(enums.Flag):
    """The flags for a channel."""

    NONE = 0 << 1
    """None."""

    PINNED = 1 << 1
    """The thread is pinned in a forum channel.

    !!! note
        As of writing, this can only be set for threads
        belonging to a forum channel.
    """

    REQUIRE_TAG = 1 << 4
    """Whether a tag is required to be specified when creating a thread in a forum channel

    !!! note
        As of writing, this can only be set for forum channels.
    """


@typing.final
class VideoQualityMode(int, enums.Enum):
    """The camera quality of the voice chat."""

    AUTO = 1
    """Video quality will be set for optimal performance."""

    FULL = 2
    """Video quality will be set to 720p."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class ChannelFollow:
    """Relationship between a news channel and a subscriber channel.

    The subscriber channel will receive crosspost messages that correspond
    to any "broadcast" announcements that the news channel creates.
    """

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    channel_id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """Return the channel ID of the channel being followed."""

    webhook_id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """Return the ID of the webhook for this follow."""

    async def fetch_channel(self) -> typing.Union[GuildNewsChannel, GuildTextChannel]:
        """Fetch the object of the guild channel being followed.

        Returns
        -------
        typing.Union[hikari.channels.GuildNewsChannel, hikari.channels.GuildTextChannel]
            The channel being followed.

            While this will usually be [`hikari.channels.GuildNewsChannel`][], if the channel's
            news status has been removed then this will be a [`hikari.channels.GuildNewsChannel`][].

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission in the guild or
            channel this follow is targeting.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        webhook = await self.app.rest.fetch_webhook(self.webhook_id)
        assert isinstance(webhook, webhooks.ChannelFollowerWebhook)
        return webhook

    def get_channel(self) -> typing.Union[GuildNewsChannel, GuildTextChannel, None]:
        """Get the channel being followed from the cache.

        !!! warning
            This will always be [`None`][] if you are not
            in the guild that this channel exists in.

        Returns
        -------
        typing.Union[hikari.channels.GuildNewsChannel, hikari.channels.GuildTextChannel, None]
            The object of the guild channel that was found in the cache or
            [`None`][]. While this will usually be [`hikari.channels.GuildNewsChannel`][] or
            [`None`][], if the channel referenced has since lost it's news
            status then this will return a [`hikari.channels.GuildNewsChannel`][].
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


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PermissionOverwrite:
    """Represents permission overwrites for a channel or role in a channel.

    You may sometimes need to make instances of this object to add/edit
    permission overwrites on channels.

    Examples
    --------
    Creating a permission overwrite.

    ```py
        overwrite = PermissionOverwrite(
            id=163979124820541440,
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

    id: snowflakes.Snowflake = attrs.field(converter=snowflakes.Snowflake, repr=True)
    """The ID of this entity."""

    type: typing.Union[PermissionOverwriteType, int] = attrs.field(converter=PermissionOverwriteType, repr=True)
    """The type of entity this overwrite targets."""

    allow: permissions.Permissions = attrs.field(
        converter=permissions.Permissions, default=permissions.Permissions.NONE, repr=True
    )
    """The permissions this overwrite allows."""

    deny: permissions.Permissions = attrs.field(
        converter=permissions.Permissions, default=permissions.Permissions.NONE, repr=True
    )
    """The permissions this overwrite denies."""

    @property
    def unset(self) -> permissions.Permissions:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        return ~(self.allow | self.deny)


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class PartialChannel(snowflakes.Unique):
    """Channel representation for cases where further detail is not provided.

    This is commonly received in HTTP API responses where full information is
    not available from Discord.
    """

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=True)
    """The channel's name. This will be missing for DM channels."""

    type: typing.Union[ChannelType, int] = attrs.field(eq=False, hash=False, repr=True)
    """The channel's type."""

    @property
    def mention(self) -> str:
        """Return a raw mention string for the channel.

        !!! note
            There are platform specific inconsistencies with mentions of
            GuildCategories, GroupDMChannels and DMChannels showing
            the correct name but not being interactable.

        Returns
        -------
        str
            The mention string to use.
        """
        return f"<#{self.id}>"

    def __str__(self) -> str:
        return self.name if self.name is not None else f"Unnamed {self.__class__.__name__} ID {self.id}"

    async def delete(self) -> PartialChannel:
        """Delete a channel in a guild, or close a DM.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.

        Returns
        -------
        hikari.channels.PartialChannel
            Object of the channel that was deleted.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
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
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.
            See [`hikari.iterators`][] for the full API for this iterator type.

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
        TypeError
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
        """
        return self.app.rest.fetch_messages(self.id, before=before, after=after, around=around)

    async def fetch_message(self, message: snowflakes.SnowflakeishOr[messages_.PartialMessage]) -> messages_.Message:
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
            If you are missing the [`hikari.permissions.Permissions.READ_MESSAGE_HISTORY`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not found in the
            given text channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        sticker: undefined.UndefinedOr[snowflakes.SnowflakeishOr[stickers_.PartialSticker]] = undefined.UNDEFINED,
        stickers: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[stickers_.PartialSticker]
        ] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = undefined.UNDEFINED,
        reply_must_exist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Create a message in this channel.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.

            Likewise, if this is a [`hikari.files.Resource`][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.

            Attachments can be passed as many different things, to aid in
            convenience.

            - If a [`pathlib.PurePath`][] or [`str`][] to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                [`hikari.files.WebResource`][] such as
                [`hikari.files.URL`][],
                [`hikari.messages.Attachment`][],
                [`hikari.emojis.Emoji`][],
                [`hikari.embeds.EmbedResource`][], etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a [`hikari.files.Bytes`][] is passed, or a [`str`][]
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a [`hikari.files.File`][], [`pathlib.PurePath`][] or
                [`str`][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of [`concurrent.futures.Executor`][] that is being used for
                the application (default is a thread pool which supports this
                behaviour).
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]]
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
        sticker : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]]
            If provided, the object or ID of a sticker to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        stickers : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.stickers.PartialSticker]]
            If provided, a sequence of the objects and IDs of up to 3 stickers
            to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be TTS (Text To Speech).
        reply : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]]
            If provided, the message to reply to.
        reply_must_exist : hikari.undefined.UndefinedOr[bool]
            If provided, whether to error if the message being replied to does
            not exist instead of sending as a normal (non-reply) message.

            This will not do anything if not being used with `reply`.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        mentions_reply : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if not being used with `reply`.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all mentions will be parsed.
            If provided, and [`False`][], no mentions will be parsed.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all mentions will be parsed.
            If provided, and [`False`][], no mentions will be parsed.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            If provided, optional flags to set on the message. If
            [`hikari.undefined.UNDEFINED`][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [`hikari.messages.MessageFlag.NONE`][] and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].

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
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        TypeError
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
            sticker=sticker,
            stickers=stickers,
            tts=tts,
            reply=reply,
            reply_must_exist=reply_must_exist,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            mentions_reply=mentions_reply,
            flags=flags,
        )

    def trigger_typing(self) -> special_endpoints.TypingIndicator:
        """Trigger typing in a given channel.

        This returns an object that can either be awaited to trigger typing
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

    async def fetch_pins(self) -> typing.Sequence[messages_.Message]:
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
            If you are missing the [hikari.permissions.Permissions.VIEW_CHANNEL]
            permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_pins(self.id)

    async def pin_message(self, message: snowflakes.SnowflakeishOr[messages_.PartialMessage]) -> None:
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found, or if the message does not exist in
            the given channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.pin_message(self.id, message)

    async def unpin_message(self, message: snowflakes.SnowflakeishOr[messages_.PartialMessage]) -> None:
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permission.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not a pinned message
            in the given channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.unpin_message(self.id, message)

    async def delete_messages(
        self,
        messages: typing.Union[
            snowflakes.SnowflakeishOr[messages_.PartialMessage],
            typing.Iterable[snowflakes.SnowflakeishOr[messages_.PartialMessage]],
            typing.AsyncIterable[snowflakes.SnowflakeishOr[messages_.PartialMessage]],
        ],
        /,
        *other_messages: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Bulk-delete messages from the channel.

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

        Parameters
        ----------
        messages
            Either the object/ID of an existing message to delete or an iterable
            (sync or async) of the objects and/or IDs of existing messages to delete.

        Other Parameters
        ----------------
        *other_messages : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The objects and/or IDs of other existing messages to delete.

        Raises
        ------
        hikari.errors.BulkDeleteError
            An error containing the messages successfully deleted, and the
            messages that were not removed. The
            [`BaseException.__cause__`][] of the exception will be the
            original error that terminated this process.
        """
        return await self.app.rest.delete_messages(self.id, messages, *other_messages)


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class PrivateChannel(PartialChannel):
    """The base for anything that is a private (non-guild bound) channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class DMChannel(PrivateChannel, TextableChannel):
    """Represents a direct message text channel that is between you and another user."""

    recipient: users.User = attrs.field(eq=False, hash=False, repr=False)
    """The user recipient of this DM."""

    @property
    def shard_id(self) -> typing.Literal[0]:
        """Return the shard ID for the shard."""
        return 0

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with: {self.recipient}"


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GroupDMChannel(PrivateChannel):
    """Represents a group direct message channel.

    !!! note
        This doesn't have the methods found on [`hikari.channels.TextableChannel`][]
        as bots cannot interact with a group DM that they own by sending or
        seeing messages in it.
    """

    owner_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the owner of the group."""

    icon_hash: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The CDN hash of the icon of the group, if an icon is set."""

    nicknames: typing.MutableMapping[snowflakes.Snowflake, str] = attrs.field(eq=False, hash=False, repr=False)
    """A mapping of set nicknames within this group DMs to user IDs."""

    recipients: typing.Mapping[snowflakes.Snowflake, users.User] = attrs.field(eq=False, hash=False, repr=False)
    """The recipients of the group DM."""

    application_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the application that created the group DM.

    If the group DM was not created by a bot, this will be [`None`][].
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
        ext : str
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no icon is present.

        Raises
        ------
        ValueError
            If `size` is not a power of two between 16 and 4096 (inclusive).
        """
        if self.icon_hash is None:
            return None

        return routes.CDN_CHANNEL_ICON.compile_to_file(
            urls.CDN_URL, channel_id=self.id, hash=self.icon_hash, size=size, file_format=ext
        )


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the guild the channel belongs to."""

    parent_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the parent channel the channel belongs to.

    For thread channels this will refer to the parent textable guild channel.
    For other guild channel types this will refer to the parent category and
    if no parent category is set for the channel, this will be [`None`][].
    For guild categories this will always be [`None`][].
    """

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Return the shard ID for the shard.

        This may be [`None`][] if the shard count is not known.
        """
        if isinstance(self.app, traits.ShardAware):
            return snowflakes.calculate_shard_id(self.app, self.guild_id)

        return None

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Return the guild linked to this channel.

        Returns
        -------
        typing.Optional[hikari.guilds.Guild]
            The linked guild object or [`None`][] if it's not cached.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_guild(self.guild_id)

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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        # Forum & Thread-only fields
        flags: undefined.UndefinedOr[ChannelFlag] = undefined.UNDEFINED,
        # Thread-only fields
        archived: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        locked: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        invitable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        applied_tags: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[ForumTag]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> PartialChannel:
        """Edit the text channel.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[[str]
            If provided, the new name for the channel.
        position : hikari.undefined.UndefinedOr[[int]
            If provided, the new position for the channel.
        topic : hikari.undefined.UndefinedOr[str]
            If provided, the new topic for the channel.
        nsfw : hikari.undefined.UndefinedOr[bool]
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.undefined.UndefinedOr[int]
            If provided, the new bitrate for the channel.
        video_quality_mode: hikari.undefined.UndefinedOr[typing.Union[hikari.channels.VideoQualityMode, int]]
            If provided, the new video quality mode for the channel.
        user_limit : hikari.undefined.UndefinedOr[int]
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new rate limit per user in the channel.
        region : hikari.undefined.UndefinedOr[typing.Union[hikari.voices.VoiceRegion, str]]
            If provided, the voice region to set for this channel. Passing
            [`None`][] here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            If provided, the new guild category for the channel.
        default_auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the auto archive duration Discord's end user client
            should default to when creating threads in this channel.

            This should be either 60, 1440, 4320 or 10080 minutes, as of
            writing.
        flags : hikari.undefined.UndefinedOr[ChannelFlag]
            If provided, the new channel flags to use for the channel. This can
            only be used on a forum channel to apply ChannelFlag.REQUIRE_TAG, or
            on a forum thread to apply ChannelFlag.PINNED.
        archived : hikari.undefined.UndefinedOr[bool]
            If provided, the new archived state for the thread. This only
            applies to threads.
        auto_archive_duration : hikari.undefined.UndefinedOr[time.Intervalish]
            If provided, the new auto archive duration for this thread. This
            only applies to threads.

            This should be either 60, 1440, 4320 or 10080 minutes, as of
            writing.
        locked : hikari.undefined.UndefinedOr[bool]
            If provided, the new locked state for the thread. This only applies
            to threads.

            If it's locked then only people with [`hikari.permissions.Permissions.MANAGE_THREADS`][] can unarchive it.
        invitable : hikari.undefined.UndefinedOr[bool]
            If provided, the new setting for whether non-moderators can invite
            new members to a private thread. This only applies to threads.
        applied_tags : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.channels.ForumTag]]
            If provided, the new tags to apply to the thread. This only applies
            to threads in a forum channel.
        reason : hikari.undefined.UndefinedOr[str]
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
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
            default_auto_archive_duration=default_auto_archive_duration,
            flags=flags,
            archived=archived,
            auto_archive_duration=auto_archive_duration,
            locked=locked,
            invitable=invitable,
            applied_tags=applied_tags,
            reason=reason,
        )


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class PermissibleGuildChannel(GuildChannel):
    """Base class for all guild channels which have permission overwrites.

    !!! note
        This doesn't apply to thread channels as they implicitly inherit
        permissions from their parent channel.
    """

    position: int = attrs.field(eq=False, hash=False, repr=False)
    """The sorting position of the channel.

    Higher numbers appear further down the channel list.
    """

    is_nsfw: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the channel is marked as NSFW."""

    permission_overwrites: typing.Mapping[snowflakes.Snowflake, PermissionOverwrite] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """The permission overwrites for the channel.

    This maps the ID of the entity in the overwrite to the overwrite data.
    """

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
            If provided, the new value of all allowed permissions.
        deny : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new value of all disallowed permissions.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`MANAGE_PERMISSIONS`][hikari.permissions.Permissions.MANAGE_ROLES]
            permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found if it is
            a role.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long
        if target_type is undefined.UNDEFINED:
            assert not isinstance(
                target, int
            ), "Cannot determine the type of the target to update. Try specifying 'target_type' manually."
            return await self.app.rest.edit_permission_overwrite(self.id, target, allow=allow, deny=deny, reason=reason)

        return await self.app.rest.edit_permission_overwrite(
            self.id, typing.cast(int, target), target_type=target_type, allow=allow, deny=deny, reason=reason
        )

    async def remove_overwrite(
        self, target: typing.Union[PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflakes.Snowflakeish]
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
            If you are missing the [`MANAGE_PERMISSIONS`][hikari.permissions.Permissions.MANAGE_ROLES]
            permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long
        return await self.app.rest.delete_permission_overwrite(self.id, target)


class TextableGuildChannel(GuildChannel, TextableChannel):
    """Mixin class for any guild channel which can have text messages in it."""

    # This is a mixin, do not add slotted fields.
    __slots__: typing.Sequence[str] = ()


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildCategory(PermissibleGuildChannel):
    """Represents a guild category channel.

    These can contain other channels inside, and act as a method for
    organisation.
    """

    parent_id: None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the parent channel the channel belongs to.

    This is always [`None`][] for categories.
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildTextChannel(PermissibleGuildChannel, TextableGuildChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    rate_limit_per_user: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The delay (in seconds) between a user can send a message to this channel.

    If there is no rate limit, this will be 0 seconds.

    !!! note
        Any user that has permissions allowing [`hikari.permissions.Permissions.MANAGE_MESSAGES`][],
        [`hikari.permissions.Permissions.MANAGE_CHANNELS`][],
        [`hikari.permissions.Permissions.ADMINISTRATOR`][] will not be limited.
        Likewise, bots will not be affected by this rate limit.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be [`None`][] in several cases; Discord does not document what
        these cases are. Trust no one!
    """

    default_auto_archive_duration: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The auto archive duration Discord's client defaults to for threads in this channel.

    This may be be either 1 hour, 1 day, 3 days or 1 week.
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildNewsChannel(PermissibleGuildChannel, TextableGuildChannel):
    """Represents an news channel."""

    topic: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be [`None`][] in several cases; Discord does not document what
        these cases are. Trust no one!
    """

    default_auto_archive_duration: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The auto archive duration Discord's client defaults to for threads in this channel.

    This may be be either 1 hour, 1 day, 3 days or 1 week.
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildVoiceChannel(PermissibleGuildChannel, TextableGuildChannel):
    """Represents a voice channel."""

    bitrate: int = attrs.field(eq=False, hash=False, repr=True)
    """The bitrate for the voice channel (in bits per second)."""

    region: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """ID of the voice region for this voice channel.

    If set to [`None`][] then this is set to "auto" mode where the used
    region will be decided based on the first person who connects to it when
    it's empty.
    """

    user_limit: int = attrs.field(eq=False, hash=False, repr=True)
    """The user limit for the voice channel.

    If this is `0`, then assume no limit.
    """

    video_quality_mode: typing.Union[VideoQualityMode, int] = attrs.field(eq=False, hash=False, repr=False)
    """The video quality mode for the voice channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildStageChannel(PermissibleGuildChannel, TextableGuildChannel):
    """Represents a stage channel."""

    bitrate: int = attrs.field(eq=False, hash=False, repr=True)
    """The bitrate for the stage channel (in bits per second)."""

    region: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """ID of the voice region for this stage channel.

    If set to [`None`][] then this is set to "auto" mode where the used
    region will be decided based on the first person who connects to it when
    it's empty.
    """

    user_limit: int = attrs.field(eq=False, hash=False, repr=True)
    """The user limit for the stage channel.

    If this is `0`, then assume no limit.
    """

    last_message_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """


@typing.final
class ForumSortOrderType(int, enums.Enum):
    """The sort order for forum channels."""

    LATEST_ACTIVITY = 0
    """Latest Activity."""

    CREATION_DATE = 1
    """Creation Date."""


@typing.final
class ForumLayoutType(int, enums.Enum):
    """The layout type for forum channels."""

    NOT_SET = 0
    """Not Set."""

    LIST_VIEW = 1
    """List View."""

    GALLERY_VIEW = 2
    """Gallery View."""


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class ForumTag(snowflakes.Unique):
    """Represents a forum tag."""

    id: snowflakes.Snowflake = attrs.field(
        eq=True, hash=True, repr=True, converter=snowflakes.Snowflake, factory=snowflakes.Snowflake.min
    )
    """The ID of the tag.

    When creating tags, this will be `0`.
    """

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of the tag."""

    moderated: bool = attrs.field(eq=False, hash=False, repr=False, default=False)
    """The whether this flag can only be applied by moderators.

    Moderators are those with [`hikari.permissions.Permissions.MANAGE_CHANNELS`][]
    or [`hikari.permissions.Permissions.ADMINISTRATOR`][] permissions.
    """

    _emoji: typing.Union[str, int, emojis.Emoji, None] = attrs.field(alias="emoji", default=None)
    # Discord will send either emoji_id or emoji_name, never both.
    # Thus, we can take in a generic "emoji" argument when the user
    # creates the class and then demystify it later.

    @property
    def unicode_emoji(self) -> typing.Optional[emojis.UnicodeEmoji]:
        """Unicode emoji of this tag."""
        if isinstance(self._emoji, str):
            return emojis.UnicodeEmoji(self._emoji)

        return None

    @property
    def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of the emoji of this tag."""
        if isinstance(self._emoji, (int, emojis.CustomEmoji)):
            return snowflakes.Snowflake(self._emoji)

        return None


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildForumChannel(PermissibleGuildChannel):
    """Represents a guild forum channel."""

    topic: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The guidelines for the channel."""

    last_thread_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last thread created in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    rate_limit_per_user: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The delay (in seconds) between a user can create threads in this channel.

    If there is no rate limit, this will be 0 seconds.

    !!! note
        Any user that has permissions allowing [`hikari.permissions.Permissions.MANAGE_MESSAGES`][],
        [`hikari.permissions.Permissions.MANAGE_CHANNELS`][],
        [`hikari.permissions.Permissions.ADMINISTRATOR`][] will not be limited.
        Likewise, bots will not be affected by this rate limit.
    """

    default_thread_rate_limit_per_user: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The default delay (in seconds) between a user can send a message in created threads.

    If there is no rate limit, this will be 0 seconds.

    !!! note
        Any user that has permissions allowing [`hikari.permissions.Permissions.MANAGE_MESSAGES`][],
        [`hikari.permissions.Permissions.MANAGE_CHANNELS`][],
        [`hikari.permissions.Permissions.ADMINISTRATOR`][] will not be limited.
        Likewise, bots will not be affected by this rate limit.
    """

    default_auto_archive_duration: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The auto archive duration Discord's client defaults to for threads in this channel.

    This may be be either 1 hour, 1 day, 3 days or 1 week.
    """

    flags: ChannelFlag = attrs.field(eq=False, hash=False, repr=False)
    """The channel flags for this channel.

    !!! note
        As of writing, the only flag that can be set is [`hikari.channels.ChannelFlag.REQUIRE_TAG`][].
    """

    available_tags: typing.Sequence[ForumTag] = attrs.field(eq=False, hash=False, repr=False)
    """The available tags to select from when creating a thread."""

    default_sort_order: ForumSortOrderType = attrs.field(eq=False, hash=False, repr=False)
    """The default sort order for the forum."""

    default_layout: ForumLayoutType = attrs.field(eq=False, hash=False, repr=False)
    """The default layout for the forum."""

    default_reaction_emoji_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the default reaction emoji."""

    default_reaction_emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attrs.field(
        eq=False, hash=False, repr=False
    )
    """Name of the default reaction emoji.

    Either the string name of the custom emoji, the object
    of the [`hikari.emojis.UnicodeEmoji`][] or [`None`][] when the relevant
    custom emoji's data is not available (e.g. the emoji has been deleted).
    """


WebhookChannelT = typing.Union[GuildTextChannel, GuildNewsChannel]
"""Union of the channel types which incoming and follower webhooks can be attached to.

The following types are in this:

* [`hikari.channels.GuildTextChannel`][]
* [`hikari.channels.GuildNewsChannel`][]
"""

WebhookChannelTypes: typing.Tuple[typing.Type[GuildTextChannel], typing.Type[GuildNewsChannel]] = (
    GuildTextChannel,
    GuildNewsChannel,
)
"""Tuple of the channel types which are valid for [`hikari.channels.WebhookChannelT`][].

This includes:

* [`hikari.channels.GuildTextChannel`][]
* [`hikari.channels.GuildNewsChannel`][]
"""


@attrs.define(kw_only=True, weakref_slot=False)
class ThreadMember:
    """Represents a thread's member."""

    thread_id: snowflakes.Snowflake = attrs.field(eq=True, repr=True)
    """ID of the thread this member is in."""

    user_id: snowflakes.Snowflake = attrs.field(eq=True, repr=True)
    """The member's user ID.

    !!! note
        This will only ever be [`None`][] on thread members attached to
        guild create events, where this is the current bot's user.
    """

    joined_at: datetime.datetime = attrs.field(eq=True, repr=True)
    """When the user joined the relevant thread."""

    flags: int = attrs.field(eq=True, repr=True)
    """Bitfield flag of the user's settings for the thread.

    !!! note
        As of writing, the values of this field's are undocumented.
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildThreadChannel(TextableGuildChannel):
    """Base class for all guild thread channels."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be [`None`][] in several cases; Discord does not document what
        these cases are. Trust no one!
    """

    rate_limit_per_user: datetime.timedelta = attrs.field(eq=False, hash=False, repr=False)
    """The delay (in seconds) between a user can send a message to this channel.

    If there is no rate limit, this will be 0 seconds.

    !!! note
        Any user that has permissions allowing [`hikari.permissions.Permissions.MANAGE_MESSAGES`][],
        [`hikari.permissions.Permissions.MANAGE_CHANNELS`][],
        [`hikari.permissions.Permissions.ADMINISTRATOR`][] will not be limited.
        Likewise, bots will not be affected by this rate limit.
    """

    approximate_message_count: int = attrs.field(eq=False, hash=False, repr=True)
    """Approximate number of messages in the thread channel.

    !!! warning
        This stops counting at 50 for threads created before 2022/06/01.
    """

    approximate_member_count: int = attrs.field(eq=False, hash=False, repr=True)
    """Approximate count of members in the thread channel.

    !!! warning
        This stop counting at 50.
    """

    is_archived: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether the thread is archived."""

    auto_archive_duration: datetime.timedelta = attrs.field(eq=False, hash=False, repr=True)
    """How long the thread will be left inactive before being automatically archived.

    As of writing this may either 1 hour, 1 day, 3 days or 1 week.
    """

    archive_timestamp: datetime.datetime = attrs.field(eq=False, hash=False, repr=True)
    """When the thread's archived state was last changed.

    !!! note
        If the thread has never been archived then this will be the thread's
        creation date and this will be changed when a thread is unarchived.
    """

    is_locked: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether the thread is locked.

    When a thread is locked, only users with [`hikari.permissions.Permissions.MANAGE_THREADS`][] permission
    can un-archive it.
    """

    member: typing.Optional[ThreadMember] = attrs.field(eq=False, hash=False, repr=True)
    """Thread member object for the current user, if they are in the thread.

    !!! note
        This is only returned by some endpoints and on private thread
        access events.
    """

    owner_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the user who created this thread."""

    parent_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """Id of this thread's textable parent channel."""

    thread_created_at: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=True)
    """When the thread was created.

    Will be [`None`][] for threads created before 2020-01-09.
    """


class GuildNewsThread(GuildThreadChannel):
    """Represents a guild news channel public thread."""

    __slots__: typing.Sequence[str] = ()


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildPublicThread(GuildThreadChannel):
    """Represents a non-news guild channel public thread."""

    applied_tag_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The IDs of the applied tags on this thread.

    This will only apply to threads created inside a forum channel.
    """

    flags: ChannelFlag = attrs.field(eq=False, hash=False, repr=False)
    """The channel flags for this thread.

    This will only apply to threads created inside a forum channel.

    !!! note
        As of writing, the only flag that can be set is [`hikari.channels.ChannelFlag.PINNED`][].
    """


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildPrivateThread(GuildThreadChannel):
    """Represents a guild private thread."""

    is_invitable: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether non-moderators can add other non-moderators to a private thread."""

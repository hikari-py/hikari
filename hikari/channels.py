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
"""Application and entities that are used to describe both DMs and guild channels on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ChannelType",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "TextChannel",
    "PrivateTextChannel",
    "GroupPrivateTextChannel",
    "GuildCategory",
    "GuildChannel",
    "GuildTextChannel",
    "GuildNewsChannel",
    "GuildStoreChannel",
    "GuildVoiceChannel",
]

import abc
import enum
import typing

import attr

from hikari import files
from hikari import permissions
from hikari import snowflakes
from hikari import undefined
from hikari import users
from hikari.utilities import attr_extensions
from hikari.utilities import constants
from hikari.utilities import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import embeds
    from hikari import guilds
    from hikari import iterators
    from hikari import messages
    from hikari import traits


@enum.unique
@typing.final
class ChannelType(enum.IntEnum):
    """The known channel types that are exposed to us by the API."""

    GUILD_TEXT = 0
    """A text channel in a guild."""

    PRIVATE_TEXT = 1
    """A direct channel between two users."""

    GUILD_VOICE = 2
    """A voice channel in a guild."""

    PRIVATE_GROUP_TEXT = 3
    """A direct channel between multiple users."""

    GUILD_CATEGORY = 4
    """An category used for organizing channels in a guild."""

    GUILD_NEWS = 5
    """A channel that can be followed and can crosspost."""

    GUILD_STORE = 6
    """A channel that show's a game's store page."""

    def __str__(self) -> str:
        return self.name


@enum.unique
@typing.final
class PermissionOverwriteType(str, enum.Enum):
    """The type of entity a Permission Overwrite targets."""

    ROLE = "role"
    """A permission overwrite that targets all the members with a specific role."""

    MEMBER = "member"
    """A permission overwrite that targets a specific guild member."""

    def __str__(self) -> str:
        return self.name


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PermissionOverwrite(snowflakes.Unique):
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

    id: snowflakes.Snowflake = attr.ib(
        converter=snowflakes.Snowflake, eq=True, hash=True, repr=True,
    )
    """The ID of this entity."""

    type: PermissionOverwriteType = attr.ib(converter=PermissionOverwriteType, eq=True, hash=True, repr=True)
    """The type of entity this overwrite targets."""

    allow: permissions.Permissions = attr.ib(
        converter=permissions.Permissions, default=permissions.Permissions.NONE, eq=False, hash=False, repr=False,
    )
    """The permissions this overwrite allows."""

    deny: permissions.Permissions = attr.ib(
        converter=permissions.Permissions, default=permissions.Permissions.NONE, eq=False, hash=False, repr=False
    )
    """The permissions this overwrite denies."""

    @property
    def unset(self) -> permissions.Permissions:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        # noinspection PyArgumentList
        return permissions.Permissions(~(self.allow | self.deny))


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PartialChannel(snowflakes.Unique):
    """Channel representation for cases where further detail is not provided.

    This is commonly received in HTTP API responses where full information is
    not available from Discord.
    """

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    name: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The channel's name. This will be missing for DM channels."""

    type: ChannelType = attr.ib(eq=False, hash=False, repr=True)
    """The channel's type."""

    def __str__(self) -> str:
        return self.name if self.name is not None else f"Unnamed {self.__class__.__name__} ID {self.id}"


class TextChannel(PartialChannel, abc.ABC):
    """A channel that can have text messages in it."""

    # This is a mixin, do not add slotted fields.
    __slots__: typing.Sequence[str] = ()

    async def send(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflakes.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages.Message:
        """Create a message in the channel this message belongs to.

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
            channel=self.id,
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

    # TODO: add examples to this and the REST method this invokes.
    def history(
        self,
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
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
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint (other than `builtins.TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `builtins.TypeError`).
        """  # noqa: E501 - Line too long
        return self.app.rest.fetch_messages(self.id, before=before, after=after, around=around)


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PrivateChannel(PartialChannel):
    """The base for anything that is a private (non-guild bound) channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PrivateTextChannel(PrivateChannel, TextChannel):
    """Represents a private text channel that is between you and another user."""

    recipient: users.User = attr.ib(eq=False, hash=False, repr=False)
    """The user recipient of this DM."""

    @property
    def shard_id(self) -> typing.Literal[0]:
        """Return the shard ID for the shard."""
        return 0

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with: {self.recipient}"


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class GroupPrivateTextChannel(PrivateChannel):
    """Represents a group private channel.

    !!! note
        This doesn't have the methods found on `TextChannel` as bots cannot
        interact with a group DM that they own by sending or seeing messages in
        it.
    """

    owner_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the owner of the group."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN hash of the icon of the group, if an icon is set."""

    nicknames: typing.MutableMapping[snowflakes.Snowflake, str] = attr.ib(eq=False, hash=False, repr=False)
    """A mapping of set nicknames within this group DMs to user IDs."""

    recipients: typing.Mapping[snowflakes.Snowflake, users.User] = attr.ib(eq=False, hash=False, repr=False)
    """The recipients of the group DM."""

    application_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the application that created the group DM.

    If the group DM was not created by a bot, this will be `builtins.None`.
    """

    def __str__(self) -> str:
        if self.name is None:
            return f"{self.__class__.__name__} with: {', '.join(str(user) for user in self.recipients.values())}"

        return self.name

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Icon for this DM channel, if set."""
        return self.format_icon()

    # noinspection PyShadowingBuiltins
    def format_icon(self, *, format: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon for this DM, if set.

        Parameters
        ----------
        format : builtins.str
            The format to use for this URL, defaults to `png`.
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
            constants.CDN_URL, channel_id=self.id, hash=self.icon_hash, size=size, file_format=format,
        )


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild the channel belongs to."""

    position: int = attr.ib(eq=False, hash=False, repr=False)
    """The sorting position of the channel.

    Higher numbers appear further down the channel list.
    """

    permission_overwrites: typing.Mapping[snowflakes.Snowflake, PermissionOverwrite] = attr.ib(
        eq=False, hash=False, repr=False
    )
    """The permission overwrites for the channel.

    This maps the ID of the entity in the overwrite to the overwrite data.
    """

    is_nsfw: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=False)
    """Whether the channel is marked as NSFW.

    !!! warning
        This will be `builtins.None` when received over the gateway in certain events
        (e.g Guild Create).
    """

    parent_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the parent category the channel belongs to.

    If no parent category is set for the channel, this will be `builtins.None`.
    """

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Return the shard ID for the shard.

        This may be `builtins.None` if the shard count is not known.
        """
        try:
            return (self.guild_id >> 22) % typing.cast(int, getattr(self.app, "shard_count"))
        except (TypeError, AttributeError, NameError):
            pass

        return None


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class GuildCategory(GuildChannel):
    """Represents a guild category channel.

    These can contain other channels inside, and act as a method for
    organisation.
    """


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class GuildTextChannel(GuildChannel, TextChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    rate_limit_per_user: datetime.timedelta = attr.ib(eq=False, hash=False, repr=False)
    """The delay (in seconds) between a user can send a message to this channel.

    If there is no rate limit, this will be 0 seconds.

    !!! note
        Any user that has permissions allowing `MANAGE_MESSAGES`,
        `MANAGE_CHANNEL`, `ADMINISTRATOR` will not be limited. Likewise, bots
        will not be affected by this rate limit.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be `builtins.None` in several cases; Discord does not document what
        these cases are. Trust no one!
    """


@attr.s(eq=True, hash=True, init=True, slots=True, kw_only=True, weakref_slot=False)
class GuildNewsChannel(GuildChannel, TextChannel):
    """Represents an news channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False, repr=False)
    """The timestamp of the last-pinned message.

    !!! note
        This may be `builtins.None` in several cases; Discord does not document what
        these cases are. Trust no one!
    """


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel.

    These were originally used to sell games when Discord had a game store. This
    was scrapped at the end of 2019, so these may disappear from the platform
    eventually.
    """


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class GuildVoiceChannel(GuildChannel):
    """Represents an voice channel."""

    bitrate: int = attr.ib(eq=False, hash=False, repr=True)
    """The bitrate for the voice channel (in bits per second)."""

    user_limit: int = attr.ib(eq=False, hash=False, repr=True)
    """The user limit for the voice channel.

    If this is `0`, then assume no limit.
    """

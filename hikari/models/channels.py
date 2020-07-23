# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Application and entities that are used to describe both DMs and guild channels on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ChannelType",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "TextChannel",
    "DMChannel",
    "GroupDMChannel",
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

from hikari.models import permissions
from hikari.models import users
from hikari.utilities import constants
from hikari.utilities import files
from hikari.utilities import routes
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime
    from hikari.api import rest as rest_app
    from hikari.models import embeds
    from hikari.models import guilds
    from hikari.models import messages
    from hikari.utilities import iterators


@enum.unique
@typing.final
class ChannelType(enum.IntEnum):
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


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True)
class PermissionOverwrite(snowflake.Unique):
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
            Permission.VIEW_CHANNEL
            | Permission.READ_MESSAGE_HISTORY
            | Permission.SEND_MESSAGES
        ),
        deny=(
            Permission.MANAGE_MESSAGES
            | Permission.SPEAK
        ),
    )
    ```
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    type: PermissionOverwriteType = attr.ib(converter=PermissionOverwriteType, eq=True, hash=True, repr=True)
    """The type of entity this overwrite targets."""

    allow: permissions.Permission = attr.ib(
        converter=permissions.Permission, default=permissions.Permission.NONE, eq=False, hash=False, repr=False,
    )
    """The permissions this overwrite allows."""

    deny: permissions.Permission = attr.ib(
        converter=permissions.Permission, default=permissions.Permission.NONE, eq=False, hash=False, repr=False
    )
    """The permissions this overwrite denies."""

    @property
    def unset(self) -> permissions.Permission:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        # noinspection PyArgumentList
        return permissions.Permission(~(self.allow | self.deny))


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PartialChannel(snowflake.Unique):
    """Channel representation for cases where further detail is not provided.

    This is commonly received in HTTP API responses where full information is
    not available from Discord.
    """

    app: rest_app.IRESTApp = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
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
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages.Message:
        """Create a message in the channel this message belongs to.

        Parameters
        ----------
        content : hikari.utilities.undefined.UndefinedOr[typing.Any]
            If specified, the message contents. If `UNDEFINED`, then nothing
            will be sent in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.models.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.

            Likewise, if this is a `hikari.utilities.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        embed : hikari.utilities.undefined.UndefinedOr[hikari.models.embeds.Embed]
            If specified, the message embed.
        attachment : hikari.utilities.undefined.UndefinedOr[hikari.utilities.files.Resourceish],
            If specified, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.utilities.undefined.UndefinedOr[typing.Sequence[hikari.utilities.files.Resourceish]],
            If specified, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        tts : hikari.utilities.undefined.UndefinedOr[builtins.bool]
            If specified, whether the message will be TTS (Text To Speech).
        nonce : hikari.utilities.undefined.UndefinedOr[builtins.str]
            If specified, a nonce that can be used for optimistic message
            sending.
        mentions_everyone : hikari.utilities.undefined.UndefinedOr[builtins.bool]
            If specified, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.utilities.undefined.UndefinedOr[typing.Collection[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.users.PartialUser] or builtins.bool]
            If specified, and `builtins.True`, all mentions will be parsed.
            If specified, and `builtins.False`, no mentions will be parsed.
            Alternatively this may be a collection of
            `hikari.utilities.snowflake.Snowflake`, or
            `hikari.models.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.utilities.undefined.UndefinedOr[typing.Collection[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.PartialRole] or builtins.bool]
            If specified, and `builtins.True`, all mentions will be parsed.
            If specified, and `builtins.False`, no mentions will be parsed.
            Alternatively this may be a collection of
            `hikari.utilities.snowflake.Snowflake`, or
            `hikari.models.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        !!! note
            Attachments can be passed as many different things, to aid in
            convenience.

            - If a `pathlib.PurePath` or `builtins.str` to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                `hikari.utilities.files.WebResource` such as
                `hikari.utilities.files.URL`,
                `hikari.models.messages.Attachment`,
                `hikari.models.emojis.Emoji`,
                `EmbedResource`, etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a `hikari.utilities.files.Bytes` is passed, or a `builtins.str`
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a `hikari.utilities.files.File`, `pathlib.PurePath` or
                `builtins.str` that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of `concurrent.futures.Executor` that is being used for
                the application (default is a thread pool which supports this
                behaviour).

        Returns
        -------
        hikari.models.messages.Message
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
            once before being able to use this _endpoint for a bot.
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
        before: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
        before : hikari.utilities.undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[hikari.utilities.snowflake.Unique]]
            If provided, fetch messages before this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        after : hikari.utilities.undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[hikari.utilities.snowflake.Unique]]
            If provided, fetch messages after this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        around : hikari.utilities.undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[hikari.utilities.snowflake.Unique]]
            If provided, fetch messages around this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.utilities.iterators.LazyIterator[hikari.models.messages.Message]
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
            The exceptions on this _endpoint (other than `builtins.TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `builtins.TypeError`).
        """  # noqa: E501 - Line too long
        return self.app.rest.fetch_messages(self.id, before=before, after=after, around=around)


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class PrivateChannel(PartialChannel):
    """The base for anything that is a private (non-guild bound) channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class DMChannel(PrivateChannel, TextChannel):
    """Represents a DM channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the last message sent in this channel.

    !!! warning
        This might point to an invalid or deleted message. Do not assume that
        this will always be valid.
    """

    recipient: users.UserImpl = attr.ib(eq=False, hash=False, repr=False)
    """The user recipient of this DM."""

    def __str__(self) -> str:
        return f"{self.__class__.__name__} with: {self.recipient}"


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GroupDMChannel(PrivateChannel):
    """Represents a DM group channel.

    !!! note
        This doesn't have the methods found on `TextChannel` as bots cannot
        interact with a group DM that they own by sending or seeing messages in
        it.
    """

    owner_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the owner of the group."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN hash of the icon of the group, if an icon is set."""

    nicknames: typing.MutableMapping[snowflake.Snowflake, str] = attr.ib(eq=False, hash=False, repr=False)
    """A mapping of set nicknames within this group DMs to user IDs."""

    recipients: typing.Mapping[snowflake.Snowflake, users.UserImpl] = attr.ib(eq=False, hash=False, repr=False)
    """The recipients of the group DM."""

    application_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the application that created the group DM.

    If the group DM was not created by a bot, this will be `builtins.None`.
    """

    def __str__(self) -> str:
        if self.name is None:
            return f"{self.__class__.__name__} with: {', '.join(str(user) for user in self.recipients.values())}"

        return self.name

    @property
    def icon(self) -> typing.Optional[files.URL]:
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
        hikari.utilities.files.URL or builtins.None
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


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild the channel belongs to."""

    position: int = attr.ib(eq=False, hash=False, repr=False)
    """The sorting position of the channel.

    Higher numbers appear further down the channel list.
    """

    permission_overwrites: typing.Mapping[snowflake.Snowflake, PermissionOverwrite] = attr.ib(
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

    parent_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the parent category the channel belongs to.

    If no parent category is set for the channel, this will be `builtins.None`.
    """

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Return the shard ID for the shard.

        This may be `builtins.None` if this channel was not received over the
        gateway in an event, or if the guild is not known, or if the shard count
        is not known.
        """
        try:
            # This is only sensible if there is a shard.
            if self.guild_id is not None:
                return (self.guild_id >> 22) % typing.cast(int, getattr(self.app, "shard_count"))
        except (TypeError, AttributeError, NameError):
            pass

        return None


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildCategory(GuildChannel):
    """Represents a guild category channel.

    These can contain other channels inside, and act as a method for
    organisation.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildTextChannel(GuildChannel, TextChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
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


@attr.s(eq=True, hash=True, init=False, slots=True, kw_only=True)
class GuildNewsChannel(GuildChannel, TextChannel):
    """Represents an news channel."""

    topic: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The topic of the channel."""

    last_message_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
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


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel.

    These were originally used to sell games when Discord had a game store. This
    was scrapped at the end of 2019, so these may disappear from the platform
    eventually.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class GuildVoiceChannel(GuildChannel):
    """Represents an voice channel."""

    bitrate: int = attr.ib(eq=False, hash=False, repr=True)
    """The bitrate for the voice channel (in bits per second)."""

    user_limit: int = attr.ib(eq=False, hash=False, repr=True)
    """The user limit for the voice channel.

    If this is `0`, then assume no limit.
    """

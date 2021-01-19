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
"""Application and entities that are used to describe messages on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "MessageType",
    "MessageFlag",
    "MessageActivityType",
    "Attachment",
    "Reaction",
    "MessageActivity",
    "Mentions",
    "MessageReference",
    "PartialMessage",
    "Message",
    "StickerFormatType",
    "Sticker",
]

import typing

import attr

from hikari import files
from hikari import guilds
from hikari import intents
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels
    from hikari import embeds as embeds_
    from hikari import emojis as emojis_
    from hikari import users as users_

_T = typing.TypeVar("_T")


@typing.final
class MessageType(int, enums.Enum):
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

    REPLY = 19
    """A message that replies to another message."""


@typing.final
class MessageFlag(enums.Flag):
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


@typing.final
class MessageActivityType(int, enums.Enum):
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


@typing.final
class StickerFormatType(int, enums.Enum):
    """The formats types of a sticker's asset."""

    PNG = 1
    """A PNG sticker."""

    APNG = 2
    """A animated PNG sticker."""

    LOTTIE = 3
    """A lottie sticker."""


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
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Sticker(snowflakes.Unique):
    """Represents the stickers found attached to messages on Discord."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    pack_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """ID of the package this sticker belongs to."""

    name: str = attr.ib(eq=False, hash=False, repr=True)
    """The name of this sticker."""

    description: str = attr.ib(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    tags: typing.Sequence[str] = attr.ib(eq=False, hash=False, repr=True)
    """A sequence of this sticker's tags."""

    asset_hash: str = attr.ib(eq=False, hash=False, repr=False)
    """The hash of this sticker's asset.

    !!! note
        The CDN endpoint for this hash is currently undocumented.
    """

    preview_asset_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The hash of this sticker's preview asset.

    !!! note
        The CDN endpoint for this hash is currently undocumented.
    """

    format_type: typing.Union[StickerFormatType, int] = attr.ib(eq=False, hash=False, repr=True)
    """The format of this sticker's asset."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class MessageActivity:
    """Represents the activity of a rich presence-enabled message."""

    type: typing.Union[MessageActivityType, int] = attr.ib(repr=True)
    """The type of message activity."""

    party_id: typing.Optional[str] = attr.ib(repr=True)
    """The party ID of the message activity."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class Mentions:
    """Description of mentions that exist in the message."""

    # We refer back to the containing message so that we can provide info about
    # entities that were not notified, and provide access to cached roles
    # through this mechanism.
    _message: PartialMessage = attr.ib()

    users: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, users_.User]] = attr.ib()
    """Users who were notified by their mention in the message."""

    role_ids: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = attr.ib()
    """IDs of roles that were notified by their mention in the message."""

    channels: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels.PartialChannel]] = attr.ib()
    """Channel mentions that reference channels in the target crosspost's guild.

    If the message is not crossposted, this will always be empty.
    """

    everyone: undefined.UndefinedOr[bool] = attr.ib()
    """Whether the message notifies using `@everyone` or `@here`."""

    @property
    def channels_ids(self) -> undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]]:
        if self.channels is undefined.UNDEFINED:
            return undefined.UNDEFINED

        return list(self.channels.keys())

    @property
    def user_ids(self) -> undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]]:
        if self.users is undefined.UNDEFINED:
            return undefined.UNDEFINED

        return list(self.users.keys())

    @property
    def members(self) -> undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, guilds.Member]]:
        """Discover any cached members notified by this message.

        If this message was sent in a DM, this will always be empty.

        !!! warning
            This will only return valid results on gateway events. For REST
            endpoints, this will potentially be empty. This is a limitation of
            Discord's API, as they do not consistently notify of the ID of the
            guild a message was sent in.

        !!! note
            If you are using a stateless application such as a stateless bot
            or a REST-only client, this will always be empty. Furthermore,
            if you are running a stateful bot and have the GUILD_MEMBERS
            intent disabled, this will also be empty.

            Members that are not cached will not appear in this mapping. This
            means that there is a very small chance that some users provided
            in `notified_users` may not be present here.
        """
        if self.users is undefined.UNDEFINED:
            return undefined.UNDEFINED

        if self._ensure_cache(intents.Intents.GUILDS, True):
            guild_id = typing.cast(snowflakes.Snowflake, self._message.guild_id)
            app = typing.cast(traits.CacheAware, self._message.app)

            return self._map_cache_maybe_discover(
                self.users,
                lambda user_id: app.cache.get_member(guild_id, user_id),
            )

        return {}

    @property
    def roles(self) -> typing.Mapping[snowflakes.Snowflake, guilds.Role]:
        """Attempt to look up the roles that are notified by this message.

        If this message was sent in a DM, this will always be empty.

        !!! warning
            This will only return valid results on gateway events. For REST
            endpoints, this will potentially be empty. This is a limitation of
            Discord's API, as they do not consistently notify of the ID of the
            guild a message was sent in.

        !!! note
            If you are using a stateless application such as a stateless bot
            or a REST-only client, this will always be empty. Furthermore,
            if you are running a stateful bot and have the GUILD intent
            disabled, this will also be empty.

            Roles that are not cached will not appear in this mapping. This
            means that there is a very small chance that some role IDs provided
            in `notifies_role_ids` may not be present here. This is a limitation
            of Discord, again.
        """
        if self._ensure_cache(intents.Intents.GUILDS, True):
            app = typing.cast(traits.CacheAware, self._message.app)

            return self._map_cache_maybe_discover(
                self.roles,
                app.cache.get_role,
            )

        return {}

    def _ensure_cache(self, intents_required: intents.Intents, needs_guild: bool) -> bool:
        app = self._message.app

        return bool(
            isinstance(app, traits.ShardAware)
            and isinstance(app, traits.CacheAware)
            and (app.intents & intents_required) == intents_required
            and (not needs_guild or self._message.guild_id)
        )

    @staticmethod
    def _map_cache_maybe_discover(
        ids: typing.Iterable[snowflakes.Snowflake],
        cache_call: typing.Callable[[snowflakes.Snowflake], typing.Optional[_T]],
    ) -> typing.Dict[snowflakes.Snowflake, _T]:
        results: typing.Dict[snowflakes.Snowflake, _T] = {}
        for id_ in ids:
            obj = cache_call(id_)
            if obj is not None:
                results[id_] = obj
        return results


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class MessageReference:
    """Represents information about a referenced message.

    This will be included in crossposted messages, channel follow add
    message, pin add messages and replies.
    """

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: typing.Optional[snowflakes.Snowflake] = attr.ib(repr=True)
    """The ID of the original message.

    This will be `builtins.None` for channel follow add messages. This may
    point to a deleted message.
    """

    channel_id: snowflakes.Snowflake = attr.ib(repr=True)
    """The ID of the channel that the original message originated from."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(repr=True)
    """The ID of the guild that the message originated from.

    This will be `builtins.None` when the original message is not from
    a guild.
    """


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class MessageApplication(guilds.PartialApplication):
    """The representation of an application used in messages."""

    cover_image_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN's hash of this application's cover image, used on the store."""

    primary_sku_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    @property
    def cover_image_url(self) -> typing.Optional[files.URL]:
        """Cover image used on the store.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image exists.
        """
        return self.format_cover_image()

    def format_cover_image(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the cover image used in the store, if set.

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
            The URL, or `builtins.None` if no cover image exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.cover_image_hash is None:
            return None

        return routes.CDN_APPLICATION_COVER.compile_to_file(
            urls.CDN_URL,
            application_id=self.id,
            hash=self.cover_image_hash,
            size=size,
            file_format=ext,
        )


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, init=True, repr=True, eq=False, weakref_slot=False)
class PartialMessage(snowflakes.Unique):
    """A message representation containing partially populated information.

    This contains arbitrary fields that may be updated in a
    `MessageUpdateEvent`, but for all other purposes should be treated as
    being optionally specified.

    !!! warning
        All fields on this model except `channel` and `id` may be set to
        `hikari.undefined.UNDEFINED` (a singleton) if we have not
        received information about their state from Discord alongside field
        nullability.
    """

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    channel_id: snowflakes.Snowflake = attr.ib(repr=True)
    """The ID of the channel that the message was sent in."""

    _guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(repr=True)
    #: Try to determine this best-effort in the property defined further
    #: down.

    author: typing.Optional[users_.User] = attr.ib(repr=True)
    """The author of this message.

    This will be `builtins.None` in some cases such as when Discord
    updates a message with an embed URL preview.
    """

    member: typing.Optional[guilds.Member] = attr.ib(repr=False)
    """The member for the author who created the message.

    If the message is not in a guild, this will be `builtins.None`.

    This will also be `builtins.None` in some cases such as when Discord updates
    a message with an embed URL preview or in messages fetched from the
    REST API.
    """

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

    mentions: Mentions = attr.ib(repr=True)
    """Description of who is mentioned in a message.

    !!! warning
        If the contents have not mutated and this is a message update event,
        some fields that are not affected may be empty instead.

        This is a Discord limitation.
    """

    attachments: undefined.UndefinedOr[typing.Sequence[Attachment]] = attr.ib(repr=False)
    """The message attachments."""

    embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = attr.ib(repr=False)
    """The message embeds."""

    reactions: undefined.UndefinedOr[typing.Sequence[Reaction]] = attr.ib(repr=False)
    """The message reactions."""

    is_pinned: undefined.UndefinedOr[bool] = attr.ib(repr=False)
    """Whether the message is pinned."""

    webhook_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = attr.ib(repr=False)
    """If the message was generated by a webhook, the webhook's ID."""

    type: undefined.UndefinedOr[typing.Union[MessageType, int]] = attr.ib(repr=False)
    """The message type."""

    activity: undefined.UndefinedNoneOr[MessageActivity] = attr.ib(repr=False)
    """The message activity."""

    application: undefined.UndefinedNoneOr[MessageApplication] = attr.ib(repr=False)
    """The message application."""

    message_reference: undefined.UndefinedNoneOr[MessageReference] = attr.ib(repr=False)
    """The message reference data."""

    flags: undefined.UndefinedNoneOr[MessageFlag] = attr.ib(repr=False)
    """The message flags."""

    stickers: undefined.UndefinedOr[typing.Sequence[Sticker]] = attr.ib(repr=False)
    """The stickers sent with this message."""

    nonce: undefined.UndefinedNoneOr[str] = attr.ib(repr=False)
    """The message nonce.

    This is a string used for validating a message was sent.
    """

    referenced_message: undefined.UndefinedNoneOr[Message] = attr.ib(repr=False)
    """The message that was replied to.

    If `type` is `MessageType.REPLY` and `hikari.undefined.UNDEFINED`, Discord's
    backend didn't attempt to fetch the message, so the status is unknown. If
    `type` is `MessageType.REPLY` and `builtins.None`, the message was deleted.
    """

    @property
    def guild_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of the guild that the message was sent in.

        This will not be present on REST API responses if the application is
        stateless or missing the `GUILDS` intent.
        """
        if self._guild_id:
            return self._guild_id

        if not isinstance(self.app, traits.CacheAware):
            return None
        # Don't check the member, as if the guild_id is missing, the member
        # will always be missing too.
        channel = self.app.cache.get_guild_channel(self.channel_id)

        if channel is None:
            return None

        return channel.guild_id

    @property
    def link(self) -> str:
        """Jump link to the message.

        Returns
        -------
        builtins.str
            The jump link to the message.
        """
        guild_id_str = "@me" if self.guild_id is None else str(self.guild_id)
        return f"{urls.BASE_URL}/channels/{guild_id_str}/{self.channel_id}/{self.id}"

    async def fetch_channel(self) -> channels.PartialChannel:
        """Fetch the channel this message was created in.

        Returns
        -------
        hikari.channels.PartialChannel
            The object of the channel this message belongs to.

        Raises
        ------
        hikari.errors.BadRequestError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenError
            If you don't have access to the channel this message belongs to.
        hikari.errors.NotFoundError
            If the channel this message was created in does not exist.
        """
        return await self.app.rest.fetch_channel(self.channel_id)

    async def edit(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
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

        Other Parameters
        ----------------
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
        mentions_reply : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if this is not a reply message.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            Sanitation for user mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid user mentions will behave
            as mentions. If `builtins.False`, all valid user mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.snowflakes.Snowflake` user IDs, or
            `hikari.users.PartialUser`-derived objects.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
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
            else will result in a `hikari.errors.ForbiddenError` being raised.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds; users in `user_mentions` not
            being mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you lack permissions to send messages in the given channel; if
            you try to change the contents of another user's message; or if you
            try to edit the flags on another user's message without the
            permissions to manage messages.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long
        return await self.app.rest.edit_message(
            message=self.id,
            channel=self.channel_id,
            content=content,
            embed=embed,
            mentions_everyone=mentions_everyone,
            mentions_reply=mentions_reply,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            flags=flags,
        )

    async def respond(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[PartialMessage], bool
        ] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> Message:
        """Create a message in the channel this message belongs to.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish],
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]],
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message will be TTS (Text To Speech).
        nonce : hikari.undefined.UndefinedOr[builtins.str]
            If provided, a nonce that can be used for optimistic message
            sending.
        reply : typing.Union[hikari.undefined.UndefinedType, hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage], builtins.bool]
            If provided and `builtins.True`, reply to this message.
            If provided and not `builtins.bool`, the message to reply to.
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
            `hikari.snowflakes.Snowflake`, or `hikari.users.PartialUser`
            derivatives to enforce mentioning specific users.
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
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content; `reply` not found
            or not in the same channel.
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

        !!! warning
            You are expected to make a connection to the gateway and identify
            once before being able to use this endpoint for a bot.
        """  # noqa: E501 - Line too long
        if reply is True:
            reply = self

        return await self.app.rest.create_message(
            channel=self.channel_id,
            content=content,
            embed=embed,
            attachment=attachment,
            attachments=attachments,
            nonce=nonce,
            tts=tts,
            reply=reply,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            mentions_reply=mentions_reply,
        )

    async def delete(self) -> None:
        """Delete this message.

        Raises
        ------
        hikari.errors.NotFoundError
            If the channel this message was created in is not found, or if the
            message has already been deleted.
        hikari.errors.ForbiddenError
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
        hikari.errors.BadRequestError
            If the emoji is invalid, unknown, or formatted incorrectly.
        hikari.errors.ForbiddenError
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error.
        hikari.errors.NotFoundError
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
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users_.PartialUser]] = undefined.UNDEFINED,
    ) -> None:
        r"""Remove a reaction from this message.

        Parameters
        ----------
        emoji : hikari.emojis.Emojiish
            The emoji to remove.

        Other Parameters
        ----------------
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
        hikari.errors.BadRequestError
            If the emoji is invalid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenError
            If this is the first reaction using this specific emoji on this
            message and you lack the `ADD_REACTIONS` permission. If you lack
            `READ_MESSAGE_HISTORY`, this may also raise this error. If you
            remove the reaction of another user without `MANAGE_MESSAGES`, this
            will be raised.
        hikari.errors.NotFoundError
            If the channel or message is not found, or if the emoji is not
            found.
        """
        if user is undefined.UNDEFINED:
            await self.app.rest.delete_my_reaction(channel=self.channel_id, message=self.id, emoji=emoji)
        else:
            await self.app.rest.delete_reaction(channel=self.channel_id, message=self.id, emoji=emoji, user=user)

    async def remove_all_reactions(self, emoji: undefined.UndefinedOr[emojis_.Emojiish] = undefined.UNDEFINED) -> None:
        r"""Remove all users' reactions for a specific emoji from the message.

        Other Parameters
        ----------------
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
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` permission, or the
            permission to view the channel
        hikari.errors.NotFoundError
            If the channel or message is not found, or if the emoji is not
            found.
        hikari.errors.BadRequestError
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

    author: users_.User
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

    mentions: Mentions
    """Who is mentioned in a message."""

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

    type: typing.Union[MessageType, int]
    """The message type."""

    activity: typing.Optional[MessageActivity]
    """The message activity."""

    application: typing.Optional[MessageApplication]
    """The message application."""

    message_reference: typing.Optional[MessageReference]
    """The message reference data."""

    flags: typing.Optional[MessageFlag]
    """The message flags."""

    stickers: typing.Sequence[Sticker]
    """The stickers sent with this message."""

    nonce: typing.Optional[str]
    """The message nonce. This is a string used for validating a message was sent."""

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
"""Application and entities that are used to describe messages on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MessageType",
    "MessageFlag",
    "MessageActivityType",
    "Attachment",
    "Reaction",
    "MessageActivity",
    "MessageInteraction",
    "MessageReference",
    "PartialMessage",
    "Message",
)

import typing

import attrs

from hikari import components as component_models
from hikari import files
from hikari import guilds
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels as channels_
    from hikari import embeds as embeds_
    from hikari import emojis as emojis_
    from hikari import stickers as stickers_
    from hikari import users as users_
    from hikari.api import special_endpoints
    from hikari.interactions import base_interactions

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

    GUILD_DISCOVERY_DISQUALIFIED = 14
    """A message to indicate that a guild has been disqualified from discovery."""

    GUILD_DISCOVERY_REQUALIFIED = 15
    """A message to indicate that a guild has re-qualified for discovery."""

    GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING = 16
    """A message to indicate that the grace period before removal from discovery has started."""

    GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING = 17
    """A message to indicate the final warning before removal from discovery."""

    REPLY = 19
    """A message that replies to another message."""

    CHAT_INPUT = 20
    """A message sent to indicate a chat input application command has been executed."""

    GUILD_INVITE_REMINDER = 22
    """A message sent to remind to invite people to the guild."""

    CONTEXT_MENU_COMMAND = 23
    """A message sent to indicate a context menu has been executed."""

    ROLE_SUBSCRIPTION_PURCHASE = 25
    """A message sent to indicate a role subscription has been purchased."""


@typing.final
class MessageFlag(enums.Flag):
    """Additional flags for message options."""

    NONE = 0
    """None."""

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

    EPHEMERAL = 1 << 6
    """This message is only visible to the user that invoked the interaction."""

    LOADING = 1 << 7
    """This message symbolizes that the interaction is 'thinking'."""

    FAILED_TO_MENTION_SOME_ROLES_IN_THREAD = 1 << 8
    """This message failed to mention some roles and add their mentions to the thread."""

    SUPPRESS_NOTIFICATIONS = 1 << 12
    """This message will not trigger push and desktop notifications."""

    IS_VOICE_MESSAGE = 1 << 13
    """This message is a voice message."""


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


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class Attachment(snowflakes.Unique, files.WebResource):
    """Represents a file attached to a message.

    You can use this object in the same way as a [hikari.files.WebResource][],
    by passing it as an attached file when creating a message, etc.

    It can also be used when editing a message to keep a previous attachment.
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    url: str = attrs.field(hash=False, eq=False, repr=True)
    """The source URL of file."""

    filename: str = attrs.field(hash=False, eq=False, repr=True)
    """The name of the file."""

    media_type: typing.Optional[str] = attrs.field(hash=False, eq=False, repr=True)
    """The media type of the file."""

    size: int = attrs.field(hash=False, eq=False, repr=True)
    """The size of the file in bytes."""

    proxy_url: str = attrs.field(hash=False, eq=False, repr=False)
    """The proxied URL of file."""

    height: typing.Optional[int] = attrs.field(hash=False, eq=False, repr=False)
    """The height of the image (if the file is an image)."""

    width: typing.Optional[int] = attrs.field(hash=False, eq=False, repr=False)
    """The width of the image (if the file is an image)."""

    is_ephemeral: bool = attrs.field(hash=False, eq=False, repr=True)
    """Whether this attachment is ephemeral.

    This is a part of the ephemeral message response interactions feature
    and indicates that the attachment will be removed after a set period of
    time (but will exist as long as their relevant message exists).
    """

    duration: typing.Optional[float] = attrs.field(hash=False, eq=False, repr=False)
    """The duration (in seconds) of the voice message."""

    waveform: typing.Optional[str] = attrs.field(hash=False, eq=False, repr=False)
    """A base64 encoded representation of the sampled waveform for the voice message."""

    def __str__(self) -> str:
        return self.filename


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class Reaction:
    """Represents a reaction in a message."""

    count: int = attrs.field(eq=False, hash=False, repr=True)
    """The number of times the emoji has been used to react."""

    emoji: typing.Union[emojis_.UnicodeEmoji, emojis_.CustomEmoji] = attrs.field(hash=True, repr=True)
    """The emoji used to react."""

    is_me: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the current user reacted using this emoji."""

    def __str__(self) -> str:
        return str(self.emoji)


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MessageActivity:
    """Represents the activity of a rich presence-enabled message."""

    type: typing.Union[MessageActivityType, int] = attrs.field(repr=True)
    """The type of message activity."""

    party_id: typing.Optional[str] = attrs.field(repr=True)
    """The party ID of the message activity."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class MessageReference:
    """Represents information about a referenced message.

    This will be included in crossposted messages, channel follow add
    message, pin add messages and replies.
    """

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    id: typing.Optional[snowflakes.Snowflake] = attrs.field(repr=True)
    """The ID of the original message.

    This will be [None][] for channel follow add messages. This may
    point to a deleted message.
    """

    channel_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The ID of the channel that the original message originated from."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attrs.field(repr=True)
    """The ID of the guild that the message originated from.

    This will be [None][] when the original message is not from
    a guild.
    """


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class MessageApplication(guilds.PartialApplication):
    """The representation of an application used in messages."""

    cover_image_hash: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The CDN's hash of this application's default rich presence invite cover image."""

    @property
    def cover_image_url(self) -> typing.Optional[files.URL]:
        """Rich presence cover image URL for this application, if set."""
        return self.make_cover_image_url()

    def make_cover_image_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the rich presence cover image URL for this application, if set.

        Parameters
        ----------
        ext : str
            The extension to use for this URL.
            supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [None][] if no cover image exists.

        Raises
        ------
        ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.cover_image_hash is None:
            return None

        return routes.CDN_APPLICATION_COVER.compile_to_file(
            urls.CDN_URL, application_id=self.id, hash=self.cover_image_hash, size=size, file_format=ext
        )


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=True, hash=True, weakref_slot=False)
class MessageInteraction:
    """Representation of information provided for a message from an interaction."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """ID of the interaction this message was sent by."""

    type: typing.Union[base_interactions.InteractionType, int] = attrs.field(eq=False, repr=True)
    """The type of interaction this message was created by."""

    name: str = attrs.field(eq=False, repr=True)
    """Name of the application command the interaction is tied to."""

    user: users_.User = attrs.field(eq=False, repr=True)
    """Object of the user who invoked this interaction."""


def _map_cache_maybe_discover(
    ids: typing.Iterable[snowflakes.Snowflake], cache_call: typing.Callable[[snowflakes.Snowflake], typing.Optional[_T]]
) -> typing.Dict[snowflakes.Snowflake, _T]:
    results: typing.Dict[snowflakes.Snowflake, _T] = {}
    for id_ in ids:
        obj = cache_call(id_)
        if obj is not None:
            results[id_] = obj
    return results


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=True, eq=False, weakref_slot=False)
class PartialMessage(snowflakes.Unique):
    """A message representation containing partially populated information.

    This contains arbitrary fields that may be updated in a
    [hikari.events.message_events.MessageUpdateEvent][], but for all other purposes should be treated as
    being optionally specified.

    !!! warning
        All fields on this model except `id` and `channel_id` may be set to
        [hikari.undefined.UNDEFINED][] if we have not received information
        about their state from Discord alongside field nullability.
    """

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    channel_id: snowflakes.Snowflake = attrs.field(hash=False, eq=False, repr=True)
    """The ID of the channel that the message was sent in."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attrs.field(hash=False, eq=False, repr=True)
    """The ID of the guild that the message was sent in or [None][] for messages out of guilds.

    !!! warning
        This will also be [None][] for messages received from the REST API.
        This is a Discord limitation as stated here <https://github.com/discord/discord-api-docs/issues/912>
    """

    author: undefined.UndefinedOr[users_.User] = attrs.field(hash=False, eq=False, repr=True)
    """The author of this message.

    This will also be [hikari.undefined.UNDEFINED][] in some cases such as when Discord
    updates a message with an embed URL preview or in messages fetched from the REST API.
    """

    member: undefined.UndefinedNoneOr[guilds.Member] = attrs.field(hash=False, eq=False, repr=False)
    """The member for the author who created the message.

    If the message is not in a guild, this will be [None][].

    This will also be [hikari.undefined.UNDEFINED][] in some cases such as when Discord
    updates a message with an embed URL preview.

    !!! warning
        This will also be [None][] for messages received from the REST API.
        This is a Discord limitation as stated here <https://github.com/discord/discord-api-docs/issues/912>
    """

    content: undefined.UndefinedNoneOr[str] = attrs.field(hash=False, eq=False, repr=False)
    """The content of the message."""

    timestamp: undefined.UndefinedOr[datetime.datetime] = attrs.field(hash=False, eq=False, repr=False)
    """The timestamp that the message was sent at."""

    edited_timestamp: undefined.UndefinedNoneOr[datetime.datetime] = attrs.field(hash=False, eq=False, repr=False)
    """The timestamp that the message was last edited at.

    Will be [None] if the message wasn't ever edited, or [hikari.undefined.UNDEFINED][]
    if the info is not available.
    """

    is_tts: undefined.UndefinedOr[bool] = attrs.field(hash=False, eq=False, repr=False)
    """Whether the message is a TTS message."""

    user_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, users_.User]] = attrs.field(
        hash=False, eq=False, repr=False
    )
    """Users who were notified by their mention in the message.

    !!! warning
        If the contents have not mutated and this is a message update event,
        some fields that are not affected may be empty instead.

        This is a Discord limitation.
    """

    role_mention_ids: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = attrs.field(
        hash=False, eq=False, repr=False
    )
    """IDs of roles that were notified by their mention in the message.

    !!! warning
        If the contents have not mutated and this is a message update event,
        some fields that are not affected may be empty instead.

        This is a Discord limitation.
    """

    channel_mentions: undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, channels_.PartialChannel]] = (
        attrs.field(hash=False, eq=False, repr=False)
    )
    """Channel mentions that reference channels in the target crosspost's guild.

    If the message is not crossposted, this will always be empty.

    !!! warning
        If the contents have not mutated and this is a message update event,
        some fields that are not affected may be empty instead.

        This is a Discord limitation.
    """

    mentions_everyone: undefined.UndefinedOr[bool] = attrs.field(hash=False, eq=False, repr=False)
    """Whether the message notifies using `@everyone` or `@here`.

    !!! warning
        If the contents have not mutated and this is a message update event,
        some fields that are not affected may be empty instead.

        This is a Discord limitation.
    """

    attachments: undefined.UndefinedOr[typing.Sequence[Attachment]] = attrs.field(hash=False, eq=False, repr=False)
    """The message attachments."""

    embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = attrs.field(hash=False, eq=False, repr=False)
    """The message embeds."""

    reactions: undefined.UndefinedOr[typing.Sequence[Reaction]] = attrs.field(hash=False, eq=False, repr=False)
    """The message reactions."""

    is_pinned: undefined.UndefinedOr[bool] = attrs.field(hash=False, eq=False, repr=False)
    """Whether the message is pinned."""

    webhook_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = attrs.field(hash=False, eq=False, repr=False)
    """If the message was generated by a webhook, the webhook's ID."""

    type: undefined.UndefinedOr[typing.Union[MessageType, int]] = attrs.field(hash=False, eq=False, repr=False)
    """The message type."""

    activity: undefined.UndefinedNoneOr[MessageActivity] = attrs.field(hash=False, eq=False, repr=False)
    """The message activity.

    !!! note
        This will only be provided for messages with rich-presence related chat
        embeds.
    """

    application: undefined.UndefinedNoneOr[MessageApplication] = attrs.field(hash=False, eq=False, repr=False)
    """The message application.

    !!! note
        This will only be provided for messages with rich-presence related chat
        embeds.
    """

    message_reference: undefined.UndefinedNoneOr[MessageReference] = attrs.field(hash=False, eq=False, repr=False)
    """The message reference data."""

    flags: undefined.UndefinedOr[MessageFlag] = attrs.field(hash=False, eq=False, repr=False)
    """The message flags."""

    stickers: undefined.UndefinedOr[typing.Sequence[stickers_.PartialSticker]] = attrs.field(
        hash=False, eq=False, repr=False
    )
    """The stickers sent with this message."""

    nonce: undefined.UndefinedNoneOr[str] = attrs.field(hash=False, eq=False, repr=False)
    """The message nonce.

    This is a string used for validating a message was sent.
    """

    referenced_message: undefined.UndefinedNoneOr[PartialMessage] = attrs.field(hash=False, eq=False, repr=False)
    """The message that was replied to.

    If `type` is [hikari.messages.MessageType.REPLY][] and [hikari.undefined.UNDEFINED][], Discord's
    backend didn't attempt to fetch the message, so the status is unknown. If
    `type` is [hikari.messages.MessageType.REPLY][] and [None][], the message was deleted.
    """

    interaction: undefined.UndefinedNoneOr[MessageInteraction] = attrs.field(hash=False, eq=False, repr=False)
    """Information about the interaction this message was created by."""

    application_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = attrs.field(hash=False, eq=False, repr=False)
    """ID of the application this message was sent by.

    !!! note
        This will only be provided for interaction messages.
    """

    components: undefined.UndefinedOr[typing.Sequence[component_models.MessageActionRowComponent]] = attrs.field(
        hash=False, eq=False, repr=False
    )
    """Sequence of the components attached to this message."""

    @property
    def channel_mention_ids(self) -> undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]]:
        """Ids of channels that reference channels in the target crosspost's guild.

        If the message is not crossposted, this will always be empty.

        !!! warning
            If the contents have not mutated and this is a message update event,
            some fields that are not affected may be empty instead.

            This is a Discord limitation.
        """
        if self.channel_mentions is undefined.UNDEFINED:
            return undefined.UNDEFINED

        return list(self.channel_mentions.keys())

    @property
    def user_mentions_ids(self) -> undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]]:
        """Ids of the users who were notified by their mention in the message.

        !!! warning
            If the contents have not mutated and this is a message update event,
            some fields that are not affected may be empty instead.

            This is a Discord limitation.
        """
        if self.user_mentions is undefined.UNDEFINED:
            return undefined.UNDEFINED

        return list(self.user_mentions.keys())

    def get_member_mentions(self) -> undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, guilds.Member]]:
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
            in [notified_users][] may not be present here.
        """
        if self.user_mentions is undefined.UNDEFINED:
            return undefined.UNDEFINED

        if isinstance(self.app, traits.CacheAware) and self.guild_id is not None:
            app = self.app
            guild_id = self.guild_id
            return _map_cache_maybe_discover(
                self.user_mentions, lambda user_id: app.cache.get_member(guild_id, user_id)
            )

        return {}

    def get_role_mentions(self) -> undefined.UndefinedOr[typing.Mapping[snowflakes.Snowflake, guilds.Role]]:
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
            in [notifies_role_ids][] may not be present here. This is a limitation
            of Discord, again.
        """
        if self.role_mention_ids is undefined.UNDEFINED:
            return undefined.UNDEFINED

        if isinstance(self.app, traits.CacheAware) and self.guild_id is not None:
            return _map_cache_maybe_discover(self.role_mention_ids, self.app.cache.get_role)

        return {}

    def make_link(self, guild: typing.Optional[snowflakes.SnowflakeishOr[guilds.PartialGuild]]) -> str:
        """Generate a jump link to this message.

        Other Parameters
        ----------------
        guild : typing.Optional[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild this message is in or [None][]
            to generate a DM message link.

            This parameter is necessary since [hikari.messages.PartialMessage.guild_id][]
            isn't returned by the REST API regardless of whether the message
            is in a DM or not.

        Returns
        -------
        str
            The jump link to the message.
        """
        guild_id_str = "@me" if guild is None else str(int(guild))
        return f"{urls.BASE_URL}/channels/{guild_id_str}/{self.channel_id}/{self.id}"

    async def fetch_channel(self) -> channels_.PartialChannel:
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
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_channel(self.channel_id)

    async def edit(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedNoneOr[typing.Union[files.Resourceish, Attachment]] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
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

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

        !!! warning
            If you specify a text `content`, `mentions_everyone`,
            `mentions_reply`, `user_mentions`, and `role_mentions` will default
            to [False][] as the message will be re-parsed for mentions. This will
            also occur if only one of the four are specified

            This is a limitation of Discord's design. If in doubt, specify all
            four of them each time.

        !!! warning
            If the message was not sent by your user, the only parameter
            you may provide to this call is the `flags` parameter. Anything
            else will result in a [hikari.errors.ForbiddenError][] being raised.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message content to update with. If
            [hikari.undefined.UNDEFINED][], then the content will not
            be changed. If `None`, then the content will be removed.

            Any other value will be cast to a `str` before sending.

            If this is a [hikari.embeds.Embed][] and neither the `embed` or
            `embeds` kwargs are provided or if this is a
            [hikari.files.Resourceish][] and neither the
            `attachment` or `attachments` kwargs are provided, the values will
            be overwritten. This allows for simpler syntax when sending an
            embed or an attachment alone.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the attachment to set on the message. If
            [hikari.undefined.UNDEFINED][], the previous attachment, if
            present, is not changed. If this is `None`, then the
            attachment is removed, if present. Otherwise, the new attachment
            that was provided will be attached.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the attachments to set on the message. If
            [hikari.undefined.UNDEFINED][], the previous attachments, if
            present, are not changed. If this is `None`, then the
            attachments is removed, if present. Otherwise, the new attachments
            that were provided will be attached.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to set for this message.
            This component will replace any previously set components and passing
            `None` will remove all components.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects set for
            this message. These components will replace any previously set
            components and passing `None` or an empty sequence will
            remove all components.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            [hikari.undefined.UNDEFINED][], the previous embed(s) are not changed.
            If this is `None` then any present embeds are removed.
            Otherwise, the new embed that was provided will be used as the
            replacement.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the embeds to set on the message. If
            [hikari.undefined.UNDEFINED][], the previous embed(s) are not changed.
            If this is `None` then any present embeds are removed.
            Otherwise, the new embeds that were provided will be used as the
            replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            Sanitation for `@everyone` mentions. If
            [hikari.undefined.UNDEFINED][], then the previous setting is
            not changed. If `True`, then `@everyone`/`@here` mentions
            in the message content will show up as mentioning everyone that can
            view the chat.
        mentions_reply : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if this is not a reply message.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            Sanitation for user mentions. If
            [hikari.undefined.UNDEFINED][], then the previous setting is
            not changed. If `True`, all valid user mentions will behave
            as mentions. If `False`, all valid user mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            [hikari.snowflakes.Snowflake][] user IDs, or
            [hikari.users.PartialUser][]-derived objects.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            Sanitation for role mentions. If
            [hikari.undefined.UNDEFINED][], then the previous setting is
            not changed. If `True`, all valid role mentions will behave
            as mentions. If `False`, all valid role mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            [hikari.snowflakes.Snowflake][] role IDs, or
            [hikari.guilds.PartialRole][]-derived objects.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            Optional flags to set on the message. If
            [hikari.undefined.UNDEFINED][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [hikari.messages.MessageFlag.NONE][] and [hikari.messages.MessageFlag.SUPPRESS_EMBEDS][]. If you
            have [hikari.permissions.Permissions.MANAGE_MESSAGES][] permissions, you can use this call to
            suppress embeds on another user's message.

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
            limits; invalid image URLs in embeds.
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
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
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
        reply: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[PartialMessage], bool
        ] = undefined.UNDEFINED,
        reply_must_exist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users_.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, MessageFlag] = undefined.UNDEFINED,
    ) -> Message:
        """Create a message in the channel this message belongs to.

        Parameters
        ----------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [hikari.undefined.UNDEFINED][], then nothing will be sent
            in the content. Any other value here will be cast to a
            `str`.

            If this is a [hikari.embeds.Embed][] and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.

            Likewise, if this is a [hikari.files.Resource][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish],
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.

            Attachments can be passed as many different things, to aid in
            convenience.

            - If a `pathlib.PurePath` or `str` to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                [hikari.files.WebResource][] such as
                [hikari.files.URL][],
                [hikari.messages.Attachment][],
                [hikari.emojis.Emoji][],
                [hikari.embeds.EmbedResource][], etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a [hikari.files.Bytes][] is passed, or a `str`
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a [hikari.files.File][], `pathlib.PurePath` or
                `str` that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of `concurrent.futures.Executor` that is being used for
                the application (default is a thread pool which supports this
                behaviour).
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
        sticker : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]]
            If provided, object or ID of a sticker to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        stickers : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.stickers.PartialSticker]]
            If provided, object or ID of up to 3 stickers to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be TTS (Text To Speech).
        reply : typing.Union[hikari.undefined.UndefinedType, hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage], bool]
            If provided and `True`, reply to this message.
            If provided and not `bool`, the message to reply to.
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
            If provided, and `True`, all mentions will be parsed.
            If provided, and `False`, no mentions will be parsed.
            Alternatively this may be a collection of
            [hikari.snowflakes.Snowflake][], or [hikari.users.PartialUser][]
            derivatives to enforce mentioning specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and `True`, all mentions will be parsed.
            If provided, and `False`, no mentions will be parsed.
            Alternatively this may be a collection of
            [hikari.snowflakes.Snowflake][], or
            [hikari.guilds.PartialRole][] derivatives to enforce mentioning
            specific roles.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            If provided, optional flags to set on the message. If
            [hikari.undefined.UNDEFINED][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [hikari.messages.MessageFlag.NONE][] and [hikari.messages.MessageFlag.SUPPRESS_EMBEDS][].

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
        if reply is True:
            reply = self

        elif reply is False:
            reply = undefined.UNDEFINED

        return await self.app.rest.create_message(
            channel=self.channel_id,
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

    @typing.overload
    async def add_reaction(self, emoji: typing.Union[str, emojis_.Emoji]) -> None: ...

    @typing.overload
    async def add_reaction(self, emoji: str, emoji_id: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]) -> None: ...

    async def add_reaction(
        self,
        emoji: typing.Union[str, emojis_.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis_.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        r"""Add a reaction to this message.

        Parameters
        ----------
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to react with.

            Note that if the emoji is an [hikari.emojis.CustomEmoji][]
            and is not from a guild the bot user is in, then this will fail.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to react with.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

            Note that this will fail if the emoji is from a guild the bot isn't
            in.

        Examples
        --------
        ```py
            # Using a unicode emoji.
            await message.add_reaction("👌")

            # Using a unicode emoji name.
            await message.add_reaction("\N{OK HAND SIGN}")

            # Using the name and id.
            await message.add_reaction("rooAYAYA", 705837374319493284)

            # Using an Emoji-derived object.
            await message.add_reaction(some_emoji_object)
        ```

        Raises
        ------
        hikari.errors.BadRequestError
            If the emoji is invalid, unknown, or formatted incorrectly.
        hikari.errors.ForbiddenError
            If this is the first reaction using this specific emoji on this
            message and you lack the [hikari.permissions.Permissions.ADD_REACTIONS][] permission. If you lack
            [hikari.permissions.Permissions.READ_MESSAGE_HISTORY][], this may also raise this error.
        hikari.errors.NotFoundError
            If the channel or message is not found, or if the emoji is not
            found.

            This will also occur if you try to add an emoji from a
            guild you are not part of if no one else has previously
            reacted with the same emoji.
        """
        await self.app.rest.add_reaction(channel=self.channel_id, message=self.id, emoji=emoji, emoji_id=emoji_id)

    @typing.overload
    async def remove_reaction(
        self,
        emoji: typing.Union[str, emojis_.Emoji],
        *,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users_.PartialUser]] = undefined.UNDEFINED,
    ) -> None: ...

    @typing.overload
    async def remove_reaction(
        self,
        emoji: str,
        emoji_id: snowflakes.SnowflakeishOr[emojis_.CustomEmoji],
        *,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users_.PartialUser]] = undefined.UNDEFINED,
    ) -> None: ...

    async def remove_reaction(
        self,
        emoji: typing.Union[str, emojis_.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis_.CustomEmoji]] = undefined.UNDEFINED,
        *,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users_.PartialUser]] = undefined.UNDEFINED,
    ) -> None:
        r"""Remove a reaction from this message.

        Parameters
        ----------
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to remove the reaction for.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to remove the reaction for.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.
        user : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]
            The user of the reaction to remove. If unspecified, then the bot's
            reaction is removed instead.

        Examples
        --------
        ```py
            # Using a unicode emoji and removing the bot's reaction from this
            # reaction.
            await message.remove_reaction("\N{OK HAND SIGN}")

            # Using a custom emoji's name and ID to remove a specific user's
            # reaction from this reaction.
            await message.remove_reaction("a:Distraction", 745991233939439616, user=some_user)

            # Using a unicode emoji and removing a specific user from this
            # reaction.
            await message.remove_reaction("\N{OK HAND SIGN}", user=some_user)

            # Using the name and id.
            await message.add_reaction("rooAYAYA", 705837374319493284)

            # Using an Emoji object and removing a specific user from this
            # reaction.
            await message.remove_reaction(some_emoji_object, user=some_user)
        ```

        Raises
        ------
        hikari.errors.BadRequestError
            If the emoji is invalid, unknown, or formatted incorrectly.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenError
            If this is the first reaction using this specific emoji on this
            message and you lack the [hikari.permissions.Permissions.ADD_REACTIONS][] permission. If you lack
            [hikari.permissions.Permissions.READ_MESSAGE_HISTORY][], this may also raise this error. If you
            remove the reaction of another user without [hikari.permissions.Permissions.MANAGE_MESSAGES][], this
            will be raised.
        hikari.errors.NotFoundError
            If the channel or message is not found, or if the emoji is not
            found.
        """
        if user is undefined.UNDEFINED:
            await self.app.rest.delete_my_reaction(
                channel=self.channel_id, message=self.id, emoji=emoji, emoji_id=emoji_id
            )
        else:
            await self.app.rest.delete_reaction(
                channel=self.channel_id, message=self.id, emoji=emoji, emoji_id=emoji_id, user=user
            )

    @typing.overload
    async def remove_all_reactions(self) -> None: ...

    @typing.overload
    async def remove_all_reactions(self, emoji: typing.Union[str, emojis_.Emoji]) -> None: ...

    @typing.overload
    async def remove_all_reactions(
        self, emoji: str, emoji_id: snowflakes.SnowflakeishOr[emojis_.CustomEmoji]
    ) -> None: ...

    async def remove_all_reactions(
        self,
        emoji: undefined.UndefinedOr[typing.Union[str, emojis_.Emoji]] = undefined.UNDEFINED,
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis_.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        r"""Remove all users' reactions for a specific emoji from the message.

        Other Parameters
        ----------------
        emoji : hikari.undefined.UndefinedOr[typing.Union[str, hikari.emojis.Emoji]]
            Object or name of the emoji to get the reactions for. If not specified
            then all reactions are removed.
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to react with.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

        Examples
        --------
        ```py
            # Using a unicode emoji and removing all 👌 reacts from the message.
            # reaction.
            await message.remove_all_reactions("\N{OK HAND SIGN}")

            # Using the name and id.
            await message.add_reaction("rooAYAYA", 705837374319493284)

            # Removing all reactions entirely.
            await message.remove_all_reactions()
        ```

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [hikari.permissions.Permissions.MANAGE_MESSAGES][] permission, or the
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
            await self.app.rest.delete_all_reactions_for_emoji(
                channel=self.channel_id, message=self.id, emoji=emoji, emoji_id=emoji_id
            )


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class Message(PartialMessage):
    """Represents a message with all known details."""

    author: users_.User = attrs.field(hash=False, eq=False, repr=True)
    """The author of this message."""

    member: typing.Optional[guilds.Member] = attrs.field(hash=False, eq=False, repr=False)
    """The member properties for the message's author."""

    content: typing.Optional[str] = attrs.field(hash=False, eq=False, repr=False)
    """The content of the message."""

    timestamp: datetime.datetime = attrs.field(hash=False, eq=False, repr=False)
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Optional[datetime.datetime] = attrs.field(hash=False, eq=False, repr=False)
    """The timestamp that the message was last edited at.

    Will be `None` if it wasn't ever edited.
    """

    is_tts: bool = attrs.field(hash=False, eq=False, repr=False)
    """Whether the message is a TTS message."""

    attachments: typing.Sequence[Attachment] = attrs.field(hash=False, eq=False, repr=False)
    """The message attachments."""

    embeds: typing.Sequence[embeds_.Embed] = attrs.field(hash=False, eq=False, repr=False)
    """The message embeds."""

    reactions: typing.Sequence[Reaction] = attrs.field(hash=False, eq=False, repr=False)
    """The message reactions."""

    is_pinned: bool = attrs.field(hash=False, eq=False, repr=False)
    """Whether the message is pinned."""

    webhook_id: typing.Optional[snowflakes.Snowflake] = attrs.field(hash=False, eq=False, repr=False)
    """If the message was generated by a webhook, the webhook's id."""

    type: typing.Union[MessageType, int] = attrs.field(hash=False, eq=False, repr=False)
    """The message type."""

    activity: typing.Optional[MessageActivity] = attrs.field(hash=False, eq=False, repr=False)
    """The message activity.

    !!! note
        This will only be provided for messages with rich-presence related chat
        embeds.
    """

    application: typing.Optional[MessageApplication] = attrs.field(hash=False, eq=False, repr=False)
    """The message application.

    !!! note
        This will only be provided for messages with rich-presence related chat
        embeds.
    """

    message_reference: typing.Optional[MessageReference] = attrs.field(hash=False, eq=False, repr=False)
    """The message reference data."""

    flags: MessageFlag = attrs.field(hash=False, eq=False, repr=True)
    """The message flags."""

    stickers: typing.Sequence[stickers_.PartialSticker] = attrs.field(hash=False, eq=False, repr=False)
    """The stickers sent with this message."""

    nonce: typing.Optional[str] = attrs.field(hash=False, eq=False, repr=False)
    """The message nonce. This is a string used for validating a message was sent."""

    referenced_message: typing.Optional[PartialMessage] = attrs.field(hash=False, eq=False, repr=False)
    """The message that was replied to.

    If `type` is [hikari.messages.MessageType.REPLY][] and `None`, the message was deleted.
    """

    interaction: typing.Optional[MessageInteraction] = attrs.field(hash=False, eq=False, repr=False)
    """Information about the interaction this message was created by."""

    application_id: typing.Optional[snowflakes.Snowflake] = attrs.field(hash=False, eq=False, repr=False)
    """ID of the application this message was sent by.

    !!! note
        This will only be provided for interaction messages.
    """

    components: typing.Sequence[component_models.MessageActionRowComponent] = attrs.field(
        hash=False, eq=False, repr=False
    )
    """Sequence of the components attached to this message."""

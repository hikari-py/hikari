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
"""Application and entities that are used to describe messages on Discord."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "MessageType",
    "MessageFlag",
    "MessageActivityType",
    "Attachment",
    "Reaction",
    "MessageActivity",
    "MessageCrosspost",
    "Message",
]

import enum
import typing

import attr

from hikari.utilities import files as files_
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import rest
    from hikari.models import applications
    from hikari.models import channels
    from hikari.models import embeds as embeds_
    from hikari.models import emojis as emojis_
    from hikari.models import guilds
    from hikari.models import users


@enum.unique
@typing.final
class MessageType(int, enum.Enum):
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
class MessageFlag(enum.IntFlag):
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

    def __str__(self) -> str:
        return self.name


@enum.unique
@typing.final
class MessageActivityType(int, enum.Enum):
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


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class Attachment(snowflake.Unique, files_.WebResource):
    """Represents a file attached to a message.

    You can use this object in the same way as a `hikari.utilities.files.WebResource`,
    by passing it as an attached file when creating a message, etc.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
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


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Reaction:
    """Represents a reaction in a message."""

    count: int = attr.ib(eq=False, hash=False, repr=True)
    """The amount of times the emoji has been used to react."""

    emoji: typing.Union[emojis_.UnicodeEmoji, emojis_.CustomEmoji] = attr.ib(eq=True, hash=True, repr=True)
    """The emoji used to react."""

    is_reacted_by_me: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the current user reacted using this emoji."""

    def __str__(self) -> str:
        return str(self.emoji)


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class MessageActivity:
    """Represents the activity of a rich presence-enabled message."""

    type: MessageActivityType = attr.ib(repr=True)
    """The type of message activity."""

    party_id: typing.Optional[str] = attr.ib(repr=True)
    """The party ID of the message activity."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class MessageCrosspost:
    """Represents information about a cross-posted message.

    This is a message that is sent in one channel/guild and may be
    "published" to another.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the message.

    !!! warning
        This may be `None` in some cases according to the Discord API
        documentation, but the situations that cause this to occur are not
        currently documented.
    """

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel that the message originated from."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild that the message originated from.

    !!! warning
        This may be `None` in some cases according to the Discord API
        documentation, but the situations that cause this to occur are not
        currently documented.
    """


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Message(snowflake.Unique):
    """Represents a message."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    channel_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the channel that the message was sent in."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The ID of the guild that the message was sent in."""

    author: users.User = attr.ib(eq=False, hash=False, repr=True)
    """The author of this message."""

    member: typing.Optional[guilds.Member] = attr.ib(eq=False, hash=False, repr=True)
    """The member properties for the message's author."""

    content: str = attr.ib(eq=False, hash=False, repr=False)
    """The content of the message."""

    timestamp: datetime.datetime = attr.ib(eq=False, hash=False, repr=True)
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Optional[datetime.datetime] = attr.ib(eq=False, hash=False, repr=False)
    """The timestamp that the message was last edited at.

    Will be `None` if it wasn't ever edited.
    """

    is_tts: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the message is a TTS message."""

    is_mentioning_everyone: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: typing.Set[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The users the message mentions."""

    role_mentions: typing.Set[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The roles the message mentions."""

    channel_mentions: typing.Set[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The channels the message mentions."""

    attachments: typing.Sequence[Attachment] = attr.ib(eq=False, hash=False, repr=False)
    """The message attachments."""

    embeds: typing.Sequence[embeds_.Embed] = attr.ib(eq=False, hash=False, repr=False)
    """The message embeds."""

    reactions: typing.Sequence[Reaction] = attr.ib(eq=False, hash=False, repr=False)
    """The message reactions."""

    is_pinned: bool = attr.ib(eq=False, hash=False, repr=False)
    """Whether the message is pinned."""

    webhook_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """If the message was generated by a webhook, the webhook's id."""

    type: MessageType = attr.ib(eq=False, hash=False, repr=False)
    """The message type."""

    activity: typing.Optional[MessageActivity] = attr.ib(eq=False, hash=False, repr=False)
    """The message activity."""

    application: typing.Optional[applications.Application] = attr.ib(eq=False, hash=False, repr=False)
    """The message application."""

    message_reference: typing.Optional[MessageCrosspost] = attr.ib(eq=False, hash=False, repr=False)
    """The message crossposted reference data."""

    flags: typing.Optional[MessageFlag] = attr.ib(eq=False, hash=False, repr=False)
    """The message flags."""

    nonce: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The message nonce. This is a string used for validating a message was sent."""

    def __str__(self) -> str:
        return self.content

    async def fetch_channel(self) -> channels.PartialChannel:
        """Fetch the channel this message was created in.

        Returns
        -------
        hikari.models.channels.PartialChannel
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
        text: typing.Union[undefined.UndefinedType, str, None] = undefined.UNDEFINED,
        *,
        embed: typing.Union[undefined.UndefinedType, embeds_.Embed, None] = undefined.UNDEFINED,
        mentions_everyone: typing.Union[bool, undefined.UndefinedType] = undefined.UNDEFINED,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, users.User]], bool, undefined.UndefinedType
        ] = undefined.UNDEFINED,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, guilds.Role]], bool, undefined.UndefinedType
        ] = undefined.UNDEFINED,
    ) -> Message:
        """Edit this message.

        All parameters are optional, meaning that if you do not specify one,
        then the corresponding piece of information will not be changed.

        Parameters
        ----------
        text : str or hikari.utilities.undefined.UndefinedType or None
            If specified, the message text to set on the message. If `None`,
            then the content is removed if already present.
        embed : hikari.models.embeds.Embed or hikari.utilities.undefined.UndefinedType or None
            If specified, the embed object to set on the message. If `None`,
            then the embed is removed if already present.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `False`.
        user_mentions : typing.Collection[hikari.models.users.User or hikari.utilities.snowflake.Snowflake or int or str] or bool
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.Snowflake or int or str] or bool
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        hikari.models.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.BadRequest
            This can be raised if the embed exceeds the defined limits;
            if the message content is specified only and empty or greater
            than `2000` characters; if neither content, file or embed
            are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you try to edit `content` or `embed` or `allowed_mentions`
            on a message you did not author.
            If you try to edit the flags on a message you did not author without
            the `MANAGE_MESSAGES` permission.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        """  # noqa: E501 - Line too long
        return await self.app.rest.edit_message(
            message=self.id,
            channel=self.channel_id,
            text=text,
            embed=embed,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def reply(
        self,
        text: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        *,
        embed: typing.Union[undefined.UndefinedType, embeds_.Embed] = undefined.UNDEFINED,
        attachment: typing.Union[undefined.UndefinedType, str, files_.Resource] = undefined.UNDEFINED,
        attachments: typing.Union[
            undefined.UndefinedType, typing.Sequence[typing.Union[str, files_.Resource]]
        ] = undefined.UNDEFINED,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, users.User]], bool
        ] = True,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, guilds.Role]], bool
        ] = True,
        nonce: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        tts: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> Message:
        """Create a message in the channel this message belongs to.

        Parameters
        ----------
        text : str or hikari.utilities.undefined.UndefinedType
            If specified, the message text to send with the message.
        nonce : str or hikari.utilities.undefined.UndefinedType
            If specified, an optional ID to send for opportunistic message
            creation. This doesn't serve any real purpose for general use,
            and can usually be ignored.
        tts : bool or hikari.utilities.undefined.UndefinedType
            If specified, whether the message will be sent as a TTS message.
        attachment : hikari.utilities.files.Resource or str or hikari.utilities.undefined.UndefinedType
            If specified, a attachment to upload, if desired. This can
            be a resource, or string of a path on your computer or a URL.
        attachments : typing.Sequence[hikari.utilities.files.Resource or str] or hikari.utilities.undefined.UndefinedType
            If specified, a sequence of attachments to upload, if desired.
            Should be between 1 and 10 objects in size (inclusive), also
            including embed attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        embed : hikari.models.embeds.Embed or hikari.utilities.undefined.UndefinedType
            If specified, the embed object to send with the message.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `False`.
        user_mentions : typing.Collection[hikari.models.users.User or hikari.utilities.snowflake.Snowflake or int or str] or bool
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.Snowflake or int or str] or bool
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        hikari.models.messages.Message
            The created message object.

        Raises
        ------
        hikari.errors.NotFound
            If the channel this message was created in is not found.
        hikari.errors.BadRequest
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, files
            or embed are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
            If you are trying to upload more than 10 files in total (including
            embed attachments).
        hikari.errors.Forbidden
            If you lack permissions to send to the channel this message belongs
            to.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        TypeError
            If both `attachment` and `attachments` are specified.
        """  # noqa: E501 - Line too long
        return await self.app.rest.create_message(
            channel=self.channel_id,
            text=text,
            nonce=nonce,
            tts=tts,
            attachment=attachment,
            attachments=attachments,
            embed=embed,
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

    async def add_reaction(self, emoji: typing.Union[str, emojis_.Emoji]) -> None:
        r"""Add a reaction to this message.

        Parameters
        ----------
        emoji : str or hikari.models.emojis.Emoji
            The emoji to add.

        Examples
        --------
            # Using a unicode emoji.
            await message.add_reaction("👌")

            # Using a unicode emoji name.
            await message.add_reaction("\N{OK HAND SIGN}")

            # Using the `name:id` format.
            await message.add_reaction("rooAYAYA:705837374319493284")

            # Using an Emoji object.
            await message.add_reaction(some_emoji_object)

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
        emoji: typing.Union[str, emojis_.Emoji],
        *,
        user: typing.Union[users.User, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> None:
        r"""Remove a reaction from this message.

        Parameters
        ----------
        emoji : str or hikari.models.emojis.Emoji
            The emoji to remove.
        user : hikari.models.users.User or hikari.utilities.undefined.UndefinedType
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

    async def remove_all_reactions(
        self, emoji: typing.Union[str, emojis_.Emoji, undefined.UndefinedType] = undefined.UNDEFINED
    ) -> None:
        r"""Remove all users' reactions for a specific emoji from the message.

        Parameters
        ----------
        emoji : str or hikari.models.emojis.Emoji or hikari.utilities.undefined.UndefinedType
            The emoji to remove all reactions for. If not specified, then all
            emojis are removed.

        Example
        --------
            # Using a unicode emoji and removing all 👌 reacts from the message.
            # reaction.
            await message.remove_all_reactions("\N{OK HAND SIGN}")

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

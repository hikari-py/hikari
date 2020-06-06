#!/usr/bin/env python3
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
"""Application and entities that are used to describe webhooks on Discord."""

from __future__ import annotations

__all__ = ["WebhookType", "Webhook"]

import enum
import typing

import attr

from hikari.models import bases
from hikari.utilities import cdn
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    from hikari.models import channels as channels_
    from hikari.models import embeds as embeds_
    from hikari.models import files as files_
    from hikari.models import guilds as guilds_
    from hikari.models import messages as messages_
    from hikari.models import users as users_


@enum.unique
class WebhookType(int, enum.Enum):
    """Types of webhook."""

    INCOMING = 1
    """Incoming webhook."""

    CHANNEL_FOLLOWER = 2
    """Channel Follower webhook."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Webhook(bases.Entity, bases.Unique):
    """Represents a webhook object on Discord.

    This is an endpoint that can have messages sent to it using standard
    HTTP requests, which enables external services that are not bots to
    send informational messages to specific channels.
    """

    type: WebhookType = attr.ib(eq=False, hash=False, repr=True)
    """The type of the webhook."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The guild ID of the webhook."""

    channel_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The channel ID this webhook is for."""

    author: typing.Optional[users_.User] = attr.ib(
        eq=False, hash=False, repr=True,
    )
    """The user that created the webhook

    !!! info
        This will be `None` when getting a webhook with bot authorization rather
        than the webhook's token.
    """

    name: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The name of the webhook."""

    avatar_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The avatar hash of the webhook."""

    token: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The token for the webhook.

    !!! info
        This is only available for incoming webhooks that are created in the
        channel settings.
    """

    async def execute(
        self,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        files: typing.Sequence[files_.BaseStream] = ...,
        embeds: typing.Sequence[embeds_.Embed] = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, users_.User]], bool
        ] = True,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, guilds_.Role]], bool
        ] = True,
    ) -> typing.Optional[messages_.Message]:
        """Execute the webhook to create a message.

        Parameters
        ----------
        content : str
            If specified, the message content to send with the message.
        username : str
            If specified, the username to override the webhook's username
            for this request.
        avatar_url : str
            If specified, the url of an image to override the webhook's
            avatar with for this request.
        tts : bool
            If specified, whether the message will be sent as a TTS message.
        wait : bool
            If specified, whether this request should wait for the webhook
            to be executed and return the resultant message object.
        files : typing.Sequence[hikari.models.files.BaseStream]
            If specified, a sequence of files to upload.
        embeds : typing.Sequence[hikari.models.embeds.Embed]
            If specified, a sequence of between `1` to `10` embed objects
            (inclusive) to send with the embed.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
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
        hikari.models.messages.Message or None
            The created message object, if `wait` is `True`, else `None`.

        Raises
        ------
        hikari.errors.NotFound
            If the current webhook is not found.
        hikari.errors.BadRequest
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, file
            or embeds are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        ValueError
            If either `Webhook.token` is `None` or more than 100 unique
            objects/entities are passed for `role_mentions` or `user_mentions.
        """
        if not self.token:
            raise ValueError("Cannot send a message using a webhook where we don't know it's token.")

        return await self._app.rest.execute_webhook(
            webhook=self.id,
            webhook_token=self.token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            files=files,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def safe_execute(
        self,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        files: typing.Sequence[files_.BaseStream] = ...,
        embeds: typing.Sequence[embeds_.Embed] = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, users_.User]], bool
        ] = False,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, guilds_.Role]], bool
        ] = False,
    ) -> typing.Optional[messages_.Message]:
        """Execute the webhook to create a message with mention safety.

        This endpoint has the same signature as
        `Webhook.execute` with the only difference being
        that `mentions_everyone`, `user_mentions` and `role_mentions` default to
        `False`.
        """
        if not self.token:
            raise ValueError("Cannot execute a webhook with a unknown token (set to `None`).")

        return await self._app.rest.safe_webhook_execute(
            webhook=self.id,
            webhook_token=self.token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            files=files,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete(self, *, use_token: typing.Optional[bool] = None,) -> None:
        """Delete this webhook.

        Parameters
        ----------
        use_token : bool or None
            If set to `True` then the webhook's token will be used for this
            request; if set to `False` then bot authorization will be used;
            if not specified then the webhook's token will be used for the
            request if it's set else bot authorization.

        Raises
        ------
        hikari.errors.NotFound
            If this webhook is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        ValueError
            If `use_token` is passed as `True` when `Webhook.token` is `None`.
        """
        if use_token and not self.token:
            raise ValueError("This webhook's token is unknown.")

        if use_token is None and self.token:
            use_token = True

        await self._app.rest.delete_webhook(webhook=self.id, webhook_token=self.token if use_token else ...)

    async def edit(
        self,
        *,
        name: str = ...,
        avatar: typing.Optional[files_.BaseStream] = ...,
        channel: typing.Union[snowflake.Snowflake, int, str, channels_.GuildChannel] = ...,
        reason: str = ...,
        use_token: typing.Optional[bool] = None,
    ) -> Webhook:
        """Edit this webhook.

        Parameters
        ----------
        name : str
            If specified, the new name string.
        avatar : hikari.models.files.BaseStream or None
            If specified, the new avatar image. If `None`, then
            it is removed.
        channel : hikari.models.channels.GuildChannel or hikari.utilities.snowflake.Snowflake or int
            If specified, the object or ID of the new channel the given
            webhook should be moved to.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed. This field will be used when using the webhook's
            token rather than bot authorization.
        use_token : bool or None
            If set to `True` then the webhook's token will be used for this
            request; if set to `False` then bot authorization will be used;
            if not specified then the webhook's token will be used for the
            request if it's set else bot authorization.

        Returns
        -------
        hikari.models.webhooks.Webhook
            The updated webhook object.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If either the webhook or the channel aren't found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        ValueError
            If `use_token` is passed as `True` when `Webhook.token` is `None`.
        """
        if use_token and not self.token:
            raise ValueError("This webhook's token is unknown.")

        if use_token is None and self.token:
            use_token = True

        return await self._app.rest.update_webhook(
            webhook=self.id,
            webhook_token=self.token if use_token else ...,
            name=name,
            avatar=avatar,
            channel=channel,
            reason=reason,
        )

    async def fetch_channel(self) -> channels_.PartialChannel:
        """Fetch the channel this webhook is for.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The object of the channel this webhook targets.

        Raises
        ------
        hikari.errors.Forbidden
            If you don't have access to the channel this webhook belongs to.
        hikari.errors.NotFound
            If the channel this message was created in does not exist.
        """
        return await self._app.rest.fetch_channel(channel=self.channel_id)

    async def fetch_guild(self) -> guilds_.Guild:
        """Fetch the guild this webhook belongs to.

        Returns
        -------
        hikari.models.guilds.Guild
            The object of the channel this message belongs to.

        Raises
        ------
        hikari.errors.Forbidden
            If you don't have access to the guild this webhook belongs to or it
            doesn't exist.
        """
        return await self._app.rest.fetch_guild(guild=self.guild_id)

    async def fetch_self(self, *, use_token: typing.Optional[bool] = None) -> Webhook:
        """Fetch this webhook.

        Parameters
        ----------
        use_token : bool or None
            If set to `True` then the webhook's token will be used for this
            request; if set to `False` then bot authorization will be used;
            if not specified then the webhook's token will be used for the
            request if it's set else bot authorization.

        Returns
        -------
        hikari.models.webhooks.Webhook
            The requested webhook object.

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the webhook is not found.
        hikari.errors.Forbidden
            If you're not in the guild that owns this webhook or
            lack the `MANAGE_WEBHOOKS` permission.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        ValueError
            If `use_token` is passed as `True` when `Webhook.token` is `None`.
        """
        if use_token and not self.token:
            raise ValueError("This webhook's token is unknown.")

        if use_token is None and self.token:
            use_token = True

        return await self._app.rest.fetch_webhook(webhook=self.id, webhook_token=self.token if use_token else ...)

    @property
    def avatar_url(self) -> str:
        """URL for this webhook's custom avatar if set, else default."""
        return self.format_avatar_url()

    @property
    def default_avatar_index(self) -> int:
        """Integer representation of this webhook's default avatar."""
        return 0

    @property
    def default_avatar_url(self) -> str:
        """URL for this webhook's default avatar."""
        return cdn.generate_cdn_url("embed", "avatars", str(self.default_avatar_index), format_="png", size=None)

    def format_avatar_url(self, format_: str = "png", size: int = 4096) -> str:
        """Generate the avatar URL for this webhook's custom avatar if set, else it's default avatar.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg`, `webp`. This will be ignored for
            default avatars which can only be `png`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        str
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if not self.avatar_hash:
            return self.default_avatar_url
        return cdn.generate_cdn_url("avatars", str(self.id), self.avatar_hash, format_=format_, size=size)

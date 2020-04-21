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
"""The logic for handling all requests to webhook endpoints."""

__all__ = ["RESTWebhookComponent"]

import abc
import typing

from hikari import bases
from hikari import channels as _channels
from hikari import embeds as _embeds
from hikari import guilds
from hikari import media
from hikari import messages as _messages
from hikari import users
from hikari import webhooks
from hikari.clients.rest import base
from hikari.internal import conversions
from hikari.internal import helpers


class RESTWebhookComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=W0223
    """The REST client component for handling requests to webhook endpoints."""

    async def fetch_webhook(
        self, webhook: bases.Hashable[webhooks.Webhook], *, webhook_token: str = ...
    ) -> webhooks.Webhook:
        """Get a given webhook.

        Parameters
        ----------
        webhook : typing.Union [ hikari.webhooks.Webhook, hikari.bases.Snowflake, int ]
            The object or ID of the webhook to get.
        webhook_token : str
            If specified, the webhook token to use to get it (bypassing this
            session's provided authorization `token`).

        Returns
        -------
        hikari.webhooks.Webhook
            The requested webhook object.

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFoundHTTPError
            If the webhook is not found.
        hikari.errors.ForbiddenHTTPError
            If you're not in the guild that owns this webhook or
            lack the `MANAGE_WEBHOOKS` permission.
        hikari.errors.UnauthorizedHTTPError
            If you pass a token that's invalid for the target webhook.
        """
        payload = await self._session.get_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
        )
        return webhooks.Webhook.deserialize(payload)

    async def update_webhook(
        self,
        webhook: bases.Hashable[webhooks.Webhook],
        *,
        webhook_token: str = ...,
        name: str = ...,
        avatar_data: typing.Optional[conversions.FileLikeT] = ...,
        channel: bases.Hashable[_channels.GuildChannel] = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Edit a given webhook.

        Parameters
        ----------
        webhook : typing.Union [ hikari.webhooks.Webhook, hikari.bases.Snowflake, int ]
            The object or ID of the webhook to edit.
        webhook_token : str
            If specified, the webhook token to use to modify it (bypassing this
            session's provided authorization `token`).
        name : str
            If specified, the new name string.
        avatar_data : hikari.internal.conversions.FileLikeT, optional
            If specified, the new avatar image file object. If `None`, then
            it is removed.
        channel : typing.Union [ hikari.channels.GuildChannel, hikari.bases.Snowflake, int ]
            If specified, the object or ID of the new channel the given
            webhook should be moved to.
        reason : str
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        hikari.webhooks.Webhook
            The updated webhook object.

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFoundHTTPError
            If either the webhook or the channel aren't found.
        hikari.errors.ForbiddenHTTPError
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        hikari.errors.UnauthorizedHTTPError
            If you pass a token that's invalid for the target webhook.
        """
        payload = await self._session.modify_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
            name=name,
            avatar=(
                conversions.get_bytes_from_resource(avatar_data)
                if avatar_data and avatar_data is not ...
                else avatar_data
            ),
            channel_id=(
                str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
                if channel and channel is not ...
                else channel
            ),
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload)

    async def delete_webhook(self, webhook: bases.Hashable[webhooks.Webhook], *, webhook_token: str = ...) -> None:
        """Delete a given webhook.

        Parameters
        ----------
        webhook : typing.Union [ hikari.webhooks.Webhook, hikari.bases.Snowflake, int ]
            The object or ID of the webhook to delete
        webhook_token : str
            If specified, the webhook token to use to delete it (bypassing this
            session's provided authorization `token`).

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFoundHTTPError
            If the webhook is not found.
        hikari.errors.ForbiddenHTTPError
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        hikari.errors.UnauthorizedHTTPError
                If you pass a token that's invalid for the target webhook.
        """
        await self._session.delete_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
        )

    async def execute_webhook(
        self,
        webhook: bases.Hashable[webhooks.Webhook],
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        file: media.IO = ...,
        embeds: typing.Sequence[_embeds.Embed] = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = True,
    ) -> typing.Optional[_messages.Message]:
        """Execute a webhook to create a message.

        Parameters
        ----------
        webhook : typing.Union [ hikari.webhooks.Webhook, hikari.bases.Snowflake, int ]
            The object or ID of the webhook to execute.
        webhook_token : str
            The token of the webhook to execute.
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
        file : hikari.media.IO
            If specified, this is a file object to send along with the webhook
            as defined in `hikari.media`.
        embeds : typing.Sequence [ hikari.embeds.Embed ]
            If specified, a sequence of `1` to `10` embed objects to send
            with the embed.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
        user_mentions : typing.Union [ typing.Collection [ typing.Union [ hikari.users.User, hikari.bases.Snowflake, int ], bool ]
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions : typing.Union [ typing.Collection [ typing.Union [ hikari.guilds.GuildRole, hikari.bases.Snowflake, int ] ], bool ]
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        hikari.messages.Message, optional
            The created message object, if `wait` is `True`, else `None`.

        Raises
        ------
        hikari.errors.NotFoundHTTPError
            If the channel ID or webhook ID is not found.
        hikari.errors.BadRequestHTTPError
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, file
            or embeds are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenHTTPError
            If you lack permissions to send to this channel.
        hikari.errors.UnauthorizedHTTPError
            If you pass a token that's invalid for the target webhook.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        """
        payload = await self._session.execute_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.UniqueEntity) else int(webhook)),
            webhook_token=webhook_token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            file=await media.safe_read_file(file) if file is not ... else ...,
            embeds=[embed.serialize() for embed in embeds] if embeds is not ... else ...,
            allowed_mentions=helpers.generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions
            ),
        )
        if wait is True:
            return _messages.Message.deserialize(payload)
        return None

    def safe_webhook_execute(
        self,
        webhook: bases.Hashable[webhooks.Webhook],
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        file: media.IO = ...,
        embeds: typing.Sequence[_embeds.Embed] = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = False,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = False,
    ) -> typing.Coroutine[typing.Any, typing.Any, typing.Optional[_messages.Message]]:
        """Execute a webhook to create a message with mention safety.

        This endpoint has the same signature as
        `RESTWebhookComponent.execute_webhook` with the only difference being
        that `mentions_everyone`, `user_mentions` and `role_mentions` default to
        `False`.
        """
        return self.execute_webhook(
            webhook=webhook,
            webhook_token=webhook_token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            file=file,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

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

from __future__ import annotations

__all__ = ["RESTWebhookComponent"]

import abc
import typing

from hikari import bases
from hikari import messages as _messages
from hikari import webhooks
from hikari.clients.rest import base
from hikari.internal import helpers

if typing.TYPE_CHECKING:
    from hikari import channels as _channels
    from hikari import embeds as _embeds
    from hikari import files as _files
    from hikari import guilds
    from hikari import users


class RESTWebhookComponent(base.BaseRESTComponent, abc.ABC):  # pylint: disable=abstract-method
    """The REST client component for handling requests to webhook endpoints."""

    async def fetch_webhook(
        self, webhook: typing.Union[bases.Snowflake, int, str, webhooks.Webhook], *, webhook_token: str = ...
    ) -> webhooks.Webhook:
        """Get a given webhook.

        Parameters
        ----------
        webhook : typing.Union[hikari.webhooks.Webhook, hikari.bases.Snowflake, int]
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
        """
        payload = await self._session.get_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.Unique) else int(webhook)),
            webhook_token=webhook_token,
        )
        return webhooks.Webhook.deserialize(payload, components=self._components)

    async def update_webhook(
        self,
        webhook: typing.Union[bases.Snowflake, int, str, webhooks.Webhook],
        *,
        webhook_token: str = ...,
        name: str = ...,
        avatar: typing.Optional[_files.BaseStream] = ...,
        channel: typing.Union[bases.Snowflake, int, str, _channels.GuildChannel] = ...,
        reason: str = ...,
    ) -> webhooks.Webhook:
        """Edit a given webhook.

        Parameters
        ----------
        webhook : typing.Union[hikari.webhooks.Webhook, hikari.bases.Snowflake, int]
            The object or ID of the webhook to edit.
        webhook_token : str
            If specified, the webhook token to use to modify it (bypassing this
            session's provided authorization `token`).
        name : str
            If specified, the new name string.
        avatar : hikari.files.BaseStream, optional
            If specified, the new avatar image. If `None`, then
            it is removed.
        channel : typing.Union[hikari.channels.GuildChannel, hikari.bases.Snowflake, int]
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
        """
        payload = await self._session.modify_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.Unique) else int(webhook)),
            webhook_token=webhook_token,
            name=name,
            avatar=await avatar.read() if avatar is not ... else ...,
            channel_id=(
                str(channel.id if isinstance(channel, bases.Unique) else int(channel))
                if channel and channel is not ...
                else channel
            ),
            reason=reason,
        )
        return webhooks.Webhook.deserialize(payload, components=self._components)

    async def delete_webhook(
        self, webhook: typing.Union[bases.Snowflake, int, str, webhooks.Webhook], *, webhook_token: str = ...
    ) -> None:
        """Delete a given webhook.

        Parameters
        ----------
        webhook : typing.Union[hikari.webhooks.Webhook, hikari.bases.Snowflake, int]
            The object or ID of the webhook to delete
        webhook_token : str
            If specified, the webhook token to use to delete it (bypassing this
            session's provided authorization `token`).

        Raises
        ------
        hikari.errors.BadRequest
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.NotFound
            If the webhook is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        hikari.errors.Unauthorized
                If you pass a token that's invalid for the target webhook.
        """
        await self._session.delete_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.Unique) else int(webhook)),
            webhook_token=webhook_token,
        )

    async def execute_webhook(  # pylint:disable=too-many-locals,line-too-long
        self,
        webhook: typing.Union[bases.Snowflake, int, str, webhooks.Webhook],
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        files: typing.Sequence[_files.BaseStream] = ...,
        embeds: typing.Sequence[_embeds.Embed] = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool
        ] = True,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.GuildRole]], bool
        ] = True,
    ) -> typing.Optional[_messages.Message]:
        """Execute a webhook to create a message.

        Parameters
        ----------
        webhook : typing.Union[hikari.webhooks.Webhook, hikari.bases.Snowflake, int]
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
        files : typing.Sequence[hikari.files.BaseStream]
            If specified, a sequence of files to upload.
        embeds : typing.Sequence[hikari.embeds.Embed]
            If specified, a sequence of between `1` to `10` embed objects
            (inclusive) to send with the embed.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
        user_mentions : typing.Union[typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]], bool]
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions : typing.Union[typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]], bool]
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        hikari.messages.Message, optional
            The created message object, if `wait` is `True`, else `None`.

        Raises
        ------
        hikari.errors.NotFound
            If the channel ID or webhook ID is not found.
        hikari.errors.BadRequest
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, file
            or embeds are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.Forbidden
            If you lack permissions to send to this channel.
        hikari.errors.Unauthorized
            If you pass a token that's invalid for the target webhook.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        """
        file_resources = []
        if files is not ...:
            file_resources += files
        if embeds is not ...:
            for embed in embeds:
                file_resources += embed.assets_to_upload

        payload = await self._session.execute_webhook(
            webhook_id=str(webhook.id if isinstance(webhook, bases.Unique) else int(webhook)),
            webhook_token=webhook_token,
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            wait=wait,
            files=file_resources if file_resources else ...,
            embeds=[embed.serialize() for embed in embeds] if embeds is not ... else ...,
            allowed_mentions=helpers.generate_allowed_mentions(
                mentions_everyone=mentions_everyone, user_mentions=user_mentions, role_mentions=role_mentions
            ),
        )
        if wait is True:
            return _messages.Message.deserialize(payload, components=self._components)
        return None

    def safe_webhook_execute(
        self,
        webhook: typing.Union[bases.Snowflake, int, str, webhooks.Webhook],
        webhook_token: str,
        *,
        content: str = ...,
        username: str = ...,
        avatar_url: str = ...,
        tts: bool = ...,
        wait: bool = False,
        files: typing.Sequence[_files.BaseStream] = ...,
        embeds: typing.Sequence[_embeds.Embed] = ...,
        mentions_everyone: bool = False,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, users.User]], bool
        ] = False,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[bases.Snowflake, int, str, guilds.GuildRole]], bool
        ] = False,
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
            files=files,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

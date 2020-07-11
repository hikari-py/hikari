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

__all__: typing.Final[typing.List[str]] = ["WebhookType", "Webhook"]

import enum
import typing

import attr

from hikari.utilities import constants
from hikari.utilities import files as files_
from hikari.utilities import routes
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api.rest import app as rest_app
    from hikari.models import channels as channels_
    from hikari.models import embeds as embeds_
    from hikari.models import guilds as guilds_
    from hikari.models import messages as messages_
    from hikari.models import users as users_


@enum.unique
@typing.final
class WebhookType(int, enum.Enum):
    """Types of webhook."""

    INCOMING = 1
    """Incoming webhook."""

    CHANNEL_FOLLOWER = 2
    """Channel Follower webhook."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Webhook(snowflake.Unique):
    """Represents a webhook object on Discord.

    This is an _endpoint that can have messages sent to it using standard
    HTTP requests, which enables external services that are not bots to
    send informational messages to specific channels.
    """

    app: rest_app.IRESTApp = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    type: WebhookType = attr.ib(eq=False, hash=False, repr=True)
    """The type of the webhook."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=True)
    """The guild ID of the webhook."""

    channel_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The channel ID this webhook is for."""

    author: typing.Optional[users_.UserImpl] = attr.ib(eq=False, hash=False, repr=True)
    """The user that created the webhook

    !!! info
        This will be `builtins.None` when getting a webhook with bot authorization rather
        than the webhook's token.
    """

    name: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=True)
    """The name of the webhook."""

    avatar_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The avatar hash of the webhook."""

    token: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The token for the webhook.

    !!! info
        This is only available for incoming webhooks that are created in the
        channel settings.
    """

    def __str__(self) -> str:
        return self.name if self.name is not None else f"Unnamed webhook ID {self.id}"

    @property
    def mention(self) -> str:
        """Return a raw mention string for the given webhook's user.

        !!! note
            This exists purely for consistency. Webhooks do not receive events
            from the gateway, and without some bot backend to support it, will
            not be able to detect mentions of their webhook.

        Example
        -------

        ```py
        >>> some_webhook.mention
        '<@123456789123456789>'
        ```

        Returns
        -------
        builtins.str
            The mention string to use.
        """
        # TODO: check if this ID the same as the optional author.id in terms of validity.
        return f"<@{self.id}>"

    async def execute(
        self,
        text: typing.Union[undefined.UndefinedType, typing.Any] = undefined.UNDEFINED,
        *,
        username: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        avatar_url: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        tts: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        attachment: typing.Union[undefined.UndefinedType, str, files_.Resource] = undefined.UNDEFINED,
        attachments: typing.Union[
            undefined.UndefinedType, typing.Sequence[typing.Union[str, files_.Resource]]
        ] = undefined.UNDEFINED,
        embeds: typing.Union[undefined.UndefinedType, typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, users_.UserImpl]],
            bool,
            undefined.UndefinedType,
        ] = undefined.UNDEFINED,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.Snowflake, int, str, guilds_.Role]], bool, undefined.UndefinedType
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Execute the webhook to create a message.

        Parameters
        ----------
        text : builtins.str or hikari.utilities.undefined.UndefinedType
            If specified, the message content to send with the message.
        username : builtins.str or hikari.utilities.undefined.UndefinedType
            If specified, the username to override the webhook's username
            for this request.
        avatar_url : builtins.str or hikari.utilities.undefined.UndefinedType
            If specified, the url of an image to override the webhook's
            avatar with for this request.
        tts : builtins.bool or hikari.utilities.undefined.UndefinedType
            If specified, whether the message will be sent as a TTS message.
        attachment : hikari.utilities.undefined.UndefinedType or builtins.str or hikari.utilities.files.Resource
            If specified, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.utilities.undefined.UndefinedType or typing.Sequence[builtins.str or hikari.utilities.files.Resource]
            If specified, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        embeds : typing.Sequence[hikari.models.embeds.Embed] or hikari.utilities.undefined.UndefinedType
            If specified, a sequence of between `1` to `10` embed objects
            (inclusive) to send with the embed.
        mentions_everyone : builtins.bool or hikari.utilities.undefined.UndefinedType
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to
            `hikari.utilities.undefined.UNDEFINED`.
        user_mentions : typing.Collection[hikari.models.users.UserImpl or hikari.utilities.snowflake.UniqueObject] or builtins.bool or hikari.utilities.undefined.UndefinedType
            Either an array of user objects/IDs to allow mentions for,
            `builtins.True` to allow all user mentions or `builtins.False` to
            block all user mentions from resolving, defaults to
            `hikari.utilities.undefined.UNDEFINED`.
        role_mentions: typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.UniqueObject] or builtins.bool or hikari.utilities.undefined.UndefinedType
            Either an array of guild role objects/IDs to allow mentions for,
            `builtins.True` to allow all role mentions or `builtins.False` to
            block all role mentions from resolving, defaults to
            `hikari.utilities.undefined.UNDEFINED`.

        Returns
        -------
        hikari.models.messages.Message
            The created message object.

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
        builtins.ValueError
            If either `Webhook.token` is `builtins.None` or more than 100 unique
            objects/entities are passed for `role_mentions` or `user_mentions.
        builtins.TypeError
            If both `attachment` and `attachments` are specified.
        """  # noqa: E501 - Line too long
        if not self.token:
            raise ValueError("Cannot send a message using a webhook where we don't know it's token.")

        return await self.app.rest.execute_webhook(
            webhook=self.id,
            token=self.token,
            text=text,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            attachment=attachment,
            attachments=attachments,
            embeds=embeds,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )

    async def delete(self, *, use_token: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED) -> None:
        """Delete this webhook.

        Parameters
        ----------
        use_token : builtins.bool or hikari.utilities.undefined.UndefinedType
            If set to `builtins.True` then the webhook's token will be used for
            this request; if set to `builtins.False` then bot authorization will
            be used; if not specified then the webhook's token will be used for
            the request if it's set else bot authorization.

        Raises
        ------
        hikari.errors.NotFound
            If this webhook is not found.
        hikari.errors.Forbidden
            If you either lack the `MANAGE_WEBHOOKS` permission or
            aren't a member of the guild this webhook belongs to.
        builtins.ValueError
            If `use_token` is passed as `builtins.True` when `Webhook.token` is
            `builtins.None`.
        """
        if use_token and self.token is None:
            raise ValueError("This webhook's token is unknown, so cannot be used.")

        token: typing.Union[undefined.UndefinedType, str]
        token = typing.cast(str, self.token) if use_token else undefined.UNDEFINED

        await self.app.rest.delete_webhook(self.id, token=token)

    async def edit(
        self,
        *,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        avatar: typing.Union[undefined.UndefinedType, None, files_.Resource] = undefined.UNDEFINED,
        channel: typing.Union[
            undefined.UndefinedType, snowflake.UniqueObject, channels_.GuildChannel
        ] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        use_token: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> Webhook:
        """Edit this webhook.

        Parameters
        ----------
        name : builtins.str or hikari.utilities.undefined.UndefinedType
            If specified, the new name string.
        avatar : hikari.utilities.files.Resource or None or hikari.utilities.undefined.UndefinedType
            If specified, the new avatar image. If `builtins.None`, then
            it is removed. If not specified, nothing is changed.
        channel : hikari.models.channels.GuildChannel or hikari.utilities.snowflake.UniqueObject or hikari.utilities.undefined.UndefinedType
            If specified, the object or ID of the new channel the given
            webhook should be moved to.
        reason : builtins.str or hikari.utilities.undefined.UndefinedType
            If specified, the audit log reason explaining why the operation
            was performed. This field will be used when using the webhook's
            token rather than bot authorization.
        use_token : builtins.bool or hikari.utilities.undefined.UndefinedType
            If set to `builtins.True` then the webhook's token will be used for
            this request; if set to `builtins.False` then bot authorization will
            be used; if not specified then the webhook's token will be used for
            the request if it's set else bot authorization.

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
        builtins.ValueError
            If `use_token` is passed as `builtins.True` when `Webhook.token` is `builtins.None`.
        """  # noqa: E501 - Line too long
        if use_token and self.token is None:
            raise ValueError("This webhook's token is unknown, so cannot be used.")

        token: typing.Union[undefined.UndefinedType, str]
        token = typing.cast(str, self.token) if use_token else undefined.UNDEFINED

        return await self.app.rest.edit_webhook(
            self.id, token=token, name=name, avatar=avatar, channel=channel, reason=reason,
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
        return await self.app.rest.fetch_channel(self.channel_id)

    async def fetch_self(
        self, *, use_token: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED
    ) -> Webhook:
        """Fetch this webhook.

        Parameters
        ----------
        use_token : builtins.bool or hikari.utilities.undefined.UndefinedType
            If set to `builtins.True` then the webhook's token will be used for
            this request; if set to `builtins.False` then bot authorization will
            be used; if not specified then the webhook's token will be used for
            the request if it's set else bot authorization.

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
        builtins.ValueError
            If `use_token` is passed as `builtins.True` when `Webhook.token`
            is `builtins.None`.
        """
        if use_token and not self.token:
            raise ValueError("This webhook's token is unknown, so cannot be used.")

        token: typing.Union[undefined.UndefinedType, str]
        token = typing.cast(str, self.token) if use_token else undefined.UNDEFINED

        return await self.app.rest.fetch_webhook(self.id, token=token)

    @property
    def avatar(self) -> files_.URL:
        """URL for this webhook's custom avatar or default avatar.

        If the webhook has a custom avatar, a URL to this is returned. Otherwise
        a URL to the default avatar is provided instead.
        """
        url = self.format_avatar()
        if url is None:
            return self.default_avatar
        return url

    @property
    def default_avatar(self) -> files_.URL:
        """URL for this webhook's default avatar.

        This is used if no avatar is set.
        """
        return routes.CDN_DEFAULT_USER_AVATAR.compile_to_file(constants.CDN_URL, discriminator=0, file_format="png",)

    # noinspection PyShadowingBuiltins
    def format_avatar(self, format: str = "png", size: int = 4096) -> typing.Optional[files_.URL]:
        """Generate the avatar URL for this webhook's custom avatar if set.

        If no avatar is specified, return `None`. In this case, you should
        use `default_avatar` instead.

        Parameters
        ----------
        format : builtins.str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg`, `webp`. This will be ignored for
            default avatars which can only be `png`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.
            Will be ignored for default avatars.

        Returns
        -------
        hikari.utilities.files.URL or builtins.None
            The URL of the resource. `builtins.None` if no avatar is set (in
            this case, use the `default_avatar` instead).

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two between 16 and 4096 (inclusive).
        """
        if self.avatar_hash is None:
            return None

        return routes.CDN_USER_AVATAR.compile_to_file(
            constants.CDN_URL, user_id=self.id, hash=self.avatar_hash, size=size, file_format=format,
        )

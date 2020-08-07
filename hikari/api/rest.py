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
"""Provides an interface for REST API implementations to follow."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IConnectorFactory", "IRESTApp", "IRESTAppFactory", "IRESTClient"]

import abc
import typing

from hikari.api import app
from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import types

    import aiohttp

    from hikari import config
    from hikari.api import special_endpoints
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import colors
    from hikari.models import embeds as embeds_
    from hikari.models import emojis
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import messages as messages_
    from hikari.models import permissions as permissions_
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks
    from hikari.utilities import date
    from hikari.utilities import files
    from hikari.utilities import iterators
    from hikari.utilities import snowflake


class IConnectorFactory(abc.ABC):
    """Provider of a connector."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def close(self) -> None:
        """Close any resources if they exist."""

    @abc.abstractmethod
    def acquire(self) -> aiohttp.BaseConnector:
        """Acquire the connector."""


class IRESTApp(app.IApp, abc.ABC):
    """Component specialization that is used for HTTP-only applications.

    This is a specific instance of a HTTP-only client provided by pooled
    implementations of `IRESTAppFactory`. It may also be used by bots
    as a base if they require HTTP-API access.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def rest(self) -> IRESTClient:
        """HTTP API Client.

        Use this to make calls to Discord's HTTP API over HTTPS.

        Returns
        -------
        IRESTClient
            The HTTP API client.
        """


class IRESTAppContextManager(IRESTApp):
    """An IRESTApp that may behave as a context manager."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def __aenter__(self) -> IRESTAppContextManager:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...


class IRESTAppFactory(abc.ABC):
    """A client factory that emits clients.

    This enables a connection pool to be shared for stateless HTTP-only
    applications such as web dashboards, while still using the HTTP architecture
    that the bot system will use.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def acquire(self, token: str, token_type: str) -> IRESTAppContextManager:
        """Acquire a HTTP client for the given authentication details.

        Parameters
        ----------
        token : builtins.str
            The token to use.
        token_type : builtins.str
            The token type to use.

        Returns
        -------
        IRESTApp
            The HTTP client to use.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""

    @property
    @abc.abstractmethod
    def http_settings(self) -> config.HTTPSettings:
        """HTTP-specific settings."""

    @property
    @abc.abstractmethod
    def proxy_settings(self) -> config.ProxySettings:
        """Proxy-specific settings."""

    @abc.abstractmethod
    async def __aenter__(self) -> IRESTAppFactory:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...


class IRESTClient(component.IComponent, abc.ABC):
    """Interface for functionality that a REST API implementation provides."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the client session."""

    @abc.abstractmethod
    async def fetch_channel(
        self, channel: snowflake.SnowflakeishOr[channels.PartialChannel]
    ) -> channels.PartialChannel:
        """Fetch a channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr
            The channel to fetch. This may be a
            `hikari.models.channels.PartialChannel` object, or the ID of an
            existing channel.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The channel. This will be a _derivative_ of
            `hikari.models.channels.PartialChannel`, depending on the type of
            channel you request for.

            This means that you may get one of
            `hikari.models.channels.PrivateTextChannel`,
            `hikari.models.channels.GroupPrivateTextChannel`,
            `hikari.models.channels.GuildTextChannel`,
            `hikari.models.channels.GuildVoiceChannel`,
            `hikari.models.channels.GuildStoreChannel`,
            `hikari.models.channels.GuildNewsChannel`.

            Likewise, the `hikari.models.channels.GuildChannel` can be used to
            determine if a channel is guild-bound, and
            `hikari.models.channels.TextChannel` can be used to determine
            if the channel provides textual functionality to the application.

            You can check for these using the `builtins.isinstance`
            builtin function.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to access the channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_channel(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        /,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        parent_category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.PartialChannel:
        """Edit a channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildChannel]
            The channel to edit. This may be a channel object, or the ID of an
            existing channel.
        name : hikari.utilities.undefined.UndefinedOr[[builtins.str]
            If provided, the new name for the channel.
        position : hikari.utilities.undefined.UndefinedOr[[builtins.int]
            If provided, the new position for the channel.
        topic : hikari.utilities.undefined.UndefinedOr[builtins.str]
            If provided, the new topic for the channel.
        nsfw : hikari.utilities.undefined.UndefinedOr[builtins.bool]
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.utilities.undefined.UndefinedOr[builtins.int]
            If provided, the new bitrate for the channel.
        user_limit : hikari.utilities.undefined.UndefinedOr[builtins.int]
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.utilities.date.Intervalish
            If provided, the new rate limit per user in the channel.
        permission_overwrites : hikari.utilities.undefined.UndefinedOr[typing.Sequence[hikari.models.channels.PermissionOverwrite]]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.utilities.undefined.UndefinedOr[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildCategory]]
            If provided, the new guild category for the channel.
        reason : hikari.utilities.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The edited channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to edit the channel
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_channel(self, channel: snowflake.SnowflakeishOr[channels.PartialChannel]) -> None:
        """Delete a channel in a guild, or close a DM.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.PartialChannel]
            The channel to delete. This may be a channel object, or the ID of an
            existing channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to delete the channel in a guild.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.
        """

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        target: typing.Union[channels.PermissionOverwrite, users.PartialUser, guilds.PartialRole],
        *,
        allow: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a target entity."""

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        target: snowflake.Snowflakeish,
        *,
        target_type: typing.Union[channels.PermissionOverwriteType, str],
        allow: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a given entity ID and type."""

    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        target: typing.Union[
            snowflake.Snowflakeish, users.PartialUser, guilds.PartialRole, channels.PermissionOverwrite
        ],
        *,
        target_type: undefined.UndefinedOr[typing.Union[channels.PermissionOverwriteType, str]] = undefined.UNDEFINED,
        allow: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a specific entity in the given guild channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildChannel]
            The channel to edit a permission overwrite in. This may be a
            channel object, or the ID of an existing channel.
        target : hikari.models.users.PartialUser or hikari.models.guilds.PartialRole or hikari.models.channels.PermissionOverwrite or hikari.utilities.snowflake.Snowflakeish
            The channel overwrite to edit. This may be a overwrite object, or the ID of an
            existing channel.
        target_type : hikari.utilities.undefined.UndefinedOr[hikari.models.channels.PermissionOverwriteType or builtins.str]
            If provided, the type of the target to update. If unset, will attempt to get
            the type from `target`.
        allow : hikari.utilities.undefined.UndefinedOr[hikari.models.permissions.Permission]
            If provided, the new vale of all allowed permissions.
        deny : hikari.utilities.undefined.UndefinedOr[hikari.models.permissions.Permission]
            If provided, the new vale of all disallowed permissions.
        reason : hikari.utilities.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.

        Raises
        ------
        builtins.TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to edit the permission overwrites.
        hikari.errors.NotFound
            If the channel is not found or the target is not found if it is
            a role.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_permission_overwrite(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        target: snowflake.SnowflakeishOr[
            typing.Union[channels.PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflake.Snowflakeish]
        ],
    ) -> None:
        """Delete a custom permission for an entity in a given guild channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildChannel]
            The channel to delete a permission overwrite in. This may be a
            channel object, or the ID of an existing channel.
        target : hikari.models.users.PartialUser or hikari.models.guilds.PartialRole or hikari.models.channels.PermissionOverwrite or hikari.utilities.snowflake.Snowflakeish
            The channel overwrite to delete.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to delete the permission overwrite.
        hikari.errors.NotFound
            If the channel is not found or the target is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_channel_invites(
        self, channel: snowflake.SnowflakeishOr[channels.GuildChannel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Fetch all invites pointing to the given guild channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildChannel]
            The channel to fetch the invites from. This may be a channel
            object, or the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.models.invites.InviteWithMetadata]
            The invites pointing to the given guild channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to view the invites for the given channel.
        hikari.errors.NotFound
            If the channel is not found in any guilds you are a member of.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_invite(
        self,
        channel: snowflake.SnowflakeishOr[channels.GuildChannel],
        *,
        max_age: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        max_uses: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        temporary: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        unique: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        target_user: undefined.UndefinedOr[snowflake.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        target_user_type: undefined.UndefinedOr[invites.TargetUserType] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        """Create an invite to the given guild channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildChannel]
            The channel to create a invite for. This may be a channel object,
            or the ID of an existing channel.
        max_age : hikari.utilities.undefined.UndefinedOr[datetime.timedelta or builtins.float or builtins.int]
            If provided, the duration of the invite before expiry.
        max_uses : hikari.utilities.undefined.UndefinedOr[builtins.int]
            If provided, the max uses the invite can have.
        temporary : hikari.utilities.undefined.UndefinedOr[builtins.bool]
            If provided, whether the invite only grants temporary membership.
        unique : hikari.utilities.undefined.UndefinedOr[builtins.bool]
            If provided, whether the invite should be unique.
        target_user : hikari.utilities.undefined.UndefinedOr[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.users.PartialUser]]
            If provided, the target user id for this invite. This may be a
            user object, or the ID of an existing user.
        target_user_type : hikari.utilities.undefined.UndefinedOr[hikari.models.invites.TargetUserType or builtins.int]
            If provided, the type of target user for this invite.
        reason : hikari.utilities.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        hikari.models.invites.InviteWithMetadata
            The invite to the given guild channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to create the given channel.
        hikari.errors.NotFound
            If the channel is not found, or if the target user does not exist,
            if specified.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def trigger_typing(
        self, channel: snowflake.SnowflakeishOr[channels.TextChannel]
    ) -> special_endpoints.TypingIndicator:
        """Trigger typing in a text channel.

        The result of this call can be awaited to trigger typing once, or
        can be used as an async context manager to continually type until the
        context manager is left.

        Examples
        --------
        ```py
        # Trigger typing just once.
        await rest.trigger_typing(channel)

        # Trigger typing repeatedly for 1 minute.
        async with rest.trigger_typing(channel):
            await asyncio.sleep(60)
        ```

        !!! warning
            Sending a message to the channel will cause the typing indicator
            to disappear until it is re-triggered.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to trigger typing in. This may be a channel object, or
            the ID of an existing channel.

        Returns
        -------
        hikari.api.special_endpoints.TypingIndicator
            A typing indicator to use.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read messages or send messages in the
            text channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the result
            is awaited or interacted with. Invoking this function itself will
            not raise any of the above types.
        """

    @abc.abstractmethod
    async def fetch_pins(
        self, channel: snowflake.SnowflakeishOr[channels.TextChannel]
    ) -> typing.Sequence[messages_.Message]:
        """Fetch the pinned messages in this text channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to fetch pins from. This may be a channel object, or
            the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.models.messages.Message]
            The pinned messages in this text channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read messages or send messages in the
            text channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def pin_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        """Pin an existing message in the given text channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to pin a message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.messages.Message]
            The message to pin. This may be a message object,
            or the ID of an existing message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to pin messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found, or if the message does not exist in
            the given channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def unpin_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        """Unpin a given message from a given text channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to unpin a message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.messages.Message]
            The message to unpin. This may be a message object, or the ID of an
            existing message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to pin messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found or the message is not a pinned message
            in the given channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_messages(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        *,
        before: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to fetch messages in. This may be a channel object, or
            the ID of an existing channel.
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
            The exceptions on this endpoint (other than `builtins.TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `builtins.TypeError`).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> messages_.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to fetch messages in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.messages.Message]
            The message to fetch. This may be a channel object, or the ID of an
            existing channel.

        Returns
        -------
        hikari.models.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found or the message is not found in the
            given text channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to create the message in.
        content : hikari.utilities.undefined.UndefinedOr[typing.Any]
            If specified, the message contents. If
            `hikari.utilities.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
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
            once before being able to use this endpoint for a bot.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def edit_message(
        self,
        channel: typing.Union[snowflake.SnowflakeishOr[channels.TextChannel]],
        message: typing.Union[snowflake.SnowflakeishOr[messages_.Message]],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedOr[messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Edit an existing message in a given channel.

        Parameters
        ----------
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The channel to create the message in. This may be
            a `hikari.models.channels.TextChannel` or the ID of an existing
            channel.
        message : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.messages.Message]
            The message to edit. This may be a `hikari.models.messages.Message`
            or the ID of an existing message.
        content : hikari.utilities.undefined.UndefinedOr[typing.Any]
            The message content to update with. If
            `hikari.utilities.undefined.UNDEFINED`, then the content will not
            be changed. If `builtins.None`, then the content will be removed.

            Any other value will be cast to a `builtins.str` before sending.

            If this is a `hikari.models.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.
        embed : hikari.utilities.undefined.UndefinedNoneOr[hikari.models.embeds.Embed]
            The embed to set on the message. If
            `hikari.utilities.undefined.UNDEFINED`, the previous embed if
            present is not changed. If this is `builtins.None`, then the embed
            is removed if present. Otherwise, the new embed value that was
            provided will be used as the replacement.
        mentions_everyone : hikari.utilities.undefined.UndefinedOr[builtins.bool]
            Sanitation for `@everyone` mentions. If
            `hikari.utilities.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, then `@everyone`/`@here` mentions
            in the message content will show up as mentioning everyone that can
            view the chat.
        user_mentions : hikari.utilities.undefined.UndefinedOr[typing.Collection[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.users.PartialUser] or builtins.bool]
            Sanitation for user mentions. If
            `hikari.utilities.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid user mentions will behave
            as mentions. If `builtins.False`, all valid user mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.utilities.snowflake.Snowflake` user IDs, or
            `hikari.models.users.PartialUser`-derived objects.
        role_mentions : hikari.utilities.undefined.UndefinedOr[typing.Collection[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.PartialRole] or builtins.bool]
            Sanitation for role mentions. If
            `hikari.utilities.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid role mentions will behave
            as mentions. If `builtins.False`, all valid role mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.utilities.snowflake.Snowflake` role IDs, or
            `hikari.models.guilds.PartialRole`-derived objects.
        flags : hikari.utilities.undefined.UndefinedOr[hikari.models.messages.MessageFlag]
            Optional flags to set on the message. If
            `hikari.utilities.undefined.UNDEFINED`, then nothing is changed.

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
            do this, `delete` the message and re-send it. This also applies
            to embed attachments.

        !!! warning
            If you specify one of `mentions_everyone`, `user_mentions`, or
            `role_mentions`, then all others will default to `builtins.False`,
            even if they were enabled previously.

            This is a limitation of Discord's design. If in doubt, specify all three of
            them each time.

        !!! warning
            If the message was not sent by your user, the only parameter
            you may provide to this call is the `flags` parameter. Anything
            else will result in a `hikari.errors.Forbidden` being raised.

        Returns
        -------
        hikari.models.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds; users in `user_mentions` not
            being mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel; if
            you try to change the contents of another user's message; or if you
            try to edit the flags on another user's message without the
            permissions to manage messages_.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_message(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        channel
        message

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the permissions to manage messages, and the message is
            not composed by your associated user.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_messages(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        /,
        *messages: snowflake.SnowflakeishOr[messages_.Message],
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
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.TextChannel]
            The text channel, or text channel ID to delete messages from.
        *messages : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.messages.Message]
            One or more messages

        Raises
        ------
        hikari.errors.BulkDeleteError
            An error containing the messages successfully deleted, and the
            messages that were not removed. The
            `builtins.BaseException.__cause__` of the exception will be the
            original error that terminated this process.
        """

    @abc.abstractmethod
    async def add_reaction(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        """Add a reaction emoji to a message in a given channel.

        Parameters
        ----------
        channel
        message
        emoji

        Raises
        ------
        hikari.errors.BadRequest
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to add reactions to messages.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_my_reaction(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        """Delete a reaction that your application user created.

        Parameters
        ----------
        channel
        message
        emoji

        Raises
        ------
        hikari.errors.BadRequest
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_reaction(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
        user: snowflake.SnowflakeishOr[users.PartialUser],
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_all_reactions(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
    ) -> None:
        ...

    @abc.abstractmethod
    def fetch_reactions_for_emoji(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        message: snowflake.SnowflakeishOr[messages_.Message],
        emoji: emojis.Emojiish,
    ) -> iterators.LazyIterator[users.User]:
        ...

    @abc.abstractmethod
    async def create_webhook(
        self,
        channel: snowflake.SnowflakeishOr[channels.TextChannel],
        name: str,
        *,
        avatar: typing.Optional[files.Resourceish] = None,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        ...

    @abc.abstractmethod
    async def fetch_webhook(
        self,
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        ...

    @abc.abstractmethod
    async def fetch_channel_webhooks(
        self, channel: snowflake.SnowflakeishOr[channels.TextChannel],
    ) -> typing.Sequence[webhooks.Webhook]:
        ...

    @abc.abstractmethod
    async def fetch_guild_webhooks(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[webhooks.Webhook]:
        ...

    @abc.abstractmethod
    async def edit_webhook(
        self,
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        channel: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.TextChannel]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        ...

    @abc.abstractmethod
    async def delete_webhook(
        self,
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def execute_webhook(
        self,
        webhook: snowflake.SnowflakeishOr[webhooks.Webhook],
        token: str,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar_url: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[users.PartialUser]], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        ...

    @abc.abstractmethod
    async def fetch_gateway_url(self) -> str:
        ...

    @abc.abstractmethod
    async def fetch_gateway_bot(self) -> gateway.GatewayBot:
        ...

    @abc.abstractmethod
    async def fetch_invite(self, invite: invites.Inviteish) -> invites.Invite:
        ...

    @abc.abstractmethod
    async def delete_invite(self, invite: invites.Inviteish) -> None:
        ...

    @abc.abstractmethod
    async def fetch_my_user(self) -> users.OwnUser:
        ...

    @abc.abstractmethod
    async def edit_my_user(
        self,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
    ) -> users.OwnUser:
        ...

    @abc.abstractmethod
    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        ...

    @abc.abstractmethod
    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        ...

    @abc.abstractmethod
    async def leave_guild(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], /) -> None:
        ...

    # THIS IS AN OAUTH2 FLOW ONLY
    @abc.abstractmethod
    async def create_dm_channel(
        self, user: snowflake.SnowflakeishOr[users.PartialUser], /
    ) -> channels.PrivateTextChannel:
        ...

    # THIS IS AN OAUTH2 FLOW BUT CAN BE USED BY BOTS ALSO
    @abc.abstractmethod
    async def fetch_application(self) -> applications.Application:
        ...

    # THIS IS AN OAUTH2 FLOW ONLY
    @abc.abstractmethod
    async def add_user_to_guild(
        self,
        access_token: str,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        ...

    @abc.abstractmethod
    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        ...

    @abc.abstractmethod
    async def fetch_user(self, user: snowflake.SnowflakeishOr[users.PartialUser]) -> users.User:
        ...

    def fetch_audit_log(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        before: undefined.UndefinedOr[snowflake.SearchableSnowflakeishOr[snowflake.Unique]] = undefined.UNDEFINED,
        user: undefined.UndefinedOr[snowflake.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        event_type: undefined.UndefinedOr[audit_logs.AuditLogEventType] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:
        ...

    @abc.abstractmethod
    async def fetch_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
    ) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    async def fetch_guild_emojis(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[emojis.KnownCustomEmoji]:
        ...

    @abc.abstractmethod
    async def create_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        image: files.Resourceish,
        *,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    async def edit_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        # likewise this only is valid for custom emojis, unicode emojis make little sense here.
        emoji: typing.Union[str, emojis.CustomEmoji],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    async def delete_emoji(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[str, emojis.CustomEmoji],
        # TODO: check this is still true? iirc I got yelled at about something similar to this when I reported it.
        # Reason is not currently supported for some reason.
    ) -> None:
        ...

    @abc.abstractmethod
    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        ...

    @abc.abstractmethod
    async def fetch_guild(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> guilds.RESTGuild:
        ...

    @abc.abstractmethod
    async def fetch_guild_preview(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildPreview:
        ...

    @abc.abstractmethod
    async def edit_guild(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[voices.VoiceRegionish] = undefined.UNDEFINED,
        verification_level: undefined.UndefinedOr[guilds.GuildVerificationLevel] = undefined.UNDEFINED,
        default_message_notifications: undefined.UndefinedOr[
            guilds.GuildMessageNotificationsLevel
        ] = undefined.UNDEFINED,
        explicit_content_filter_level: undefined.UndefinedOr[
            guilds.GuildExplicitContentFilterLevel
        ] = undefined.UNDEFINED,
        afk_channel: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildVoiceChannel]] = undefined.UNDEFINED,
        afk_timeout: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        owner: undefined.UndefinedOr[snowflake.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        splash: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        banner: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        system_channel: undefined.UndefinedNoneOr[
            snowflake.SnowflakeishOr[channels.GuildTextChannel]
        ] = undefined.UNDEFINED,
        rules_channel: undefined.UndefinedNoneOr[
            snowflake.SnowflakeishOr[channels.GuildTextChannel]
        ] = undefined.UNDEFINED,
        public_updates_channel: undefined.UndefinedNoneOr[
            snowflake.SnowflakeishOr[channels.GuildTextChannel]
        ] = undefined.UNDEFINED,
        preferred_locale: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        ...

    @abc.abstractmethod
    async def delete_guild(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> None:
        ...

    @abc.abstractmethod
    async def fetch_guild_channels(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[channels.GuildChannel]:
        ...

    @abc.abstractmethod
    async def create_guild_text_channel(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildTextChannel:
        ...

    @abc.abstractmethod
    async def create_guild_news_channel(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildNewsChannel:
        ...

    @abc.abstractmethod
    async def create_guild_voice_channel(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflake.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildVoiceChannel:
        ...

    @abc.abstractmethod
    async def create_guild_category(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels.GuildCategory:
        ...

    @abc.abstractmethod
    async def reposition_channels(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, typing.Union[snowflake.SnowflakeishOr[channels.GuildChannel]]],
    ) -> None:
        ...

    @abc.abstractmethod
    async def fetch_member(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], user: snowflake.SnowflakeishOr[users.PartialUser],
    ) -> guilds.Member:
        ...

    @abc.abstractmethod
    def fetch_members(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]
    ) -> iterators.LazyIterator[guilds.Member]:
        ...

    @abc.abstractmethod
    async def edit_member(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflake.SnowflakeishOr[channels.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def edit_my_nick(
        self,
        guild: snowflake.SnowflakeishOr[guilds.Guild],
        nick: typing.Optional[str],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def add_role_to_member(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        role: snowflake.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def remove_role_from_member(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        role: snowflake.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def kick_user(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    kick_member = kick_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def ban_user(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_days: undefined.UndefinedNoneOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    ban_member = ban_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def unban_user(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        user: snowflake.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    unban_member = unban_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def fetch_ban(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], user: snowflake.SnowflakeishOr[users.PartialUser],
    ) -> guilds.GuildMemberBan:
        ...

    @abc.abstractmethod
    async def fetch_bans(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        ...

    @abc.abstractmethod
    async def fetch_roles(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],) -> typing.Sequence[guilds.Role]:
        ...

    @abc.abstractmethod
    async def create_role(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        ...

    @abc.abstractmethod
    async def reposition_roles(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflake.SnowflakeishOr[guilds.PartialRole]],
    ) -> None:
        ...

    @abc.abstractmethod
    async def edit_role(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        role: snowflake.SnowflakeishOr[guilds.PartialRole],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permission] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        ...

    @abc.abstractmethod
    async def delete_role(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild], role: snowflake.SnowflakeishOr[guilds.PartialRole],
    ) -> None:
        ...

    @abc.abstractmethod
    async def estimate_guild_prune_count(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
    ) -> int:
        """Estimate the guild prune count.

        Parameters
        ----------
        guild : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.PartialGuild]
            The guild to estimate the guild prune count for. This may be a guild object,
            or the ID of an existing channel.
        days : hikari.utilities.undefined.UndefinedOr[builtins.int]
            If provided, number of days to count prune for.
        include_roles : hikari.utilities.undefined.UndefinedOr[typing.Collection[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.PartialRole][
            If provided, the role(s) to include. By default, this endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.

        Returns
        -------
        builtins.int
            The estimated guild prune count.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBERS` permission.
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def begin_guild_prune(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        compute_prune_count: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[
            typing.Collection[snowflake.SnowflakeishOr[guilds.PartialRole]]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Optional[int]:
        """Begin the guild prune.

        Parameters
        ----------
        guild : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.PartialGuild]
            The guild to begin the guild prune in. This may be a guild object,
            or the ID of an existing channel.
        days : hikari.utilities.undefined.UndefinedOr[builtins.int]
            If provided, number of days to count prune for.
        compute_prune_count: hikari.utilities.snowflake.SnowflakeishOr[builtins.bool]
            If provided, whether to return the prune count. This is discouraged
            for large guilds.
        include_roles : hikari.utilities.undefined.UndefinedOr[typing.Collection[hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.PartialRole]]]
            If provided, the role(s) to include. By default, this endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.
        reason : hikari.utilities.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        builtins.int or builtins.None
            If `compute_prune_count` is not provided or `builtins.True`, the
            number of members pruned.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBERS` permission.
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_guild_voice_regions(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        ...

    @abc.abstractmethod
    async def fetch_guild_invites(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        ...

    @abc.abstractmethod
    async def fetch_integrations(
        self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Integration]:
        ...

    @abc.abstractmethod
    async def edit_integration(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflake.SnowflakeishOr[guilds.Integration],
        *,
        expire_behaviour: undefined.UndefinedOr[guilds.IntegrationExpireBehaviour] = undefined.UNDEFINED,
        expire_grace_period: undefined.UndefinedOr[date.Intervalish] = undefined.UNDEFINED,
        enable_emojis: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_integration(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflake.SnowflakeishOr[guilds.Integration],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def sync_integration(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        integration: snowflake.SnowflakeishOr[guilds.Integration],
    ) -> None:
        ...

    @abc.abstractmethod
    async def fetch_widget(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildWidget:
        ...

    @abc.abstractmethod
    async def edit_widget(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        *,
        channel: undefined.UndefinedNoneOr[snowflake.SnowflakeishOr[channels.GuildChannel]] = undefined.UNDEFINED,
        enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.GuildWidget:
        ...

    @abc.abstractmethod
    async def fetch_vanity_url(self, guild: snowflake.SnowflakeishOr[guilds.PartialGuild]) -> invites.VanityURL:
        ...

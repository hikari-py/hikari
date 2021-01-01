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
"""Special additional endpoints used by the REST API."""
from __future__ import annotations

__all__: typing.List[str] = ["TypingIndicator", "GuildBuilder"]

import abc
import typing

import attr

from hikari import undefined

if typing.TYPE_CHECKING:
    import types

    from hikari import channels
    from hikari import colors
    from hikari import files
    from hikari import guilds
    from hikari import permissions as permissions_
    from hikari import snowflakes
    from hikari import voices
    from hikari.internal import time


class TypingIndicator(abc.ABC):
    """Result type of `hikari.api.rest.RESTClient.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.

    !!! note
        This is a helper class that is used by `hikari.api.rest.RESTClient`.
        You should only ever need to use instances of this class that are
        produced by that API.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def __await__(self) -> typing.Generator[None, typing.Any, None]:
        ...

    @abc.abstractmethod
    async def __aenter__(self) -> None:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exception_type: typing.Type[BaseException],
        exception: BaseException,
        exception_traceback: types.TracebackType,
    ) -> None:
        ...


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildBuilder(abc.ABC):
    """Result type of `hikari.api.rest.RESTClient.guild_builder`.

    This is used to create a guild in a tidy way using the HTTP API, since
    the logic behind creating a guild on an API level is somewhat confusing
    and detailed.

    !!! note
        This is a helper class that is used by `hikari.api.rest.RESTClient`.
        You should only ever need to use instances of this class that are
        produced by that API, thus, any details about the constructor are
        omitted from the following examples for brevity.

    Examples
    --------
    Creating an empty guild.

    ```py
    guild = await rest.guild_builder("My Server!").create()
    ```

    Creating a guild with an icon

    ```py
    from hikari.files import WebResourceStream

    guild_builder = rest.guild_builder("My Server!")
    guild_builder.icon = WebResourceStream("cat.png", "http://...")
    guild = await guild_builder.create()
    ```

    Adding roles to your guild.

    ```py
    from hikari.permissions import Permissions

    guild_builder = rest.guild_builder("My Server!")

    everyone_role_id = guild_builder.add_role("@everyone")
    admin_role_id = guild_builder.add_role("Admins", permissions=Permissions.ADMINISTRATOR)

    await guild_builder.create()
    ```

    !!! warning
        The first role must always be the `@everyone` role.

    !!! note
        If you call `add_role`, the default roles provided by discord will
        be created. This also applies to the `add_` functions for
        text channels/voice channels/categories.

    !!! note
        Functions that return a `hikari.snowflakes.Snowflake` do
        **not** provide the final ID that the object will have once the
        API call is made. The returned IDs are only able to be used to
        re-reference particular objects while building the guild format.

        This is provided to allow creation of channels within categories,
        and to provide permission overwrites.

    Adding a text channel to your guild.

    ```py
    guild_builder = rest.guild_builder("My Server!")

    category_id = guild_builder.add_category("My safe place")
    channel_id = guild_builder.add_text_channel("general", parent_id=category_id)

    await guild_builder.create()
    ```
    """

    default_message_notifications: undefined.UndefinedOr[guilds.GuildMessageNotificationsLevel] = attr.ib(
        default=undefined.UNDEFINED
    )
    """Default message notification level that can be overwritten.

    If not overridden, this will use the Discord default level.
    """

    explicit_content_filter_level: undefined.UndefinedOr[guilds.GuildExplicitContentFilterLevel] = attr.ib(
        default=undefined.UNDEFINED
    )
    """Explicit content filter level that can be overwritten.

    If not overridden, this will use the Discord default level.
    """

    icon: undefined.UndefinedOr[files.Resourceish] = attr.ib(default=undefined.UNDEFINED)
    """Guild icon to use that can be overwritten.

    If not overridden, the guild will not have an icon.
    """

    region: undefined.UndefinedOr[voices.VoiceRegionish] = attr.ib(default=undefined.UNDEFINED)
    """Guild voice channel region to use that can be overwritten.

    If not overridden, the guild will use the default voice region for Discord.
    """

    verification_level: undefined.UndefinedOr[typing.Union[guilds.GuildVerificationLevel, int]] = attr.ib(
        default=undefined.UNDEFINED
    )
    """Verification level required to join the guild that can be overwritten.

    If not overridden, the guild will use the default verification level for
    Discord.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the guild to create.

        Returns
        -------
        builtins.str
            The guild name.
        """

    @abc.abstractmethod
    async def create(self) -> guilds.RESTGuild:
        """Send the request to Discord to create the guild.

        The application user will be added to this guild as soon as it is
        created. All IDs that were provided when building this guild will
        become invalid and will be replaced with real IDs.

        Returns
        -------
        hikari.guilds.RESTGuild
            The created guild.

        Raises
        ------
        hikari.errors.BadRequestError
            If any values set in the guild builder are invalid.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are already in 10 guilds.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def add_role(
        self,
        name: str,
        /,
        *,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        """Create a role.

        !!! warning
            The first role you create must always be the `@everyone` role.

        Parameters
        ----------
        name : builtins.str
            The role's name.

        Other Parameters
        ----------------
        permissions : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the permissions for the role.
        color : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            If provided, the role's color.
        colour : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            An alias for `color`.
        hoist : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to hoist the role.
        mentionable : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to make the role mentionable.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The dummy ID for this role that can be used temporarily to refer
            to this object while designing the guild layout.

            When the guild is created, this will be replaced with a different
            ID.

        Raises
        ------
        builtins.ValueError
            If you are defining the first role, but did not name it `@everyone`.
        builtins.TypeError
            If you specify both `color` and `colour` together or if you try to
            specify `color`, `colour`, `hoisted`, `mentionable` or `position` for
            the `@everyone` role.
        """

    @abc.abstractmethod
    def add_category(
        self,
        name: str,
        /,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        """Create a category channel.

        Parameters
        ----------
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the category.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the category.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The dummy ID for this channel that can be used temporarily to refer
            to this object while designing the guild layout.

            When the guild is created, this will be replaced with a different
            ID.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def add_text_channel(
        self,
        name: str,
        /,
        *,
        parent_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        """Create a text channel.

        Parameters
        ----------
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the channel (relative to the
            category, if any).
        topic : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the channels topic. Maximum 1024 characters.
        nsfw : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the ammount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The dummy ID for this channel that can be used temporarily to refer
            to this object while designing the guild layout.

            When the guild is created, this will be replaced with a different
            ID.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def add_voice_channel(
        self,
        name: str,
        /,
        *,
        parent_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        """Create a voice channel.

        Parameters
        ----------
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the channel (relative to the
            category, if any).
        user_limit : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the maximum users in the channel at once.
            Must be between 0 and 99 with 0 meaning no limit.
        bitrate : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the bitrate for the channel. Must be
            between 8000 and 96000 or 8000 and 128000 for VIP
            servers.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The dummy ID for this channel that can be used temporarily to refer
            to this object while designing the guild layout.

            When the guild is created, this will be replaced with a different
            ID.
        """  # noqa: E501 - Line too long

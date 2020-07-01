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
"""Special additional endpoints used by the REST API."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["TypingIndicator", "GuildBuilder"]

import abc
import typing

import attr

from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import types

    from hikari.models import channels
    from hikari.models import colors
    from hikari.models import guilds
    from hikari.models import permissions as permissions_
    from hikari.utilities import date
    from hikari.utilities import files
    from hikari.utilities import snowflake


class TypingIndicator(abc.ABC):
    """Result type of `hiarki.net.rest.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.
    """

    __slots__ = ()

    def __enter__(self) -> typing.NoReturn:
        raise TypeError("Use 'async with' rather than 'with' when triggering the typing indicator.")

    @abc.abstractmethod
    def __await__(self) -> typing.Generator[None, typing.Any, None]:
        ...

    @abc.abstractmethod
    async def __aenter__(self) -> None:
        ...

    @abc.abstractmethod
    async def __aexit__(self, ex_t: typing.Type[Exception], ex_v: Exception, exc_tb: types.TracebackType) -> None:
        ...


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class GuildBuilder:
    """A helper class used to construct a prototype for a guild.

    This is used to create a guild in a tidy way using the HTTP API, since
    the logic behind creating a guild on an API level is somewhat confusing
    and detailed.

    !!! note
        This is a helper class that is used by `hikari.impl.http.HTTP`.
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
    from hikari.models.files import WebResourceStream

    guild_builder = rest.guild_builder("My Server!")
    guild_builder.icon = WebResourceStream("cat.png", "http://...")
    guild = await guild_builder.create()
    ```

    Adding roles to your guild.

    ```py
    from hikari.models.permissions import Permission

    guild_builder = rest.guild_builder("My Server!")

    everyone_role_id = guild_builder.add_role("@everyone")
    admin_role_id = guild_builder.add_role("Admins", permissions=Permission.ADMINISTRATOR)

    await guild_builder.create()
    ```

    !!! warning
        The first role must always be the `@everyone` role.

    !!! note
        Functions that return a `hikari.utilities.snowflake.Snowflake` do
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

    default_message_notifications: typing.Union[
        undefined.UndefinedType, guilds.GuildMessageNotificationsLevel
    ] = undefined.UNDEFINED
    """Default message notification level that can be overwritten.

    If not overridden, this will use the Discord default level.
    """

    explicit_content_filter_level: typing.Union[
        undefined.UndefinedType, guilds.GuildExplicitContentFilterLevel
    ] = undefined.UNDEFINED
    """Explicit content filter level that can be overwritten.

    If not overridden, this will use the Discord default level.
    """

    icon: typing.Union[undefined.UndefinedType, files.URL] = undefined.UNDEFINED
    """Guild icon to use that can be overwritten.

    If not overridden, the guild will not have an icon.
    """

    region: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED
    """Guild voice channel region to use that can be overwritten.

    If not overridden, the guild will use the default voice region for Discord.
    """

    verification_level: typing.Union[undefined.UndefinedType, guilds.GuildVerificationLevel] = undefined.UNDEFINED
    """Verification level required to join the guild that can be overwritten.

    If not overridden, the guild will use the default verification level for
    Discord.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Guild name."""

    @abc.abstractmethod
    async def create(self) -> guilds.Guild:
        """Send the request to Discord to create the guild.

        The application user will be added to this guild as soon as it is
        created. All IDs that were provided when building this guild will
        become invalid and will be replaced with real IDs.

        Returns
        -------
        hikari.models.guilds.Guild
            The created guild.

        Raises
        ------
        hikari.errors.BadRequest
            If any values set in the guild builder are invalid.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you are already in 10 guilds.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def add_role(
        self,
        name: str,
        /,
        *,
        color: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        colour: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        hoisted: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        mentionable: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        permissions: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        """Create a role.

        !!! note
            The first role you create must always be the `@everyone` role, and
            must have that name. This role will ignore the `hoisted`, `color`,
            `colour`, `mentionable` and `position` parameters.

        Parameters
        ----------
        name : builtins.str
            The role name.
        color : hikari.utilities.undefined.UndefinedType or hikari.models.colors.Color
            The colour of the role to use. If unspecified, then the default
            colour is used instead.
        colour : hikari.utilities.undefined.UndefinedType or hikari.models.colors.Color
            Alias for the `color` parameter for non-american users.
        hoisted : hikari.utilities.undefined.UndefinedType or builtins.bool
            If `builtins.True`, the role will show up in the user sidebar in a separate
            category if it is the highest hoisted role. If `builtins.False`, or
            unspecified, then this will not occur.
        mentionable : hikari.utilities.undefined.UndefinedType or builtins.bool
            If `builtins.True`, then the role will be able to be mentioned.
        permissions : hikari.utilities.undefined.UndefinedType or hikari.models.permissions.Permission
            The optional permissions to enforce on the role. If unspecified,
            the default permissions for roles will be used.

            !!! note
                The default permissions are **NOT** the same as providing
                zero permissions. To set no permissions, you should
                pass `Permission(0)` explicitly.
        position : hikari.utilities.undefined.UndefinedType or builtins.int
            If specified, the position to place the role in.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The dummy ID for this role that can be used temporarily to refer
            to this object while designing the guild layout.

            When the guild is created, this will be replaced with a different
            ID.

        Raises
        ------
        builtins.ValueError
            If you are defining the first role, but did not name it `@everyone`.
        builtins.TypeError
            If you specify both `color` and `colour` together.
        """

    @abc.abstractmethod
    def add_category(
        self,
        name: str,
        /,
        *,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        """Create a category channel.

        Parameters
        ----------
        name : builtins.str
            The name of the category.
        position : hikari.utilities.undefined.UndefinedType or builtins.int
            The position to place the category in, if specified.
        permission_overwrites : hikari.utilities.undefined.UndefinedType or typing.Collection[hikari.models.channels.PermissionOverwrite]
            If defined, a collection of one or more
            `hikari.models.channels.PermissionOverwrite` objects.
        nsfw : hikari.utilities.undefined.UndefinedType or builtins.bool
            If `builtins.True`, the channel is marked as NSFW and only users
            over 18 years of age should be given access.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
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
        parent_id: typing.Union[undefined.UndefinedType, snowflake.Snowflake] = undefined.UNDEFINED,
        topic: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        rate_limit_per_user: typing.Union[undefined.UndefinedType, date.TimeSpan] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        """Create a text channel.

        Parameters
        ----------
        name : builtins.str
            The name of the category.
        position : hikari.utilities.undefined.UndefinedType or builtins.int
            The position to place the category in, if specified.
        permission_overwrites : hikari.utilities.undefined.UndefinedType or typing.Collection[hikari.models.channels.PermissionOverwrite]
            If defined, a collection of one or more
            `hikari.models.channels.PermissionOverwrite` objects.
        nsfw : hikari.utilities.undefined.UndefinedType or builtins.bool
            If `builtins.True`, the channel is marked as NSFW and only users
            over 18 years of age should be given access.
        parent_id : hikari.utilities.undefined.UndefinedType or hikari.utilities.snowflake.Snowflake
            If defined, should be a snowflake ID of a category channel
            that was made with this builder. If provided, this channel will
            become a child channel of that category.
        topic : hikari.utilities.undefined.UndefinedType or builtins.str
            If specified, the topic to set on the channel.
        rate_limit_per_user : hikari.utilities.undefined.UndefinedType or hikari.utilities.date.TimeSpan
            If specified, the time to wait between allowing consecutive messages
            to be sent. If not specified, this will not be enabled.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
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
        parent_id: typing.Union[undefined.UndefinedType, snowflake.Snowflake] = undefined.UNDEFINED,
        bitrate: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        user_limit: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        """Create a voice channel.

        Parameters
        ----------
        name : builtins.str
            The name of the category.
        position : hikari.utilities.undefined.UndefinedType or builtins.int
            The position to place the category in, if specified.
        permission_overwrites : hikari.utilities.undefined.UndefinedType or typing.Collection[hikari.models.channels.PermissionOverwrite]
            If defined, a collection of one or more
            `hikari.models.channels.PermissionOverwrite` objects.
        nsfw : hikari.utilities.undefined.UndefinedType or builtins.bool
            If `builtins.True`, the channel is marked as NSFW and only users
            over 18 years of age should be given access.
        parent_id : hikari.utilities.undefined.UndefinedType or hikari.utilities.snowflake.Snowflake
            If defined, should be a snowflake ID of a category channel
            that was made with this builder. If provided, this channel will
            become a child channel of that category.
        bitrate : hikari.utilities.undefined.UndefinedType or builtins.int
            If specified, the bitrate to set on the channel.
        user_limit : hikari.utilities.undefined.UndefinedType or builtins.int
            If specified, the maximum number of users to allow in the voice
            channel.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The dummy ID for this channel that can be used temporarily to refer
            to this object while designing the guild layout.

            When the guild is created, this will be replaced with a different
            ID.
        """  # noqa: E501 - Line too long

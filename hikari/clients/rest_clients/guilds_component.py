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
"""The logic for handling requests to guild endpoints."""

__all__ = ["RESTGuildComponent"]

import abc
import datetime
import typing

from hikari import audit_logs
from hikari import bases
from hikari import channels as _channels
from hikari import colors
from hikari import emojis
from hikari import guilds
from hikari import invites
from hikari import permissions as _permissions
from hikari import users
from hikari import voices
from hikari import webhooks
from hikari.clients.rest_clients import component_base
from hikari.internal import conversions
from hikari.internal import pagination


def _get_member_id(member: guilds.GuildMember) -> str:
    return str(member.user.id)


class RESTGuildComponent(component_base.BaseRESTComponent, abc.ABC):  # pylint: disable=W0223
    """The REST client component for handling requests to guild endpoints."""

    async def fetch_audit_log(
        self,
        guild: bases.Hashable[guilds.Guild],
        *,
        user: bases.Hashable[users.User] = ...,
        action_type: typing.Union[audit_logs.AuditLogEventType, int] = ...,
        limit: int = ...,
        before: typing.Union[datetime.datetime, bases.Hashable[audit_logs.AuditLogEntry]] = ...,
    ) -> audit_logs.AuditLog:
        """Get an audit log object for the given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the audit logs for.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the user to filter by.
        action_type : :obj:`~typing.Union` [ :obj:`~hikari.audit_logs.AuditLogEventType`, :obj:`~int` ]
            If specified, the action type to look up. Passing a raw integer
            for this may lead to unexpected behaviour.
        limit : :obj:`~int`
            If specified, the limit to apply to the number of records.
            Defaults to ``50``. Must be between ``1`` and ``100`` inclusive.
        before : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.audit_logs.AuditLogEntry`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the entry that all retrieved
            entries should have occurred befor.

        Returns
        -------
        :obj:`~hikari.audit_logs.AuditLog`
            An audit log object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the given permissions to view an audit log.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild does not exist.
        """
        if isinstance(before, datetime.datetime):
            before = str(bases.Snowflake.from_datetime(before))
        elif before is not ...:
            before = str(before.id if isinstance(before, bases.UniqueEntity) else int(before))
        payload = await self._session.get_guild_audit_log(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=(str(user.id if isinstance(user, bases.UniqueEntity) else int(user)) if user is not ... else ...),
            action_type=action_type,
            limit=limit,
            before=before,
        )
        return audit_logs.AuditLog.deserialize(payload)

    def fetch_audit_log_entries_before(
        self,
        guild: bases.Hashable[guilds.Guild],
        *,
        before: typing.Union[datetime.datetime, bases.Hashable[audit_logs.AuditLogEntry], None] = None,
        user: bases.Hashable[users.User] = ...,
        action_type: typing.Union[audit_logs.AuditLogEventType, int] = ...,
        limit: typing.Optional[int] = None,
    ) -> audit_logs.AuditLogIterator:
        """Return an async iterator that retrieves a guild's audit log entries.

        This will return the audit log entries before a given entry object/ID or
        from the first guild audit log entry.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID or object of the guild to get audit log entries for
        before : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.audit_logs.AuditLogEntry`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], optional
            If specified, the ID or object of the entry or datetime to get
            entries that happened before otherwise this will start from the
            newest entry.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the user to filter by.
        action_type : :obj:`~typing.Union` [ :obj:`~hikari.audit_logs.AuditLogEventType`, :obj:`~int` ]
            If specified, the action type to look up. Passing a raw integer
            for this may lead to unexpected behaviour.
        limit : :obj:`~int`, optional
            If specified, the limit for how many entries this iterator should
            return, defaults to unlimited.

        Example
        -------
        .. code-block:: python

            audit_log_entries = client.fetch_audit_log_entries_before(guild, before=9876543, limit=6969)
            async for entry in audit_log_entries:
                if (user := audit_log_entries.users[entry.user_id]).is_bot:
                    await client.ban_member(guild, user)

        Note
        ----
        The returned iterator has the attributes ``users``, ``members`` and
        ``integrations`` which are mappings of snowflake IDs to objects for the
        relevant entities that are referenced by the retrieved audit log
        entries. These will be filled over time as more audit log entries are
        fetched by the iterator.

        Returns
        -------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.audit_logs.AuditLogIterator`
            An async iterator of the audit log entries in a guild (from newest
            to oldest).
        """
        if isinstance(before, datetime.datetime):
            before = str(bases.Snowflake.from_datetime(before))
        elif before is not None:
            before = str(before.id if isinstance(before, bases.UniqueEntity) else int(before))
        return audit_logs.AuditLogIterator(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            request=self._session.get_guild_audit_log,
            before=before,
            user_id=(str(user.id if isinstance(user, bases.UniqueEntity) else int(user)) if user is not ... else ...),
            action_type=action_type,
            limit=limit,
        )

    async def fetch_guild_emoji(
        self, guild: bases.Hashable[guilds.Guild], emoji: bases.Hashable[emojis.GuildEmoji],
    ) -> emojis.GuildEmoji:
        """Get an updated emoji object from a specific guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the emoji from.
        emoji : :obj:`~typing.Union` [ :obj:`~hikari.emojis.GuildEmoji`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the emoji to get.

        Returns
        -------
        :obj:`~hikari.emojis.GuildEmoji`
            A guild emoji object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you aren't a member of said guild.
        """
        payload = await self._session.get_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            emoji_id=str(emoji.id if isinstance(emoji, bases.UniqueEntity) else int(emoji)),
        )
        return emojis.GuildEmoji.deserialize(payload)

    async def fetch_guild_emojis(self, guild: bases.Hashable[guilds.Guild]) -> typing.Sequence[emojis.GuildEmoji]:
        """Get emojis for a given guild object or ID.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the emojis for.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.emojis.GuildEmoji` ]
            A list of guild emoji objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you aren't a member of the guild.
        """
        payload = await self._session.list_guild_emojis(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [emojis.GuildEmoji.deserialize(emoji) for emoji in payload]

    async def create_guild_emoji(
        self,
        guild: bases.Hashable[guilds.GuildRole],
        name: str,
        image_data: conversions.FileLikeT,
        *,
        roles: typing.Sequence[bases.Hashable[guilds.GuildRole]] = ...,
        reason: str = ...,
    ) -> emojis.GuildEmoji:
        """Create a new emoji for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to create the emoji in.
        name : :obj:`~str`
            The new emoji's name.
        image_data : ``hikari.internal.conversions.FileLikeT``
            The ``128x128`` image data.
        roles : :obj:`~typing.Sequence` [ :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            If specified, a list of role objects or IDs for which the emoji
            will be whitelisted. If empty, all roles are whitelisted.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.emojis.GuildEmoji`
            The newly created emoji object.

        Raises
        ------
        :obj:`~ValueError`
            If ``image`` is :obj:`~None`.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or aren't a
            member of said guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you attempt to upload an image larger than ``256kb``, an empty
            image or an invalid image format.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            name=name,
            image=conversions.get_bytes_from_resource(image_data),
            roles=[str(role.id if isinstance(role, bases.UniqueEntity) else int(role)) for role in roles]
            if roles is not ...
            else ...,
            reason=reason,
        )
        return emojis.GuildEmoji.deserialize(payload)

    async def update_guild_emoji(
        self,
        guild: bases.Hashable[guilds.Guild],
        emoji: bases.Hashable[emojis.GuildEmoji],
        *,
        name: str = ...,
        roles: typing.Sequence[bases.Hashable[guilds.GuildRole]] = ...,
        reason: str = ...,
    ) -> emojis.GuildEmoji:
        """Edits an emoji of a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to which the emoji to edit belongs to.
        emoji : :obj:`~typing.Union` [ :obj:`~hikari.emojis.GuildEmoji`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the emoji to edit.
        name : :obj:`~str`
            If specified, a new emoji name string. Keep unspecified to leave the
            name unchanged.
        roles : :obj:`~typing.Sequence` [ :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            If specified, a list of objects or IDs for the new whitelisted
            roles. Set to an empty list to whitelist all roles.
            Keep unspecified to leave the same roles already set.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.emojis.GuildEmoji`
            The updated emoji object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or are not a
            member of the given guild.
        """
        payload = await self._session.modify_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            emoji_id=str(emoji.id if isinstance(emoji, bases.UniqueEntity) else int(emoji)),
            name=name,
            roles=[str(role.id if isinstance(role, bases.UniqueEntity) else int(role)) for role in roles]
            if roles is not ...
            else ...,
            reason=reason,
        )
        return emojis.GuildEmoji.deserialize(payload)

    async def delete_guild_emoji(
        self, guild: bases.Hashable[guilds.Guild], emoji: bases.Hashable[emojis.GuildEmoji],
    ) -> None:
        """Delete an emoji from a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to delete the emoji from.
        emoji : :obj:`~typing.Union` [ :obj:`~hikari.emojis.GuildEmoji`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild emoji to be deleted.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the emoji aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_EMOJIS`` permission or aren't a
            member of said guild.
        """
        await self._session.delete_guild_emoji(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            emoji_id=str(emoji.id if isinstance(emoji, bases.UniqueEntity) else int(emoji)),
        )

    async def create_guild(
        self,
        name: str,
        *,
        region: typing.Union[voices.VoiceRegion, str] = ...,
        icon_data: conversions.FileLikeT = ...,
        verification_level: typing.Union[guilds.GuildVerificationLevel, int] = ...,
        default_message_notifications: typing.Union[guilds.GuildMessageNotificationsLevel, int] = ...,
        explicit_content_filter: typing.Union[guilds.GuildExplicitContentFilterLevel, int] = ...,
        roles: typing.Sequence[guilds.GuildRole] = ...,
        channels: typing.Sequence[_channels.GuildChannelBuilder] = ...,
    ) -> guilds.Guild:
        """Create a new guild.

        Warning
        -------
        Can only be used by bots in less than ``10`` guilds.

        Parameters
        ----------
        name : :obj:`~str`
            The name string for the new guild (``2-100`` characters).
        region : :obj:`~str`
            If specified, the voice region ID for new guild. You can use
            :meth:`fetch_guild_voice_regions` to see which region IDs are
            available.
        icon_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the guild icon image data.
        verification_level : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildVerificationLevel`, :obj:`~int` ]
            If specified, the verification level. Passing a raw int for this
            may lead to unexpected behaviour.
        default_message_notifications : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildMessageNotificationsLevel`, :obj:`~int` ]
            If specified, the default notification level. Passing a raw int for
            this may lead to unexpected behaviour.
        explicit_content_filter : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildExplicitContentFilterLevel`, :obj:`~int` ]
            If specified, the explicit content filter. Passing a raw int for
            this may lead to unexpected behaviour.
        roles : :obj:`~typing.Sequence` [ :obj:`~hikari.guilds.GuildRole` ]
            If specified, an array of role objects to be created alongside the
            guild. First element changes the ``@everyone`` role.
        channels : :obj:`~typing.Sequence` [ :obj:`~hikari.channels.GuildChannelBuilder` ]
            If specified, an array of guild channel builder objects to be
            created within the guild.

        Returns
        -------
        :obj:`~hikari.guilds.Guild`
            The newly created guild object.

        Raises
        ------
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are in ``10`` or more guilds.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide unsupported fields like ``parent_id`` in channel
            objects.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild(
            name=name,
            region=getattr(region, "id", region),
            icon=conversions.get_bytes_from_resource(icon_data),
            verification_level=verification_level,
            default_message_notifications=default_message_notifications,
            explicit_content_filter=explicit_content_filter,
            roles=[role.serialize() for role in roles] if roles is not ... else ...,
            channels=[channel.serialize() for channel in channels] if channels is not ... else ...,
        )
        return guilds.Guild.deserialize(payload)

    async def fetch_guild(self, guild: bases.Hashable[guilds.Guild]) -> guilds.Guild:
        """Get a given guild's object.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get.

        Returns
        -------
        :obj:`~hikari.guilds.Guild`
            The requested guild object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you don't have access to the guild.
        """
        payload = await self._session.get_guild(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return guilds.Guild.deserialize(payload)

    async def fetch_guild_preview(self, guild: bases.Hashable[guilds.Guild]) -> guilds.GuildPreview:
        """Get a given guild's object.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the preview object for.

        Returns
        -------
        :obj:`~hikari.guilds.GuildPreview`
            The requested guild preview object.

        Note
        ----
        Unlike other guild endpoints, the bot doesn't have to be in the target
        guild to get it's preview.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of UINT64.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found or it isn't ``PUBLIC``.
        """
        payload = await self._session.get_guild_preview(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return guilds.GuildPreview.deserialize(payload)

    async def update_guild(
        self,
        guild: bases.Hashable[guilds.Guild],
        *,
        name: str = ...,
        region: typing.Union[voices.VoiceRegion, str] = ...,
        verification_level: typing.Union[guilds.GuildVerificationLevel, int] = ...,
        default_message_notifications: typing.Union[guilds.GuildMessageNotificationsLevel, int] = ...,
        explicit_content_filter: typing.Union[guilds.GuildExplicitContentFilterLevel, int] = ...,
        afk_channel: bases.Hashable[_channels.GuildVoiceChannel] = ...,
        afk_timeout: typing.Union[datetime.timedelta, int] = ...,
        icon_data: conversions.FileLikeT = ...,
        owner: bases.Hashable[users.User] = ...,
        splash_data: conversions.FileLikeT = ...,
        system_channel: bases.Hashable[_channels.Channel] = ...,
        reason: str = ...,
    ) -> guilds.Guild:
        """Edit a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to be edited.
        name : :obj:`~str`
            If specified, the new name string for the guild (``2-100`` characters).
        region : :obj:`~str`
            If specified, the new voice region ID for guild. You can use
            :meth:`fetch_guild_voice_regions` to see which region IDs are
            available.
        verification_level : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildVerificationLevel`, :obj:`~int` ]
            If specified, the new verification level. Passing a raw int for this
            may lead to unexpected behaviour.
        default_message_notifications : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildMessageNotificationsLevel`, :obj:`~int` ]
            If specified, the new default notification level. Passing a raw int
            for this may lead to unexpected behaviour.
        explicit_content_filter : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildExplicitContentFilterLevel`, :obj:`~int` ]
            If specified, the new explicit content filter. Passing a raw int for
            this may lead to unexpected behaviour.
        afk_channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildVoiceChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID for the new AFK voice channel.
        afk_timeout : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~int` ]
            If specified, the new AFK timeout seconds timedelta.
        icon_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the new guild icon image file data.
        owner : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the new guild owner.
        splash_data : ``hikari.internal.conversions.FileLikeT``
            If specified, the new new splash image file data.
        system_channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildVoiceChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the new system channel.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.guilds.Guild`
            The edited guild object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = await self._session.modify_guild(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            name=name,
            region=getattr(region, "id", region) if region is not ... else ...,
            verification_level=verification_level,
            default_message_notifications=default_message_notifications,
            explicit_content_filter=explicit_content_filter,
            afk_timeout=afk_timeout.total_seconds() if isinstance(afk_timeout, datetime.timedelta) else afk_timeout,
            afk_channel_id=(
                str(afk_channel.id if isinstance(afk_channel, bases.UniqueEntity) else int(afk_channel))
                if afk_channel is not ...
                else ...
            ),
            icon=conversions.get_bytes_from_resource(icon_data) if icon_data is not ... else ...,
            owner_id=(
                str(owner.id if isinstance(owner, bases.UniqueEntity) else int(owner)) if owner is not ... else ...
            ),
            splash=conversions.get_bytes_from_resource(splash_data) if splash_data is not ... else ...,
            system_channel_id=(
                str(system_channel.id if isinstance(system_channel, bases.UniqueEntity) else int(system_channel))
                if system_channel is not ...
                else ...
            ),
            reason=reason,
        )
        return guilds.Guild.deserialize(payload)

    async def delete_guild(self, guild: bases.Hashable[guilds.Guild]) -> None:
        """Permanently deletes the given guild.

        You must be owner of the guild to perform this action.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to be deleted.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are not the guild owner.
        """
        await self._session.delete_guild(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )

    async def fetch_guild_channels(
        self, guild: bases.Hashable[guilds.Guild]
    ) -> typing.Sequence[_channels.GuildChannel]:
        """Get all the channels for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the channels from.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.channels.GuildChannel` ]
            A list of guild channel objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        payload = await self._session.list_guild_channels(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [_channels.deserialize_channel(channel) for channel in payload]

    async def create_guild_channel(
        self,
        guild: bases.Hashable[guilds.Guild],
        name: str,
        channel_type: typing.Union[_channels.ChannelType, int] = ...,
        position: int = ...,
        topic: str = ...,
        nsfw: bool = ...,
        rate_limit_per_user: typing.Union[datetime.timedelta, int] = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        permission_overwrites: typing.Sequence[_channels.PermissionOverwrite] = ...,
        parent_category: bases.Hashable[_channels.GuildCategory] = ...,
        reason: str = ...,
    ) -> _channels.GuildChannel:
        """Create a channel in a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to create the channel in.
        name : :obj:`~str`
            If specified, the name for the channel. This must be
            inclusively between ``1` and ``100`` characters in length.
        channel_type: :obj:`~typing.Union` [ :obj:`~hikari.channels.ChannelType`, :obj:`~int` ]
            If specified, the channel type, passing through a raw integer here
            may lead to unexpected behaviour.
        position : :obj:`~int`
            If specified, the position to change the channel to.
        topic : :obj:`~str`
            If specified, the topic to set. This is only applicable to
            text channels. This must be inclusively between ``0`` and ``1024``
            characters in length.
        nsfw : :obj:`~bool`
            If specified, whether the channel will be marked as NSFW.
            Only applicable for text channels.
        rate_limit_per_user : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~int` ]
            If specified, the second time delta the user has to wait before
            sending another message.  This will not apply to bots, or to
            members with ``MANAGE_MESSAGES`` or ``MANAGE_CHANNEL`` permissions.
            This must be inclusively between ``0`` and ``21600`` seconds.
        bitrate : :obj:`~int`
            If specified, the bitrate in bits per second allowable for the
            channel. This only applies to voice channels and must be inclusively
            between ``8000`` and ``96000`` for normal servers or ``8000`` and
            ``128000`` for VIP servers.
        user_limit : :obj:`~int`
            If specified, the max number of users to allow in a voice channel.
            This must be between ``0`` and ``99`` inclusive, where
            ``0`` implies no limit.
        permission_overwrites : :obj:`~typing.Sequence` [ :obj:`~hikari.channels.PermissionOverwrite` ]
            If specified, the list of permission overwrite objects that are
            category specific to replace the existing overwrites with.
        parent_category : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildCategory`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            If specified, the object or ID of the parent category to set for
             the channel.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.channels.GuildChannel`
            The newly created channel object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_CHANNEL`` permission or are not in the
            guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide incorrect options for the corresponding channel type
            (e.g. a ``bitrate`` for a text channel).
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild_channel(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            name=name,
            type_=channel_type,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=(
                int(rate_limit_per_user.total_seconds())
                if isinstance(rate_limit_per_user, datetime.timedelta)
                else rate_limit_per_user
            ),
            bitrate=bitrate,
            user_limit=user_limit,
            permission_overwrites=(
                [po.serialize() for po in permission_overwrites] if permission_overwrites is not ... else ...
            ),
            parent_id=(
                str(parent_category.id if isinstance(parent_category, bases.UniqueEntity) else int(parent_category))
                if parent_category is not ...
                else ...
            ),
            reason=reason,
        )
        return _channels.deserialize_channel(payload)

    async def reposition_guild_channels(
        self,
        guild: bases.Hashable[guilds.Guild],
        channel: typing.Tuple[int, bases.Hashable[_channels.GuildChannel]],
        *additional_channels: typing.Tuple[int, bases.Hashable[_channels.GuildChannel]],
    ) -> None:
        """Edits the position of one or more given channels.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild in which to edit the channels.
        channel : :obj:`~typing.Tuple` [ :obj:`~int` , :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            The first channel to change the position of. This is a tuple of the
            integer position the channel object or ID.
        *additional_channels : :obj:`~typing.Tuple` [ :obj:`~int`, :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            Optional additional channels to change the position of. These must
            be tuples of integer positions to change to and the channel object
            or ID and the.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or any of the channels aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_CHANNELS`` permission or are not a
            member of said guild or are not in the guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide anything other than the ``id`` and ``position``
            fields for the channels.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.modify_guild_channel_positions(
            str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            *[
                (str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)), position)
                for position, channel in [channel, *additional_channels]
            ],
        )

    async def fetch_member(
        self, guild: bases.Hashable[guilds.Guild], user: bases.Hashable[users.User],
    ) -> guilds.GuildMember:
        """Get a given guild member.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the member from.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the member to get.

        Returns
        -------
        :obj:`~hikari.guilds.GuildMember`
            The requested member object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the member aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you don't have access to the target guild.
        """
        payload = await self._session.get_guild_member(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
        )
        return guilds.GuildMember.deserialize(payload)

    def fetch_members_after(
        self,
        guild: bases.Hashable[guilds.Guild],
        *,
        after: typing.Union[datetime.datetime, bases.Hashable[users.User]] = 0,
        limit: typing.Optional[int] = None,
    ) -> typing.AsyncIterator[guilds.GuildMember]:
        """Get an async iterator of all the members in a given guild.

        This returns the member objects with a user object/ID that was created
        after the given user object/ID or from the member object or the oldest
        user.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the members from.
        limit : :obj:`~int`
            If specified, the maximum number of members this iterator
            should return.
        after : :obj:`~typing.Union` [ :obj:`~datetime.datetime`, :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the user this iterator should start
            after if specified, else this will start at the oldest user.

        Example
        -------
        .. code-block:: python

            async for user in client.fetch_members_after(guild, after=9876543, limit=1231):
                if member.user.username[0] in HOIST_BLACKLIST:
                    await client.update_member(member, nickname="💩")

        Returns
        -------
        :obj:`~typing.AsyncIterator` [ :obj:`~hikari.guilds.GuildMember` ]
            An async iterator of member objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        if isinstance(after, datetime.datetime):
            after = str(bases.Snowflake.from_datetime(after))
        else:
            after = str(after.id if isinstance(after, bases.UniqueEntity) else int(after))
        return pagination.pagination_handler(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            deserializer=guilds.GuildMember.deserialize,
            direction="after",
            request=self._session.list_guild_members,
            reversing=False,
            start=after,
            limit=limit,
            id_getter=_get_member_id,
        )

    async def update_member(
        self,
        guild: bases.Hashable[guilds.Guild],
        user: bases.Hashable[users.User],
        nickname: typing.Optional[str] = ...,
        roles: typing.Sequence[bases.Hashable[guilds.GuildRole]] = ...,
        mute: bool = ...,
        deaf: bool = ...,
        voice_channel: typing.Optional[bases.Hashable[_channels.GuildVoiceChannel]] = ...,
        reason: str = ...,
    ) -> None:
        """Edits a guild's member, any unspecified fields will not be changed.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to edit the member from.
        user : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildMember`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the member to edit.
        nickname : :obj:`~str`, optional
            If specified, the new nickname string. Setting it to :obj:`~None`
            explicitly will clear the nickname.
        roles : :obj:`~typing.Sequence` [ :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            If specified, a list of role IDs the member should have.
        mute : :obj:`~bool`
            If specified, whether the user should be muted in the voice channel
            or not.
        deaf : :obj:`~bool`
            If specified, whether the user should be deafen in the voice
            channel or not.
        voice_channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildVoiceChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], optional
            If specified, the ID of the channel to move the member to. Setting
            it to :obj:`~None` explicitly will disconnect the user.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild, user, channel or any of the roles aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack any of the applicable permissions
            (``MANAGE_NICKNAMES``, ``MANAGE_ROLES``, ``MUTE_MEMBERS``, ``DEAFEN_MEMBERS`` or ``MOVE_MEMBERS``).
            Note that to move a member you must also have permission to connect
            to the end channel. This will also be raised if you're not in the
            guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you pass ``mute``, ``deaf`` or ``channel_id`` while the member
            is not connected to a voice channel.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.modify_guild_member(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
            nick=nickname,
            roles=(
                [str(role.id if isinstance(role, bases.UniqueEntity) else int(role)) for role in roles]
                if roles is not ...
                else ...
            ),
            mute=mute,
            deaf=deaf,
            channel_id=(
                str(voice_channel.id if isinstance(voice_channel, bases.UniqueEntity) else int(voice_channel))
                if voice_channel is not ...
                else ...
            ),
            reason=reason,
        )

    async def update_my_member_nickname(
        self, guild: bases.Hashable[guilds.Guild], nickname: typing.Optional[str], *, reason: str = ...,
    ) -> None:
        """Edits the current user's nickname for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to change the nick on.
        nickname : :obj:`~str`, optional
            The new nick string. Setting this to `None` clears the nickname.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``CHANGE_NICKNAME`` permission or are not in the
            guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide a disallowed nickname, one that is too long, or one
            that is empty.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        await self._session.modify_current_user_nick(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            nick=nickname,
            reason=reason,
        )

    async def add_role_to_member(
        self,
        guild: bases.Hashable[guilds.Guild],
        user: bases.Hashable[users.User],
        role: bases.Hashable[guilds.GuildRole],
        *,
        reason: str = ...,
    ) -> None:
        """Add a role to a given member.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the member you want to add the role to.
        role : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the role you want to add.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild, member or role aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        await self._session.add_guild_member_role(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
            role_id=str(role.id if isinstance(role, bases.UniqueEntity) else int(role)),
            reason=reason,
        )

    async def remove_role_from_member(
        self,
        guild: bases.Hashable[guilds.Guild],
        user: bases.Hashable[users.User],
        role: bases.Hashable[guilds.GuildRole],
        *,
        reason: str = ...,
    ) -> None:
        """Remove a role from a given member.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the member you want to remove the role from.
        role : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the role you want to remove.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild, member or role aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        await self._session.remove_guild_member_role(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
            role_id=str(role.id if isinstance(role, bases.UniqueEntity) else int(role)),
            reason=reason,
        )

    async def kick_member(
        self, guild: bases.Hashable[guilds.Guild], user: bases.Hashable[users.User], *, reason: str = ...,
    ) -> None:
        """Kicks a user from a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the member you want to kick.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or member aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBERS`` permission or are not in the guild.
        """
        await self._session.remove_guild_member(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
            reason=reason,
        )

    async def fetch_ban(
        self, guild: bases.Hashable[guilds.Guild], user: bases.Hashable[users.User],
    ) -> guilds.GuildMemberBan:
        """Get a ban from a given guild.

        Parameters
        ----------
         guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to get the ban from.
         user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the user to get the ban information for.

        Returns
        -------
        :obj:`~hikari.guilds.GuildMemberBan`
            A ban object for the requested user.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the user aren't found, or if the user is not
            banned.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_ban(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
        )
        return guilds.GuildMemberBan.deserialize(payload)

    async def fetch_bans(self, guild: bases.Hashable[guilds.Guild],) -> typing.Sequence[guilds.GuildMemberBan]:
        """Get the bans for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to get the bans from.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.guilds.GuildMemberBan` ]
            A list of ban objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_bans(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [guilds.GuildMemberBan.deserialize(ban) for ban in payload]

    async def ban_member(
        self,
        guild: bases.Hashable[guilds.Guild],
        user: bases.Hashable[users.User],
        *,
        delete_message_days: typing.Union[datetime.timedelta, int] = ...,
        reason: str = ...,
    ) -> None:
        """Bans a user from a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild the member belongs to.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the member you want to ban.
        delete_message_days : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~int` ]
            If specified, the tim delta of how many days of messages from the
            user should be removed.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or member aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not in the guild.
        """
        await self._session.create_guild_ban(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
            delete_message_days=getattr(delete_message_days, "days", delete_message_days),
            reason=reason,
        )

    async def unban_member(
        self, guild: bases.Hashable[guilds.Guild], user: bases.Hashable[users.User], *, reason: str = ...,
    ) -> None:
        """Un-bans a user from a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to un-ban the user from.
        user : :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the user you want to un-ban.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or member aren't found, or the member is not
            banned.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``BAN_MEMBERS`` permission or are not a in the
            guild.
        """
        await self._session.remove_guild_ban(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            user_id=str(user.id if isinstance(user, bases.UniqueEntity) else int(user)),
            reason=reason,
        )

    async def fetch_roles(
        self, guild: bases.Hashable[guilds.Guild],
    ) -> typing.Mapping[bases.Snowflake, guilds.GuildRole]:
        """Get the roles for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to get the roles from.

        Returns
        -------
        :obj:`~typing.Mapping` [ :obj:`~hikari.entities.Snowflake`, :obj:`~hikari.guilds.GuildRole` ]
            A list of role objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you're not in the guild.
        """
        payload = await self._session.get_guild_roles(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return {role.id: role for role in map(guilds.GuildRole.deserialize, payload)}

    async def create_role(
        self,
        guild: bases.Hashable[guilds.Guild],
        *,
        name: str = ...,
        permissions: typing.Union[_permissions.Permission, int] = ...,
        color: typing.Union[colors.Color, int] = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        reason: str = ...,
    ) -> guilds.GuildRole:
        """Create a new role for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to create the role on.
        name : :obj:`~str`
            If specified, the new role name string.
        permissions : :obj:`~typing.Union` [ :obj:`~hikari.permissions.Permission`, :obj:`~int` ]
            If specified, the permissions integer for the role, passing a raw
            integer rather than the int flag may lead to unexpected results.
        color : :obj:`~typing.Union` [ :obj:`~hikari.colors.Color`, :obj:`~int` ]
            If specified, the color for the role.
        hoist : :obj:`~bool`
            If specified, whether the role will be hoisted.
        mentionable : :obj:`~bool`
           If specified, whether the role will be able to be mentioned by any
           user.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.guilds.GuildRole`
            The newly created role object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the
            guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the role attributes.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.create_guild_role(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            name=name,
            permissions=permissions,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            reason=reason,
        )
        return guilds.GuildRole.deserialize(payload)

    async def reposition_roles(
        self,
        guild: bases.Hashable[guilds.Guild],
        role: typing.Tuple[int, bases.Hashable[guilds.GuildRole]],
        *additional_roles: typing.Tuple[int, bases.Hashable[guilds.GuildRole]],
    ) -> typing.Sequence[guilds.GuildRole]:
        """Edits the position of two or more roles in a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the guild the roles belong to.
        role : :obj:`~typing.Tuple` [ :obj:`~int`, :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            The first role to move. This is a tuple of the integer position and
            the role object or ID.
        *additional_roles : :obj:`~typing.Tuple` [ :obj:`~int`, :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ]
            Optional extra roles to move. These must be tuples of the integer
            position and the role object or ID.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.guilds.GuildRole` ]
            A list of all the guild roles.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or any of the roles aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the
            guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the `position` fields.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_guild_role_positions(
            str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            *[
                (str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel)), position)
                for position, channel in [role, *additional_roles]
            ],
        )
        return [guilds.GuildRole.deserialize(role) for role in payload]

    async def update_role(
        self,
        guild: bases.Hashable[guilds.Guild],
        role: bases.Hashable[guilds.GuildRole],
        *,
        name: str = ...,
        permissions: typing.Union[_permissions.Permission, int] = ...,
        color: typing.Union[colors.Color, int] = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        reason: str = ...,
    ) -> guilds.GuildRole:
        """Edits a role in a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild the role belong to.
        role : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the role you want to edit.
        name : :obj:`~str`
            If specified, the new role's name string.
        permissions : :obj:`~typing.Union` [ :obj:`~hikari.permissions.Permission`, :obj:`~int` ]
            If specified, the new permissions integer for the role, passing a
            raw integer for this may lead to unexpected behaviour.
        color : :obj:`~typing.Union` [ :obj:`~hikari.colors.Color`, :obj:`~int` ]
            If specified, the new color for the new role passing a raw integer
            for this may lead to unexpected behaviour.
        hoist : :obj:`~bool`
            If specified, whether the role should hoist or not.
        mentionable : :obj:`~bool`
            If specified, whether the role should be mentionable or not.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.guilds.GuildRole`
            The edited role object.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or role aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or you're not in the
            guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the role attributes.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        payload = await self._session.modify_guild_role(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            role_id=str(role.id if isinstance(role, bases.UniqueEntity) else int(role)),
            name=name,
            permissions=permissions,
            color=color,
            hoist=hoist,
            mentionable=mentionable,
            reason=reason,
        )
        return guilds.GuildRole.deserialize(payload)

    async def delete_role(self, guild: bases.Hashable[guilds.Guild], role: bases.Hashable[guilds.GuildRole],) -> None:
        """Delete a role from a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to remove the role from.
        role : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the role you want to delete.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the role aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_ROLES`` permission or are not in the guild.
        """
        await self._session.delete_guild_role(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            role_id=str(role.id if isinstance(role, bases.UniqueEntity) else int(role)),
        )

    async def estimate_guild_prune_count(
        self, guild: bases.Hashable[guilds.Guild], days: typing.Union[datetime.timedelta, int],
    ) -> int:
        """Get the estimated prune count for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to get the count for.
        days : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~int` ]
            The time delta of days to count prune for (at least ``1``).

        Returns
        -------
        :obj:`~int`
            The number of members estimated to be pruned.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBERS`` or you are not in the guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you pass an invalid amount of days.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        return await self._session.get_guild_prune_count(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            days=getattr(days, "days", days),
        )

    async def begin_guild_prune(
        self,
        guild: bases.Hashable[guilds.Guild],
        days: typing.Union[datetime.timedelta, int],
        *,
        compute_prune_count: bool = ...,
        reason: str = ...,
    ) -> int:
        """Prunes members of a given guild based on the number of inactive days.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild you want to prune member of.
        days : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~int` ]
            The time delta of inactivity days you want to use as filter.
        compute_prune_count : :obj:`~bool`
            Whether a count of pruned members is returned or not.
            Discouraged for large guilds out of politeness.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~int`, optional
            The number of members who were kicked if ``compute_prune_count``
            is :obj:`~True`, else :obj:`~None`.

        Raises
        ------
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found:
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``KICK_MEMBER`` permission or are not in the guild.
        :obj:`~hikari.errors.BadRequestHTTPError`
            If you provide invalid values for the ``days`` or
            ``compute_prune_count`` fields.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        """
        return await self._session.begin_guild_prune(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            days=getattr(days, "days", days),
            compute_prune_count=compute_prune_count,
            reason=reason,
        )

    async def fetch_guild_voice_regions(
        self, guild: bases.Hashable[guilds.Guild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        """Get the voice regions for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the voice regions for.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.voices.VoiceRegion` ]
            A list of voice region objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you are not in the guild.
        """
        payload = await self._session.get_guild_voice_regions(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [voices.VoiceRegion.deserialize(region) for region in payload]

    async def fetch_guild_invites(
        self, guild: bases.Hashable[guilds.Guild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Get the invites for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the invites for.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.invites.InviteWithMetadata` ]
            A list of invite objects (with metadata).

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_invites(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [invites.InviteWithMetadata.deserialize(invite) for invite in payload]

    async def fetch_integrations(self, guild: bases.Hashable[guilds.Guild]) -> typing.Sequence[guilds.GuildIntegration]:
        """Get the integrations for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the integrations for.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.guilds.GuildIntegration` ]
            A list of integration objects.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        payload = await self._session.get_guild_integrations(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [guilds.GuildIntegration.deserialize(integration) for integration in payload]

    async def update_integration(
        self,
        guild: bases.Hashable[guilds.Guild],
        integration: bases.Hashable[guilds.GuildIntegration],
        *,
        expire_behaviour: typing.Union[guilds.IntegrationExpireBehaviour, int] = ...,
        expire_grace_period: typing.Union[datetime.timedelta, int] = ...,
        enable_emojis: bool = ...,
        reason: str = ...,
    ) -> None:
        """Edits an integrations for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to which the integration belongs to.
        integration : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildIntegration`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the integration to update.
        expire_behaviour : :obj:`~typing.Union` [ :obj:`~hikari.guilds.IntegrationExpireBehaviour`, :obj:`~int` ]
            If specified, the behaviour for when an integration subscription
            expires (passing a raw integer for this may lead to unexpected
            behaviour).
        expire_grace_period : :obj:`~typing.Union` [ :obj:`~datetime.timedelta`, :obj:`~int` ]
            If specified, time time delta of how many days the integration will
            ignore lapsed subscriptions for.
        enable_emojis : :obj:`~bool`
            If specified, whether emojis should be synced for this integration.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        await self._session.modify_guild_integration(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            integration_id=str(integration.id if isinstance(integration, bases.UniqueEntity) else int(integration)),
            expire_behaviour=expire_behaviour,
            expire_grace_period=getattr(expire_grace_period, "days", expire_grace_period),
            enable_emojis=enable_emojis,
            reason=reason,
        )

    async def delete_integration(
        self,
        guild: bases.Hashable[guilds.Guild],
        integration: bases.Hashable[guilds.GuildIntegration],
        *,
        reason: str = ...,
    ) -> None:
        """Delete an integration for the given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to which the integration belongs to.
        integration : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildIntegration`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the integration to delete.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        await self._session.delete_guild_integration(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            integration_id=str(integration.id if isinstance(integration, bases.UniqueEntity) else int(integration)),
            reason=reason,
        )

    async def sync_guild_integration(
        self, guild: bases.Hashable[guilds.Guild], integration: bases.Hashable[guilds.GuildIntegration],
    ) -> None:
        """Sync the given integration's subscribers/emojis.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to which the integration belongs to.
        integration : :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildIntegration`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The ID of the integration to sync.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If either the guild or the integration aren't found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you lack the ``MANAGE_GUILD`` permission or are not in the guild.
        """
        await self._session.sync_guild_integration(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            integration_id=str(integration.id if isinstance(integration, bases.UniqueEntity) else int(integration)),
        )

    async def fetch_guild_embed(self, guild: bases.Hashable[guilds.Guild],) -> guilds.GuildEmbed:
        """Get the embed for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the embed for.

        Returns
        -------
        :obj:`~hikari.guilds.GuildEmbed`
            A guild embed object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in
            the guild.
        """
        payload = await self._session.get_guild_embed(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return guilds.GuildEmbed.deserialize(payload)

    async def update_guild_embed(
        self,
        guild: bases.Hashable[guilds.Guild],
        *,
        channel: bases.Hashable[_channels.GuildChannel] = ...,
        enabled: bool = ...,
        reason: str = ...,
    ) -> guilds.GuildEmbed:
        """Edits the embed for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to edit the embed for.
        channel : :obj:`~typing.Union` [ :obj:`~hikari.channels.GuildChannel`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], optional
            If specified, the object or ID of the channel that this embed's
            invite should target. Set to :obj:`~None` to disable invites for this
            embed.
        enabled : :obj:`~bool`
            If specified, whether this embed should be enabled.
        reason : :obj:`~str`
            If specified, the audit log reason explaining why the operation
            was performed.

        Returns
        -------
        :obj:`~hikari.guilds.GuildEmbed`
            The updated embed object.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in
            the guild.
        """
        payload = await self._session.modify_guild_embed(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)),
            channel_id=(
                str(channel.id if isinstance(channel, bases.UniqueEntity) else int(channel))
                if channel is not ...
                else ...
            ),
            enabled=enabled,
            reason=reason,
        )
        return guilds.GuildEmbed.deserialize(payload)

    async def fetch_guild_vanity_url(self, guild: bases.Hashable[guilds.Guild],) -> invites.VanityUrl:
        """
        Get the vanity URL for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to get the vanity URL for.

        Returns
        -------
        :obj:`~hikari.invites.VanityUrl`
            A partial invite object containing the vanity URL in the ``code``
            field.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_GUILD`` permission or are not in
            the guild.
        """
        payload = await self._session.get_guild_vanity_url(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return invites.VanityUrl.deserialize(payload)

    def format_guild_widget_image(self, guild: bases.Hashable[guilds.Guild], *, style: str = ...) -> str:
        """Get the URL for a guild widget.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID of the guild to form the widget.
        style : :obj:`~str`
            If specified, the syle of the widget.

        Returns
        -------
        :obj:`~str`
            A URL to retrieve a PNG widget for your guild.

        Note
        ----
        This does not actually make any form of request, and shouldn't be
        awaited. Thus, it doesn't have rate limits either.

        Warning
        -------
        The guild must have the widget enabled in the guild settings for this
        to be valid.
        """
        return self._session.get_guild_widget_image_url(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild)), style=style
        )

    async def fetch_guild_webhooks(self, guild: bases.Hashable[guilds.Guild]) -> typing.Sequence[webhooks.Webhook]:
        """Get all webhooks for a given guild.

        Parameters
        ----------
        guild : :obj:`~typing.Union` [ :obj:`~hikari.guilds.Guild`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ]
            The object or ID for the guild to get the webhooks from.

        Returns
        -------
        :obj:`~typing.Sequence` [ :obj:`~hikari.webhooks.Webhook` ]
            A list of webhook objects for the given guild.

        Raises
        ------
        :obj:`~hikari.errors.BadRequestHTTPError`
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        :obj:`~hikari.errors.NotFoundHTTPError`
            If the guild is not found.
        :obj:`~hikari.errors.ForbiddenHTTPError`
            If you either lack the ``MANAGE_WEBHOOKS`` permission or
            aren't a member of the given guild.
        """
        payload = await self._session.get_guild_webhooks(
            guild_id=str(guild.id if isinstance(guild, bases.UniqueEntity) else int(guild))
        )
        return [webhooks.Webhook.deserialize(webhook) for webhook in payload]

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
"""Events that fire when Stage instances are created/updated/deleted."""

from __future__ import annotations

import abc
import typing

import attr

from hikari import channels, intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions
from hikari.stage_instances import StageInstance

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any event that involves Stage instances."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that relates to this event.
        """

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the channel that this event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the channel that relates to this event.
        """

    @property
    @abc.abstractmethod
    def stage_id(self) -> snowflakes.Snowflake:
        """ID of the stage instance that this event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the stage instance that this event relates to.
        """


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceCreateEvent(StageInstanceEvent):
    """Event fired when a Stage instance is created"""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    stage_instance: StageInstance = attr.field()
    """The Stage instance that was created."""

    @property
    def stage_id(self) -> snowflakes.Snowflake:
        return self.stage_instance.id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from StageInstanceEvent>>.
        return self.stage_instance.guild_id

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild where the Stage instance was created.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from StageInstanceEvent>>.

        return self.stage_instance.channel_id

    @property
    def channel(self) -> typing.Optional[channels.GuildStageChannel]:
        """Get the cached channel where the Stage instance was created.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.channels.GuildStageChannel]
            The channel that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.guild_id)
        assert isinstance(channel, channels.GuildStageChannel)
        return channel


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceEditEvent(StageInstanceEvent):
    """Event fired when a Stage instance is edited"""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    stage_instance: StageInstance = attr.field()
    """The Stage instance that was edited."""

    @property
    def stage_id(self) -> snowflakes.Snowflake:
        return self.stage_instance.id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from StageInstanceEvent>>.
        return self.stage_instance.guild_id

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild where the Stage instance was edited.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from StageInstanceEvent>>.
        return self.stage_instance.channel_id

    @property
    def channel(self) -> typing.Optional[channels.GuildStageChannel]:
        """Get the cached channel where the Stage instance was edited.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.channels.GuildStageChannel]
            The channel that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.guild_id)
        assert isinstance(channel, channels.GuildStageChannel)
        return channel


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceDeleteEvent(StageInstanceEvent):
    """Event fired when a Stage instance is deleted"""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    stage_instance: StageInstance = attr.field()
    """The Stage instance that was deleted."""

    @property
    def stage_id(self) -> snowflakes.Snowflake:
        return self.stage_instance.id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from StageInstanceEvent>>.
        return self.stage_instance.guild_id

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild where the Stage instance was deleted.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from StageInstanceEvent>>.
        return self.stage_instance.channel_id

    @property
    def channel(self) -> typing.Optional[channels.GuildStageChannel]:
        """Get the cached channel where the Stage instance was deleted.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.channels.GuildStageChannel]
            The channel that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.guild_id)
        assert isinstance(channel, channels.GuildStageChannel)
        return channel

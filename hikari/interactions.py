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
"""TODO: this"""

from __future__ import annotations

__all__: typing.List[str] = [
    "OptionType",
    "OptionValueT",
    "CommandChoice",
    "CommandOption",
    "Command",
    "InteractionType",
    "CommandInteractionData",
    "CommandInteractionOption",
    "CommandInteraction",
]

import typing

import attr

from hikari import guilds
from hikari import permissions as permissions_
from hikari import snowflakes
from hikari import traits
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import guilds
    from hikari import snowflakes


RawOptionValueT = typing.Union[str, int, bool]
OptionValueT = typing.Union[str, int, bool, snowflakes.Snowflake]


@typing.final
class OptionType(int, enums.Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    STR = STRING
    INTEGER = 4
    INT = INTEGER
    BOOLEAN = 5
    BOOL = BOOLEAN
    USER = 6
    CHANNEL = 7
    ROLE = 8


@typing.final
class InteractionType(int, enums.Enum):
    PING = 1
    APPLICATION_COMMAND = 2


@typing.final
class InteractionResponseType(int, enums.Enum):
    PONG = 1
    ACKNOWLEDGE = 2
    CHANNEL_MESSAGE = 3
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    ACKNOWLEDGE_WITH_SOURCE = 5


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandChoice:
    name: str = attr.ib(eq=True, hash=False, repr=True)
    value: RawOptionValueT = attr.ib(eq=True, hash=False, repr=True)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandOption:
    type: typing.Union[OptionType, int] = attr.ib(eq=True, hash=False, repr=True)
    name: str = attr.ib(eq=True, hash=False, repr=True)
    description: str = attr.ib(eq=True, hash=False, repr=False)
    is_first: bool = attr.ib(eq=True, hash=False, repr=True)
    is_required: bool = attr.ib(eq=True, hash=False, repr=False)
    choices: typing.Optional[typing.Sequence[CommandChoice]] = attr.ib(eq=True, hash=False, repr=False)
    options: typing.Optional[typing.Sequence[CommandOption]] = attr.ib(eq=True, hash=False, repr=False)


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Command(snowflakes.Unique):
    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    application_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)

    name: str = attr.ib(eq=False, hash=False, repr=True)

    description: str = attr.ib(eq=False, hash=False, repr=False)

    options: typing.Optional[typing.Sequence[CommandOption]] = attr.ib(eq=False, hash=False, repr=False)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteractionOption:
    name: str = attr.ib(eq=True, hash=False, repr=True)
    value: typing.Optional[typing.Sequence[RawOptionValueT]] = attr.ib(eq=True, hash=False, repr=True)
    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.ib(eq=True, hash=False, repr=True)


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteractionData(snowflakes.Unique):
    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.ib(eq=False, hash=False, repr=True)

    options: typing.Optional[typing.Sequence[CommandInteractionOption]] = attr.ib(eq=True, hash=False, repr=True)


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class InteractionMember(guilds.Member):
    permissions: permissions_.Permissions = attr.ib(eq=False, hash=False, repr=True)


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PartialInteraction(snowflakes.Unique):
    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    type: typing.Union[InteractionType, int] = attr.ib(eq=False, hash=False, repr=True)

    token: str = attr.ib(eq=False, hash=False, repr=False)

    version: int = attr.ib(eq=False, hash=False, repr=True)


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class CommandInteraction(PartialInteraction):
    data: typing.Optional[CommandInteractionData] = attr.ib(eq=False, hash=False, repr=False)

    channel_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)

    guild_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)

    member: InteractionMember = attr.ib(eq=False, hash=False, repr=True)

    async def fetch_channel(self) -> channels.PartialChannel:
        return await self.app.rest.fetch_channel(self.channel_id)

    async def fetch_guild(self) -> guilds.RESTGuild:
        return await self.app.rest.fetch_guild(self.guild_id)

    def get_channel(self) -> typing.Optional[channels.PartialChannel]:
        if isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_guild_channel(self.channel_id)

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        if isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_guild(self.guild_id)

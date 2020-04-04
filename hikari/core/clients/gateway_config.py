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
"""Gateway and sharding configuration objects and options."""
__all__ = ["GatewayConfig", "ShardConfig"]

import datetime
import re
import typing

import hikari.internal.conversions
from hikari.internal import assertions
from hikari.internal import marshaller
from hikari.core import entities
from hikari.core import gateway_entities
from hikari.core import guilds
from hikari.core.clients import protocol_config
from hikari.net import codes as net_codes


def _parse_shard_info(payload):
    range_matcher = re.search(r"(\d+)\s*(\.{2,3})\s*(\d+)", payload)

    if not range_matcher:
        if isinstance(payload, str):
            payload = int(payload)

        if isinstance(payload, int):
            return [payload]

        raise ValueError('expected shard_ids to be one of int, list of int, or range string ("x..y")')

    minimum, range_mod, maximum = range_matcher.groups()
    minimum, maximum = int(minimum), int(maximum)
    if len(range_mod) == 3:
        maximum += 1

    return [*range(minimum, maximum)]


@marshaller.attrs(kw_only=True, init=False)
class ShardConfig(entities.HikariEntity, entities.Deserializable):
    """Manual sharding configuration.

    All fields are optional kwargs that can be passed to the constructor.

    "Deserialized" and "unspecified" defaults are only applicable if you
    create the object using :meth:`deserialize`.
    """

    #: The shard IDs to produce shard connections for.
    #:
    #: If being deserialized, this can be several formats.
    #:     ``12``, ``"12"``:
    #:         A specific shard ID.
    #:     ``[0, 1, 2, 3, 8, 9, 10]``, ``["0", "1", "2", "3", "8", "9", "10"]``:
    #:         A sequence of shard IDs.
    #:     ``"5..16"``:
    #:         A range string. Two periods indicate a range of ``[5, 16)``
    #:         (inclusive beginning, exclusive end).
    #:     ``"5...16"``:
    #:         A range string. Three periods indicate a range of
    #:         ``[5, 17]`` (inclusive beginning, inclusive end).
    #:     ``None``:
    #:         The ``shard_count`` will be considered and that many shards will
    #:         be created for you.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`int` ]
    shard_ids: typing.Sequence[int] = marshaller.attrib(
        deserializer=_parse_shard_info, if_none=None, if_undefined=None,
    )

    #: The number of shards the entire distributed application should consist
    #: of. If you run multiple instances of the bot, you should ensure this
    #: value is consistent.
    #:
    #: :type: :obj:`int`
    shard_count: int = marshaller.attrib(deserializer=int)

    # noinspection PyMissingConstructor
    def __init__(self, *, shard_ids: typing.Optional[typing.Iterable[int]] = None, shard_count: int) -> None:
        self.shard_ids = [*shard_ids] if shard_ids else [*range(shard_count)]

        for shard_id in self.shard_ids:
            assertions.assert_that(shard_id < shard_count, "shard_count must be greater than any shard ids")

        self.shard_count = shard_count


@marshaller.attrs(kw_only=True)
class GatewayConfig(entities.HikariEntity, entities.Deserializable):
    """Gateway and sharding configuration.

    All fields are optional kwargs that can be passed to the constructor.

    "Deserialized" and "unspecified" defaults are only applicable if you
    create the object using :meth:`deserialize`.
    """

    #: Whether to enable debugging mode for the generated shards. Usually you
    #: don't want to enable this.
    #:
    #: :type: :obj:`bool`
    debug: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)

    #: The initial activity to set all shards to when starting the gateway. If
    #: ``None``, then no activity will be set.
    #:
    #: :type: :obj:`hikari.core.gateway_entities.GatewayActivity`, optional
    initial_activity: typing.Optional[gateway_entities.GatewayActivity] = marshaller.attrib(
        deserializer=gateway_entities.GatewayActivity.deserialize, if_none=None, if_undefined=None, default=None
    )

    #: The initial status to set the shards to when starting the gateway.
    #:
    #: :type: :obj:`str`
    initial_status: guilds.PresenceStatus = marshaller.attrib(
        deserializer=guilds.PresenceStatus.__getitem__, if_undefined=lambda: "online", default="online",
    )

    #: Whether to show up as AFK or not on sign-in.
    #:
    #: :type: :obj:`bool`
    initial_is_afk: bool = marshaller.attrib(deserializer=bool, if_undefined=False, default=False)

    #: The idle time to show on signing in, or ``None`` to not show an idle
    #: time.
    #:
    #: :type: :obj:`datetime.datetime`, optional
    initial_idle_since: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=hikari.internal.conversions.unix_epoch_to_ts, if_none=None, if_undefined=None, default=None
    )

    #: The intents to use for the connection.
    #:
    #: If being deserialized, this can be an integer bitfield, or a sequence of
    #: intent names. If
    #: unspecified, this will be set to ``None``.
    #:
    #: :type: :obj:`hikari.net.codes.GatewayIntent`, optional
    #:
    #: Examples
    #: --------
    #:
    #: .. code-block:: python
    #:
    #:    # Python example
    #:    GatewayIntent.GUILDS | GatewayIntent.GUILD_MESSAGES
    #:
    #: ..code-block:: js
    #:
    #:    // JSON example, using explicit bitfield values
    #:    513
    #:    // JSON example, using an array of names
    #:    [ "GUILDS", "GUILD_MESSAGES" ]
    #:
    #: See :obj:`hikari.net.codes.GatewayIntent` for valid names of
    #: intents you can use. Integer values are as documented on Discord's
    #: developer portal.
    #:
    #: Warnings
    #: --------
    #: If you are using the V7 gateway implementation, you will NEED to provide
    #: explicit intent values for this field in order to get online.
    #: Additionally, intents that are classed by Discord as being privileged
    #: will require you to whitelist your application in order to use them.
    #:
    #: If you are using the V6 gateway implementation, setting this to ``None``
    #: will simply opt you into every event you can subscribe to.
    intents: typing.Optional[net_codes.GatewayIntent] = marshaller.attrib(
        deserializer=lambda value: marshaller.dereference_int_flag(net_codes.GatewayIntent, value),
        if_undefined=None,
        default=None,
    )

    #: The large threshold to use.
    large_threshold: int = marshaller.attrib(deserializer=int, if_undefined=lambda: 250, default=True)

    #: Low level protocol details, such as proxy configuration and SSL settings.
    #:
    #: This is only used while creating the HTTP connection that the websocket
    #: is upgraded from.
    #:
    #: If unspecified, defaults are used.
    #:
    #: :type: :obj:`hikari.core.protocol_config.HTTPProtocolConfig`
    protocol: typing.Optional[protocol_config.HTTPProtocolConfig] = marshaller.attrib(
        deserializer=protocol_config.HTTPProtocolConfig.deserialize, if_undefined=None, default=None,
    )

    #: Manual sharding configuration to use. If this is ``None``, or
    #: unspecified, then auto sharding configuration will be performed for you
    #: based on defaults suggested by Discord.
    #:
    #: :type: :obj:`ShardConfig`, optional
    shard_config: typing.Optional[ShardConfig] = marshaller.attrib(
        deserializer=ShardConfig.deserialize, if_undefined=None, default=None,
    )

    #: The token to use, if applicable.
    #:
    #: If ``None`` or not specified, whatever is in the global token field on
    #: the config will be used. Note that you will have to specify this value
    #: somewhere; you will not be able to connect without it.
    #:
    #: :type: :obj:`str`, optional
    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, if_undefined=None, default=None)

    #: Whether to use zlib compression on the gateway for inbound messages or
    #: not. Usually you want this turned on.
    #:
    #: :type: :obj:`bool`
    use_compression: bool = marshaller.attrib(deserializer=bool, if_undefined=True, default=True)

    #: The gateway API version to use.
    #:
    #: If unspecified, then V6 is used.
    #:
    #: :type: :obj:`int`
    version: int = marshaller.attrib(deserializer=int, if_undefined=lambda: 6, default=6)

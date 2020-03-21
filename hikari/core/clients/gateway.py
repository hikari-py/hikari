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
import typing

from hikari.internal_utilities import marshaller


@marshaller.attrs()
class GatewayActivity:
    #: The activity name.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str, serializer=str)

    #: The activity url. Only valid for ``STREAMING`` activities.
    #:
    #: :type: :obj:`str`, optional
    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_none=None, if_undefined=None)

    # TODO: implement enum for this.
    #: The activity type.
    #:
    #: :type: :obj:`int`
    type: int = marshaller.attrib(deserializer=int, serializer=int, if_undefined=0)


@marshaller.attrs()
class GatewayConfig:
    #: Whether to enable debugging mode for the generated shards. Usually you
    #: don't want to enable this.
    #:
    #: :type: :obj:`bool`
    debug: bool = marshaller.attrib(deserializer=bool, if_undefined=False)

    #: The initial activity to set all shards to when starting the gateway. If
    #: ``None``, then no activity will be set.
    #:
    #: :type: :obj:`GatewayActivity`
    initial_activity: typing.Optional[GatewayActivity] = marshaller.attrib(
        deserializer=bool, if_none=None, if_undefined=None
    )

    # TODO: implement enum for this
    #: The initial status to set the shards to when starting the gateway.
    #:
    #: :type: :obj:`str`
    initial_status: str = marshaller.attrib(deserializer=str, if_undefined="online")

    #: Whether to use zlib compression on the gateway for inbound messages or
    #: not. Usually you want this turned on.
    #:
    #: :type: :obj:`bool`
    use_compression: bool = marshaller.attrib(deserializer=bool, if_undefined=True)


class Gateway:
    def __init__(self, gateway_config: GatewayConfig):
        pass

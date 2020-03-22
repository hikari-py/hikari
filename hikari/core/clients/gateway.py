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

from hikari.core import entities
from hikari.internal_utilities import marshaller


@marshaller.attrs()
class GatewayActivity(entities.Deserializable):
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

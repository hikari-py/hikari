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
"""HTTP (REST) API configuration objects and options."""

__all__ = ["HTTPConfig"]

import typing

from hikari.core import entities
from hikari.core.configs import protocol as protocol_
from hikari.internal_utilities import marshaller


@marshaller.attrs(kw_only=True)
class HTTPConfig(entities.Deserializable):
    """HTTP API configuration.

    All fields are optional kwargs that can be passed to the constructor.

    "Deserialized" and "unspecified" defaults are only applicable if you
    create the object using :meth:`deserialize`.
    """

    #: Low level protocol details, such as proxy configuration and SSL settings.
    #:
    #: If unspecified, defaults are used.
    #:
    #: :type: :obj:`hikari.core.configs.protocol.HTTPProtocolConfig`
    protocol: typing.Optional[protocol_.HTTPProtocolConfig] = marshaller.attrib(
        deserializer=protocol_.HTTPProtocolConfig.deserialize, if_undefined=None, default=None,
    )

    #: The token to use, if applicable.
    #:
    #: Note that this should not start with ``Bot`` or ``Bearer``. This is
    #: detected automatically.
    #:
    #: If ``None`` or not specified, whatever is in the global token field on
    #: the config will be used.
    #:
    #: :type: :obj:`str`, optional
    token: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, if_undefined=None, default=None)

    #: The HTTP API version to use.
    #:
    #: If unspecified, then V7 is used.
    #:
    #: :type: :obj:`int`
    version: int = marshaller.attrib(deserializer=int, if_undefined=lambda: 7, default=7)

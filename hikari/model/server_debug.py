#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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

from __future__ import annotations

__all__ = ("DataCenter", "DebugData")

import datetime
import dataclasses


@dataclasses.dataclass()
class DataCenter:
    """Represents a data center. These are represented by an IATA airport code."""

    __slots__ = ("iata_code", "location", "airport", "country")

    #: Airport code
    iata_code: str
    #: Data center location
    location: str
    #: Data center airport name
    airport: str
    #: Data center country
    country: str

    def __str__(self):
        return f"{self.airport} ({self.iata_code}), {self.location}, {self.country}"


@dataclasses.dataclass()
class DebugData:
    """The response provided from Discord's CGI trace."""

    __slots__ = ("fl", "ip", "ts", "h", "visit_scheme", "uag", "colo", "http", "loc", "tls", "sni", "warp")

    #: Unknown, possibly some form of correlation ID.
    fl: str
    #: Your IP
    ip: str
    #: UTC unix timestamp.
    ts: datetime.datetime
    #: The host that was hit.
    h: str
    #: Scheme used
    visit_scheme: str
    #: User agent used
    uag: str
    #: Data Center info.
    colo: DataCenter
    #: HTTP version used.
    http: str
    #: Apparent location
    loc: str
    #: TLS/SSL version used.
    tls: str
    #: Unknown, possibly the content type of this response.
    sni: str
    #: Unknown.
    warp: str

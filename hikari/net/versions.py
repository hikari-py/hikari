#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""API version enumeration."""
__all__ = ["HTTPAPIVersion", "GatewayVersion"]

import enum


class HTTPAPIVersion(enum.IntEnum):
    """Supported versions for the REST API."""

    #: The V6 API. This is currently the stable release that should be used unless you have a reason
    #: to use V7 otherwise.
    V6 = 6

    #: Development API version. This is not documented at the time of writing, and is subject to
    #: change at any time without warning.
    V7 = 7

    #: The recommended stable API release to default to.
    STABLE = V6


class GatewayVersion(enum.IntEnum):
    """Supported versions for the Gateway."""

    #: The V6 API. This is currently the stable release that should be used unless you have a reason
    #: to use V7 otherwise.
    V6 = 6

    #: Development API version. This is not documented at the time of writing, and is subject to
    #: change at any time without warning.
    V7 = 7

    #: The recommended stable API release to default to.
    STABLE = V6

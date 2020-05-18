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
from __future__ import annotations

__all__ = ["IBot"]

import abc

from hikari.api import gateway_dispatcher
from hikari.api import gateway_zookeeper
from hikari.api import rest_app


class IBot(rest_app.IRESTApp, gateway_zookeeper.IGatewayZookeeper, gateway_dispatcher.IGatewayDispatcher, abc.ABC):
    """Component for single-process bots.

    Bots are components that have access to a REST API, an event dispatcher,
    and an event consumer.

    Additionally, bots will contain a collection of Gateway client objects.
    """

    __slots__ = ()

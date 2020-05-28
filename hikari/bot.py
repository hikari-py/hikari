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

from hikari import app as app_
from hikari import http_settings as http_settings_


class IBot(app_.IRESTApp, app_.IGatewayZookeeper, app_.IGatewayDispatcher, abc.ABC):
    """Component for single-process bots.

    Bots are components that have access to a REST API, an event dispatcher,
    and an event consumer.

    Additionally, bots will contain a collection of Gateway client objects.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def http_settings(self) -> http_settings_.HTTPSettings:
        """The HTTP settings to use."""

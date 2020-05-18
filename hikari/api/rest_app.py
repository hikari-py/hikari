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

__all__ = ["IRESTApp"]

import abc

from hikari.api import base_app
from hikari.rest import client


class IRESTApp(base_app.IBaseApp, abc.ABC):
    """Component specialization that is used for REST-only applications.

    Examples may include web dashboards, or applications where no gateway
    connection is required. As a result, no event conduit is provided by
    these implementations.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def rest(self) -> client.RESTClient:
        """REST API."""

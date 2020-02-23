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
"""
The Hikari Object Relational Model.

This provides an object-oriented interface to the Discord API, and provides features
such as the ability to cache certain objects and details that the API provides us, as
well as providing an expandable and extendable interface to wrap them together in.

The ORM is separated into several domains of components. This is done to allow
you to easily write new components if this library does not fit your use case.
"""
from hikari.orm import client
from hikari.orm import client_options
from hikari.orm import fabric
from hikari.orm import gateway
from hikari.orm import http
from hikari.orm import models
from hikari.orm import state
from hikari.orm.gateway import event_types

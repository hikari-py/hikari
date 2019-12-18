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
"""
from hikari.orm import chunker
from hikari.orm import chunker_impl
from hikari.orm import dispatching_event_adapter
from hikari.orm import dispatching_event_adapter_impl
from hikari.orm import event_handler
from hikari.orm import events
from hikari.orm import fabric
from hikari.orm import http_adapter
from hikari.orm import models
from hikari.orm import state_registry
from hikari.orm import state_registry_impl

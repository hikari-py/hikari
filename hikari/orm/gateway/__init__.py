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
Contains all components required to interact with the gateway implementation
provided in :mod:`hikari.net.gateway`. This includes parsers of incoming events
from dicts and lists to objects, as well as chunker handlers.
"""
from hikari.orm.gateway import base_chunker
from hikari.orm.gateway import base_event_handler
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.gateway import chunk_mode
from hikari.orm.gateway import dispatching_event_adapter
from hikari.orm.gateway import dispatching_event_adapter_impl

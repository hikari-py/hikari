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
"""Provides the internal framework for processing the lifetime of a bot.

The API for this part of the framework has been split into groups of
abstract base classes, and corresponding implementations. This allows
several key components to be implemented separately, in case you have a
specific use case you want to provide (such as placing stuff on a message
queue if you distribute your bot).

The overall structure is as follows:

.. inheritance-diagram::
    hikari.state.event_dispatcher
    hikari.state.raw_event_consumer
    hikari.state.event_manager
    hikari.state.stateless_event_manager_impl
"""
__all__ = []

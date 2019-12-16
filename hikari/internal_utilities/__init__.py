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
"""
Various utilities used internally within this API. These are not bound to the versioning contact, and are considered
to be implementation detail that could change at any time, so should not be used outside this library.
"""
from hikari.internal_utilities import assertions
from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.internal_utilities import delegate
from hikari.internal_utilities import io_helpers
from hikari.internal_utilities import logging_helpers
from hikari.internal_utilities import meta
from hikari.internal_utilities import transformations
from hikari.internal_utilities import unspecified
from hikari.internal_utilities import user_agent

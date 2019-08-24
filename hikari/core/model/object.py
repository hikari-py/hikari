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
import copy
import typing

from hikari.core.model import base


@base.dataclass()
class PartialObject(base.Snowflake):
    """
    Representation of a partially constructed object. This may be returned by some components instead of a correctly
    initialized object if information is not available.

    Any other attributes that were provided with this object are accessible by using dot-notation as normal, but will
    not be documented here and should not be relied on. Your mileage may vary.
    """

    __slots__ = ("id", "_other_attrs")

    #: The ID of this object.
    id: int
    _other_attrs: typing.Dict[str, typing.Any]

    @staticmethod
    def from_dict(payload):
        payload = copy.copy(payload)
        return PartialObject(id=int(payload.pop("id")), _other_attrs=payload)

    def __getattr__(self, item):
        return self._other_attrs[item]

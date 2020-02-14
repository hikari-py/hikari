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
Other useful typehints that are uncategorised.
"""
import typing

from hikari.internal_utilities import unspecified

T = typing.TypeVar("T")

#: This can be considered the same as :class:`typing.Optional`, which is a value that can be
#: optionally set to `None`. We distinguish between `None` and not specifying something at all
#: when it is a default argument in several places, so this has been redefined with a clearer name.
Nullable = typing.Optional

#: A special type hint for an argument that can take the value of
#: :attr:`hikari.internal_utilities.unspecified.UNSPECIFIED`. This often defines a value that unless
#: explicitly changed, should be treated as if it is not there at all. This is used to distinguish
#: this case from a value being specified explicitly as `None`.
NotRequired = typing.Union[T, unspecified.Unspecified]

#: Shorthand for :attr:`Nullable` AND :attr:`NotRequired`.
NullableNotRequired = typing.Union[T, None, unspecified.Unspecified]

__all__ = ["Nullable", "NotRequired", "NullableNotRequired"]
JSONObject = typing.MutableMapping[str, typing.Any]
JSONArray = typing.Sequence[typing.Any]
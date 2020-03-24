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
"""Datastructure bases."""
__all__ = ["HikariEntity", "Serializable", "Deserializable", "RawEntityT", "UNSET"]

import abc
import typing

from hikari.internal_utilities import marshaller
from hikari.internal_utilities import singleton_meta


RawEntityT = typing.Union[
    None, bool, int, float, str, bytes, typing.Sequence[typing.Any], typing.Mapping[str, typing.Any]
]

T_contra = typing.TypeVar("T_contra", contravariant=True)
T_co = typing.TypeVar("T_co", covariant=True)


class Unset(metaclass=singleton_meta.SingletonMeta):
    def __bool__(self):
        return False

    def __repr__(self):
        return type(self).__name__.upper()

    __str__ = __repr__


#: A variable used for certain update events where a field being unset will
#: mean that it's not being acted on, mostly just seen attached to event models.
UNSET = Unset()


@marshaller.attrs(slots=True)
class HikariEntity(metaclass=abc.ABCMeta):
    """The base for any entity used in this API."""

    __slots__ = ()


class Deserializable:
    """A mixin for any type that allows deserialization from a raw value
    into a Hikari entity.
    """

    __slots__ = ()

    @classmethod
    def deserialize(cls: typing.Type[T_contra], payload: RawEntityT) -> T_contra:
        return marshaller.HIKARI_ENTITY_MARSHALLER.deserialize(payload, cls)


class Serializable:
    """A mixin for any type that allows serialization from a Hikari entity
    into a raw value.
    """

    __slots__ = ()

    def serialize(self: T_co) -> RawEntityT:
        return marshaller.HIKARI_ENTITY_MARSHALLER.serialize(self)

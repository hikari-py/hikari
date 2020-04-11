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

import attr

from hikari.internal import marshaller
from hikari.internal import meta

RawEntityT = typing.Union[
    None, bool, int, float, str, bytes, typing.Sequence[typing.Any], typing.Mapping[str, typing.Any]
]

T_contra = typing.TypeVar("T_contra", contravariant=True)
T_co = typing.TypeVar("T_co", covariant=True)


class Unset(metaclass=meta.SingletonMeta):
    """A singleton value that represents an unset field."""

    def __bool__(self):
        return False

    def __repr__(self):
        return type(self).__name__.upper()

    __str__ = __repr__


#: A variable used for certain update events where a field being unset will
#: mean that it's not being acted on, mostly just seen attached to event models.
UNSET = Unset()


@marshaller.marshallable()
@attr.s(slots=True)
class HikariEntity(metaclass=abc.ABCMeta):
    """The base for any entity used in this API."""


class Deserializable:
    """Mixin that enables the class to be deserialized from a raw entity."""

    __slots__ = ()

    @classmethod
    def deserialize(cls: typing.Type[T_contra], payload: RawEntityT) -> T_contra:
        """Deserialize the given payload into the object.

        Parameters
        ----------
        payload
            The payload to deserialize into the object.
        """
        return marshaller.HIKARI_ENTITY_MARSHALLER.deserialize(payload, cls)


class Serializable:
    """Mixin that enables an instance of the class to be serialized."""

    __slots__ = ()

    def serialize(self: T_co) -> RawEntityT:
        """Serialize this instance into a naive value."""
        return marshaller.HIKARI_ENTITY_MARSHALLER.serialize(self)

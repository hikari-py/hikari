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
__all__ = ["HikariEntity", "ISerializable", "IDeserializable", "RawEntityT"]

import abc
import typing

import attr

RawEntityT = typing.Union[
    None, bool, int, float, str, bytes, typing.Sequence[typing.Any], typing.Mapping[str, typing.Any]
]

T_contra = typing.TypeVar("T_contra", contravariant=True)
T_co = typing.TypeVar("T_co", covariant=True)


@attr.s(slots=True)
class HikariEntity(metaclass=abc.ABCMeta):
    """The base for any entity used in this API."""

    __slots__ = ()


class IDeserializable(typing.Protocol):
    """An interface for any type that allows deserialization from a raw value
    into a Hikari entity.
    """

    @classmethod
    def deserialize(cls: typing.Type[T_contra], payload: RawEntityT) -> T_contra:
        ...


class ISerializable(typing.Protocol):
    """An interface for any type that allows serialization from a Hikari entity
    into a raw value.
    """

    def serialize(self: T_co) -> RawEntityT:
        ...

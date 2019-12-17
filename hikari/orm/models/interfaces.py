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
Model ABCs and mixins.
"""
from __future__ import annotations

import abc
import copy
import datetime
import typing

from hikari.internal_utilities import assertions
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.orm import fabric

T = typing.TypeVar("T")
U = typing.TypeVar("U")


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class BestEffortEnumMixin:
    """
    An enum interface extension that allows for trying to get a parsed value or falling back to the original input.
    """

    __slots__ = ()

    @classmethod
    def get_best_effort_from_name(cls: typing.Type[T], value: U) -> typing.Union[T, U]:
        """Attempt to parse the given value into an enum instance, or if failing, return the input value."""
        try:
            return cls[value]
        except KeyError:
            return value

    @classmethod
    def get_best_effort_from_value(cls: typing.Type[T], value: U) -> typing.Union[T, U]:
        """Attempt to parse the given value into an enum instance, or if failing, return the input value."""
        try:
            return cls(value)
        except ValueError:
            return value

    def __str__(self):
        return self.name

    __repr__ = __str__


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class INamedEnum:
    """
    A mixin for an enum that is produced from a string by Discord. This ensures that the key can be looked up from a
    lowercase value that discord provides and use a Pythonic key name that is in upper case.
    """

    __slots__ = ()

    @classmethod
    def from_discord_name(cls, name: str):
        """
        Consume a string as described on the Discord API documentation and return a member of this enum, or
        raise a :class:`KeyError` if the name is invalid.
        """
        return cls[name.upper()]

    def __str__(self):
        return self.name

    __repr__ = __str__


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class IModel(metaclass=abc.ABCMeta):
    """
    Base type for any model in this API.

    Provides several key functionalities such as the ability to control how internal references get
    copied if :meth:`copy`ing this object.

    If you need some fields to be copied across by reference regardless of being requested to produce a new copy, you
    should specify their names in the `__copy_byref__` class var. This will prevent :func:`copy.copy` being
    invoked on them when duplicating the object to produce a before and after view when a change is made.

    Warning:
        Copy functionality on this base is only implemented for slotted derived classes.
    """

    __slots__ = ()

    #: We want a fast way of knowing all the slotted fields instances of this subclass may provide without heavy
    #: recursive introspection every time an update event occurs and we need to create a shallow one-level-deep copy
    #: of the object.
    __all_slots__ = ()

    #: Tracks the fields we shouldn't clone. This always includes the state.
    __copy_by_ref__: typing.ClassVar[typing.Tuple] = ("_fabric",)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        if "__slots__" not in cls.__dict__:
            raise TypeError(f"{cls.__module__}.{cls.__qualname__} must be slotted to derive from {IModel.__name__}.")

        is_interface = kwargs.get("interface", False)

        # If an interface and has no `__init__`, then inject a dummy constructor that is abstract to make
        # the class into an ABC.
        if is_interface and "__init__" not in cls.__dict__:

            @abc.abstractmethod
            def __init__(_self, *init_args, **init_kwargs):
                super().__init__(*init_args, **init_kwargs)

            setattr(cls, "__init__", __init__)

        assertions.assert_subclasses(type(cls.__slots__), tuple, "__slots__ should be a tuple")

        copy_by_ref = set()
        slots = set()

        for base in cls.mro():
            next_slots = getattr(base, "__slots__", data_structures.EMPTY_COLLECTION)
            next_refs = getattr(base, "__copy_by_ref__", data_structures.EMPTY_COLLECTION)
            for ref in next_refs:
                copy_by_ref.add(ref)
            for slot in next_slots:
                slots.add(slot)

        cls.__copy_by_ref__ = tuple(copy_by_ref)
        cls.__all_slots__ = tuple(slots)

    def copy(self, copy_func=copy.copy):
        """
        Create a copy of this object.

        Return:
            the copy of this object.
        """
        # Make a new instance without the internal attributes.
        cls = type(self)

        # Calls the base initialization function for the given object to allocate the initial empty shell. We usually
        # would use this if we overrode `__new__`. Unlike using `__reduce_ex__` and `__reduce__`, this does not invoke
        # pickle, so should be much more efficient than pickling and unpickling to get an empty object.
        # This also ensures all methods are referenced, but no instance variables get bound, which is just what we need.

        # noinspection PySuperArguments
        instance = super(IModel, cls).__new__(cls)

        for attr in cls.__all_slots__:
            attr_val = getattr(self, attr)
            if attr in self.__copy_by_ref__:
                setattr(instance, attr, attr_val)
            else:
                setattr(instance, attr, copy_func(attr_val))

        return instance

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        """
        Updates the internal state of an existing instance of this object from a raw Discord payload.
        """
        return NotImplemented


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class ISnowflake(IModel):
    """
    Mixin type for any type that specifies an ID. The implementation is expected to implement that
    field.

    Warning:
         Inheriting this class injects a `__hash__` that will operate on the `id` attribute.

    Note:
         Any derivative of this class becomes fully comparable and sortable due to implementing
         the comparison operators `<`, `<=`, `>=`, and `>`. These operators will operate on the
         `id` field.

    Warning:
         This implementation will respect the assumption for any good Python model that the
         behaviour of `__eq__` and the behaviour of `__hash__` should be as close as possible.
         Thus, the `__eq__` operation will be overridden to implement comparison that returns true
         if and only if the classes for both implementations being compared are exactly the same
         and if their IDs both match directly, unless a custom `__hash__` has also been provided.
    """

    __slots__ = ()

    #: The ID of this object.
    #:
    #: :type: :class:`int`
    id: int

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self.id >> 22
        return date_helpers.discord_epoch_to_datetime(epoch)

    @property
    def internal_worker_id(self) -> int:
        """The internal worker ID that created this object on Discord."""
        return (self.id & 0x3E0_000) >> 17

    @property
    def internal_process_id(self) -> int:
        """The internal process ID that created this object on Discord."""
        return (self.id & 0x1F_000) >> 12

    @property
    def increment(self) -> int:
        """The increment of Discord's system when this object was made."""
        return self.id & 0xFFF

    def __lt__(self, other) -> bool:
        if not isinstance(other, ISnowflake):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id < other.id

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __gt__(self, other) -> bool:
        if not isinstance(other, ISnowflake):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id > other.id

    def __ge__(self, other) -> bool:
        return self > other or self == other

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return type(self) == type(other) and self.id == other.id

    def __ne__(self, other) -> bool:
        return not self == other

    def __int__(self) -> int:
        return self.id


class UnknownObject(ISnowflake):
    """
    Represents an unresolved object with an ID that we cannot currently make sense of, or that
    may be only partially complete.

    This usually should not be returned for bots using a gateway with a valid cache. However, if
    the cache is incomplete, or you are using a static HTTP client only, this will likely occur
    regularly within models. The way to resolve these is to manually call the HTTP endpoint to fetch
    the correct details.

    This can also be used as a placeholder for objects you do not currently have a full copy of.
    """
    __slots__ = ("id",)

    def __init__(self, id: int) -> None:
        self.id = id


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class IStatefulModel(IModel):
    """
    Base information and utilities for any model that is expected to have a reference to a `_fabric`.

    Each implementation is expected to provide a `_fabric` slot and implement a constructor that
    sets that slot where appropriate.
    """

    #: Since this is a mixin, all slots must be empty. This prevents issues from subclassing other slotted classes
    #: and then mixing in this one later.
    __slots__ = ()

    #: The base fabric for the ORM instance.
    _fabric: fabric.Fabric

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        is_interface_or_mixin = kwargs.get("interface", False)
        delegate_fabricated = kwargs.get("delegate_fabricated", False)
        has_fabric_slot = len(cls.__all_slots__) > 0 and "_fabric" in cls.__all_slots__

        if not (is_interface_or_mixin or delegate_fabricated or has_fabric_slot):
            raise TypeError(
                f"{cls.__module__}.{cls.__qualname__} derives from {IStatefulModel.__name__}, "
                f"but does not provide '_fabric' as a slotted member in this or any base classes. "
                f"If this is meant to be an interface, pass the 'interface' or 'delegate_fabricated' "
                f"kwarg to the class constructor (e.g. `class Foo(Fabricated, interface=True)`) to "
                f"suppress this error."
            )


#: The valid types of a raw unformatted snowflake.
RawSnowflakeT = typing.Union[int, str]

#: A raw snowflake type or an :class:`ISnowflake` instance.
SnowflakeLikeT = typing.Union[RawSnowflakeT, ISnowflake, UnknownObject]


__all__ = [
    "ISnowflake",
    "BestEffortEnumMixin",
    "INamedEnum",
    "IStatefulModel",
    "IModel",
    "RawSnowflakeT",
    "SnowflakeLikeT",
]

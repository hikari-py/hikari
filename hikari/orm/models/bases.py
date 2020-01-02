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
import asyncio
import copy
import dataclasses
import datetime
import enum
import typing

from hikari.internal_utilities import assertions
from hikari.internal_utilities import compat
from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.orm import fabric

T = typing.TypeVar("T")
U = typing.TypeVar("U")


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
        #  We only want this to default to the value for non-int based enums.
        return self.name.lower() if isinstance(self, int) else self.value


class NamedEnumMixin(BestEffortEnumMixin):
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
        return self.name.lower()


class BaseModel(metaclass=abc.ABCMeta):
    """
    Base type for any model in this API.

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
            raise TypeError(f"{cls.__module__}.{cls.__qualname__} must be slotted to derive from {BaseModel.__name__}.")

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
            next_slots = getattr(base, "__slots__", containers.EMPTY_COLLECTION)
            next_refs = getattr(base, "__copy_by_ref__", containers.EMPTY_COLLECTION)
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
        instance = super(BaseModel, cls).__new__(cls)

        for attr in cls.__all_slots__:
            attr_val = getattr(self, attr)
            if attr in self.__copy_by_ref__:
                setattr(instance, attr, attr_val)
            else:
                setattr(instance, attr, copy_func(attr_val))

        return instance

    def update_state(self, payload: containers.JSONObject) -> None:
        """
        Updates the internal state of an existing instance of this object from a raw Discord payload.
        """
        return NotImplemented


class SnowflakeMixin:
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
    def is_resolved(self) -> bool:
        """
        Returns False if the object represents an uncached placeholder for an element that needs to
        be fetched manually from the API. For all well formed models, this is always going to be True.
        """
        return True

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self.id >> 22
        return dates.discord_epoch_to_datetime(epoch)

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
        if not isinstance(other, SnowflakeMixin):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id < other.id

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __gt__(self, other) -> bool:
        if not isinstance(other, SnowflakeMixin):
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


class BaseModelWithFabric(BaseModel):
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
                f"{cls.__module__}.{cls.__qualname__} derives from {BaseModelWithFabric.__name__}, "
                f"but does not provide '_fabric' as a slotted member in this or any base classes. "
                f"If this is meant to be an interface, pass the 'interface' or 'delegate_fabricated' "
                f"kwarg to the class constructor (e.g. `class Foo(Fabricated, interface=True)`) to "
                f"suppress this error."
            )


class UnknownObject(typing.Generic[T], SnowflakeMixin):
    """
    Represents an unresolved object with an ID that we cannot currently make sense of, or that
    may be only partially complete.

    This usually should not be returned for bots using a gateway with a valid cache. However, if
    the cache is incomplete, or you are using a static HTTP client only, this will likely occur
    regularly within models. The way to resolve these is to manually call the HTTP endpoint to fetch
    the correct details, or to await the object, which acts as a lazy call to the HTTP endpoint you'd
    usually want to call manually.

    You should never need to initialize this yourself.

    Example usage:
        >>> # Assuming we have no gateway running and are only using the HTTP API on its own.
        >>> channel = await http.fetch_channel(1234)
        >>> guild = channel.guild if channel.guild.is_resolved else await channel.guild
        >>> assert channel.guild.is_resolved   # the channel's guild should now also be resolved
    """

    __slots__ = ("id", "_future", "_callbacks", "__weakref__")

    _CALLBACK_MUX_ALREADY_CALLED = ...

    def __init__(self, id: int, resolver_partial: containers.PartialCoroutineProtocolT[T] = None,) -> None:
        self.id = id
        self._future = resolver_partial
        self._callbacks = []

    # noinspection PyCallingNonCallable
    def __await__(self) -> T:
        if self._future is None:
            raise NotImplementedError("Cannot resolve this value currently")
        if not isinstance(self._future, asyncio.Future):
            # noinspection PyUnresolvedReferences
            self._future = compat.asyncio.create_task(
                self._future(), name=f"executing {self._future.func.__name__} on UnknownObject with ID {self.id}"
            )
            self._future.add_done_callback(self._invoke_callbacks)

        yield from self._future
        return self._future.result()

    def _invoke_callbacks(self, completed_task) -> None:
        # A callback multiplexer mechanism.
        result = completed_task.result()
        for callback in self._callbacks:
            callback(result)
        self._callbacks = self._CALLBACK_MUX_ALREADY_CALLED

    def add_done_callback(self, callback: typing.Callable[[T], typing.Any]) -> None:
        """
        Store the given callback and execute it once this UnknownObject has been awaited
        for the first time. This is scheduled as a callback on a multiplexer for the
        underlying asyncio task that is created.

        If the object has already been awaited, this is scheduled to be executed
        as soon as possible on the event loop instead.

        Warning:
            It is important to note that these callbacks get scheduled on the
            current asyncio eventloop. This means you must not do blocking work
            in these calls. Consider delegating to a
            :class:`concurrent.futures.Executor` implementation instead in this
            scenario.

        Args:
            callback:
                A normal function taking the resolved value to replace this object
                with as the sole argument.
        """
        if self._callbacks is self._CALLBACK_MUX_ALREADY_CALLED:
            asyncio.get_running_loop().call_soon(callback, self._future.result())
        else:
            self._callbacks.append(callback)

    @property
    def is_resolved(self) -> bool:
        """
        Returns False always.
        """
        return False


DictImplT = typing.TypeVar("DictImplT", typing.Dict, dict)
DictFactoryT = typing.Union[typing.Type[DictImplT], typing.Callable[[], DictImplT]]


class DictFactory(dict):
    """
    A dictionary factory used for ensuring that values like enums and models are returned in a serializable format.
    """

    def __init__(self, seq=None, **kwargs) -> None:
        kwargs.update(seq or containers.EMPTY_SEQUENCE)
        super().__init__((key, self._convert(value)) for key, value in kwargs.items() if value is not None)

    def __setitem__(self, key, item) -> None:
        super().__setitem__(key, self._convert(item))

    @classmethod
    def _convert(cls, value: typing.Any) -> typing.Any:
        """Try to convert a value, and return the result or original value."""
        if isinstance(value, MarshalMixin):
            value = value.to_dict(dict_factory=cls)
        #  This should cover all int based enums.
        elif isinstance(value, int):
            value = int(value)
        elif isinstance(value, NamedEnumMixin):
            value = str(value)
        elif isinstance(value, enum.Enum):
            value = value.value

        return value


class MarshalMixin:
    """
    A mixin used for making serializable models.

    Note:
        Any model inheriting from this will need to be decorated with :func:`dataclasses.dataclass` with a dataclass
         styled `__init__`.
    """

    __slots__ = ()

    def to_dict(self, *, dict_factory: DictFactoryT = DictFactory) -> DictImplT:
        """Get a dictionary of the the values held by the current object."""
        return dict_factory((a, getattr(self, a)) for a in self.__slots__)

    # noinspection PyArgumentList,PyDataclass
    @classmethod
    def from_dict(cls, payload: containers.JSONObject):
        """Initialise the current model from a Discord payload."""
        return cls(**{field.name: payload.get(field.name) for field in dataclasses.fields(cls)})


#: The valid types of a raw unformatted snowflake.
RawSnowflakeT = typing.Union[int, str]

#: A raw snowflake type or an :class:`ISnowflake` instance.
SnowflakeLikeT = typing.Union[RawSnowflakeT, SnowflakeMixin, UnknownObject]

__all__ = [
    "SnowflakeMixin",
    "BestEffortEnumMixin",
    "NamedEnumMixin",
    "BaseModelWithFabric",
    "BaseModel",
    "RawSnowflakeT",
    "SnowflakeLikeT",
    "DictFactory",
    "MarshalMixin",
    "DictImplT",
    "DictFactoryT",
]

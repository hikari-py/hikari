# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Implementation of parts of Python's `enum` protocol to be more performant."""
from __future__ import annotations

__all__: typing.List[str] = ["Enum", "Flag"]

import functools
import operator
import sys
import types
import typing

_T = typing.TypeVar("_T")
_MAX_CACHED_MEMBERS: typing.Final[int] = 1 << 12


class _EnumNamespace(typing.Dict[str, typing.Any]):
    __slots__: typing.Sequence[str] = ("base", "names_to_values", "values_to_names")

    def __init__(self, base: typing.Type[typing.Any]) -> None:
        super().__init__()
        self.base = base
        self.names_to_values: typing.Dict[str, typing.Any] = {}
        self.values_to_names: typing.Dict[str, typing.Any] = {}
        self["__doc__"] = "An enumeration."

    def __getitem__(self, name: str) -> typing.Any:
        try:
            return super().__getitem__(name)
        except KeyError:
            try:
                return self.names_to_values[name]
            except KeyError:
                raise KeyError(name) from None

    def __setitem__(self, name: str, value: typing.Any) -> None:
        if name == "" or name == "mro":
            raise TypeError(f"Invalid enum member name: {name!r}")

        if name.startswith("_"):
            # Dunder/sunder, so skip.
            super().__setitem__(name, value)
            return

        if hasattr(value, "__get__") or hasattr(value, "__set__") or hasattr(value, "__del__"):
            super().__setitem__(name, value)
            return

        if not isinstance(value, self.base):
            raise TypeError(f"Expected member {name} to be of type {self.base.__name__} but was {type(value).__name__}")

        name = sys.intern(name)

        if issubclass(self.base, str):
            value = sys.intern(value)
        else:
            try:
                # This will fail if unhashable.
                hash(value)
            except TypeError:
                raise TypeError(f"Cannot have unhashable values in this enum type ({name}: {value!r})") from None

        if name in self.names_to_values:
            raise TypeError("Cannot define same name twice")
        if value in self.values_to_names:
            # We must have defined some alias, so just register the name
            self.names_to_values[name] = value
            return

        self.names_to_values[name] = value
        self.values_to_names[value] = name


# We refer to these from the metaclasses, but obviously this won't work
# until these classes are created, and since they use the metaclasses as
# a base metaclass, we have to give these values for _EnumMeta to not
# flake out when initializing them.
_Enum = NotImplemented


class _EnumMeta(type):
    def __call__(cls, value: typing.Any) -> typing.Any:
        try:
            return cls._value_to_member_map_[value]
        except KeyError:
            # If we cant find the value, just return what got casted in
            return value

    def __getitem__(cls, name: str) -> typing.Any:
        return cls._name_to_member_map_[name]

    def __contains__(cls, item: typing.Any) -> bool:
        return item in cls._value_to_member_map_

    def __iter__(cls) -> typing.Iterator[typing.Any]:
        yield from cls._name_to_member_map_.values()

    @staticmethod
    def __new__(
        mcs: typing.Type[_T],
        name: str,
        bases: typing.Tuple[typing.Type[typing.Any], ...],
        namespace: typing.Union[typing.Dict[str, typing.Any], _EnumNamespace],
    ) -> _T:
        global _Enum

        if _Enum is NotImplemented:
            # noinspection PyRedundantParentheses
            return (_Enum := super().__new__(mcs, name, bases, namespace))

        assert isinstance(namespace, _EnumNamespace)

        base, enum_type = bases

        new_namespace = {
            "__objtype__": base,
            "__enumtype__": enum_type,
            "_name_to_member_map_": (name_to_member := {}),
            "_value_to_member_map_": (value_to_member := {}),
            "_member_names_": (member_names := []),
            # Required to be immutable by enum API itself.
            "__members__": types.MappingProxyType(namespace.names_to_values),
            **namespace,
            **{
                name: value
                for name, value in Enum.__dict__.items()
                if name not in ("__class__", "__module__", "__doc__")
            },
        }

        cls = super().__new__(mcs, name, bases, new_namespace)

        for name, value in namespace.names_to_values.items():
            # Patching the member init call is around 100ns faster per call than
            # using the default type.__call__ which would make us do the lookup
            # in cls.__new__. Reason for this is that python will also always
            # invoke cls.__init__ if we do this, so we end up with two function
            # calls.
            member = cls.__new__(cls, value)
            member._name_ = name
            member._value_ = value
            name_to_member[name] = member
            value_to_member[value] = member
            member_names.append(name)
            setattr(cls, name, member)

        return cls

    @classmethod
    def __prepare__(
        mcs, name: str, bases: typing.Tuple[typing.Type[typing.Any], ...] = ()
    ) -> typing.Union[typing.Dict[str, typing.Any], _EnumNamespace]:
        if _Enum is NotImplemented:
            if name != "Enum":
                raise TypeError("First instance of _EnumMeta must be Enum")
            return _EnumNamespace(object)

        try:
            # Fails if Enum is not defined. We check this in `__new__` properly.
            base, enum_type = bases

            if isinstance(base, _EnumMeta):
                raise TypeError("First base to an enum must be the type to combine with, not _EnumMeta")

            return _EnumNamespace(base)
        except ValueError:
            raise TypeError("Expected exactly two base classes for an enum") from None

    def __repr__(cls) -> str:
        return f"<enum {cls.__name__}>"

    __str__ = __repr__


class Enum(metaclass=_EnumMeta):
    """Clone of Python's `enum.Enum` implementation.

    This is designed to be faster and more efficient than Python's
    implementation, while retaining the majority of the external interface
    that Python's `enum.Enum` provides.

    An `Enum` is a simple class containing a discrete set of constant values
    that can be used in place of this type. This acts as a type-safe way
    of representing a set number of "things".

    !!! warning
        Some semantics such as subtype checking and instance checking may
        differ. It is recommended to compare these values using the
        `==` operator rather than the `is` operator for safety reasons.

    Special Members on the class
    ----------------------------
    * `__enumtype__` :
        Always `Enum`.
    * `__members__` :
        An immutable `typing.Mapping` that maps each member name to the member
        value.
    * ` __objtype__` :
        Always the first type that the enum is derived from. For example:

    ```py
    >>> class UserType(str, Enum):
    ...     USER = "user"
    ...     PARTIAL = "partial"
    ...     MEMBER = "member"
    >>> print(UserType.__objtype__)
    <class 'builtins.str'>
    ```

    Operators on the class
    ----------------------
    * `EnumType["FOO"]` :
        Return the member that has the name `FOO`, raising a `builtins.KeyError`
        if it is not present.
    * `EnumType.FOO` :
        Return the member that has the name `FOO`, raising a
        `builtins.AttributeError` if it is not present.
    * `EnumType(x)` :
        Attempt to cast `x` to the enum type by finding an existing member that
        has the same __value__. If this fails, you should expect a
        `builtins.ValueError` to be raised.

    Operators on each enum member
    -----------------------------
    * `e1 == e2` : `builtins.bool`
        Compare equality.
    * `e1 != e2` : `builtins.bool`
        Compare inequality.
    * `builtins.repr(e)` : `builtins.str`
        Get the machine readable representation of the enum member `e`.
    * `builtins.str(e)` : `builtins.str`
        Get the `builtins.str` name of the enum member `e`.

    Special properties on each enum member
    --------------------------------------
    * `name` : `builtins.str`
        The name of the member.
    * `value` :
        The value of the member. The type depends on the implementation type
        of the enum you are using.

    All other methods and operators on enum members are inherited from the
    member's __value__. For example, an enum extending `builtins.int` would
    be able to be used as an `int` type outside these overridden definitions.
    """

    _name_to_member_map_: typing.Final[typing.ClassVar[typing.Mapping[str, Enum]]]
    _value_to_member_map_: typing.Final[typing.ClassVar[typing.Mapping[int, Enum]]]
    _member_names_: typing.Final[typing.ClassVar[typing.Sequence[str]]]
    __members__: typing.Final[typing.ClassVar[typing.Mapping[str, Enum]]]
    __objtype__: typing.Final[typing.ClassVar[typing.Type[typing.Any]]]
    __enumtype__: typing.Final[typing.ClassVar[typing.Type[Enum]]]
    _name_: typing.Final[str]
    _value_: typing.Final[typing.Any]

    @property
    def name(self) -> str:
        """Return the name of the enum member as a `builtins.str`."""
        return self._name_

    @property
    @typing.no_type_check
    def value(self):
        """Return the value of the enum member."""
        return self._value_

    def __repr__(self) -> str:
        return f"<{type(self).__name__}.{self._name_}: {self._value_!r}>"

    def __str__(self) -> str:
        return self._name_ or "NO_NAME"


_Flag = NotImplemented


def _name_resolver(members: typing.Dict[int, _Flag], value: int) -> typing.Generator[str, typing.Any, None]:
    bit = 1
    has_yielded = False
    remaining = value
    while bit <= value:
        if member := members.get(bit):
            # Use ._value_ to prevent overhead of making new members each time.
            # Also lets my testing logic for the cache size be more accurate.
            if member._value_ & remaining == member._value_:
                remaining ^= member._value_
                yield member.name
                has_yielded = True
        bit <<= 1

    if not has_yielded:
        yield f"UNKNOWN 0x{value:x}"
    elif remaining:
        yield hex(remaining)


class _FlagMeta(type):
    def __call__(cls, value: typing.Any = 0) -> typing.Any:
        try:
            return cls._value_to_member_map_[value]
        except KeyError:
            # We only need this ability here usually, so overloading operators
            # is an overkill and would add more overhead.

            if value < 0:
                # Convert to a positive value instead.
                return cls.__everything__ - ~value

            temp_members = cls._temp_members_
            # For huge enums, don't ever cache anything. We could consume masses of memory otherwise
            # (e.g. Permissions)
            try:
                # Try to get a cached value.
                return temp_members[value]
            except KeyError:
                # If we cant find the value, just return what got casted in by generating a pseudomember
                # and caching it. We cant use weakref because int is not weak referenceable, annoyingly.
                # TODO: make the cache update thread-safe by using setdefault instead of assignment.
                pseudomember = cls.__new__(cls, value)
                temp_members[value] = pseudomember
                pseudomember._name_ = None
                pseudomember._value_ = value
                if len(temp_members) > _MAX_CACHED_MEMBERS:
                    temp_members.popitem()

                return pseudomember

    def __getitem__(cls, name: str) -> typing.Any:
        return cls._name_to_member_map_[name]

    def __iter__(cls) -> typing.Iterator[typing.Any]:
        yield from cls._name_to_member_map_.values()

    @classmethod
    def __prepare__(
        mcs, name: str, bases: typing.Tuple[typing.Type[typing.Any], ...] = ()
    ) -> typing.Union[typing.Dict[str, typing.Any], _EnumNamespace]:
        if _Flag is NotImplemented:
            if name != "Flag":
                raise TypeError("First instance of _FlagMeta must be Flag")
            return _EnumNamespace(object)

        # Fails if Flag is not defined.
        if len(bases) == 1 and bases[0] == Flag:
            return _EnumNamespace(int)
        raise TypeError("Cannot define another Flag base type")

    @staticmethod
    def __new__(
        mcs: typing.Type[_T],
        name: str,
        bases: typing.Tuple[typing.Type[typing.Any], ...],
        namespace: typing.Union[typing.Dict[str, typing.Any], _EnumNamespace],
    ) -> _T:
        global _Flag

        if _Flag is NotImplemented:
            # noinspection PyRedundantParentheses
            return (_Flag := super().__new__(mcs, name, bases, namespace))

        assert isinstance(namespace, _EnumNamespace)
        new_namespace = {
            "__objtype__": int,
            "__enumtype__": _Flag,
            "_name_to_member_map_": (name_to_member := {}),
            "_value_to_member_map_": (value_to_member := {}),
            "_powers_of_2_to_member_map_": (powers_of_2_map := {}),
            # We cant weakref, as we inherit from int. Turns out that is significantly
            # slower anyway, so it isn't important for now. We just manually limit
            # the cache size.
            # This also randomly ends up with a 0 value in it at the start
            # during the next for loop. I cannot work out for the life of me
            # why this happens.
            "_temp_members_": {},
            "_member_names_": (member_names := []),
            # Required to be immutable by enum API itself.
            "__members__": types.MappingProxyType(namespace.names_to_values),
            **namespace,
            # This copies over all methods, including operator overloads. This
            # has the effect of making pdoc aware of any methods or properties
            # we defined on Flag.
            **{
                name: value
                for name, value in Flag.__dict__.items()
                if name not in ("__class__", "__module__", "__doc__")
            },
        }

        cls = super().__new__(mcs, name, (int, *bases), new_namespace)

        for name, value in namespace.names_to_values.items():
            # Patching the member init call is around 100ns faster per call than
            # using the default type.__call__ which would make us do the lookup
            # in cls.__new__. Reason for this is that python will also always
            # invoke cls.__init__ if we do this, so we end up with two function
            # calls.
            member = cls.__new__(cls, value)
            member._name_ = name
            member._value_ = value
            name_to_member[name] = member
            value_to_member[value] = member
            member_names.append(name)
            setattr(cls, name, member)

            if not (value & value - 1):
                powers_of_2_map[value] = member

        all_bits = functools.reduce(operator.or_, value_to_member.keys())
        all_bits_member = cls.__new__(cls, all_bits)
        all_bits_member._name_ = None
        all_bits_member._value_ = all_bits
        setattr(cls, "__everything__", all_bits_member)

        return cls

    def __repr__(cls) -> str:
        return f"<enum {cls.__name__}>"

    __str__ = __repr__


class Flag(metaclass=_FlagMeta):
    """Clone of Python's `enum.Flag` implementation.

    This is designed to be faster and more efficient than Python's
    implementation, while retaining the majority of the external interface
    that Python's `enum.Flag` provides.

    In simple terms, an `Flag` is a set of wrapped constant `builtins.int`
    values that can be combined in any combination to make a special value.
    This is a more efficient way of combining things like permissions together
    into a single integral value, and works by setting individual `1`s and `0`s
    on the binary representation of the integer.

    This implementation has extra features, in that it will actively behave
    like a `builtins.set` as well.

    !!! warning
        Despite wrapping `builtins.int` values, conceptually this does not
        behave as if it were a subclass of `int`.

    !!! danger
        Some semantics such as subtype checking and instance checking may
        differ. It is recommended to compare these values using the
        `==` operator rather than the `is` operator for safety reasons.

        Especially where pseudo-members created from combinations are cached,
        results of using of `is` may not be deterministic. This is a side
        effect of some internal performance improvements.

        Failing to observe this __will__ result in unexpected behaviour
        occurring in your application!

    Special Members on the class
    ----------------------------
    * `__enumtype__` :
        Always `Flag`.
    * `__everything__` :
        A special member with all documented bits set.
    * `__members__` :
        An immutable `typing.Mapping` that maps each member name to the member
        value.
    * ` __objtype__` :
        Always `builtins.int`.

    Operators on the class
    ----------------------
    * `FlagType["FOO"]` :
        Return the member that has the name `FOO`, raising a `builtins.KeyError`
        if it is not present.
    * `FlagType.FOO` :
        Return the member that has the name `FOO`, raising a
        `builtins.AttributeError` if it is not present.
    * `FlagType(x)` :
        Attempt to cast `x` to the enum type by finding an existing member that
        has the same __value__. If this fails, then a special __composite__
        instance of the type is made. The name of this type is a combination of
        all members that combine to make the bitwise value.

    Operators on each flag member
    -----------------------------
    * `e1 & e2` :
        Bitwise `AND` operation. Will return a member that contains all flags
        that are common between both oprands on the values. This also works with
        one of the oprands being an `builtins.int`eger. You may instead use
        the `intersection` method.
    * `e1 | e2` :
        Bitwise `OR` operation. Will return a member that contains all flags
        that appear on at least one of the oprands. This also works with
        one of the oprands being an `builtins.int`eger. You may instead use
        the `union` method.
    * `e1 ^ e2` :
        Bitwise `XOR` operation. Will return a member that contains all flags
        that only appear on at least one and at most one of the oprands.
        This also works with one of the oprands being an `builtins.int`eger.
        You may instead use the `symmetric_difference` method.
    * `~e` :
        Return the inverse of this value. This is equivalent to disabling all
        flags that are set on this value and enabling all flags that are
        not set on this value. Note that this will behave slightly differently
        to inverting a pure int value. You may instead use the `invert` method.
    * `e1 - e2` :
        Bitwise set difference operation. Returns all flags set on `e1` that are
        not set on `e2` as well. You may instead use the `difference`
        method.
    * `bool(e)` : `builtins.bool`
        Return `builtins.True` if `e` has a non-zero value, otherwise
        `builtins.False`.
    * `E.A in e`: `builtins.bool`
        `builtins.True` if `E.A` is in `e`. This is functionally equivalent
        to `E.A & e == E.A`.
    * `iter(e)` :
        Explode the value into a iterator of each __documented__ flag that can
        be combined to make up the value `e`. Returns an iterator across all
        well-defined flags that make up this value. This will only include the
        flags explicitly defined on this `Flag` type and that are individual
        powers of two (this means if converted to twos-compliment binary,
        exactly one bit must be a `1`). In simple terms, this means that you
        should not expect combination flags to be returned.
    * `e1 == e2` : `builtins.bool`
        Compare equality.
    * `e1 != e2` : `builtins.bool`
        Compare inequality.
    * `e1 < e2` : `builtins.bool`
        Compare by ordering.
    * `builtins.int(e)` : `builtins.int`
        Get the integer value of this flag
    * `builtins.repr(e)` : `builtins.str`
        Get the machine readable representation of the flag member `e`.
    * `builtins.str(e)` : `builtins.str`
        Get the `builtins.str` name of the flag member `e`.

    Special properties on each flag member
    --------------------------------------
    * `e.name` : `builtins.str`
        The name of the member. For composite members, this will be generated.
    * `e.value` : `builtins.int`
        The value of the member.

    Special members on each flag member
    -----------------------------------
    * `e.all(E.A, E.B, E.C, ...)` : `builtins.bool`
        Returns `builtins.True` if __all__ of `E.A`, `E.B`, `E.C`, et cetera
        make up the value of `e`.
    * `e.any(E.A, E.B, E.C, ...)` : `builtins.bool`
        Returns `builtins.True` if __any__ of `E.A`, `E.B`, `E.C`, et cetera
        make up the value of `e`.
    * `e.none(E.A, E.B, E.C, ...)` : `builtins.bool`
        Returns `builtins.True` if __none__ of `E.A`, `E.B`, `E.C`, et cetera
        make up the value of `e`.
    * `e.split()` : `typing.Sequence`
        Explode the value into a sequence of each __documented__ flag that can
        be combined to make up the value `e`. Returns a sorted sequence of each
        power-of-two flag that makes up the value `e`. This is equivalent to
        `list(iter(e))`.

    All other methods and operators on `Flag` members are inherited from the
    member's __value__.

    !!! note
        Due to limitations around how this is re-implemented, this class is not
        considered a subclass of `Enum` at runtime, even if MyPy believes this
        is possible
    """

    _name_to_member_map_: typing.Final[typing.ClassVar[typing.Mapping[str, Flag]]]
    _value_to_member_map_: typing.Final[typing.ClassVar[typing.Mapping[int, Flag]]]
    _powers_of_2_to_member_map_: typing.Final[typing.ClassVar[typing.Mapping[int, Flag]]]
    _temp_members_: typing.Final[typing.ClassVar[typing.Mapping[int, Flag]]]
    _member_names_: typing.Final[typing.ClassVar[typing.Sequence[str]]]
    __members__: typing.Final[typing.ClassVar[typing.Mapping[str, Flag]]]
    __objtype__: typing.Final[typing.ClassVar[typing.Type[int]]]
    __enumtype__: typing.Final[typing.ClassVar[typing.Type[Flag]]]
    _name_: typing.Final[str]
    _value_: typing.Final[int]

    @property
    def name(self) -> str:
        """Return the name of the flag combination as a `builtins.str`."""
        if self._name_ is None:
            self._name_ = "|".join(_name_resolver(self._value_to_member_map_, self._value_))
        return self._name_

    @property
    def value(self) -> int:
        """Return the `builtins.int` value of the flag."""
        return self._value_

    def all(self: _T, *flags: _T) -> bool:
        """Check if all of the given flags are part of this value.

        Returns
        -------
        builtins.bool
            `builtins.True` if any of the given flags are part of this value.
            Otherwise, return `builtins.False`.
        """
        return all((flag & self) == flag for flag in flags)

    def any(self: _T, *flags: _T) -> bool:
        """Check if any of the given flags are part of this value.

        Returns
        -------
        builtins.bool
            `builtins.True` if any of the given flags are part of this value.
            Otherwise, return `builtins.False`.
        """
        return any((flag & self) == flag for flag in flags)

    def difference(self: _T, other: typing.Union[_T, int]) -> _T:
        """Perform a set difference with the other set.

        This will return all flags in this set that are not in the other value.

        Equivalent to using the subtraction `-` operator.
        """
        return self.__class__(self & ~int(other))

    def intersection(self: _T, other: typing.Union[_T, int]) -> _T:
        """Return a combination of flags that are set for both given values.

        Equivalent to using the "AND" `&` operator.
        """
        return self.__class__(self._value_ & int(other))

    def invert(self: _T) -> _T:
        """Return a set of all flags not in the current set."""
        return self.__class__(self.__class__.__everything__._value_ & ~self._value_)

    def is_disjoint(self: _T, other: typing.Union[_T, int]) -> bool:
        """Return whether two sets have a intersection or not.

        If the two sets have an intersection, then this returns
        `builtins.False`. If no common flag values exist between them, then
        this returns `builtins.True`.
        """
        return not (self & other)

    def is_subset(self: _T, other: typing.Union[_T, int]) -> bool:
        """Return whether another set contains this set or not.

        Equivalent to using the "in" operator.
        """
        return (self & other) == other

    def is_superset(self: _T, other: typing.Union[_T, int]) -> bool:
        """Return whether this set contains another set or not."""
        return (self & other) == self

    def none(self: _T, *flags: _T) -> bool:
        """Check if none of the given flags are part of this value.

        !!! note
            This is essentially the opposite of `Flag.any`.

        Returns
        -------
        builtins.bool
            `builtins.True` if none of the given flags are part of this value.
            Otherwise, return `builtins.False`.
        """
        return not self.any(*flags)

    def split(self: _T) -> typing.Sequence[_T]:
        """Return a list of all defined atomic values for this flag.

        Any unrecognised bits will be omitted for brevity.

        The result will be a name-sorted `typing.Sequence` of each membe
        """
        return sorted(
            (member for member in self.__class__._powers_of_2_to_member_map_.values() if member.value & self),
            # Assumption: powers of 2 already have a cached value.
            key=lambda m: m._name_,
        )

    def symmetric_difference(self: _T, other: typing.Union[_T, int]) -> _T:
        """Return a set with the symmetric differences of two flag sets.

        Equivalent to using the "XOR" `^` operator.

        For `a ^ b`, this can be considered the same as `(a - b) | (b - a)`.
        """
        return self.__class__(self._value_ ^ int(other))

    def union(self: _T, other: typing.Union[_T, int]) -> _T:
        """Return a combination of all flags in this set and the other set.

        Equivalent to using the "OR" `~` operator.
        """
        return self.__class__(self._value_ | int(other))

    isdisjoint = is_disjoint
    issubset = is_subset
    issuperset = is_superset
    # Exists since Python's `set` type is inconsistent with naming, so this
    # will prevent tripping people up unnecessarily because we do not
    # name inconsistently.

    # This one isn't in Python's set, but the inconsistency is triggering my OCD
    # so this is being defined anyway.
    symmetricdifference = symmetric_difference

    def __bool__(self) -> bool:
        return bool(self._value_)

    def __int__(self) -> int:
        return self._value_

    def __iter__(self: _T) -> typing.Iterator[_T]:
        return iter(self.split())

    def __len__(self) -> int:
        return len(self.split())

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}: {self.value!r}>"

    def __rsub__(self: _T, other: typing.Union[int, _T]) -> _T:
        # This logic has to be reversed to be correct, since order matters for
        # a subtraction operator. This also ensures `int - _T -> _T` is a valid
        # case for us.
        return self.__class__(other) - self

    def __str__(self) -> str:
        return self.name

    __contains__ = is_subset
    __rand__ = __and__ = intersection
    __ror__ = __or__ = union
    __sub__ = difference
    __rxor__ = __xor__ = symmetric_difference
    __invert__ = invert

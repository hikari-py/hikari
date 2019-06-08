#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dataclasses
import enum


# IMPORT THE OPCODE MODULE INSIDE TESTS TO PREVENT SYNTAX ERRORS BLOWING OUT THE ENTIRE SUITE.


def test_int_member_accessors():
    from hikari.net import opcodes

    expected_value = 999
    expected_desc = "call the police"

    i = opcodes.IntMember(expected_value, expected_desc)

    assert i.value == expected_value, f"value was {i.value}"
    assert i.description == expected_desc, f"description was {i.description}"
    assert int(i) == expected_value, f"int cast produced {int(i)}"
    assert str(i) == expected_desc, f"str cast produced {str(i)}"
    assert repr(i) == f"{expected_value} ({expected_desc})", f"repr cast produced {repr(i)}"


def test_int_member_is_hashable_correctly():
    from hikari.net import opcodes

    a = opcodes.IntMember(1, "a")
    b = opcodes.IntMember(1, "b")
    c = opcodes.IntMember(2, "c")

    d = {a: a, b: b, c: c}

    assert len(d) == 2
    assert (all(k is not a for k in d.keys())) ^ (
        all(k is not b for k in d.keys())
    ), "Both a and b are in or are not in the map which is not correct as they should both share the same hash code"
    assert c in d


def test_int_member_is_comparable_correctly():
    from hikari.net import opcodes

    a = opcodes.IntMember(1, "a")
    b = opcodes.IntMember(1, "b")
    c = opcodes.IntMember(2, "c")

    assert a == b
    assert a != c
    assert a < c
    assert a <= c
    assert c > a
    assert c >= a


# noinspection PyDataclass
def test_int_member_is_immutable():
    from hikari.net import opcodes

    expected_value = 999
    expected_desc = "call the police"
    i = opcodes.IntMember(expected_value, expected_desc)

    try:
        i.value = 12
        assert False, "No error was raised, class is not immutable :("
    except dataclasses.FrozenInstanceError:
        pass

    try:
        i.description = 12
        assert False, "No error was raised, class is not immutable :("
    except dataclasses.FrozenInstanceError:
        pass


def test_enum_compatibility():
    from hikari.net import opcodes

    class SomeIntEnum(enum.IntEnum):
        FOO = opcodes.IntMember(12, "this is foo")
        BAR = opcodes.IntMember(13, "this is bar")
        BAZ = opcodes.IntMember(14, "this is baz")

    assert SomeIntEnum(12) is SomeIntEnum.FOO
    assert SomeIntEnum.FOO is SomeIntEnum(12)
    assert SomeIntEnum(12) == SomeIntEnum.FOO
    assert SomeIntEnum.FOO == SomeIntEnum(12)

    assert SomeIntEnum(13) is not SomeIntEnum.FOO
    assert SomeIntEnum.FOO is not SomeIntEnum(13)
    assert SomeIntEnum(13) != SomeIntEnum.FOO
    assert SomeIntEnum.FOO != SomeIntEnum(13)

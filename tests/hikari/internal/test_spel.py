# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
from __future__ import annotations

import typing

import pytest

from hikari.internal import spel


class _Child:
    def __init__(self, name: str, foo: typing.Any = None) -> None:
        self.name = name
        self.foo = foo


class _Target:
    def __init__(self, foo: typing.Any = None, child: _Child | None = None) -> None:
        self.foo = foo
        self.child = child

    def raise_error(self) -> typing.NoReturn:
        raise RuntimeError("boom")


class _MethodTarget:
    def __init__(self, result: typing.Any) -> None:
        self.result = result

    def foo(self) -> typing.Any:
        return self.result


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


@pytest.mark.parametrize("expression", ["foo", ".foo"])
def test_attr_getter_returns_attribute_value(expression: str) -> None:
    value = object()
    target = _Target(foo=value)

    assert spel.AttrGetter(expression)(target) is value


def test_attr_getter_resolves_nested_attributes() -> None:
    value = object()
    target = _Target(child=_Child("child", foo=value))

    assert spel.AttrGetter("child.foo")(target) is value


def test_attr_getter_calls_method_without_arguments() -> None:
    value = object()
    target = _MethodTarget(value)

    assert spel.AttrGetter("foo()")(target) is value


def test_attr_getter_composes_attributes_and_method() -> None:
    target = _Target(child=_Child("hello"))

    assert spel.AttrGetter("child.name.upper()")(target) == "HELLO"


@pytest.mark.parametrize(("value", "expected"), [("text", False), ("", True), (0, True), (object(), False)])
def test_attr_getter_negates_attribute_value(value: typing.Any, expected: bool) -> None:
    assert spel.AttrGetter("!foo")(_Target(foo=value)) is expected


@pytest.mark.parametrize(("content", "expected"), [("123", False), ("abc", True)])
def test_attr_getter_negates_method_result(content: str, expected: bool) -> None:
    assert spel.AttrGetter("content.!isdigit()")(_Message(content)) is expected


@pytest.mark.parametrize(("value", "expected"), [("text", False), ("", True)])
def test_attr_getter_invert_all_negates_final_result(value: typing.Any, expected: bool) -> None:
    target = _Target(child=_Child("child", foo=value))

    assert spel.AttrGetter("!.child.foo")(target) is expected


def test_attr_getter_propagates_missing_attribute_error() -> None:
    with pytest.raises(AttributeError):
        spel.AttrGetter("missing")(_Target())


def test_attr_getter_propagates_method_exceptions() -> None:
    with pytest.raises(RuntimeError, match="boom"):
        spel.AttrGetter("raise_error()")(_Target())

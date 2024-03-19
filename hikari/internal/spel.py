# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""HikariSPEL (Hikari SimPle Expression Language).

HikariSPEL (Hikari SimPle Expression Language) is a super-simple expression
language used in this module for quickly mapping values to other values and
producing streams of changes. This somewhat mirrors other programming languages
like Java which have a proper Stream API.

The concept of HikariSPEL is that you are trying to look at the attribute
of something. So, running `"bar.baz.bork"` against an object `foo` would be
equivalent to `foo.bar.baz.bork` in pure Python. The reason for doing this is
Python lambdas are clunky, and using a nested function is nasty boilerplate.

For applying `"bar.baz"` to `foo`, we assume `bar` is an attribute or property
of `foo`, and `baz` is an attribute or property of `foo.bar`. We may instead
want to invoke a method that takes no parameters (looking at [`str.islower`][], as
an example. To do this, we append `()` onto the attribute name. For example,
applying `author.username.islower()` to a [`hikari.messages.Message`][]
object.

All expressions may start with a ``.``. You can negate the whole expression
by instead starting them with `!.`.

You may also want to negate a condition. To do this, prepend `!` to the
attribute name. For example, to check if a message was not made by a bot,
you could run `author.!is_bot` on a [`hikari.messages.Message`][] object.
Likewise, to check if the input was not a number, you could run
`content.!isdigit()`.

This expression language is highly experimental and may change without
prior notice for the time being.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = ("AttrGetter",)

import operator
import typing

InputValueT = typing.TypeVar("InputValueT")
ReturnValueT = typing.TypeVar("ReturnValueT")


class AttrGetter(typing.Generic[InputValueT, ReturnValueT]):
    """An attribute getter that can resolve nested attributes and methods.

    This follows the SPEL definition for how to define expressions. Expressions
    may be preceded with an optional `.` to aid in readability.
    """

    __slots__: typing.Sequence[str] = ("pipeline", "invert_all")

    def __init__(self, attr_name: str) -> None:
        self.invert_all: bool = False

        if attr_name.startswith("!."):
            attr_name = attr_name[2:]
            self.invert_all = True

        elif attr_name.startswith("."):
            attr_name = attr_name[1:]

        self.pipeline: typing.List[typing.Callable[[typing.Any], typing.Any]] = []

        for operation in attr_name.split("."):
            self.pipeline.append(self._transform(operation))

    def _transform(self, attr_name: str) -> typing.Callable[[typing.Any], typing.Any]:
        if attr_name.startswith("!"):
            attr_name = attr_name[1:]
            invert = True
        else:
            invert = False

        op = self._to_op(attr_name)

        if invert:
            return lambda value: not op(value)

        return op

    @staticmethod
    def _to_op(attr_name: str) -> typing.Callable[[typing.Any], typing.Any]:
        op = operator.methodcaller(attr_name[:-2]) if attr_name.endswith("()") else operator.attrgetter(attr_name)
        return typing.cast("typing.Callable[[typing.Any], typing.Any]", op)

    def __call__(self, item: InputValueT) -> ReturnValueT:
        result: typing.Any = item
        for op in self.pipeline:
            result = op(result)

        return typing.cast("ReturnValueT", (not result) if self.invert_all else result)

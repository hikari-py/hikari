# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
import typing

import pytest

from hikari.utilities import reflect


# noinspection PyUnusedLocal
class TestResolveSignature:
    def test_handles_normal_references(self):
        def foo(bar: str, bat: int) -> str:
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_normal_no_annotations(self):
        def foo(bar, bat):
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is reflect.EMPTY
        assert signature.parameters["bat"].annotation is reflect.EMPTY
        assert signature.return_annotation is reflect.EMPTY

    def test_handles_forward_annotated_parameters(self):
        def foo(bar: "str", bat: "int") -> str:
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_forward_annotated_return(self):
        def foo(bar: str, bat: int) -> "str":
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_forward_annotations(self):
        def foo(bar: "str", bat: "int") -> "str":
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_mixed_annotations(self):
        def foo(bar: str, bat: "int"):
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is reflect.EMPTY

    def test_handles_None(self):
        def foo(bar: None) -> None:
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is None
        assert signature.return_annotation is None

    def test_handles_NoneType(self):
        def foo(bar: type(None)) -> type(None):
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is None
        assert signature.return_annotation is None

    def test_handles_only_return_annotated(self):
        def foo(bar, bat) -> str:
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is reflect.EMPTY
        assert signature.parameters["bat"].annotation is reflect.EMPTY
        assert signature.return_annotation is str

    def test_handles_nested_annotations(self):
        def foo(bar: typing.Optional[typing.Iterator[int]]):
            ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation == typing.Optional[typing.Iterator[int]]


class Class:
    pass


@pytest.mark.parametrize(
    ["args", "expected_name"],
    [
        ([Class], __name__),
        ([Class()], __name__),
        ([Class, "Foooo", "bar", "123"], f"{__name__}.Foooo.bar.123"),
        ([Class(), "qux", "QUx", "940"], f"{__name__}.qux.QUx.940"),
    ],
)
def test_get_logger(args, expected_name):
    assert reflect.get_logger(*args).name == expected_name

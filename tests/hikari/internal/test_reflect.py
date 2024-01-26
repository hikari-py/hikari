# -*- coding: utf-8 -*-
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
import inspect
import sys
import typing

import mock
import pytest

from hikari.internal import reflect


@pytest.mark.skipif(sys.version_info >= (3, 10), reason="This strategy is specific to 3.10 > versions")
class TestResolveSignatureOldStrategy:
    def test_handles_normal_references(self):
        def foo(bar: str, bat: int) -> str: ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_normal_no_annotations(self):
        def foo(bar, bat): ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is reflect.EMPTY
        assert signature.parameters["bat"].annotation is reflect.EMPTY
        assert signature.return_annotation is reflect.EMPTY

    def test_handles_forward_annotated_parameters(self):
        def foo(bar: "str", bat: "int") -> str: ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_forward_annotated_return(self):
        def foo(bar: str, bat: int) -> "str": ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_forward_annotations(self):
        def foo(bar: "str", bat: "int") -> "str": ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_mixed_annotations(self):
        def foo(bar: str, bat: "int"): ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is reflect.EMPTY

    def test_handles_None(self):
        def foo(bar: None) -> None: ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is None
        assert signature.return_annotation is None

    def test_handles_NoneType(self):
        def foo(bar: type(None)) -> type(None): ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is None
        assert signature.return_annotation is None

    def test_handles_only_return_annotated(self):
        def foo(bar, bat) -> str: ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is reflect.EMPTY
        assert signature.parameters["bat"].annotation is reflect.EMPTY
        assert signature.return_annotation is str

    def test_handles_nested_annotations(self):
        def foo(bar: typing.Optional[typing.Iterator[int]]): ...

        signature = reflect.resolve_signature(foo)
        assert signature.parameters["bar"].annotation == typing.Optional[typing.Iterator[int]]


@pytest.mark.skipif(sys.version_info < (3, 10), reason="This strategy is specific to 3.10 <= versions")
def test_resolve_signature():
    foo = object()

    with mock.patch.object(inspect, "signature") as signature:
        sig = reflect.resolve_signature(foo)

    assert sig is signature.return_value
    signature.assert_called_once_with(foo, eval_str=True)

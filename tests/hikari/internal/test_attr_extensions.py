# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import contextlib
import copy as stdlib_copy

import attr
import mock

from hikari.internal import attr_extensions


def test_invalidate_shallow_copy_cache():
    attr_extensions._SHALLOW_COPIERS = {int: object(), str: object()}
    assert attr_extensions.invalidate_shallow_copy_cache() is None
    assert attr_extensions._SHALLOW_COPIERS == {}


def test_invalidate_deep_copy_cache():
    attr_extensions._DEEP_COPIERS = {str: object(), int: object(), object: object()}
    assert attr_extensions.invalidate_deep_copy_cache() is None
    assert attr_extensions._DEEP_COPIERS == {}


def test_get_fields_definition():
    @attr.s(init=True)
    class StubModel:
        foo: int = attr.ib(init=True)
        bar: bool = attr.ib(init=False)
        bam: bool = attr.ib(init=False)
        _voodoo: str = attr.ib(init=True)
        Bat: bool = attr.ib(init=True)

    fields = {field.name: field for field in attr.fields(StubModel)}
    new_model = attr_extensions.get_fields_definition(StubModel)
    assert new_model == (
        [(fields["foo"], "foo"), (fields["_voodoo"], "voodoo"), (fields["Bat"], "Bat")],
        [fields["bar"], fields["bam"]],
    )


def test_generate_shallow_copier():
    @attr.s(init=True)
    class StubModel:
        _foo: int = attr.ib(init=True)
        baaaa: str = attr.ib(init=True)
        _blam: bool = attr.ib(init=True)
        not_init: int = attr.ib(init=False)
        no: bytes = attr.ib(init=True)

    old_model = StubModel(foo=42, baaaa="sheep", blam=True, no=b"okokokok")
    old_model.not_init = 54234

    copier = attr_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert new_model._foo is old_model._foo
    assert new_model.baaaa is old_model.baaaa
    assert new_model._blam is old_model._blam
    assert new_model.not_init is old_model.not_init
    assert new_model.no is old_model.no


def test_generate_shallow_copier_with_init_only_arguments():
    @attr.s(init=True)
    class StubModel:
        _gfd: int = attr.ib(init=True)
        baaaa: str = attr.ib(init=True)
        _blambat: bool = attr.ib(init=True)
        no: bytes = attr.ib(init=True)

    old_model = StubModel(gfd=42, baaaa="sheep", blambat=True, no=b"okokokok")

    copier = attr_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert new_model._gfd is old_model._gfd
    assert new_model.baaaa is old_model.baaaa
    assert new_model._blambat is old_model._blambat
    assert new_model.no is old_model.no


def test_generate_shallow_copier_with_only_non_init_attrs():
    @attr.s(init=True)
    class StubModel:
        _gfd: int = attr.ib(init=False)
        baaaa: str = attr.ib(init=False)
        _blambat: bool = attr.ib(init=False)
        no: bytes = attr.ib(init=False)

    old_model = StubModel()
    old_model._gfd = 42
    old_model.baaaa = "sheep"
    old_model._blambat = True
    old_model.no = b"okokokok"

    copier = attr_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert new_model._gfd is old_model._gfd
    assert new_model.baaaa is old_model.baaaa
    assert new_model._blambat is old_model._blambat
    assert new_model.no is old_model.no


def test_generate_shallow_copier_with_no_attributes():
    @attr.s(init=True)
    class StubModel:
        ...

    old_model = StubModel()

    copier = attr_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert isinstance(new_model, StubModel)


def test_get_or_generate_shallow_copier_for_cached_copier():
    mock_copier = object()

    @attr.s(init=True)
    class StubModel:
        ...

    attr_extensions._SHALLOW_COPIERS = {
        type("b", (), {}): object(),
        StubModel: mock_copier,
        type("a", (), {}): object(),
    }

    assert attr_extensions.get_or_generate_shallow_copier(StubModel) is mock_copier


def test_get_or_generate_shallow_copier_for_uncached_copier():
    mock_copier = object()

    @attr.s(init=True)
    class StubModel:
        ...

    with mock.patch.object(attr_extensions, "generate_shallow_copier", return_value=mock_copier):
        assert attr_extensions.get_or_generate_shallow_copier(StubModel) is mock_copier

        attr_extensions.generate_shallow_copier.assert_called_once_with(StubModel)

    assert attr_extensions._SHALLOW_COPIERS[StubModel] is mock_copier


def test_copy_attrs():
    mock_result = object()
    mock_copier = mock.Mock(return_value=mock_result)

    @attr.s(init=True)
    class StubModel:
        ...

    model = StubModel()

    with mock.patch.object(attr_extensions, "get_or_generate_shallow_copier", return_value=mock_copier):
        assert attr_extensions.copy_attrs(model) is mock_result

        attr_extensions.get_or_generate_shallow_copier.assert_called_once_with(StubModel)

    mock_copier.assert_called_once_with(model)


def test_generate_deep_copier():
    @attr.s
    class StubBaseClass:
        recursor: int = attr.ib(init=True)
        _field: bool = attr.ib(init=True)
        foo: str = attr.ib(init=True)
        end: str = attr.ib(init=False)
        _blam: bool = attr.ib(init=False)

    model = StubBaseClass(recursor=431, field=True, foo="blam")
    model.end = "the way"
    model._blam = "555555"
    old_model_fields = stdlib_copy.copy(model)
    copied_recursor = object()
    copied_field = object()
    copied_foo = object()
    copied_end = object()
    copied_blam = object()
    memo = {123: object()}

    with mock.patch.object(
        stdlib_copy,
        "deepcopy",
        side_effect=[copied_recursor, copied_field, copied_foo, copied_end, copied_blam],
    ):
        attr_extensions.generate_deep_copier(StubBaseClass)(model, memo)

        stdlib_copy.deepcopy.assert_has_calls(
            [
                mock.call(old_model_fields.recursor, memo),
                mock.call(old_model_fields._field, memo),
                mock.call(old_model_fields.foo, memo),
                mock.call(old_model_fields.end, memo),
                mock.call(old_model_fields._blam, memo),
            ]
        )

    assert model.recursor is copied_recursor
    assert model._field is copied_field
    assert model.foo is copied_foo
    assert model.end is copied_end
    assert model._blam is copied_blam


def test_generate_deep_copier_with_only_init_attributes():
    @attr.s
    class StubBaseClass:
        recursor: int = attr.ib(init=True)
        _field: bool = attr.ib(init=True)
        foo: str = attr.ib(init=True)

    model = StubBaseClass(recursor=431, field=True, foo="blam")
    old_model_fields = stdlib_copy.copy(model)
    copied_recursor = object()
    copied_field = object()
    copied_foo = object()
    memo = {123: object()}

    with mock.patch.object(
        stdlib_copy,
        "deepcopy",
        side_effect=[copied_recursor, copied_field, copied_foo],
    ):
        attr_extensions.generate_deep_copier(StubBaseClass)(model, memo)

        stdlib_copy.deepcopy.assert_has_calls(
            [
                mock.call(old_model_fields.recursor, memo),
                mock.call(old_model_fields._field, memo),
                mock.call(old_model_fields.foo, memo),
            ]
        )

    assert model.recursor is copied_recursor
    assert model._field is copied_field
    assert model.foo is copied_foo


def test_generate_deep_copier_with_only_non_init_attributes():
    @attr.s
    class StubBaseClass:
        end: str = attr.ib(init=False)
        _blam: bool = attr.ib(init=False)

    model = StubBaseClass()
    model.end = "the way"
    model._blam = "555555"
    old_model_fields = stdlib_copy.copy(model)
    copied_end = object()
    copied_blam = object()
    memo = {123: object()}

    with mock.patch.object(
        stdlib_copy,
        "deepcopy",
        side_effect=[copied_end, copied_blam],
    ):
        attr_extensions.generate_deep_copier(StubBaseClass)(model, memo)

        stdlib_copy.deepcopy.assert_has_calls(
            [
                mock.call(old_model_fields.end, memo),
                mock.call(old_model_fields._blam, memo),
            ]
        )

    assert model.end is copied_end
    assert model._blam is copied_blam


def test_generate_deep_copier_with_no_attributes():
    @attr.s
    class StubBaseClass:
        ...

    model = StubBaseClass()
    memo = {123: object()}

    with mock.patch.object(
        stdlib_copy,
        "deepcopy",
        side_effect=NotImplementedError,
    ):
        attr_extensions.generate_deep_copier(StubBaseClass)(model, memo)

        stdlib_copy.deepcopy.assert_not_called()


def test_get_or_generate_deep_copier_for_cached_function():
    class StubClass:
        ...

    mock_copier = object()
    attr_extensions._DEEP_COPIERS = {}

    with mock.patch.object(attr_extensions, "generate_deep_copier", return_value=mock_copier):
        assert attr_extensions.get_or_generate_deep_copier(StubClass) is mock_copier

        attr_extensions.generate_deep_copier.assert_called_once_with(StubClass)

    assert attr_extensions._DEEP_COPIERS[StubClass] is mock_copier


def test_get_or_generate_deep_copier_for_uncached_function():
    class StubClass:
        ...

    mock_copier = object()
    attr_extensions._DEEP_COPIERS = {StubClass: mock_copier}

    with mock.patch.object(attr_extensions, "generate_deep_copier"):
        assert attr_extensions.get_or_generate_deep_copier(StubClass) is mock_copier

        attr_extensions.generate_deep_copier.assert_not_called()


def test_deep_copy_attrs_without_memo():
    class StubClass:
        ...

    mock_object = StubClass()
    mock_result = object()
    mock_copier = mock.Mock(mock_result)

    stack = contextlib.ExitStack()
    stack.enter_context(mock.patch.object(attr_extensions, "get_or_generate_deep_copier", return_value=mock_copier))
    stack.enter_context(mock.patch.object(stdlib_copy, "copy", return_value=mock_result))

    with stack:
        assert attr_extensions.deep_copy_attrs(mock_object) is mock_result

        stdlib_copy.copy.assert_called_once_with(mock_object)
        attr_extensions.get_or_generate_deep_copier.assert_called_once_with(StubClass)

    mock_copier.assert_called_once_with(mock_result, {id(mock_object): mock_result})


def test_deep_copy_attrs_with_memo():
    class StubClass:
        ...

    mock_object = StubClass()
    mock_result = object()
    mock_copier = mock.Mock(mock_result)
    mock_other_object = object()

    stack = contextlib.ExitStack()
    stack.enter_context(mock.patch.object(attr_extensions, "get_or_generate_deep_copier", return_value=mock_copier))
    stack.enter_context(mock.patch.object(stdlib_copy, "copy", return_value=mock_result))

    with stack:
        assert attr_extensions.deep_copy_attrs(mock_object, {1235342: mock_other_object}) is mock_result

        stdlib_copy.copy.assert_called_once_with(mock_object)
        attr_extensions.get_or_generate_deep_copier.assert_called_once_with(StubClass)

    mock_copier.assert_called_once_with(mock_result, {id(mock_object): mock_result, 1235342: mock_other_object})


class TestCopyDecorator:
    def test___copy__(self):
        mock_result = object()
        mock_copier = mock.Mock(return_value=mock_result)

        @attr.s()
        @attr_extensions.with_copy
        class StubClass:
            ...

        model = StubClass()

        with mock.patch.object(attr_extensions, "get_or_generate_shallow_copier", return_value=mock_copier):
            assert stdlib_copy.copy(model) is mock_result

            attr_extensions.get_or_generate_shallow_copier.assert_called_once_with(StubClass)

        mock_copier.assert_called_once_with(model)

    def test___deep__copy(self):
        class CopyingMock(mock.Mock):
            def __call__(self, /, *args, **kwargs):
                args = list(args)
                args[1] = dict(args[1])
                return super().__call__(*args, **kwargs)

        mock_result = object()
        mock_copier = CopyingMock(return_value=mock_result)

        @attr.s()
        @attr_extensions.with_copy
        class StubClass:
            ...

        model = StubClass()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(attr_extensions, "get_or_generate_deep_copier", return_value=mock_copier))
        stack.enter_context(mock.patch.object(stdlib_copy, "copy", return_value=mock_result))

        with stack:
            assert stdlib_copy.deepcopy(model) is mock_result

            stdlib_copy.copy.assert_called_once_with(model)
            attr_extensions.get_or_generate_deep_copier.assert_called_once_with(StubClass)

        mock_copier.assert_called_once_with(mock_result, {id(model): mock_result})

    def test_copy_decorator_inheritance(self):
        @attr_extensions.with_copy
        @attr.s()
        class ParentClass:
            ...

        class Foo(ParentClass):
            ...

        assert Foo.__copy__ == attr_extensions.copy_attrs
        assert Foo.__deepcopy__ == attr_extensions.deep_copy_attrs

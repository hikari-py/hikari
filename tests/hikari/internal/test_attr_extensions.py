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
import contextlib
import copy as stdlib_copy

import attrs
import mock

from hikari.internal import attrs_extensions


def test_invalidate_shallow_copy_cache():
    attrs_extensions._SHALLOW_COPIERS = {int: object(), str: object()}
    assert attrs_extensions.invalidate_shallow_copy_cache() is None
    assert attrs_extensions._SHALLOW_COPIERS == {}


def test_invalidate_deep_copy_cache():
    attrs_extensions._DEEP_COPIERS = {str: object(), int: object(), object: object()}
    assert attrs_extensions.invalidate_deep_copy_cache() is None
    assert attrs_extensions._DEEP_COPIERS == {}


def test_get_fields_definition():
    @attrs.define()
    class StubModel:
        foo: int = attrs.field()
        bar: bool = attrs.field(init=False)
        bam: bool = attrs.field(init=False)
        _voodoo: str = attrs.field(alias="voodoo")
        Bat: bool = attrs.field()

    fields = {field.name: field for field in attrs.fields(StubModel)}
    new_model = attrs_extensions.get_fields_definition(StubModel)
    assert new_model == (
        [(fields["foo"], "foo"), (fields["_voodoo"], "voodoo"), (fields["Bat"], "Bat")],
        [fields["bar"], fields["bam"]],
    )


def test_generate_shallow_copier():
    @attrs.define()
    class StubModel:
        _foo: int = attrs.field(alias="foo")
        baaaa: str = attrs.field()
        _blam: bool = attrs.field(alias="blam")
        not_init: int = attrs.field(init=False)
        no: bytes = attrs.field()

    old_model = StubModel(foo=42, baaaa="sheep", blam=True, no=b"okokokok")
    old_model.not_init = 54234

    copier = attrs_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert new_model._foo is old_model._foo
    assert new_model.baaaa is old_model.baaaa
    assert new_model._blam is old_model._blam
    assert new_model.not_init is old_model.not_init
    assert new_model.no is old_model.no


def test_generate_shallow_copier_with_init_only_arguments():
    @attrs.define()
    class StubModel:
        _gfd: int = attrs.field(alias="gfd")
        baaaa: str = attrs.field()
        _blambat: bool = attrs.field(alias="blambat")
        no: bytes = attrs.field()

    old_model = StubModel(gfd=42, baaaa="sheep", blambat=True, no=b"okokokok")

    copier = attrs_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert new_model._gfd is old_model._gfd
    assert new_model.baaaa is old_model.baaaa
    assert new_model._blambat is old_model._blambat
    assert new_model.no is old_model.no


def test_generate_shallow_copier_with_only_non_init_attrs():
    @attrs.define()
    class StubModel:
        _gfd: int = attrs.field(init=False)
        baaaa: str = attrs.field(init=False)
        _blambat: bool = attrs.field(init=False)
        no: bytes = attrs.field(init=False)

    old_model = StubModel()
    old_model._gfd = 42
    old_model.baaaa = "sheep"
    old_model._blambat = True
    old_model.no = b"okokokok"

    copier = attrs_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert new_model._gfd is old_model._gfd
    assert new_model.baaaa is old_model.baaaa
    assert new_model._blambat is old_model._blambat
    assert new_model.no is old_model.no


def test_generate_shallow_copier_with_no_attributes():
    @attrs.define()
    class StubModel: ...

    old_model = StubModel()

    copier = attrs_extensions.generate_shallow_copier(StubModel)
    new_model = copier(old_model)

    assert new_model is not old_model
    assert isinstance(new_model, StubModel)


def test_get_or_generate_shallow_copier_for_cached_copier():
    mock_copier = object()

    @attrs.define()
    class StubModel: ...

    attrs_extensions._SHALLOW_COPIERS = {
        type("b", (), {}): object(),
        StubModel: mock_copier,
        type("a", (), {}): object(),
    }

    assert attrs_extensions.get_or_generate_shallow_copier(StubModel) is mock_copier


def test_get_or_generate_shallow_copier_for_uncached_copier():
    mock_copier = object()

    @attrs.define()
    class StubModel: ...

    with mock.patch.object(attrs_extensions, "generate_shallow_copier", return_value=mock_copier):
        assert attrs_extensions.get_or_generate_shallow_copier(StubModel) is mock_copier

        attrs_extensions.generate_shallow_copier.assert_called_once_with(StubModel)

    assert attrs_extensions._SHALLOW_COPIERS[StubModel] is mock_copier


def test_copy_attrs():
    mock_result = object()
    mock_copier = mock.Mock(return_value=mock_result)

    @attrs.define()
    class StubModel: ...

    model = StubModel()

    with mock.patch.object(attrs_extensions, "get_or_generate_shallow_copier", return_value=mock_copier):
        assert attrs_extensions.copy_attrs(model) is mock_result

        attrs_extensions.get_or_generate_shallow_copier.assert_called_once_with(StubModel)

    mock_copier.assert_called_once_with(model)


def test_generate_deep_copier():
    @attrs.define
    class StubBaseClass:
        recursor: int = attrs.field()
        _field: bool = attrs.field(alias="field")
        foo: str = attrs.field()
        end: str = attrs.field(init=False)
        _blam: bool = attrs.field(init=False)

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
        stdlib_copy, "deepcopy", side_effect=[copied_recursor, copied_field, copied_foo, copied_end, copied_blam]
    ):
        attrs_extensions.generate_deep_copier(StubBaseClass)(model, memo)

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
    @attrs.define
    class StubBaseClass:
        recursor: int = attrs.field()
        _field: bool = attrs.field(alias="field")
        foo: str = attrs.field()

    model = StubBaseClass(recursor=431, field=True, foo="blam")
    old_model_fields = stdlib_copy.copy(model)
    copied_recursor = object()
    copied_field = object()
    copied_foo = object()
    memo = {123: object()}

    with mock.patch.object(stdlib_copy, "deepcopy", side_effect=[copied_recursor, copied_field, copied_foo]):
        attrs_extensions.generate_deep_copier(StubBaseClass)(model, memo)

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
    @attrs.define
    class StubBaseClass:
        end: str = attrs.field(init=False)
        _blam: bool = attrs.field(init=False)

    model = StubBaseClass()
    model.end = "the way"
    model._blam = "555555"
    old_model_fields = stdlib_copy.copy(model)
    copied_end = object()
    copied_blam = object()
    memo = {123: object()}

    with mock.patch.object(stdlib_copy, "deepcopy", side_effect=[copied_end, copied_blam]):
        attrs_extensions.generate_deep_copier(StubBaseClass)(model, memo)

        stdlib_copy.deepcopy.assert_has_calls(
            [mock.call(old_model_fields.end, memo), mock.call(old_model_fields._blam, memo)]
        )

    assert model.end is copied_end
    assert model._blam is copied_blam


def test_generate_deep_copier_with_no_attributes():
    @attrs.define
    class StubBaseClass: ...

    model = StubBaseClass()
    memo = {123: object()}

    with mock.patch.object(stdlib_copy, "deepcopy", side_effect=NotImplementedError):
        attrs_extensions.generate_deep_copier(StubBaseClass)(model, memo)

        stdlib_copy.deepcopy.assert_not_called()


def test_get_or_generate_deep_copier_for_cached_function():
    class StubClass: ...

    mock_copier = object()
    attrs_extensions._DEEP_COPIERS = {}

    with mock.patch.object(attrs_extensions, "generate_deep_copier", return_value=mock_copier):
        assert attrs_extensions.get_or_generate_deep_copier(StubClass) is mock_copier

        attrs_extensions.generate_deep_copier.assert_called_once_with(StubClass)

    assert attrs_extensions._DEEP_COPIERS[StubClass] is mock_copier


def test_get_or_generate_deep_copier_for_uncached_function():
    class StubClass: ...

    mock_copier = object()
    attrs_extensions._DEEP_COPIERS = {StubClass: mock_copier}

    with mock.patch.object(attrs_extensions, "generate_deep_copier"):
        assert attrs_extensions.get_or_generate_deep_copier(StubClass) is mock_copier

        attrs_extensions.generate_deep_copier.assert_not_called()


def test_deep_copy_attrs_without_memo():
    class StubClass: ...

    mock_object = StubClass()
    mock_result = object()
    mock_copier = mock.Mock(mock_result)

    stack = contextlib.ExitStack()
    stack.enter_context(mock.patch.object(attrs_extensions, "get_or_generate_deep_copier", return_value=mock_copier))
    stack.enter_context(mock.patch.object(stdlib_copy, "copy", return_value=mock_result))

    with stack:
        assert attrs_extensions.deep_copy_attrs(mock_object) is mock_result

        stdlib_copy.copy.assert_called_once_with(mock_object)
        attrs_extensions.get_or_generate_deep_copier.assert_called_once_with(StubClass)

    mock_copier.assert_called_once_with(mock_result, {id(mock_object): mock_result})


def test_deep_copy_attrs_with_memo():
    class StubClass: ...

    mock_object = StubClass()
    mock_result = object()
    mock_copier = mock.Mock(mock_result)
    mock_other_object = object()

    stack = contextlib.ExitStack()
    stack.enter_context(mock.patch.object(attrs_extensions, "get_or_generate_deep_copier", return_value=mock_copier))
    stack.enter_context(mock.patch.object(stdlib_copy, "copy", return_value=mock_result))

    with stack:
        assert attrs_extensions.deep_copy_attrs(mock_object, {1235342: mock_other_object}) is mock_result

        stdlib_copy.copy.assert_called_once_with(mock_object)
        attrs_extensions.get_or_generate_deep_copier.assert_called_once_with(StubClass)

    mock_copier.assert_called_once_with(mock_result, {id(mock_object): mock_result, 1235342: mock_other_object})


class TestCopyDecorator:
    def test___copy__(self):
        mock_result = object()
        mock_copier = mock.Mock(return_value=mock_result)

        @attrs.define()
        @attrs_extensions.with_copy
        class StubClass: ...

        model = StubClass()

        with mock.patch.object(attrs_extensions, "get_or_generate_shallow_copier", return_value=mock_copier):
            assert stdlib_copy.copy(model) is mock_result

            attrs_extensions.get_or_generate_shallow_copier.assert_called_once_with(StubClass)

        mock_copier.assert_called_once_with(model)

    def test___deep__copy(self):
        class CopyingMock(mock.Mock):
            def __call__(self, /, *args, **kwargs):
                args = list(args)
                args[1] = dict(args[1])
                return super().__call__(*args, **kwargs)

        mock_result = object()
        mock_copier = CopyingMock(return_value=mock_result)

        @attrs.define()
        @attrs_extensions.with_copy
        class StubClass: ...

        model = StubClass()
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(attrs_extensions, "get_or_generate_deep_copier", return_value=mock_copier)
        )
        stack.enter_context(mock.patch.object(stdlib_copy, "copy", return_value=mock_result))

        with stack:
            assert stdlib_copy.deepcopy(model) is mock_result

            stdlib_copy.copy.assert_called_once_with(model)
            attrs_extensions.get_or_generate_deep_copier.assert_called_once_with(StubClass)

        mock_copier.assert_called_once_with(mock_result, {id(model): mock_result})

    def test_copy_decorator_inheritance(self):
        @attrs_extensions.with_copy
        @attrs.define()
        class ParentClass: ...

        class Foo(ParentClass): ...

        assert Foo.__copy__ == attrs_extensions.copy_attrs
        assert Foo.__deepcopy__ == attrs_extensions.deep_copy_attrs

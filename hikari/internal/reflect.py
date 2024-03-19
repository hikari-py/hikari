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
"""Reflection utilities."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("resolve_signature",)

import functools
import inspect
import sys
import typing

if typing.TYPE_CHECKING:
    _T = typing.TypeVar("_T")

EMPTY: typing.Final[typing.Any] = inspect.Parameter.empty
"""A singleton that empty annotations will be set to in [`resolve_signature`][]."""


def resolve_signature(func: typing.Callable[..., typing.Any]) -> inspect.Signature:
    """Get the [`inspect.Signature`][] of `func` with resolved forward annotations.

    !!! warning
        This will use [`eval`][] to resolve string type-hints and forward
        references. This has a slight performance overhead, so attempt to cache
        this info as much as possible.

    Parameters
    ----------
    func : typing.Callable[..., typing.Any]
        The function to get the resolved annotations from.

    Returns
    -------
    inspect.Signature
        A [`inspect.Signature`][] object with all forward reference annotations
        resolved.
    """
    if sys.version_info >= (3, 10):
        return inspect.signature(func, eval_str=True)

    signature = inspect.signature(func)
    resolved_typehints = typing.get_type_hints(func)
    params: typing.List[inspect.Parameter] = []

    none_type = type(None)
    for name, param in signature.parameters.items():
        if isinstance(param.annotation, str):
            param = param.replace(annotation=resolved_typehints[name] if name in resolved_typehints else EMPTY)
        if param.annotation is none_type:
            param = param.replace(annotation=None)
        params.append(param)

    return_annotation = resolved_typehints.get("return", EMPTY)
    if return_annotation is none_type:
        return_annotation = None

    return signature.replace(parameters=params, return_annotation=return_annotation)


def profiled(call: typing.Callable[..., _T]) -> typing.Callable[..., _T]:  # pragma: no cover
    """Decorate a callable and profile each invocation of it.

    Profile results are dumped to stdout.

    !!! warning
        This is NOT part of the public API. It should be considered to be
        internal detail and will likely be removed without prior warning in
        the future. You have been warned!
    """
    import cProfile

    if inspect.iscoroutinefunction(call):
        raise TypeError("cannot profile async calls")

    @functools.wraps(call)
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        print("Profiling", call.__module__ + "." + call.__qualname__)  # noqa: T201 print disallowed.
        cProfile.runctx("result = call(*args, **kwargs)", globals=globals(), locals=locals(), filename=None, sort=1)
        return locals()["result"]

    return wrapped

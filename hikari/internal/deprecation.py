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
"""Deprecation utils."""

from __future__ import annotations

__all__: typing.List[str] = ["deprecated", "warn_deprecated"]

import functools
import inspect
import typing
import warnings

if typing.TYPE_CHECKING:
    T = typing.TypeVar("T", bound=typing.Callable[..., typing.Any])


def warn_deprecated(
    obj: typing.Any,
    /,
    *,
    version: typing.Optional[str] = None,
    alternative: typing.Optional[str] = None,
    stack_level: int = 3,
) -> None:
    """Raise a deprecated warning.

    Parameters
    ----------
    obj: typing.Any
        The object that is deprecated.

    Other Parameters
    ----------------
    version: typing.Optional[str]
        If specified, the version it will be removed in.
    alternative: typing.Optional[str]
        If specified, the alternative to use.
    stack_level: int
        The stack level for the warning. Defaults to `3`.
    """
    if inspect.isclass(obj) or inspect.isfunction(obj):
        obj = f"{obj.__module__}.{obj.__qualname__}"

    version_str = f"version {version}" if version is not None else "a following version"
    message = f"'{obj}' is deprecated and will be removed in {version_str}."

    if alternative is not None:
        message += f" You can use '{alternative}' instead."

    warnings.warn(message, category=DeprecationWarning, stacklevel=stack_level)


def deprecated(
    version: typing.Optional[str] = None, alternative: typing.Optional[str] = None
) -> typing.Callable[[T], T]:
    """Mark a function as deprecated.

    Other Parameters
    ----------------
    version: typing.Optional[str]
        If specified, the version it will be removed in.
    alternative: typing.Optional[str]
        If specified, the alternative to use.
    """

    def decorator(obj: T) -> T:
        type_str = "class" if inspect.isclass(obj) else "function"
        version_str = f"version {version}" if version is not None else "a following version"
        alternative_str = f"You can use `{alternative}` instead." if alternative else ""

        doc = inspect.getdoc(obj) or ""
        doc += (
            "\n"
            "!!! warning\n"
            f"    This {type_str} is deprecated and will be removed in {version_str}.\n"
            f"    {alternative_str}\n"
        )
        obj.__doc__ = doc

        @functools.wraps(obj)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            warn_deprecated(obj, version=version, alternative=alternative, stack_level=3)
            return obj(*args, **kwargs)

        return typing.cast("T", wrapper)

    return decorator

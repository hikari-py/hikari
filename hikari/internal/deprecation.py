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

__all__: typing.List[str] = ["warn_deprecated", "deprecated"]

import functools
import inspect
import typing
import warnings

if typing.TYPE_CHECKING:
    T = typing.TypeVar("T", bound=typing.Callable[..., typing.Any])


def warn_deprecated(obj: typing.Any, additional_information: str, /, *, stack_level: int = 3) -> None:
    """Raise a deprecated warning.

    Parameters
    ----------
    obj: typing.Any
        The object that is deprecated.
    additional_information: str
        Additional information on the deprecation for the user.

    Other Parameters
    ----------------
    stack_level: int
        The stack level for the warning. Defaults to `3`.
    """
    if inspect.isclass(obj):
        action = ("Instantiation of", "class")
        obj = f"{obj.__module__}.{obj.__qualname__}"
    else:
        if inspect.isfunction(obj):
            obj = f"{obj.__module__}.{obj.__qualname__}"

        action = ("Call to", "function/method")

    warnings.warn(
        f"{action[0]} deprecated {action[1]} {obj!r} ({additional_information})",
        category=DeprecationWarning,
        stacklevel=stack_level,
    )


def deprecated(version: str, additional_information: str) -> typing.Callable[[T], T]:
    """Mark a function or object as being deprecated.

    Parameters
    ----------
    version: typing.Any
        The version this function or object is deprecated in.
    additional_information: str
        Additional information on the deprecation for the user.
    """

    def decorator(obj: T) -> T:
        old_doc = inspect.getdoc(obj)

        # If the docstring is inherited we can assume that the deprecation warning was already added there
        if old_doc:
            first_line_end = old_doc.index("\n")
            obj.__doc__ = (
                old_doc[:first_line_end]
                + f"\n\n.. deprecated:: {version}\n    {additional_information}"
                + old_doc[first_line_end:]
            )

        @functools.wraps(obj)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            warn_deprecated(obj, additional_information)
            return obj(*args, **kwargs)

        return typing.cast("T", wrapper)

    return decorator

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
"""Deprecation utils."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("warn_deprecated", "deprecated")

import functools
import inspect
import typing
import warnings

from hikari import _about as hikari_about
from hikari.internal import ux

if typing.TYPE_CHECKING:
    T = typing.TypeVar("T", bound=typing.Callable[..., typing.Any])


def warn_deprecated(name: str, /, *, removal_version: str, additional_info: str, stack_level: int = 3) -> None:
    """Issue a deprecation warning.

    Parameters
    ----------
    name : str
        What is being deprecated
    removal_version : str
        The version it will be removed in.
    additional_info : str
        Additional information on the deprecation for the user.
    stack_level : int
        The stack level to issue the warning in.
    """
    if ux.HikariVersion(hikari_about.__version__) >= ux.HikariVersion(removal_version):
        raise DeprecationWarning(f"{name!r} is passed its removal version ({removal_version})")

    warnings.warn(
        f"[hikari] {name!r} is deprecated and will be removed in {removal_version}. {additional_info}",
        category=DeprecationWarning,
        stacklevel=stack_level,
    )


def _deprecation_wrapper(fn: T, removal_version: str, additional_info: str, obj: typing.Any = None) -> T:
    name = (obj or fn).__name__

    @functools.wraps(fn)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        warn_deprecated(name, removal_version=removal_version, additional_info=additional_info)
        return fn(*args, **kwargs)

    return typing.cast("T", wrapper)


def deprecated(*, deprecation_version: str, removal_version: str, additional_info: str) -> typing.Callable[[T], T]:
    """Mark a function or object as being deprecated.

    Parameters
    ----------
    deprecation_version : str
        The version it got deprecated in.
    removal_version : str
        The version it will be removed in.
    additional_info : str
        Additional information on the deprecation for the user.
    """

    def decorator(obj: T) -> T:
        old_doc = inspect.getdoc(obj) or ""

        first_line_end = old_doc.find("\n")
        obj.__doc__ = (
            old_doc[:first_line_end]
            + f"\n\n.. deprecated:: {deprecation_version}\n"
            + f"    It is scheduled for removal in `{removal_version}`.\n\n"
            + f"    {additional_info}\n"
            + old_doc[first_line_end:]
        )

        if inspect.isclass(obj):
            # We want to warn about the deprecation in both the init and the subclass of a class
            obj.__init__ = _deprecation_wrapper(obj.__init__, removal_version, additional_info, obj=obj)
            obj.__init_subclass__ = _deprecation_wrapper(
                obj.__init_subclass__, removal_version, additional_info, obj=obj
            )
        else:
            obj = _deprecation_wrapper(obj, removal_version, additional_info)

        return typing.cast("T", obj)

    return decorator

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

__all__: typing.Sequence[str] = ("deprecated", "warn_deprecated", "check_if_past_removal")

import typing
import warnings

from hikari import _about as hikari_about
from hikari.internal import ux


def check_if_past_removal(what: str, /, *, removal_version: str) -> None:
    """Check if a deprecation is passed its removal version.

    Parameters
    ----------
    what : str
        What is being deprecated.

    Other Parameters
    ----------------
    removal_version : str
        The version it will be removed in.

    Raises
    ------
    DeprecationWarning
        If the deprecated item is past its removal version.
    """
    if ux.HikariVersion(hikari_about.__version__) >= ux.HikariVersion(removal_version):
        raise DeprecationWarning(f"{what} is passed its removal version ({removal_version})")


def warn_deprecated(
    what: str, /, *, removal_version: str, additional_info: str, stack_level: int = 3, quote: bool = True
) -> None:
    """Issue a deprecation warning.

    If the item is past its deprecation version, an error will be raised instead.

    Parameters
    ----------
    what : str
        What is being deprecated.

    Other Parameters
    ----------------
    removal_version : str
        The version it will be removed in.
    additional_info : str
        Additional information on the deprecation for the user.
    stack_level : int
        The stack level to issue the warning in.
    quote : bool
        Whether to quote [`what`][] when displaying the deprecation

    Raises
    ------
    DeprecationWarning
        If the deprecated item is past its removal version.
    """
    if quote:
        what = repr(what)

    check_if_past_removal(what, removal_version=removal_version)

    warnings.warn(
        f"{what} is deprecated and will be removed in `{removal_version}`. {additional_info}",
        category=DeprecationWarning,
        stacklevel=stack_level,
    )


if typing.TYPE_CHECKING:
    from typing_extensions import deprecated

else:

    def deprecated(*args, **kwargs):
        """Mark a function, overload, or class as deprecated for type-checkers.

        This has no runtime side-effects.
        """
        return lambda value: value

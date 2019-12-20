#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Decorators used to document, deprecate, or incubate other components in this API.
"""
import asyncio
import functools
import inspect
import textwrap
import warnings


def _format_name(element):
    if asyncio.iscoroutinefunction(element):
        return f"`coroutine function {element.__module__}.{element.__qualname__}{inspect.signature(element)}`"
    if inspect.isfunction(element):
        return f"`function {element.__module__}.{element.__qualname__}{inspect.signature(element)}`"
    if inspect.isclass(element):
        if issubclass(element, type):
            type_name = "metaclass"
        else:
            type_name = "class"
        return f"`{type_name} {element.__module__}.{element.__qualname__}`"
    if isinstance(element, str):
        return f"`{element.replace('`', '')}`"
    return f"{element!r}"


def _append_doc(element, text):
    element.__doc__ = textwrap.dedent(element.__doc__ or "") + "\n\n" + text


def _warning_rst(text):
    return "Warning:\n" + textwrap.indent(text, " " * 4)


def _warn_new(element, warning, category):
    old_new = element.__new__

    @functools.wraps(element.__new__)
    def __new__(cls, *args, **kwargs):
        warnings.warn(warning, category, stacklevel=2)
        return old_new(cls, *args, **kwargs)

    element.__new__ = __new__
    _append_doc(element, _warning_rst(warning))
    return element


def _warn_func(element, warning, category):
    @functools.wraps(element)
    def func(*args, **kwargs):
        warnings.warn(warning, category, stacklevel=2)
        return element(*args, **kwargs)

    _append_doc(func, _warning_rst(warning))
    return func


def deprecated(*alternatives, element_name=None):
    """
    Creates a decorator for a given element to mark it as deprecated with a warning when being invoked/used
    for the first time.
    """

    def decorator(element):
        wrap = _warn_new if inspect.isclass(element) else _warn_func
        name = _format_name(element) if element_name is None else element_name
        message = f"{name} is deprecated and will be removed in a future release without further warning."

        if alternatives:
            message += "\n\nAlternatives to consider:\n    - "
            message += "\n    - ".join(map(_format_name, alternatives))

        return wrap(element, message, DeprecationWarning)

    return decorator


def incubating(*, message=""):
    """
    Annotate the element as incubating (it is still experimental or being planned, and may not be
    final).
    """

    def decorator(element):
        _append_doc(
            element,
            _warning_rst(
                "This feature is currently incubating. This means that it may have breaking changes or be "
                f"removed/replaced without warning. Please treat it as an experimental feature. {message}"
            ),
        )
        return element

    return decorator

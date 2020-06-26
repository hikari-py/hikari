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
"""Barebones implementation of a cache that never stores anything.

This is used to enable compatibility with REST applications and stateless
bots where desired.
"""
from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = []

import functools
import inspect
import typing

from hikari import errors
from hikari.api import cache


def _fail(*_: typing.Any, **__: typing.Any) -> typing.NoReturn:
    raise errors.HikariError(
        "This component has not got a cache enabled, and is stateless. "
        "Operations relying on a cache will always fail."
    )


# Generate a stub from the implementation dynamically. This way it is one less
# thing to keep up to date in the future.
@typing.no_type_check
def _generate():
    namespace = {
        "__doc__": (
            "A stateless cache implementation that implements dummy operations for "
            "each of the required attributes of a functional cache implementation. "
            "Any descriptors will always return `NotImplemented`, and any methods "
            "will always raise `hikari.errors.HikariError` when being invoked."
        ),
        "__init__": lambda *_, **__: None,
        "__init_subclass__": staticmethod(lambda *args, **kwargs: _fail(*args, **kwargs)),
        "__slots__": (),
        "__module__": __name__,
    }

    for name, member in inspect.getmembers(cache.ICacheComponent):
        if name in namespace:
            # Skip stuff we already have defined above.
            continue

        if inspect.isabstract(member):
            namespace[name] = NotImplemented

        if getattr(member, "__isabstractmethod__", False) is True:
            # If we were to inspect an instance of the class, it would invoke the properties to
            # get their value. Thus, it is not considered a safe thing to do to have them raise
            # exceptions on invocation.
            if hasattr(member, "__get__"):
                doc = getattr(member, "__doc__", None)
                new_member = property(lambda self: NotImplemented, _fail, lambda self: NotImplemented, doc)
            else:
                new_member = functools.wraps(member)(_fail)

            namespace[name] = new_member

    return typing.final(type("StatelessCacheImpl", (cache.ICacheComponent,), namespace))


# noinspection PyTypeChecker
StatelessCacheImpl: typing.Final[typing.Type[cache.ICacheComponent]] = _generate()

del _generate

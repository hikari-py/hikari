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
Utilities for creating and naming loggers in this library in a consistent way.
"""
import inspect
import logging
import typing
import uuid

from hikari.internal_utilities import type_hints


def get_named_logger(obj: type_hints.Nullable[typing.Any] = None, *extra_objs: typing.Any) -> logging.Logger:
    """
    Builds an appropriately named logger. If called with no arguments or with `NoneType`, the current module is used
    to produce the name. If this is run from a location where no module info is available, a random UUID is used
    instead.

    If the passed object is an instance of a class, the class is used instead.

    If a class is provided/used, then the fully qualified package and class name is used to name the logger.

    If a string is provided, then the string is used as the name. This is not recommended.

    Args:
        obj:
            the object to study to produce a logger for.
        extra_objs:
            optional extra components to add to the end of the logger name.

    Returns:
        a created logger.
    """
    try:
        if obj is None:
            stack = inspect.stack()
            frame = stack[1]
            module_name = frame[0]

            # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
            # prevents "leaking memory" on the interpreter stack if the user disabled gc cyclic
            # reference detection.
            del stack, frame

            obj = inspect.getmodule(module_name)

            # No module was found... maybe we are in an interactive session or some compiled module?
            if obj is None:
                raise AttributeError
            else:
                obj = obj.__name__
        elif not isinstance(obj, str):
            if not isinstance(obj, type):
                obj = type(obj)

            obj = f"{obj.__module__}.{obj.__qualname__}"
    except AttributeError:
        obj = str(uuid.uuid4())

    if extra_objs:
        extras = ", ".join(map(str, extra_objs))
        obj = f"{obj}[{extras}]"

    return logging.getLogger(obj)

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
"""Utilities for creating and naming loggers in this library in a consistent way."""
__all__ = ["get_named_logger"]

import logging
import typing


def get_named_logger(obj: typing.Any, *extra_objs: typing.Any) -> logging.Logger:
    """Builds an appropriately named logger.

    If the passed object is an instance of a class, the class is used instead.

    If a class is provided/used, then the fully qualified package and class name is used to name the logger.

    If a string is provided, then the string is used as the name. This is not recommended.

    Parameters
    ----------
    obj
        The object to study to produce a logger for.
    extra_objs
        optional extra components to add to the end of the logger name.

    Returns
    -------
    :obj:`logging.Logger`
        A created logger.
    """
    if not isinstance(obj, str):
        if not isinstance(obj, type):
            obj = type(obj)

        obj = f"{obj.__module__}.{obj.__qualname__}"

    if extra_objs:
        extras = ", ".join(map(str, extra_objs))
        obj = f"{obj}[{extras}]"

    return logging.getLogger(obj)

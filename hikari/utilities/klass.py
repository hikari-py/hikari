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
"""Various metatypes and utilities for configuring classes."""

from __future__ import annotations

__all__ = ["get_logger", "SingletonMeta", "Singleton"]

import abc
import logging
import typing


def get_logger(cls: typing.Union[typing.Type, typing.Any], *additional_args: str) -> logging.Logger:
    """Get an appropriately named logger for the given class or object.

    Parameters
    ----------
    cls : typing.Type OR object
        A type or instance of a type to make a logger in the name of.
    *additional_args : str
        Additional tokens to append onto the logger name, separated by `.`.
        This is useful in some places to append info such as shard ID to each
        logger to enable shard-specific logging, for example.

    Returns
    -------
    logging.Logger
        The logger to use.
    """
    cls = cls if isinstance(cls, type) else type(cls)
    return logging.getLogger(".".join((cls.__module__, cls.__qualname__, *additional_args)))


class SingletonMeta(abc.ABCMeta):
    """Metaclass that makes the class a singleton.

    Once an instance has been defined at runtime, it will exist until the
    interpreter that created it is terminated.

    Examples
    --------
        >>> class Unknown(metaclass=SingletonMeta):
        ...     def __init__(self):
        ...         print("Initialized an Unknown!")

        >>> Unknown() is Unknown()    # True

    !!! note
        The constructors of instances of this metaclass must not take any
        arguments other than `self`.

    !!! warning
        Constructing instances of class instances of this metaclass may not be
        thread safe.
    """

    __slots__ = ()

    ___instances___ = {}

    # Disable type-checking to hide a bug in IntelliJ for the time being.
    @typing.no_type_check
    def __call__(cls):
        if cls not in SingletonMeta.___instances___:
            SingletonMeta.___instances___[cls] = super().__call__()
        return SingletonMeta.___instances___[cls]


class Singleton(abc.ABC, metaclass=SingletonMeta):
    """Base type for anything implementing the `SingletonMeta` metaclass.

    Once an instance has been defined at runtime, it will exist until the
    interpreter that created it is terminated.

    Examples
    --------
        >>> class MySingleton(Singleton):
        ...    pass

        >>> assert MySingleton() is MySingleton()

    !!! note
        The constructors of child classes must not take any arguments other than
        `self`.

    !!! warning
        Constructing instances of this class or derived classes may not be
        thread safe.
    """

    __slots__ = ()

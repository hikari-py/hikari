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

__all__: typing.List[str] = ["get_logger", "SingletonMeta", "Singleton"]

import abc
import logging
import typing


def get_logger(obj: typing.Union[typing.Type[typing.Any], typing.Any], *additional_args: str) -> logging.Logger:
    """Get an appropriately named logger for the given class or object.

    Parameters
    ----------
    obj : typing.Type or object
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
    if isinstance(obj, str):
        return logging.getLogger(obj)

    obj = obj if isinstance(obj, type) else type(obj)
    return logging.getLogger(".".join((obj.__module__, obj.__qualname__, *additional_args)))


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

    ___instances___: typing.Dict[typing.Type[typing.Any], typing.Any] = {}

    def __call__(cls, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if cls not in SingletonMeta.___instances___:
            SingletonMeta.___instances___[cls] = super().__call__(*args, **kwargs)
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

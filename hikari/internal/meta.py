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
"""Various functional types and metatypes.

|internal|
"""
__all__ = ["SingletonMeta", "Singleton"]

import abc
import inspect
import typing

from hikari.internal import more_collections


class SingletonMeta(type):
    """Metaclass that makes the class a singleton.

    Once an instance has been defined at runtime, it will exist until the
    interpreter that created it is terminated.

    Example
    -------
    .. code-block:: python

        >>> class Unknown(metaclass=SingletonMeta):
        ...     def __init__(self):
        ...         print("Initialized an Unknown!")

        >>> Unknown() is Unknown()    # True

    Note
    ----
    The constructors of instances of this metaclass must not take any arguments
    other than ``self``.

    Warning
    -------
    Constructing instances of class instances of this metaclass may not be
    thread safe.
    """

    # pylint: disable=E1136
    ___instance_dict_t___ = more_collections.WeakKeyDictionary[typing.Type[typing.Any], typing.Any]
    # pylint: enable=E1136
    ___instances___: ___instance_dict_t___ = more_collections.WeakKeyDictionary()
    __slots__ = ()

    def __call__(cls):
        if cls not in SingletonMeta.___instances___:
            SingletonMeta.___instances___[cls] = super().__call__()
        return SingletonMeta.___instances___[cls]


class Singleton(metaclass=SingletonMeta):
    """Base type for anything implementing the :obj:`~SingletonMeta` metaclass.

    Once an instance has been defined at runtime, it will exist until the
    interpreter that created it is terminated.

    Example
    -------
    .. code-block:: python

        >>> class MySingleton(Singleton):
        ...    pass

        >>> assert MySingleton() is MySingleton()

    Note
    ----
    The constructors of child classes must not take any arguments other than
    ``self``.

    Warning
    -------
    Constructing instances of this class or derived classes may not be thread
    safe.
    """


class UniqueFunctionMeta(abc.ABCMeta):
    """Metaclass for mixins that are expected to provide unique function names.

    If subclassing from two mixins that are derived from this type and both
    mixins provide the same function, a type error is raised when the class is
    defined.

    Note
    ----
    This metaclass derives from :obj:`~abc.ABCMeta`, and thus is compatible
    with abstract method conduit.
    """

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        routines = {}

        for base in bases:
            for identifier, method in inspect.getmembers(base, inspect.isroutine):
                if identifier.startswith("__"):
                    continue

                if identifier in routines and method != routines[identifier]:
                    raise TypeError(
                        f"Conflicting methods {routines[identifier].__qualname__} and {method.__qualname__} found."
                    )

                routines[identifier] = method

        return super().__prepare__(name, bases, **kwargs)

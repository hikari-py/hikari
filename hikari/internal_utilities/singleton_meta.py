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
"""Singleton metaclass"""
__all__ = ["SingletonMeta"]


class SingletonMeta(type):
    """Metaclass that makes the class a singleton. 
    
    Once an instance has been defined at runtime, it will exist until the interpreter 
    that created it is terminated.

    Example
    --------
    .. code-block:: python

        >>> class Unknown(metaclass=SingletonMeta):
        ...     def __init__(self):
        ...         print("Initialized an Unknown!")
        >>> Unknown() is Unknown()    # True

    Note
    ----
    The constructors of these classes must not take any arguments other than ``self``.

    Warning
    -------
    This is not thread safe.
    """

    ___instances___ = {}
    __slots__ = ()

    def __call__(cls):
        if cls not in SingletonMeta.___instances___:
            SingletonMeta.___instances___[cls] = super().__call__()
        return SingletonMeta.___instances___[cls]

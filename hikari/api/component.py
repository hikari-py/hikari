# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Base interface for any internal components of an application."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IComponent"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari.api import rest as rest_app


class IComponent(abc.ABC):
    """A component that makes up part of the application.

    Objects that derive from this should usually be attributes on the
    `hikari.api.rest.IRESTApp` object.

    Examples
    --------
    See the source code for `hikari.api.entity_factory.IEntityFactoryComponent`,
    `hikari.api.cache.ICacheComponent`, and
    `hikari.api.event_dispatcher.IEventDispatcherComponent`
    for examples of usage.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def app(self) -> rest_app.IRESTApp:
        """Return the Application that owns this component.

        Returns
        -------
        hikari.api.rest.IRESTApp
            The application implementation that owns this component.
        """

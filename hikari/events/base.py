#!/usr/bin/env python3
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
"""Bases for components and entities that are used to describe Discord gateway events."""
from __future__ import annotations

__all__ = ["HikariEvent", "get_required_intents_for", "requires_intents", "no_catch", "is_no_catch_event"]

import abc
import typing

import attr

from hikari import bases
from hikari.internal import marshaller
from hikari.internal import more_collections

if typing.TYPE_CHECKING:
    from hikari import intents


# Base event, is not deserialized
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class HikariEvent(bases.Entity, abc.ABC):
    """The base class that all events inherit from."""


_HikariEventT = typing.TypeVar("_HikariEventT", contravariant=True)
_REQUIRED_INTENTS_ATTR: typing.Final[str] = "___required_intents___"
_NO_THROW_ATTR: typing.Final[str] = "___no_throw___"


def get_required_intents_for(event_type: typing.Type[HikariEvent]) -> typing.Collection[intents.Intent]:
    """Retrieve the intents that are required to listen to an event type.

    Parameters
    ----------
    event_type : typing.Type[HikariEvent]
        The event type to get required intents for.

    Returns
    -------
    typing.Collection[hikari.intents.Intent]
        Collection of acceptable subset combinations of intent needed to
        be able to receive the given event type.
    """
    return getattr(event_type, _REQUIRED_INTENTS_ATTR, more_collections.EMPTY_COLLECTION)


def requires_intents(
    first: intents.Intent, *rest: intents.Intent
) -> typing.Callable[[typing.Type[_HikariEventT]], typing.Type[_HikariEventT]]:
    """Decorate an event type to define what intents it requires.

    Parameters
    ----------
    first : hikari.intents.Intent
        First combination of intents that are acceptable in order to receive
        the decorated event type.
    *rest : hikari.intents.Intent
        Zero or more additional combinations of intents to require for this
        event to be subscribed to.

    """

    def decorator(cls: typing.Type[_HikariEventT]) -> typing.Type[_HikariEventT]:
        setattr(cls, _REQUIRED_INTENTS_ATTR, [first, *rest])
        return cls

    return decorator


def no_catch():
    """Decorate an event type to indicate errors should not be handled.

    This is useful for exception event types that you do not want to
    have invoked recursively.
    """

    def decorator(cls: typing.Type[_HikariEventT]) -> typing.Type[_HikariEventT]:
        setattr(cls, _NO_THROW_ATTR, True)
        return cls

    return decorator


def is_no_catch_event(obj: typing.Union[_HikariEventT, typing.Type[_HikariEventT]]) -> bool:
    """Return True if this event is marked as `no_catch`."""
    return getattr(obj, _NO_THROW_ATTR, False)

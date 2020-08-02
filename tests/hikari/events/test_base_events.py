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
import attr

from hikari.events import base_events
from hikari.models import intents


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyGuildEVent(base_events.Event):
    pass


@base_events.no_recursive_throw()
@base_events.requires_intents(intents.Intent.GUILD_PRESENCES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyPresenceEvent(base_events.Event):
    pass


@base_events.no_recursive_throw()
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ErrorEvent(base_events.Event):
    pass


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyGuildDerivedEvent(DummyGuildEVent):
    pass


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class DummyPresenceDerivedEvent(DummyPresenceEvent):
    pass


def test_is_no_recursive_throw_event_marked():
    assert base_events.is_no_recursive_throw_event(DummyPresenceEvent)
    assert base_events.is_no_recursive_throw_event(ErrorEvent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildEVent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildDerivedEvent)


def test_requires_intents():
    assert list(base_events.get_required_intents_for(DummyGuildEVent)) == [intents.Intent.GUILDS]
    assert list(base_events.get_required_intents_for(DummyPresenceEvent)) == [intents.Intent.GUILD_PRESENCES]
    assert list(base_events.get_required_intents_for(ErrorEvent)) == []


def test_inherited_requires_intents():
    assert list(base_events.get_required_intents_for(DummyPresenceDerivedEvent)) == [intents.Intent.GUILD_PRESENCES]
    assert list(base_events.get_required_intents_for(DummyGuildDerivedEvent)) == [intents.Intent.GUILDS]


def test_inherited_is_no_recursive_throw_event():
    assert base_events.is_no_recursive_throw_event(DummyPresenceDerivedEvent)
    assert not base_events.is_no_recursive_throw_event(DummyGuildDerivedEvent)

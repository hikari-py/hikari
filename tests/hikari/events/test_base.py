import pytest
import attr

import hikari.events.base as base
from hikari.models import intents


@base.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class FooEvent(base.Event):
    pass


@base.no_catch()
@base.requires_intents(intents.Intent.GUILD_PRESENCES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class BarEvent(base.Event):
    pass


@base.no_catch()
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ErrorEvent(base.Event):
    pass


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class FooInheritedEvent(FooEvent):
    pass


@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class BarInheritedEvent(BarEvent):
    pass


def test_no_catch_marked():
    assert base.is_no_catch_event(BarEvent)
    assert base.is_no_catch_event(ErrorEvent)
    assert not base.is_no_catch_event(FooEvent)
    assert not base.is_no_catch_event(FooInheritedEvent)


def test_requires_intents():
    assert list(base.get_required_intents_for(FooEvent)) == [intents.Intent.GUILDS]
    assert list(base.get_required_intents_for(BarEvent)) == [intents.Intent.GUILD_PRESENCES]
    assert list(base.get_required_intents_for(ErrorEvent)) == []


def test_inherited_requires_intents():
    assert list(base.get_required_intents_for(BarInheritedEvent)) == [intents.Intent.GUILD_PRESENCES]
    assert list(base.get_required_intents_for(FooInheritedEvent)) == [intents.Intent.GUILDS]


def test_inherited_no_catch():
    assert base.is_no_catch_event(BarInheritedEvent)
    assert not base.is_no_catch_event(FooInheritedEvent)

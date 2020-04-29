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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
from hikari import intents
from hikari.events import base
from hikari.internal import more_collections

# Base event, is not deserialized
class TestHikariEvent:
    ...


def test_get_required_intents_for():
    class StubEvent:
        ___required_intents___ = [intents.Intent.DIRECT_MESSAGES]

    base.get_required_intents_for(StubEvent()) == [intents.Intent.DIRECT_MESSAGES]


def test_get_required_intents_for_when_none_required():
    class StubEvent:
        ...

    base.get_required_intents_for(StubEvent()) == more_collections.EMPTY_COLLECTION


def test_requires_intents():
    @base.requires_intents(intents.Intent.DIRECT_MESSAGES, intents.Intent.DIRECT_MESSAGE_REACTIONS)
    class StubEvent:
        ...

    assert StubEvent().___required_intents___ == [
        intents.Intent.DIRECT_MESSAGES,
        intents.Intent.DIRECT_MESSAGE_REACTIONS,
    ]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import pytest

from hikari.orm.models import emojis
from hikari.orm.models import messages
from hikari.orm.models import reactions
from tests.hikari import _helpers


@pytest.mark.model
def test_parse_Reaction():
    m = _helpers.mock_model(messages.Message)
    e = _helpers.mock_model(emojis.UnicodeEmoji)
    r = reactions.Reaction(9, e, m)
    assert r.message is m
    assert r.emoji is e
    assert r.count == 9
    r.__repr__()

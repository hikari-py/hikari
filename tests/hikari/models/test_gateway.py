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

import datetime

from hikari.models import gateway


def test_SessionStartLimit_used_property():
    obj = gateway.SessionStartLimit(
        total=100, remaining=2, reset_after=datetime.timedelta(seconds=1), max_concurrency=1
    )
    obj.total = 100
    obj.remaining = 12

    assert obj.used == 88


def test_SessionStartLimit_reset_at_property():
    obj = gateway.SessionStartLimit(
        total=100, remaining=2, reset_after=datetime.timedelta(hours=1, days=10), max_concurrency=1
    )
    obj._created_at = datetime.datetime(2020, 7, 22, 22, 22, 36, 988017, tzinfo=datetime.timezone.utc)

    assert obj.reset_at == datetime.datetime(2020, 8, 1, 23, 22, 36, 988017, tzinfo=datetime.timezone.utc)

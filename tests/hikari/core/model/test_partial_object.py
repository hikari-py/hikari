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
import hikari.core.model.object


@pytest.mark.model
def test_PartialObject_just_id():
    assert hikari.core.model.object.PartialObject.from_dict({"id": "123456"}) is not None


@pytest.mark.model
def test_PartialObject_dynamic_attrs():
    po = hikari.core.model.object.PartialObject.from_dict({"id": "123456", "foo": 69, "bar": False})
    assert po.id == 123456
    assert po.foo == 69
    assert po.bar is False

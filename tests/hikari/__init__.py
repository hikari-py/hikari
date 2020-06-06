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
import asyncio
import contextlib
import sys

import pytest

_real_new_event_loop = asyncio.new_event_loop


def _new_event_loop():
    loop = _real_new_event_loop()
    loop.set_debug(True)

    with contextlib.suppress(AttributeError):
        # provisional since py37
        sys.set_coroutine_origin_tracking_depth(20)

    return loop


asyncio.new_event_loop = _new_event_loop


_pytest_parametrize = pytest.mark.parametrize


def parametrize(*args, **kwargs):
    # Force ids to be strified by default for readability.
    kwargs.setdefault("ids", repr)
    return _pytest_parametrize(*args, **kwargs)


pytest.mark.parametrize = parametrize

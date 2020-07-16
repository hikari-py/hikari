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
import sys

import pytest

sys.set_coroutine_origin_tracking_depth(100)


class TestingPolicy(asyncio.DefaultEventLoopPolicy):
    def set_event_loop(self, loop) -> None:
        loop.set_debug(True)
        super().set_event_loop(loop)


asyncio.set_event_loop_policy(TestingPolicy())


_pytest_parametrize = pytest.mark.parametrize


def parametrize(*args, **kwargs):
    # Force ids to be strified by default for readability.
    kwargs.setdefault("ids", repr)
    return _pytest_parametrize(*args, **kwargs)


pytest.mark.parametrize = parametrize

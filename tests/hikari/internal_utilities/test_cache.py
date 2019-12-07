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
import functools
from unittest import mock

from hikari.internal_utilities import cache


def test_init_CachedCall_makes_partial():
    def call():
        pass

    cached_call = cache.CachedCall(call)
    assert isinstance(cached_call._call, functools.partial)


def test_init_CachedCall_sets_value_to_sentinel():
    def call():
        pass

    cached_call = cache.CachedCall(call)
    assert cached_call._value is cached_call._sentinel


def test_call_CachedCall_first_time_sets_value():
    call = mock.MagicMock(return_value=27)

    cached_call = cache.CachedCall(call, 9, k=18)

    cached_call()

    call.assert_called_with(9, k=18)

    assert cached_call._value == 27


def test_call_CachedCall_first_time_returns_value():
    call = mock.MagicMock(return_value=27)

    cached_call = cache.CachedCall(call, 9, k=18)

    assert cached_call() == 27


def test_call_CachedCall_second_time_does_not_reset_value():
    call = mock.MagicMock(return_value=27)
    cached_call = cache.CachedCall(call, 9, k=18)

    cached_call()
    sentinel = object()
    cached_call._value = sentinel
    cached_call()
    call.assert_called_once()


def test_call_CachedCall_second_time_returns_value():
    call = mock.MagicMock(return_value=27)
    cached_call = cache.CachedCall(call, 9, k=18)

    cached_call()
    sentinel = object()
    cached_call._value = sentinel
    assert cached_call() is sentinel


def test_CachedCall_wrap():
    spy = mock.MagicMock()
    sentinel = object()

    @cache.CachedCall.wrap(9, 18, 27, name="nekokatt")
    def test(a, b, c, *, name):
        spy(a, b, c, name=name)
        return sentinel

    assert test() is sentinel
    assert test() is sentinel
    spy.assert_called_once_with(9, 18, 27, name="nekokatt")


def test_CachedCall___qualname__():
    def potato():
        pass

    cached_call = cache.CachedCall(potato)

    assert cached_call.__qualname__ == "test_CachedCall___qualname__.<locals>.potato"

# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import inspect

import mock
import pytest

from hikari import users
from hikari.api import cache
from hikari.impl import stateless_cache


class TestStatelessCache:
    @pytest.fixture
    def component(self):
        return stateless_cache.StatelessCacheImpl()

    def test_get_me(self, component):
        me = mock.Mock(spec_set=users.OwnUser)
        component._me = me
        assert component.get_me() is me

    def test_set_me(self, component):
        me = mock.Mock(spec_set=users.OwnUser)
        component._me = object()
        component.set_me(me)
        assert component._me is me

    @pytest.mark.parametrize("method", sorted(cache.MutableCache.__abstractmethods__ - {"get_me", "set_me", "app"}))
    def test_stateless_method_raises_NotImplementedError(self, component, method):
        with pytest.raises(NotImplementedError):
            method_impl = getattr(component, method)
            arg_count = len(inspect.signature(method_impl).parameters)
            args = [object()] * arg_count
            method_impl(*args)

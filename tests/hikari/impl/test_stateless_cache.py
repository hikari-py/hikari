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
import inspect

import mock
import pytest

from hikari.api import cache
from hikari.api import rest
from hikari.impl import stateless_cache
from hikari.models import users


class TestStatelessCache:
    @pytest.fixture
    def app(self):
        return mock.Mock(spec_set=rest.IRESTApp)

    @pytest.fixture
    def component(self, app):
        return stateless_cache.StatelessCacheImpl(app)

    def test_app_property(self, component, app):
        assert component.app is app

    def test_get_me(self, component):
        me = mock.Mock(spec_set=users.OwnUser)
        component._me = me
        assert component.get_me() is me

    def test_set_me(self, component):
        me = mock.Mock(spec_set=users.OwnUser)
        component._me = object()
        component.set_me(me)
        assert component._me is me

    @pytest.mark.parametrize("method", sorted(cache.ICacheComponent.__abstractmethods__ - {"get_me", "set_me", "app"}))
    def test_stateless_method_raises_NotImplementedError(self, component, method):
        with pytest.raises(NotImplementedError):
            method_impl = getattr(component, method)
            arg_count = len(inspect.signature(method_impl).parameters)
            args = [mock.Mock()] * arg_count
            method_impl(*args)

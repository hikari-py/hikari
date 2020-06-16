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
import aiohttp
import mock

from hikari.net import tracing


class TestBaseTracer:
    def test_sets_logger(self):
        logger = mock.MagicMock()
        impl = type("Impl", (tracing.BaseTracer,), {})(logger)
        assert impl.logger is logger

    def test_trace_config_is_cached(self):
        logger = mock.MagicMock()
        impl = type("Impl", (tracing.BaseTracer,), {})(logger)
        tc = impl.trace_config
        assert impl.trace_config is tc

    def test_trace_config_is_instance_of_TraceConfig(self):
        logger = mock.MagicMock()
        impl = type("Impl", (tracing.BaseTracer,), {})(logger)
        assert isinstance(impl.trace_config, aiohttp.TraceConfig)

    def test_trace_config_collects_methods_matching_name_prefix(self):
        class Impl(tracing.BaseTracer):
            def on_connection_create_end(self):
                pass

            def this_should_be_ignored(self):
                pass

        i = Impl(mock.MagicMock())

        assert i.on_connection_create_end in i.trace_config.on_connection_create_end

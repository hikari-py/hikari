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

from __future__ import annotations

import logging
import typing
from concurrent import futures

from hikari import http_settings
from hikari.api import rest_app
from hikari.impl import cache as cache_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.internal import helpers
from hikari.internal import urls
from hikari.rest import client as rest_client_

if typing.TYPE_CHECKING:
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_


class RESTAppImpl(rest_app.IRESTApp):
    def __init__(
        self,
        config: http_settings.HTTPSettings,
        debug: bool = False,
        token: typing.Optional[str] = None,
        token_type: typing.Optional[str] = None,
        rest_url: str = urls.REST_API_URL,
        version: int = 6,
    ) -> None:
        self._logger = helpers.get_logger(self)
        self._rest = rest_client_.RESTClient(
            app=self,
            config=config,
            debug=debug,
            token=token,
            token_type=token_type,
            rest_url=rest_url,
            version=version,
        )
        self._cache = cache_impl.CacheImpl()
        self._entity_factory = entity_factory_impl.EntityFactoryImpl()

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def close(self) -> None:
        await self._rest.close()

    @property
    def thread_pool(self) -> typing.Optional[futures.ThreadPoolExecutor]:
        # XXX: fixme
        return None

    @property
    def rest(self) -> rest_client_.RESTClient:
        return self._rest

    @property
    def cache(self) -> cache_.ICache:
        return self._cache

    @property
    def entity_factory(self) -> entity_factory_.IEntityFactory:
        return self._entity_factory

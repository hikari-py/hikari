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
"""Basic implementation the components for a single-process bot."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["BotAppImpl"]

import asyncio
import inspect
import logging
import os
import platform
import sys
import typing

from hikari.api import bot
from hikari.impl import cache as cache_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_manager
from hikari.impl import gateway_zookeeper
from hikari.impl import stateless_cache as stateless_cache_impl
from hikari.models import presences
from hikari.net import http_settings as http_settings_
from hikari.net import rate_limits
from hikari.net import rest
from hikari.net import strings
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import concurrent.futures
    import datetime

    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_consumer as event_consumer_
    from hikari.api import event_dispatcher as event_dispatcher_
    from hikari.events import base as base_events
    from hikari.models import gateway as gateway_models
    from hikari.models import intents as intents_

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotAppImpl(gateway_zookeeper.AbstractGatewayZookeeper, bot.IBotApp):
    """Implementation of an auto-sharded bot application.

    Parameters
    ----------
    config : hikari.utilities.undefined.UndefinedType or hikari.net.http_settings.HTTPSettings
        Optional aiohttp settings to apply to the REST components, gateway
        shards, and voice websockets. If undefined, then sane defaults are used.
    debug : bool
        Defaulting to `False`, if `True`, then each payload sent and received
        on the gateway will be dumped to debug logs, and every REST API request
        and response will also be dumped to logs. This will provide useful
        debugging context at the cost of performance. Generally you do not
        need to enable this.
    gateway_compression : bool
        Defaulting to `True`, if `True`, then zlib transport compression is used
        for each shard connection. If `False`, no compression is used.
    gateway_version : int
        The version of the gateway to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to using v6.
    initial_activity : hikari.models.presences.Activity or None or hikari.utilities.undefined.UndefinedType
        The initial activity to have on each shard.
    initial_activity : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
        The initial status to have on each shard.
    initial_idle_since : datetime.datetime or None or hikari.utilities.undefined.UndefinedType
        The initial time to show as being idle since, or `None` if not idle,
        for each shard.
    initial_idle_since : bool or hikari.utilities.undefined.UndefinedType
        If `True`, each shard will appear as being AFK on startup. If `False`,
        each shard will appear as _not_ being AFK.
    intents : hikari.models.intents.Intent or None
        The intents to use for each shard. If `None`, then no intents are
        passed. Note that on the version `7` gateway, this will cause an
        immediate connection close with an error code.
    large_threshold : int
        The number of members that need to be in a guild for the guild to be
        considered large. Defaults to the maximum, which is `250`.
    logging_level : str or int or None
        If not `None`, then this will be the logging level set if you have not
        enabled logging already. In this case, it should be a valid
        `logging` level that can be passed to `logging.basicConfig`. If you have
        already initialized logging, then this is irrelevant and this
        parameter can be safely ignored. If you set this to `None`, then no
        logging will initialize if you have a reason to not use any logging
        or simply wish to initialize it in your own time instead.

        !!! note
            Initializating logging means already have a handler in the root logger.
            This is usually achived by calling `logging.basicConfig` or adding the
            handler another way.
    rest_version : int
        The version of the REST API to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to v6.
    shard_ids : typing.Set[int] or undefined.UndefinedType
        A set of every shard ID that should be created and started on startup.
        If left undefined along with `shard_count`, then auto-sharding is used
        instead, which is the default.
    shard_count : int or undefined.UndefinedType
        The number of shards in the entire application. If left undefined along
        with `shard_ids`, then auto-sharding is used instead, which is the
        default.
    stateless : bool
        If `True`, the bot will not implement a cache, and will be considered
        stateless. If `False`, then a cache will be used (this is the default).
    token : str
        The bot token to use. This should not start with a prefix such as
        `Bot `, but instead only contain the token itself.

    !!! note
        The default parameters for `shard_ids` and `shard_count` are marked as
        undefined. When both of these are left to the default value, the
        application will use the Discord-provided recommendation for the number
        of shards to start.

        If only one of these two parameters are specified, expect a `TypeError`
        to be raised.

        Likewise, all shard_ids must be greater-than or equal-to `0`, and
        less than `shard_count` to be valid. Failing to provide valid
        values will result in a `ValueError` being raised.

    !!! note
        If all four of `initial_activity`, `initial_idle_since`,
        `initial_is_afk`, and `initial_status` are not defined and left to their
        default values, then the presence will not be _updated_ on startup
        at all.

    Raises
    ------
    TypeError
        If sharding information is not specified correctly.
    ValueError
        If sharding information is provided, but is unfeasible or invalid.
    """

    if typing.TYPE_CHECKING:
        EventT = typing.TypeVar("EventT", bound=base_events.Event)
        PredicateT = typing.Callable[[base_events.Event], typing.Union[bool, typing.Coroutine[None, typing.Any, bool]]]
        SyncCallbackT = typing.Callable[[base_events.Event], None]
        AsyncCallbackT = typing.Callable[[base_events.Event], typing.Coroutine[None, typing.Any, None]]
        CallbackT = typing.Union[SyncCallbackT, AsyncCallbackT]

    def __init__(
        self,
        *,
        config: typing.Union[undefined.UndefinedType, http_settings_.HTTPSettings] = undefined.UNDEFINED,
        debug: bool = False,
        gateway_compression: bool = True,
        gateway_version: int = 6,
        initial_activity: typing.Union[undefined.UndefinedType, presences.Activity, None] = undefined.UNDEFINED,
        initial_idle_since: typing.Union[undefined.UndefinedType, datetime.datetime, None] = undefined.UNDEFINED,
        initial_is_afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        initial_status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        intents: typing.Optional[intents_.Intent] = None,
        large_threshold: int = 250,
        logging_level: typing.Union[str, int, None] = "INFO",
        rest_version: int = 6,
        rest_url: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        shard_ids: typing.Union[typing.Set[int], undefined.UndefinedType] = undefined.UNDEFINED,
        shard_count: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        stateless: bool = False,
        thread_pool_executor: typing.Optional[concurrent.futures.Executor] = None,
        token: str,
    ) -> None:
        if logging_level is not None and not _LOGGER.hasHandlers():
            logging.basicConfig(format=self.__get_logging_format())
            _LOGGER.setLevel(logging_level)

        self.__print_banner()

        config = http_settings_.HTTPSettings() if config is undefined.UNDEFINED else config

        if stateless:
            self._cache = stateless_cache_impl.StatelessCacheImpl()
            _LOGGER.info("this application will be stateless! Cache-based operations will be unavailable!")
        else:
            self._cache = cache_impl.InMemoryCacheComponentImpl(app=self)

        self._config = config
        self._event_manager = event_manager.EventManagerImpl(app=self)
        self._entity_factory = entity_factory_impl.EntityFactoryComponentImpl(app=self)
        self._global_ratelimit = rate_limits.ManualRateLimiter()

        self._rest = rest.REST(  # noqa: S106 - Possible hardcoded password
            app=self,
            config=config,
            debug=debug,
            global_ratelimit=self._global_ratelimit,
            token=token,
            token_type=strings.BOT_TOKEN,  # nosec
            rest_url=rest_url,
            version=rest_version,
        )
        self._thread_pool_executor = thread_pool_executor

        super().__init__(
            config=config,
            debug=debug,
            initial_activity=initial_activity,
            initial_idle_since=initial_idle_since,
            initial_is_afk=initial_is_afk,
            initial_status=initial_status,
            intents=intents,
            large_threshold=large_threshold,
            shard_ids=shard_ids,
            shard_count=shard_count,
            token=token,
            compression=gateway_compression,
            version=gateway_version,
        )

    @property
    def event_dispatcher(self) -> event_dispatcher_.IEventDispatcherComponent:
        return self._event_manager

    @property
    def cache(self) -> cache_.ICacheComponent:
        return self._cache

    @property
    def entity_factory(self) -> entity_factory_.IEntityFactoryComponent:
        return self._entity_factory

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._thread_pool_executor

    @property
    def rest(self) -> rest.REST:
        return self._rest

    @property
    def event_consumer(self) -> event_consumer_.IEventConsumerComponent:
        return self._event_manager

    @property
    def http_settings(self) -> http_settings_.HTTPSettings:
        return self._config

    def listen(
        self, event_type: typing.Union[undefined.UndefinedType, typing.Type[EventT]] = undefined.UNDEFINED,
    ) -> typing.Callable[[CallbackT], CallbackT]:
        return self.event_dispatcher.listen(event_type)

    def subscribe(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]]:
        return self.event_dispatcher.subscribe(event_type, callback)

    def unsubscribe(
        self,
        event_type: typing.Type[EventT],
        callback: typing.Callable[[EventT], typing.Coroutine[None, typing.Any, None]],
    ) -> None:
        return self.event_dispatcher.unsubscribe(event_type, callback)

    async def wait_for(
        self, event_type: typing.Type[EventT], predicate: PredicateT, timeout: typing.Union[float, int, None],
    ) -> EventT:
        return await self.event_dispatcher.wait_for(event_type, predicate, timeout)

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        return self.event_dispatcher.dispatch(event)

    async def close(self) -> None:
        await super().close()
        await self._rest.close()
        self._global_ratelimit.close()

    async def fetch_sharding_settings(self) -> gateway_models.GatewayBot:
        return await self.rest.fetch_gateway_bot()

    @staticmethod
    def __print_banner() -> None:
        from hikari import _about

        version = _about.__version__
        sourcefile = typing.cast(str, inspect.getsourcefile(_about))
        path = os.path.abspath(os.path.dirname(sourcefile))
        python_implementation = platform.python_implementation()
        python_version = platform.python_version()
        operating_system = " ".join((platform.system(), *platform.architecture()))
        python_compiler = platform.python_compiler()

        copyright_str = f"{_about.__copyright__}, licensed under {_about.__license__}"
        version_str = f"hikari v{version} (installed in {path})"
        impl_str = f"Running on {python_implementation} v{python_version}, {python_compiler}, ({operating_system})"
        doc_line = f"Documentation: {_about.__docs__}"
        guild_line = f"Support: {_about.__discord_invite__}"
        line_len = max(len(version_str), len(copyright_str), len(impl_str), len(guild_line), len(doc_line))

        copyright_str = f"|*   {copyright_str:^{line_len}}   *|"
        impl_str = f"|*   {impl_str:^{line_len}}   *|"
        version_str = f"|*   {version_str:^{line_len}}   *|"
        doc_line = f"|*   {doc_line:^{line_len}}   *|"
        guild_line = f"|*   {guild_line:^{line_len}}   *|"
        line_len = max(len(version_str), len(copyright_str), len(impl_str), len(guild_line), len(doc_line)) - 4

        top_line = "//" + ("=" * line_len) + r"\\"
        bottom_line = r"\\" + ("=" * line_len) + "//"

        lines = "".join(
            f"{line}\n" for line in (top_line, version_str, copyright_str, impl_str, doc_line, guild_line, bottom_line)
        )

        for handler in _LOGGER.handlers or ([logging.lastResort] if logging.lastResort is not None else []):
            if isinstance(handler, logging.StreamHandler):
                handler.stream.write(lines)

    @staticmethod
    def __get_logging_format() -> str:
        # Modified from
        # https://github.com/django/django/blob/master/django/core/management/color.py

        plat = sys.platform
        supports_color = False

        # isatty is not always implemented, https://code.djangoproject.com/ticket/6223
        is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

        if plat != "Pocket PC":
            if plat == "win32":
                supports_color |= os.getenv("TERM_PROGRAM", None) == "mintty"
                supports_color |= "ANSICON" in os.environ
                supports_color |= is_a_tty
            else:
                supports_color = is_a_tty

            supports_color |= bool(os.getenv("PYCHARM_HOSTED", ""))

        if supports_color:
            blue = "\033[1;35m"
            gray = "\033[1;37m"
            green = "\033[1;32m"
            red = "\033[1;31m"
            yellow = "\033[1;33m"
            default = "\033[0m"
        else:
            blue = gray = green = red = yellow = default = ""

        return (
            f"{red}%(levelname)-1.1s {yellow}%(name)-25.25s {green}#%(lineno)-4d {blue}%(asctime)23.23s"
            f"{default} :: {gray}%(message)s{default}"
        )

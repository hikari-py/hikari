# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Event handling logic."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["EventManagerComponentBase", "EventManagerComponentImpl"]

import asyncio
import logging
import typing
import warnings

from hikari import errors
from hikari.api import event_consumer
from hikari.api import event_dispatcher
from hikari.events import base_events
from hikari.events import shard_events
from hikari.models import intents
from hikari.utilities import aio
from hikari.utilities import reflect

if typing.TYPE_CHECKING:
    from hikari.api import bot
    from hikari.api import shard as gateway_shard
    from hikari.utilities import data_binding

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")

if typing.TYPE_CHECKING:
    ListenerMapT = typing.MutableMapping[
        typing.Type[event_dispatcher.EventT_co],
        typing.MutableSequence[event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]],
    ]
    WaiterT = typing.Tuple[
        event_dispatcher.PredicateT[event_dispatcher.EventT_co], asyncio.Future[event_dispatcher.EventT_co]
    ]
    WaiterMapT = typing.MutableMapping[typing.Type[event_dispatcher.EventT_co], typing.MutableSet[WaiterT]]


def _default_predicate(_: event_dispatcher.EventT_inv) -> bool:
    return True


class EventManagerComponentBase(event_dispatcher.IEventDispatcherComponent, event_consumer.IEventConsumerComponent):
    """Provides functionality to consume and dispatch events.

    Does not define how to handle specific event cases.

    Specific event handlers should be in functions named `on_xxx` where `xxx`
    is the raw event name being dispatched in lower-case.
    """

    __slots__: typing.Sequence[str] = ("_app", "_intents", "_listeners", "_waiters")

    def __init__(self, app: bot.IBotApp, intents_: typing.Optional[intents.Intent]) -> None:
        self._app = app
        self._intents = intents_
        self._listeners: ListenerMapT = {}
        self._waiters: WaiterMapT = {}

    @property
    @typing.final
    def app(self) -> bot.IBotApp:
        return self._app

    async def consume_raw_event(
        self, shard: gateway_shard.IGatewayShard, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        try:
            callback = getattr(self, "on_" + event_name.lower())
        except AttributeError:
            _LOGGER.debug("ignoring unknown event %s", event_name)
        else:
            await callback(shard, payload)

    def subscribe(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
        *,
        _nested: int = 0,
    ) -> event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]:
        # `_nested` is used to show the correct source code snippet if an intent
        # warning is triggered.

        # If None, the user is on v6 with intents disabled, so we don't care.
        if self._intents is not None:
            # Collection of combined bitfield combinations of intents that
            # could be enabled to receive this event.
            expected_intent_groups = base_events.get_required_intents_for(event_type)

            if expected_intent_groups:
                for expected_intent_group in expected_intent_groups:
                    if (self._intents & expected_intent_group) == expected_intent_group:
                        break
                else:
                    expected_intents_str = ", ".join(map(str, expected_intent_groups))

                    warnings.warn(
                        f"You have tried to listen to {event_type.__name__}, but this will only ever be triggered if "
                        f"you enable one of the following intents: {expected_intents_str}.",
                        category=errors.IntentWarning,
                        stacklevel=_nested + 2,
                    )

        if event_type not in self._listeners:
            self._listeners[event_type] = []

        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Event callbacks must be coroutine functions (`async def')")

        _LOGGER.debug(
            "subscribing callback 'async def %s%s' to event-type %s.%s",
            getattr(callback, "__name__", "<anon>"),
            reflect.resolve_signature(callback),
            event_type.__module__,
            event_type.__qualname__,
        )

        self._listeners[event_type].append(callback)

        return callback

    def get_listeners(
        self, event_type: typing.Type[event_dispatcher.EventT_co], *, polymorphic: bool = True,
    ) -> typing.Collection[event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]]:
        if polymorphic:
            listeners: typing.List[event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]] = []
            for subscribed_event_type, subscribed_listeners in self._listeners.items():
                if issubclass(subscribed_event_type, event_type):
                    listeners += subscribed_listeners
            return listeners
        else:
            items = self._listeners.get(event_type)
            if items is not None:
                return items[:]

            return []

    def has_listener(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
        *,
        polymorphic: bool = True,
    ) -> bool:
        if polymorphic:
            for subscribed_event_type, listeners in self._listeners.items():
                if issubclass(subscribed_event_type, event_type) and callback in listeners:
                    return True
            return False
        else:
            if event_type not in self._listeners:
                return False
            return callback in self._listeners[event_type]

    def unsubscribe(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
    ) -> None:
        if event_type in self._listeners:
            _LOGGER.debug(
                "unsubscribing callback %s%s from event-type %s.%s",
                getattr(callback, "__name__", "<anon>"),
                reflect.resolve_signature(callback),
                event_type.__module__,
                event_type.__qualname__,
            )
            self._listeners[event_type].remove(callback)
            if not self._listeners[event_type]:
                del self._listeners[event_type]

    def listen(
        self, event_type: typing.Optional[typing.Type[event_dispatcher.EventT_co]] = None,
    ) -> typing.Callable[
        [event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]],
        event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
    ]:
        def decorator(
            callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
        ) -> event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]:
            nonlocal event_type

            signature = reflect.resolve_signature(callback)
            params = signature.parameters.values()

            if len(params) != 1:
                raise TypeError("Event listener must have exactly one parameter, the event object.")

            event_param = next(iter(params))

            if event_type is None:
                if event_param.annotation is event_param.empty:
                    raise TypeError("Must provide the event type in the @listen decorator or as a type hint!")

                event_type = event_param.annotation

                if not isinstance(event_type, type) or not issubclass(event_type, base_events.Event):
                    raise TypeError("Event type must derive from Event")

            self.subscribe(event_type, callback, _nested=1)
            return callback

        return decorator

    async def wait_for(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_dispatcher.PredicateT[event_dispatcher.EventT_co]] = None,
    ) -> event_dispatcher.EventT_co:

        if predicate is None:
            predicate = _default_predicate

        future: asyncio.Future[event_dispatcher.EventT_co] = asyncio.get_event_loop().create_future()

        if event_type not in self._waiters:
            self._waiters[event_type] = set()

        self._waiters[event_type].add((predicate, future))

        return await asyncio.wait_for(future, timeout=timeout) if timeout is not None else await future

    async def _test_waiter(
        self,
        cls: typing.Type[event_dispatcher.EventT_inv],
        event: event_dispatcher.EventT_inv,
        predicate: event_dispatcher.PredicateT[event_dispatcher.EventT_inv],
        future: asyncio.Future[event_dispatcher.EventT_inv],
    ) -> None:
        try:
            result = predicate(event)
            if asyncio.iscoroutine(result):
                result = await result  # type: ignore

            if not result:
                return

        except Exception as ex:
            future.set_exception(ex)
        else:
            future.set_result(event)

        self._waiters[cls].remove((predicate, future))
        if not self._waiters[cls]:
            del self._waiters[cls]

    def dispatch(self, event: event_dispatcher.EventT_inv) -> asyncio.Future[typing.Any]:
        if not isinstance(event, base_events.Event):
            raise TypeError(f"Events must be subclasses of {base_events.Event.__name__}, not {type(event).__name__}")

        # We only need to iterate through the MRO until we hit Event, as
        # anything after that is random garbage we don't care about, as they do
        # not describe event types. This improves efficiency as well.
        mro = type(event).mro()

        tasks: typing.List[typing.Coroutine[None, typing.Any, None]] = []

        for cls in mro[: mro.index(base_events.Event) + 1]:

            if cls in self._listeners:
                for callback in self._listeners[cls]:
                    tasks.append(self._invoke_callback(callback, event))

            if cls in self._waiters:
                for predicate, future in self._waiters[cls]:
                    # noinspection PyTypeChecker
                    tasks.append(self._test_waiter(cls, event, predicate, future))

        return asyncio.gather(*tasks) if tasks else aio.completed_future()

    async def _invoke_callback(
        self, callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_inv], event: event_dispatcher.EventT_inv
    ) -> None:
        try:
            result = callback(event)
            if asyncio.iscoroutine(result):
                await result

        except Exception as ex:
            # Skip the first frame in logs, we don't care for it.
            trio = type(ex), ex, ex.__traceback__.tb_next if ex.__traceback__ is not None else None

            if base_events.is_no_recursive_throw_event(event):
                _LOGGER.error("an exception occurred handling an event, but it has been ignored", exc_info=trio)
            else:
                _LOGGER.error("an exception occurred handling an event", exc_info=trio)
                await self.dispatch(
                    base_events.ExceptionEvent(
                        app=self.app,
                        shard=getattr(event, "shard") if isinstance(event, shard_events.ShardEvent) else None,
                        exception=ex,
                        failed_event=event,
                        failed_callback=callback,
                    )
                )


class EventManagerComponentImpl(EventManagerComponentBase):
    """Provides event handling logic for Discord events."""

    __slots__: typing.Sequence[str] = ()

    async def on_connected(self, shard: gateway_shard.IGatewayShard, _: data_binding.JSONObject) -> None:
        """Handle connection events.

        This is a synthetic event produced by the gateway implementation in
        Hikari.
        """
        await self.dispatch(shard_events.ShardConnectedEvent(shard=shard))

    async def on_disconnected(self, shard: gateway_shard.IGatewayShard, _: data_binding.JSONObject) -> None:
        """Handle disconnection events.

        This is a synthetic event produced by the gateway implementation in
        Hikari.
        """
        await self.dispatch(shard_events.ShardDisconnectedEvent(shard=shard))

    async def on_ready(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#ready for more info."""
        await self.dispatch(self.app.event_factory.deserialize_ready_event(shard, payload))

    async def on_resumed(self, shard: gateway_shard.IGatewayShard, _: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#resumed for more info."""
        # TODO: this should be in entity factory
        await self.dispatch(shard_events.ShardResumedEvent(shard=shard))

    async def on_channel_create(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-create for more info."""
        await self.dispatch(self.app.event_factory.deserialize_channel_create_event(shard, payload))

    async def on_channel_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_channel_update_event(shard, payload))

    async def on_channel_delete(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-delete for more info."""
        await self.dispatch(self.app.event_factory.deserialize_channel_delete_event(shard, payload))

    async def on_channel_pins_update(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-pins-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_channel_pins_update_event(shard, payload))

    async def on_guild_create(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-create for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_create_event(shard, payload))

    async def on_guild_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_update_event(shard, payload))

    async def on_guild_delete(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-delete for more info."""
        if payload.get("unavailable", False):
            await self.dispatch(self.app.event_factory.deserialize_guild_unavailable_event(shard, payload))
        else:
            await self.dispatch(self.app.event_factory.deserialize_guild_leave_event(shard, payload))

    async def on_guild_ban_add(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-add for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_ban_add_event(shard, payload))

    async def on_guild_ban_remove(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-remove for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_ban_remove_event(shard, payload))

    async def on_guild_emojis_update(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-emojis-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_emojis_update_event(shard, payload))

    async def on_guild_integrations_update(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-integrations-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_integrations_update_event(shard, payload))

    async def on_guild_member_add(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-add for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_member_add_event(shard, payload))

    async def on_guild_member_remove(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-remove for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_member_remove_event(shard, payload))

    async def on_guild_member_update(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_member_update_event(shard, payload))

    async def on_guild_members_chunk(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-members-chunk for more info."""
        # TODO: implement chunking components.
        await self.dispatch(self.app.event_factory.deserialize_guild_member_chunk_event(shard, payload))

    async def on_guild_role_create(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-create for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_role_create_event(shard, payload))

    async def on_guild_role_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_role_update_event(shard, payload))

    async def on_guild_role_delete(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-delete for more info."""
        await self.dispatch(self.app.event_factory.deserialize_guild_role_delete_event(shard, payload))

    async def on_invite_create(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-create for more info."""
        await self.dispatch(self.app.event_factory.deserialize_invite_create_event(shard, payload))

    async def on_invite_delete(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-delete for more info."""
        await self.dispatch(self.app.event_factory.deserialize_invite_delete_event(shard, payload))

    async def on_message_create(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-create for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_create_event(shard, payload))

    async def on_message_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_update_event(shard, payload))

    async def on_message_delete(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_delete_event(shard, payload))

    async def on_message_delete_bulk(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete-bulk for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_delete_bulk_event(shard, payload))

    async def on_message_reaction_add(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-add for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_reaction_add_event(shard, payload))

    async def on_message_reaction_remove(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_reaction_remove_event(shard, payload))

    async def on_message_reaction_remove_all(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-all for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_reaction_remove_all_event(shard, payload))

    async def on_message_reaction_remove_emoji(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-emoji for more info."""
        await self.dispatch(self.app.event_factory.deserialize_message_reaction_remove_emoji_event(shard, payload))

    async def on_presence_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#presence-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_presence_update_event(shard, payload))

    async def on_typing_start(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#typing-start for more info."""
        await self.dispatch(self.app.event_factory.deserialize_typing_start_event(shard, payload))

    async def on_user_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#user-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_own_user_update_event(shard, payload))

    async def on_voice_state_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-state-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_voice_state_update_event(shard, payload))

    async def on_voice_server_update(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-server-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_voice_server_update_event(shard, payload))

    async def on_webhooks_update(self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#webhooks-update for more info."""
        await self.dispatch(self.app.event_factory.deserialize_webhook_update_event(shard, payload))

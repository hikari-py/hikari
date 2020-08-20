# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Implementation for a singleton bot event factory."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["EventFactoryImpl"]

import datetime
import typing

from hikari import channels as channel_models
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import users as user_models
from hikari.api import event_factory
from hikari.api import shard as gateway_shard
from hikari.events import channel_events
from hikari.events import guild_events
from hikari.events import member_events
from hikari.events import message_events
from hikari.events import reaction_events
from hikari.events import role_events
from hikari.events import shard_events
from hikari.events import typing_events
from hikari.events import user_events
from hikari.events import voice_events
from hikari.utilities import data_binding
from hikari.utilities import date


class EventFactoryImpl(event_factory.EventFactory):
    """Implementation for a single-application bot event factory."""

    def __init__(self, app: traits.RESTAware) -> None:
        self._app = app

    ##################
    # CHANNEL EVENTS #
    ##################

    def deserialize_channel_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelCreateEvent:
        channel = self._app.entity_factory.deserialize_channel(payload)
        if isinstance(channel, channel_models.GuildChannel):
            return channel_events.GuildChannelCreateEvent(app=self._app, shard=shard, channel=channel)
        if isinstance(channel, channel_models.PrivateChannel):
            return channel_events.PrivateChannelCreateEvent(app=self._app, shard=shard, channel=channel)
        raise TypeError(f"Expected GuildChannel or PrivateChannel but received {type(channel).__name__}")

    def deserialize_channel_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelUpdateEvent:
        channel = self._app.entity_factory.deserialize_channel(payload)
        if isinstance(channel, channel_models.GuildChannel):
            return channel_events.GuildChannelUpdateEvent(app=self._app, shard=shard, channel=channel)
        if isinstance(channel, channel_models.PrivateChannel):
            return channel_events.PrivateChannelUpdateEvent(app=self._app, shard=shard, channel=channel)
        raise TypeError(f"Expected GuildChannel or PrivateChannel but received {type(channel).__name__}")

    def deserialize_channel_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelDeleteEvent:
        channel = self._app.entity_factory.deserialize_channel(payload)
        if isinstance(channel, channel_models.GuildChannel):
            return channel_events.GuildChannelDeleteEvent(app=self._app, shard=shard, channel=channel)
        if isinstance(channel, channel_models.PrivateChannel):
            return channel_events.PrivateChannelDeleteEvent(app=self._app, shard=shard, channel=channel)
        raise TypeError(f"Expected GuildChannel or PrivateChannel but received {type(channel).__name__}")

    def deserialize_channel_pins_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.PinsUpdateEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])

        # Turns out this _can_ be None or not present. Only set it if it is actually available.
        if (raw := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp: typing.Optional[datetime.datetime] = date.iso8601_datetime_string_to_datetime(raw)
        else:
            last_pin_timestamp = None

        if "guild_id" in payload:
            return channel_events.GuildPinsUpdateEvent(
                app=self._app,
                shard=shard,
                channel_id=channel_id,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                last_pin_timestamp=last_pin_timestamp,
            )

        return channel_events.PrivatePinsUpdateEvent(
            app=self._app, shard=shard, channel_id=channel_id, last_pin_timestamp=last_pin_timestamp
        )

    def deserialize_webhook_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.WebhookUpdateEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        return channel_events.WebhookUpdateEvent(app=self._app, shard=shard, channel_id=channel_id, guild_id=guild_id,)

    def deserialize_typing_start_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> typing_events.TypingEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        user_id = snowflakes.Snowflake(payload["user_id"])
        # Turns out that this endpoint uses seconds rather than milliseconds.
        timestamp = date.unix_epoch_to_datetime(payload["timestamp"], is_millis=False)

        if "guild_id" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])
            member = self._app.entity_factory.deserialize_member(payload["member"], guild_id=guild_id)
            return typing_events.GuildTypingEvent(
                app=self._app,
                shard=shard,
                channel_id=channel_id,
                guild_id=guild_id,
                user_id=user_id,
                timestamp=timestamp,
                member=member,
            )

        return typing_events.PrivateTypingEvent(
            app=self._app, shard=shard, channel_id=channel_id, user_id=user_id, timestamp=timestamp
        )

    def deserialize_invite_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteCreateEvent:
        invite = self._app.entity_factory.deserialize_invite_with_metadata(payload)
        return channel_events.InviteCreateEvent(app=self._app, shard=shard, invite=invite)

    def deserialize_invite_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteDeleteEvent:

        if "guild_id" not in payload:
            raise TypeError("Expected guild invite delete, but received unexpected payload")

        return channel_events.InviteDeleteEvent(
            app=self._app,
            shard=shard,
            code=payload["code"],
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
        )

    ################
    # GUILD EVENTS #
    ################

    def deserialize_guild_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildAvailableEvent:
        guild_information = self._app.entity_factory.deserialize_gateway_guild(payload)
        assert guild_information.channels is not None
        assert guild_information.members is not None
        assert guild_information.presences is not None
        assert guild_information.voice_states is not None
        return guild_events.GuildAvailableEvent(
            app=self._app,
            shard=shard,
            guild=guild_information.guild,
            emojis=guild_information.emojis,
            roles=guild_information.roles,
            channels=guild_information.channels,
            members=guild_information.members,
            presences=guild_information.presences,
            voice_states=guild_information.voice_states,
        )

    def deserialize_guild_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUpdateEvent:
        guild_information = self._app.entity_factory.deserialize_gateway_guild(payload)
        return guild_events.GuildUpdateEvent(
            app=self._app,
            shard=shard,
            guild=guild_information.guild,
            emojis=guild_information.emojis,
            roles=guild_information.roles,
        )

    def deserialize_guild_leave_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildLeaveEvent:
        return guild_events.GuildLeaveEvent(app=self._app, shard=shard, guild_id=snowflakes.Snowflake(payload["id"]))

    def deserialize_guild_unavailable_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUnavailableEvent:
        return guild_events.GuildUnavailableEvent(
            app=self._app, shard=shard, guild_id=snowflakes.Snowflake(payload["id"])
        )

    def deserialize_guild_ban_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanCreateEvent:
        return guild_events.BanCreateEvent(
            app=self._app,
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            user=self._app.entity_factory.deserialize_user(payload["user"]),
        )

    def deserialize_guild_ban_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanDeleteEvent:
        return guild_events.BanDeleteEvent(
            app=self._app,
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            user=self._app.entity_factory.deserialize_user(payload["user"]),
        )

    def deserialize_guild_emojis_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.EmojisUpdateEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        emojis = [
            self._app.entity_factory.deserialize_known_custom_emoji(emoji, guild_id=guild_id)
            for emoji in payload["emojis"]
        ]
        return guild_events.EmojisUpdateEvent(app=self._app, shard=shard, guild_id=guild_id, emojis=emojis)

    def deserialize_guild_integrations_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationsUpdateEvent:
        return guild_events.IntegrationsUpdateEvent(
            app=self._app, shard=shard, guild_id=snowflakes.Snowflake(payload["guild_id"]),
        )

    def deserialize_guild_member_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberCreateEvent:
        member = self._app.entity_factory.deserialize_member(payload)
        return member_events.MemberCreateEvent(app=self._app, shard=shard, member=member)

    def deserialize_guild_member_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberUpdateEvent:
        member = self._app.entity_factory.deserialize_member(payload)
        return member_events.MemberUpdateEvent(app=self._app, shard=shard, member=member)

    def deserialize_guild_member_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberDeleteEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        user = self._app.entity_factory.deserialize_user(payload["user"])
        return member_events.MemberDeleteEvent(app=self._app, shard=shard, guild_id=guild_id, user=user)

    def deserialize_guild_role_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleCreateEvent:
        role = self._app.entity_factory.deserialize_role(
            payload["role"], guild_id=snowflakes.Snowflake(payload["guild_id"]),
        )
        return role_events.RoleCreateEvent(app=self._app, shard=shard, role=role)

    def deserialize_guild_role_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleUpdateEvent:
        role = self._app.entity_factory.deserialize_role(
            payload["role"], guild_id=snowflakes.Snowflake(payload["guild_id"]),
        )
        return role_events.RoleUpdateEvent(app=self._app, shard=shard, role=role)

    def deserialize_guild_role_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleDeleteEvent:
        return role_events.RoleDeleteEvent(
            app=self._app,
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            role_id=snowflakes.Snowflake(payload["role_id"]),
        )

    def deserialize_presence_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.PresenceUpdateEvent:
        presence = self._app.entity_factory.deserialize_member_presence(payload)

        user_payload = payload["user"]
        user: typing.Optional[user_models.PartialUser] = None
        # Here we're told that the only guaranteed field is "id", so if we only get 1 field in the user payload then
        # then we've only got an ID and there's no reason to form a user object.
        if len(user_payload) > 1:
            # PartialUser
            discriminator = user_payload["discriminator"] if "discriminator" in user_payload else undefined.UNDEFINED
            flags: undefined.UndefinedOr[user_models.UserFlag] = undefined.UNDEFINED
            if "public_flags" in user_payload:
                flags = user_models.UserFlag(user_payload["public_flags"])

            user = user_models.PartialUserImpl(
                app=self._app,
                id=snowflakes.Snowflake(user_payload["id"]),
                discriminator=discriminator,
                username=user_payload.get("username", undefined.UNDEFINED),
                avatar_hash=user_payload.get("avatar", undefined.UNDEFINED),
                is_bot=user_payload.get("bot", undefined.UNDEFINED),
                is_system=user_payload.get("system", undefined.UNDEFINED),
                flags=flags,
            )
            # noinspection PyArgumentList

        return guild_events.PresenceUpdateEvent(app=self._app, shard=shard, presence=presence, user=user)

    ##################
    # MESSAGE EVENTS #
    ##################

    def deserialize_message_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageCreateEvent:
        message = self._app.entity_factory.deserialize_message(payload)

        if message.guild_id is None:
            return message_events.PrivateMessageCreateEvent(app=self._app, shard=shard, message=message)

        return message_events.GuildMessageCreateEvent(app=self._app, shard=shard, message=message)

    def deserialize_message_update_event(  # noqa: CFQ001
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageUpdateEvent:
        message = self._app.entity_factory.deserialize_partial_message(payload)

        if message.guild_id is None:
            return message_events.PrivateMessageUpdateEvent(app=self._app, shard=shard, message=message)

        return message_events.GuildMessageUpdateEvent(app=self._app, shard=shard, message=message)

    def deserialize_message_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageDeleteEvent:
        message = self._app.entity_factory.deserialize_partial_message(payload)

        if message.guild_id is None:
            return message_events.PrivateMessageDeleteEvent(app=self._app, shard=shard, message=message)

        return message_events.GuildMessageDeleteEvent(app=self._app, shard=shard, message=message)

    def deserialize_message_delete_bulk_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageBulkDeleteEvent:
        if "guild_id" not in payload:
            raise NotImplementedError("No implementation for private message bulk delete events")

        return message_events.GuildMessageBulkDeleteEvent(
            app=self._app,
            shard=shard,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            message_ids=[snowflakes.Snowflake(message_id) for message_id in payload["ids"]],
        )

    def deserialize_message_reaction_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionAddEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])
        emoji = self._app.entity_factory.deserialize_emoji(payload["emoji"])

        if "member" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])
            member = self._app.entity_factory.deserialize_member(payload["member"], guild_id=guild_id)
            return reaction_events.GuildReactionAddEvent(
                app=self._app, shard=shard, member=member, channel_id=channel_id, message_id=message_id, emoji=emoji,
            )

        user_id = snowflakes.Snowflake(payload["user_id"])
        return reaction_events.PrivateReactionAddEvent(
            app=self._app, shard=shard, channel_id=channel_id, message_id=message_id, user_id=user_id, emoji=emoji,
        )

    def deserialize_message_reaction_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])
        user_id = snowflakes.Snowflake(payload["user_id"])
        emoji = self._app.entity_factory.deserialize_emoji(payload["emoji"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteEvent(
                app=self._app,
                shard=shard,
                user_id=user_id,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
                emoji=emoji,
            )

        return reaction_events.PrivateReactionDeleteEvent(
            app=self._app, shard=shard, user_id=user_id, channel_id=channel_id, message_id=message_id, emoji=emoji,
        )

    def deserialize_message_reaction_remove_all_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteAllEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteAllEvent(
                app=self._app,
                shard=shard,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
            )

        # TODO: check if this can even occur.
        return reaction_events.PrivateReactionDeleteAllEvent(
            app=self._app, shard=shard, channel_id=channel_id, message_id=message_id,
        )

    def deserialize_message_reaction_remove_emoji_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEmojiEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])
        emoji = self._app.entity_factory.deserialize_emoji(payload["emoji"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteEmojiEvent(
                app=self._app,
                shard=shard,
                emoji=emoji,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
            )

        # TODO: check if this can even occur.
        return reaction_events.PrivateReactionDeleteEmojiEvent(
            app=self._app, shard=shard, emoji=emoji, channel_id=channel_id, message_id=message_id,
        )

    ################
    # OTHER EVENTS #
    ################

    def deserialize_ready_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.ShardReadyEvent:
        gateway_version = int(payload["v"])
        my_user = self._app.entity_factory.deserialize_my_user(payload["user"])
        unavailable_guilds = [snowflakes.Snowflake(guild["id"]) for guild in payload["guilds"]]
        session_id = payload["session_id"]

        return shard_events.ShardReadyEvent(
            app=self._app,
            shard=shard,
            actual_gateway_version=gateway_version,
            session_id=session_id,
            my_user=my_user,
            unavailable_guilds=unavailable_guilds,
        )

    def deserialize_own_user_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> user_events.OwnUserUpdateEvent:
        return user_events.OwnUserUpdateEvent(
            app=self._app, shard=shard, user=self._app.entity_factory.deserialize_my_user(payload)
        )

    def deserialize_guild_member_chunk_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.MemberChunkEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        index = int(payload["chunk_index"])
        count = int(payload["chunk_count"])
        members = {
            snowflakes.Snowflake(m["user"]["id"]): self._app.entity_factory.deserialize_member(m, guild_id=guild_id)
            for m in payload["members"]
        }
        # Note, these IDs may be returned as ints or strings based on whether they're over a certain value.
        not_found = [snowflakes.Snowflake(sn) for sn in payload["not_found"]] if "not_found" in payload else []

        nonce = typing.cast("typing.Optional[str]", payload.get("nonce"))

        if (presence_payloads := payload.get("include_presences")) is not None:
            presences = {
                snowflakes.Snowflake(p["user"]["id"]): self._app.entity_factory.deserialize_member_presence(
                    p, guild_id=guild_id
                )
                for p in presence_payloads
            }
        else:
            presences = {}

        return guild_events.MemberChunkEvent(
            app=self._app,
            shard=shard,
            guild_id=guild_id,
            members=members,
            index=index,
            count=count,
            not_found=not_found,
            presences=presences,
            nonce=nonce,
        )

    ################
    # VOICE EVENTS #
    ################

    def deserialize_voice_state_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceStateUpdateEvent:
        state = self._app.entity_factory.deserialize_voice_state(payload)
        return voice_events.VoiceStateUpdateEvent(app=self._app, shard=shard, state=state)

    def deserialize_voice_server_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        token = payload["token"]
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        raw_endpoint = payload["endpoint"]
        return voice_events.VoiceServerUpdateEvent(
            app=self._app, shard=shard, guild_id=guild_id, token=token, raw_endpoint=raw_endpoint
        )

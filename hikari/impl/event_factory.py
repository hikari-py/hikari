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
"""Implementation for a singleton bot event factory."""

from __future__ import annotations

__all__: typing.List[str] = ["EventFactoryComponentImpl"]

import datetime
import typing

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
from hikari.models import channels as channel_models
from hikari.models import guilds as guild_models
from hikari.models import presences as presence_models
from hikari.models import users as user_models
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import bot


class EventFactoryComponentImpl(event_factory.IEventFactoryComponent):
    """Implementation for a single-application bot event factory."""

    def __init__(self, app: bot.IBotApp) -> None:
        self._app = app

    @property
    def app(self) -> bot.IBotApp:
        return self._app

    ##################
    # CHANNEL EVENTS #
    ##################

    def deserialize_channel_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelCreateEvent:
        channel = self.app.entity_factory.deserialize_channel(payload)
        if isinstance(channel, channel_models.GuildChannel):
            return channel_events.GuildChannelCreateEvent(shard=shard, channel=channel)
        if isinstance(channel, channel_models.PrivateChannel):
            return channel_events.PrivateChannelCreateEvent(shard=shard, channel=channel)
        raise TypeError(f"Expected GuildChannel or PrivateChannel but received {type(channel).__name__}")

    def deserialize_channel_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelUpdateEvent:
        channel = self.app.entity_factory.deserialize_channel(payload)
        if isinstance(channel, channel_models.GuildChannel):
            return channel_events.GuildChannelUpdateEvent(shard=shard, channel=channel)
        if isinstance(channel, channel_models.PrivateChannel):
            return channel_events.PrivateChannelUpdateEvent(shard=shard, channel=channel)
        raise TypeError(f"Expected GuildChannel or PrivateChannel but received {type(channel).__name__}")

    def deserialize_channel_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelDeleteEvent:
        channel = self.app.entity_factory.deserialize_channel(payload)
        if isinstance(channel, channel_models.GuildChannel):
            return channel_events.GuildChannelDeleteEvent(shard=shard, channel=channel)
        if isinstance(channel, channel_models.PrivateChannel):
            return channel_events.PrivateChannelDeleteEvent(shard=shard, channel=channel)
        raise TypeError(f"Expected GuildChannel or PrivateChannel but received {type(channel).__name__}")

    def deserialize_channel_pins_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelPinsUpdateEvent:
        channel_id = snowflake.Snowflake(payload["channel_id"])

        # Turns out this _can_ be None or not present. Only set it if it is actually available.
        if (raw_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = date.iso8601_datetime_string_to_datetime(raw_timestamp)
        else:
            last_pin_timestamp = None

        if "guild_id" in payload:
            return channel_events.GuildChannelPinsUpdateEvent(
                shard=shard,
                channel_id=channel_id,
                guild_id=snowflake.Snowflake(payload["guild_id"]),
                last_pin_timestamp=last_pin_timestamp,
            )

        return channel_events.PrivateChannelPinsUpdateEvent(
            shard=shard, channel_id=channel_id, last_pin_timestamp=last_pin_timestamp
        )

    def deserialize_webhook_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.WebhookUpdateEvent:
        guild_id = snowflake.Snowflake(payload["guild_id"])
        channel_id = snowflake.Snowflake(payload["channel_id"])
        return channel_events.WebhookUpdateEvent(shard=shard, channel_id=channel_id, guild_id=guild_id,)

    def deserialize_typing_start_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> typing_events.TypingEvent:
        channel_id = snowflake.Snowflake(payload["channel_id"])
        user_id = snowflake.Snowflake(payload["user_id"])
        # Turns out that this endpoint uses seconds rather than milliseconds.
        timestamp = date.unix_epoch_to_datetime(payload["timestamp"], is_millis=False)

        if "guild_id" in payload:
            guild_id = snowflake.Snowflake(payload["guild_id"])
            member = self.app.entity_factory.deserialize_member(payload["member"])
            return typing_events.GuildTypingEvent(
                shard=shard,
                channel_id=channel_id,
                guild_id=guild_id,
                user_id=user_id,
                timestamp=timestamp,
                member=member,
            )

        return typing_events.PrivateTypingEvent(
            shard=shard, channel_id=channel_id, user_id=user_id, timestamp=timestamp
        )

    def deserialize_invite_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteCreateEvent:
        invite = self.app.entity_factory.deserialize_invite_with_metadata(payload)
        return channel_events.InviteCreateEvent(shard=shard, invite=invite)

    def deserialize_invite_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteDeleteEvent:

        if "guild_id" not in payload:
            raise TypeError("Expected guild invite delete, but received unexpected payload")

        return channel_events.InviteDeleteEvent(
            shard=shard,
            code=payload["code"],
            channel_id=snowflake.Snowflake(payload["channel_id"]),
            guild_id=snowflake.Snowflake(payload["guild_id"]),
        )

    ################
    # GUILD EVENTS #
    ################

    def deserialize_guild_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildAvailableEvent:
        guild = self.app.entity_factory.deserialize_guild(payload)
        return guild_events.GuildAvailableEvent(shard=shard, guild=guild)

    def deserialize_guild_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUpdateEvent:
        guild = self.app.entity_factory.deserialize_guild(payload)
        return guild_events.GuildUpdateEvent(shard=shard, guild=guild)

    def deserialize_guild_leave_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildLeaveEvent:
        return guild_events.GuildLeaveEvent(shard=shard, guild_id=snowflake.Snowflake(payload["id"]))

    def deserialize_guild_unavailable_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUnavailableEvent:
        return guild_events.GuildUnavailableEvent(shard=shard, guild_id=snowflake.Snowflake(payload["id"]))

    def deserialize_guild_ban_add_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanCreateEvent:
        return guild_events.BanCreateEvent(
            shard=shard,
            guild_id=snowflake.Snowflake(payload["guild_id"]),
            user=self.app.entity_factory.deserialize_user(payload["user"]),
        )

    def deserialize_guild_ban_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanDeleteEvent:
        return guild_events.BanDeleteEvent(
            shard=shard,
            guild_id=snowflake.Snowflake(payload["guild_id"]),
            user=self.app.entity_factory.deserialize_user(payload["user"]),
        )

    def deserialize_guild_emojis_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.EmojisUpdateEvent:
        guild_id = snowflake.Snowflake(payload["guild_id"])
        emojis = [
            self.app.entity_factory.deserialize_known_custom_emoji(emoji, guild_id=guild_id)
            for emoji in payload["emojis"]
        ]
        return guild_events.EmojisUpdateEvent(shard=shard, guild_id=guild_id, emojis=emojis)

    def deserialize_guild_integrations_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationsUpdateEvent:
        return guild_events.IntegrationsUpdateEvent(shard=shard, guild_id=snowflake.Snowflake(payload["guild_id"]),)

    def deserialize_guild_member_add_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberCreateEvent:
        member = self.app.entity_factory.deserialize_member(payload)
        return member_events.MemberCreateEvent(shard=shard, member=member)

    def deserialize_guild_member_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberUpdateEvent:
        member = self.app.entity_factory.deserialize_member(payload)
        return member_events.MemberUpdateEvent(shard=shard, member=member)

    def deserialize_guild_member_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberDeleteEvent:
        guild_id = snowflake.Snowflake(payload["guild_id"])
        user = self.app.entity_factory.deserialize_user(payload["user"])
        return member_events.MemberDeleteEvent(shard=shard, guild_id=guild_id, user=user)

    def deserialize_guild_role_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleCreateEvent:
        role = self.app.entity_factory.deserialize_role(
            payload["role"], guild_id=snowflake.Snowflake(payload["guild_id"]),
        )
        return role_events.RoleCreateEvent(shard=shard, role=role)

    def deserialize_guild_role_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleUpdateEvent:
        role = self.app.entity_factory.deserialize_role(
            payload["role"], guild_id=snowflake.Snowflake(payload["guild_id"]),
        )
        return role_events.RoleUpdateEvent(shard=shard, role=role)

    def deserialize_guild_role_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleDeleteEvent:
        return role_events.RoleDeleteEvent(
            shard=shard,
            guild_id=snowflake.Snowflake(payload["guild_id"]),
            role_id=snowflake.Snowflake(payload["role_id"]),
        )

    def deserialize_presence_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.PresenceUpdateEvent:
        presence = self.app.entity_factory.deserialize_member_presence(payload)

        user_payload = payload["user"]
        user: typing.Optional[user_models.PartialUser]
        # Here we're told that the only guaranteed field is "id", so if we only get 1 field in the user payload then
        # then we've only got an ID and there's no reason to form a user object.
        if len(user_payload) > 1:
            # PartialUser
            user = user_models.PartialUser()
            user.app = self._app
            user.id = snowflake.Snowflake(user_payload["id"])
            user.discriminator = (
                user_payload["discriminator"] if "discriminator" in user_payload else undefined.UNDEFINED
            )
            user.username = user_payload.get("username", undefined.UNDEFINED)
            user.avatar_hash = user_payload.get("avatar", undefined.UNDEFINED)
            user.is_bot = user_payload.get("bot", undefined.UNDEFINED)
            user.is_system = user_payload.get("system", undefined.UNDEFINED)
            # noinspection PyArgumentList
            user.flags = (
                user_models.UserFlag(user_payload["public_flags"])
                if "public_flags" in user_payload
                else undefined.UNDEFINED
            )
        else:
            user = None

        return guild_events.PresenceUpdateEvent(shard=shard, presence=presence, user=user)

    ##################
    # MESSAGE EVENTS #
    ##################

    def deserialize_message_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageCreateEvent:
        message = self.app.entity_factory.deserialize_message(payload)

        if message.guild_id is None:
            return message_events.PrivateMessageCreateEvent(shard=shard, message=message)

        return message_events.GuildMessageCreateEvent(shard=shard, message=message)

    def deserialize_message_update_event(  # noqa: CFQ001
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageUpdateEvent:
        message = self.app.entity_factory.deserialize_partial_message(payload)

        if message.guild_id is None:
            return message_events.PrivateMessageUpdateEvent(shard=shard, message=message)

        return message_events.GuildMessageUpdateEvent(shard=shard, message=message)

    def deserialize_message_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageDeleteEvent:
        message = self.app.entity_factory.deserialize_partial_message(payload)

        if message.guild_id is None:
            return message_events.PrivateMessageDeleteEvent(shard=shard, message=message)

        return message_events.GuildMessageDeleteEvent(shard=shard, message=message)

    def deserialize_message_delete_bulk_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageBulkDeleteEvent:
        if "guild_id" not in payload:
            raise NotImplementedError("No implementation for private message bulk delete events")

        return message_events.GuildMessageBulkDeleteEvent(
            shard=shard,
            channel_id=snowflake.Snowflake(payload["channel_id"]),
            guild_id=snowflake.Snowflake(payload["guild_id"]),
            message_ids=[snowflake.Snowflake(message_id) for message_id in payload["ids"]],
        )

    def deserialize_message_reaction_add_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionAddEvent:
        message_reaction_add.user_id = snowflake.Snowflake(payload["user_id"])

        if "member" in payload:

            member = self.app.deserialize_member(
                payload["member"], guild_id=typing.cast(snowflake.Snowflake, message_reaction_add.guild_id)
            )

        message_reaction_add.emoji = self.deserialize_emoji(payload["emoji"])
        return message_reaction_add

    def deserialize_message_reaction_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEvent:
        message_reaction_remove = message_events.MessageReactionRemoveEvent()
        message_reaction_remove.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_remove)
        message_reaction_remove.user_id = snowflake.Snowflake(payload["user_id"])
        message_reaction_remove.emoji = self.deserialize_emoji(payload["emoji"])
        return message_reaction_remove

    def deserialize_message_reaction_remove_all_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteAllEvent:
        message_reaction_event = message_events.MessageReactionRemoveAllEvent()
        message_reaction_event.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_event)
        return message_reaction_event

    def deserialize_message_reaction_remove_emoji_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEmojiEvent:
        message_reaction_remove_emoji = message_events.MessageReactionRemoveEmojiEvent()
        message_reaction_remove_emoji.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_remove_emoji)
        message_reaction_remove_emoji.emoji = self.deserialize_emoji(payload["emoji"])
        return message_reaction_remove_emoji

    ################
    # OTHER EVENTS #
    ################

    def deserialize_ready_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.ShardReadyEvent:
        ready_event = other_events.ReadyEvent()
        ready_event.shard = shard
        ready_event.gateway_version = int(payload["v"])
        ready_event.my_user = self.deserialize_my_user(payload["user"])
        ready_event.unavailable_guilds = {
            snowflake.Snowflake(guild["id"]): self.deserialize_unavailable_guild(guild) for guild in payload["guilds"]
        }
        ready_event.session_id = payload["session_id"]

        # Shouldn't ever be none, but if it is, we don't care.
        if (shard_data := payload.get("shard")) is not None:
            ready_event.shard_id = int(shard_data[0])
            ready_event.shard_count = int(shard_data[1])
        else:
            ready_event.shard_id = ready_event.shard_count = None

        return ready_event

    def deserialize_own_user_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> user_events.OwnUserUpdateEvent:
        my_user_update = other_events.OwnUserUpdateEvent()
        my_user_update.my_user = self.deserialize_my_user(payload)
        return my_user_update

    def deserialize_guild_member_chunk_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.MemberChunkEvent:
        chunk = other_events.MemberChunkEvent()
        chunk.app = self._app
        chunk.guild_id = snowflake.Snowflake(payload["guild_id"])
        chunk.members = {
            snowflake.Snowflake(member["user"]["id"]): self.deserialize_member(member, guild_id=chunk.guild_id)
            for member in payload["members"]
        }
        chunk.index = int(payload["chunk_index"])
        chunk.count = int(payload["chunk_count"])
        # Note, these IDs may be returned as ints or strings based on whether they're over the max safe js number size.
        chunk.not_found = [snowflake.Snowflake(sn) for sn in payload["not_found"]] if "not_found" in payload else []

        if (presence_payloads := payload.get("presences")) is not None:
            presences = {
                snowflake.Snowflake(presence["user"]["id"]): self.deserialize_member_presence(presence)
                for presence in presence_payloads
            }
        else:
            presences = {}
        chunk.presences = presences

        chunk.nonce = payload.get("nonce")
        return chunk

    ################
    # VOICE EVENTS #
    ################

    def deserialize_voice_state_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceStateUpdateEvent:
        voice_state_update = voice_events.VoiceStateUpdateEvent()
        voice_state_update.state = self.deserialize_voice_state(payload)
        return voice_state_update

    def deserialize_voice_server_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        voice_server_update = voice_events.VoiceServerUpdateEvent()
        voice_server_update.token = payload["token"]
        voice_server_update.guild_id = snowflake.Snowflake(payload["guild_id"])
        voice_server_update._endpoint = payload["endpoint"]
        return voice_server_update

    def serialize_gateway_presence(
        self,
        idle_since: typing.Optional[datetime.datetime],
        afk: bool,
        status: presence_models.Status,
        activity: typing.Optional[presence_models.Activity],
    ) -> data_binding.JSONObject:
        payload = data_binding.JSONObjectBuilder()

        if activity is not None:
            payload.put("game", {"name": activity.name, "url": activity.url, "type": activity.type})
        else:
            payload.put("game", None)

        payload.put("since", int(idle_since.timestamp() * 1_000) if idle_since is not None else None)
        payload.put("afk", afk)

        # Turns out Discord don't document this properly. I can send "offline"
        # to the gateway, but it will actually just result in the bot not
        # changing the status. I have to set it to "invisible" instead to get
        # this to work...
        payload.put("status", "invisible" if status is presence_models.Status.OFFLINE else status)

        return payload

    def serialize_gateway_voice_state_update(
        self,
        guild: typing.Union[guild_models.Guild, snowflake.SnowflakeishOr],
        channel: typing.Union[channel_models.GuildVoiceChannel, snowflake.SnowflakeishOr, None],
        self_mute: bool,
        self_deaf: bool,
    ) -> data_binding.JSONObject:
        return {
            "guild_id": str(int(guild)),
            "channel_id": str(int(channel)) if channel is not None else None,
            "self_mute": self_mute,
            "self_deaf": self_deaf,
        }

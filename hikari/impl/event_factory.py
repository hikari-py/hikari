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

__all__: typing.Final[typing.List[str]] = ["EventFactoryComponentImpl"]

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
    ) -> channel_events.PinsUpdateEvent:
        channel_id = snowflake.Snowflake(payload["channel_id"])

        # Turns out this _can_ be None or not present. Only set it if it is actually available.
        if (raw := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp: typing.Optional[datetime.datetime] = date.iso8601_datetime_string_to_datetime(raw)
        else:
            last_pin_timestamp = None

        if "guild_id" in payload:
            return channel_events.GuildPinsUpdateEvent(
                shard=shard,
                channel_id=channel_id,
                guild_id=snowflake.Snowflake(payload["guild_id"]),
                last_pin_timestamp=last_pin_timestamp,
            )

        return channel_events.PrivatePinsUpdateEvent(
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
            member = self.app.entity_factory.deserialize_member(payload["member"], guild_id=guild_id)
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
        guild_information = self.app.entity_factory.deserialize_gateway_guild(payload)
        assert guild_information.channels is not None
        assert guild_information.members is not None
        assert guild_information.presences is not None
        assert guild_information.voice_states is not None
        return guild_events.GuildAvailableEvent(
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
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUpdateEvent:
        guild_information = self.app.entity_factory.deserialize_gateway_guild(payload)
        return guild_events.GuildUpdateEvent(
            shard=shard, guild=guild_information.guild, emojis=guild_information.emojis, roles=guild_information.roles,
        )

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
        user: typing.Optional[user_models.PartialUser] = None
        # Here we're told that the only guaranteed field is "id", so if we only get 1 field in the user payload then
        # then we've only got an ID and there's no reason to form a user object.
        if len(user_payload) > 1:
            # PartialUser
            discriminator = user_payload["discriminator"] if "discriminator" in user_payload else undefined.UNDEFINED
            flags: undefined.UndefinedOr[user_models.UserFlag] = undefined.UNDEFINED
            if "public_flags" in user_payload:
                flags = user_models.UserFlag(user_payload["public_flags"])

            user = user_models.PartialUser(
                app=self._app,
                id=snowflake.Snowflake(user_payload["id"]),
                discriminator=discriminator,
                username=user_payload.get("username", undefined.UNDEFINED),
                avatar_hash=user_payload.get("avatar", undefined.UNDEFINED),
                is_bot=user_payload.get("bot", undefined.UNDEFINED),
                is_system=user_payload.get("system", undefined.UNDEFINED),
                flags=flags,
            )
            # noinspection PyArgumentList

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
        channel_id = snowflake.Snowflake(payload["channel_id"])
        message_id = snowflake.Snowflake(payload["message_id"])
        emoji = self.app.entity_factory.deserialize_emoji(payload["emoji"])

        if "member" in payload:
            guild_id = snowflake.Snowflake(payload["guild_id"])
            member = self.app.entity_factory.deserialize_member(payload["member"], guild_id=guild_id)
            return reaction_events.GuildReactionAddEvent(
                shard=shard, member=member, channel_id=channel_id, message_id=message_id, emoji=emoji,
            )

        user_id = snowflake.Snowflake(payload["user_id"])
        return reaction_events.PrivateReactionAddEvent(
            shard=shard, channel_id=channel_id, message_id=message_id, user_id=user_id, emoji=emoji,
        )

    def deserialize_message_reaction_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEvent:
        channel_id = snowflake.Snowflake(payload["channel_id"])
        message_id = snowflake.Snowflake(payload["message_id"])
        user_id = snowflake.Snowflake(payload["user_id"])
        emoji = self.app.entity_factory.deserialize_emoji(payload["emoji"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteEvent(
                shard=shard,
                user_id=user_id,
                guild_id=snowflake.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
                emoji=emoji,
            )

        return reaction_events.PrivateReactionDeleteEvent(
            shard=shard, user_id=user_id, channel_id=channel_id, message_id=message_id, emoji=emoji,
        )

    def deserialize_message_reaction_remove_all_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteAllEvent:
        channel_id = snowflake.Snowflake(payload["channel_id"])
        message_id = snowflake.Snowflake(payload["message_id"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteAllEvent(
                shard=shard,
                guild_id=snowflake.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
            )

        # TODO: check if this can even occur.
        return reaction_events.PrivateReactionDeleteAllEvent(shard=shard, channel_id=channel_id, message_id=message_id,)

    def deserialize_message_reaction_remove_emoji_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEmojiEvent:
        channel_id = snowflake.Snowflake(payload["channel_id"])
        message_id = snowflake.Snowflake(payload["message_id"])
        emoji = self.app.entity_factory.deserialize_emoji(payload["emoji"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteEmojiEvent(
                shard=shard,
                emoji=emoji,
                guild_id=snowflake.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
            )

        # TODO: check if this can even occur.
        return reaction_events.PrivateReactionDeleteEmojiEvent(
            shard=shard, emoji=emoji, channel_id=channel_id, message_id=message_id,
        )

    ################
    # OTHER EVENTS #
    ################

    def deserialize_ready_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.ShardReadyEvent:
        gateway_version = int(payload["v"])
        my_user = self.app.entity_factory.deserialize_my_user(payload["user"])
        unavailable_guilds = [snowflake.Snowflake(guild["id"]) for guild in payload["guilds"]]
        session_id = payload["session_id"]

        return shard_events.ShardReadyEvent(
            shard=shard,
            actual_gateway_version=gateway_version,
            session_id=session_id,
            my_user=my_user,
            unavailable_guilds=unavailable_guilds,
        )

    def deserialize_own_user_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> user_events.OwnUserUpdateEvent:
        return user_events.OwnUserUpdateEvent(shard=shard, user=self.app.entity_factory.deserialize_my_user(payload),)

    def deserialize_guild_member_chunk_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.MemberChunkEvent:
        guild_id = snowflake.Snowflake(payload["guild_id"])
        index = int(payload["chunk_index"])
        count = int(payload["chunk_count"])
        members = {
            snowflake.Snowflake(m["user"]["id"]): self.app.entity_factory.deserialize_member(m, guild_id=guild_id)
            for m in payload["members"]
        }
        # Note, these IDs may be returned as ints or strings based on whether they're over a certain value.
        not_found = [snowflake.Snowflake(sn) for sn in payload["not_found"]] if "not_found" in payload else []

        nonce = typing.cast("typing.Optional[str]", payload.get("nonce"))

        if (presence_payloads := payload.get("presences")) is not None:
            presences = {
                snowflake.Snowflake(p["user"]["id"]): self.app.entity_factory.deserialize_member_presence(
                    p, guild_id=guild_id
                )
                for p in presence_payloads
            }
        else:
            presences = {}

        return guild_events.MemberChunkEvent(
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
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceStateUpdateEvent:
        state = self.app.entity_factory.deserialize_voice_state(payload)
        return voice_events.VoiceStateUpdateEvent(shard=shard, state=state)

    def deserialize_voice_server_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        token = payload["token"]
        guild_id = snowflake.Snowflake(payload["guild_id"])
        raw_endpoint = payload["endpoint"]
        return voice_events.VoiceServerUpdateEvent(
            shard=shard, guild_id=guild_id, token=token, raw_endpoint=raw_endpoint
        )

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
        guild: snowflake.SnowflakeishOr[guild_models.PartialGuild],
        channel: typing.Optional[snowflake.SnowflakeishOr[channel_models.GuildVoiceChannel]],
        self_mute: bool,
        self_deaf: bool,
    ) -> data_binding.JSONObject:
        return {
            "guild_id": str(int(guild)),
            "channel_id": str(int(channel)) if channel is not None else None,
            "self_mute": self_mute,
            "self_deaf": self_deaf,
        }

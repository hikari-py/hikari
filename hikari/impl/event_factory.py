# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = ["EventFactoryImpl"]

import datetime
import types
import typing

from hikari import applications as application_models
from hikari import channels as channel_models
from hikari import colors
from hikari import emojis as emojis_models
from hikari import snowflakes
from hikari import undefined
from hikari import users as user_models
from hikari.api import event_factory
from hikari.events import channel_events
from hikari.events import guild_events
from hikari.events import interaction_events
from hikari.events import lifetime_events
from hikari.events import member_events
from hikari.events import message_events
from hikari.events import reaction_events
from hikari.events import role_events
from hikari.events import shard_events
from hikari.events import typing_events
from hikari.events import user_events
from hikari.events import voice_events
from hikari.internal import collections
from hikari.internal import data_binding
from hikari.internal import time

if typing.TYPE_CHECKING:
    from hikari import guilds as guild_models
    from hikari import invites as invite_models
    from hikari import messages as messages_models
    from hikari import presences as presences_models
    from hikari import traits
    from hikari import voices as voices_models
    from hikari.api import shard as gateway_shard


class EventFactoryImpl(event_factory.EventFactory):
    """Implementation for a single-application bot event factory."""

    __slots__: typing.Sequence[str] = ("_app",)

    def __init__(self, app: traits.RESTAware) -> None:
        self._app = app

    ##################
    # CHANNEL EVENTS #
    ##################

    def deserialize_guild_channel_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.GuildChannelCreateEvent:
        channel = self._app.entity_factory.deserialize_channel(payload)
        assert isinstance(channel, channel_models.GuildChannel), "DM channel create events are undocumented behaviour"
        return channel_events.GuildChannelCreateEvent(shard=shard, channel=channel)

    def deserialize_guild_channel_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_channel: typing.Optional[channel_models.GuildChannel],
    ) -> channel_events.GuildChannelUpdateEvent:
        channel = self._app.entity_factory.deserialize_channel(payload)
        assert isinstance(channel, channel_models.GuildChannel), "DM channel update events are undocumented behaviour"
        return channel_events.GuildChannelUpdateEvent(shard=shard, channel=channel, old_channel=old_channel)

    def deserialize_guild_channel_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.GuildChannelDeleteEvent:
        channel = self._app.entity_factory.deserialize_channel(payload)
        assert isinstance(channel, channel_models.GuildChannel), "DM channel delete events are undocumented behaviour"
        return channel_events.GuildChannelDeleteEvent(shard=shard, channel=channel)

    def deserialize_channel_pins_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.PinsUpdateEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])

        # Turns out this can be None or not present. Only set it if it is actually available.
        if (raw := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp: typing.Optional[datetime.datetime] = time.iso8601_datetime_string_to_datetime(raw)
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

        return channel_events.DMPinsUpdateEvent(
            app=self._app, shard=shard, channel_id=channel_id, last_pin_timestamp=last_pin_timestamp
        )

    def deserialize_webhook_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.WebhookUpdateEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        return channel_events.WebhookUpdateEvent(
            app=self._app,
            shard=shard,
            channel_id=channel_id,
            guild_id=guild_id,
        )

    def deserialize_invite_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteCreateEvent:
        invite = self._app.entity_factory.deserialize_invite_with_metadata(payload)
        return channel_events.InviteCreateEvent(shard=shard, invite=invite)

    def deserialize_invite_delete_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_invite: typing.Optional[invite_models.InviteWithMetadata],
    ) -> channel_events.InviteDeleteEvent:
        return channel_events.InviteDeleteEvent(
            app=self._app,
            shard=shard,
            code=payload["code"],
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            old_invite=old_invite,
        )

    #################
    # TYPING EVENTS #
    ##################

    def deserialize_typing_start_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> typing_events.TypingEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        # Turns out that this endpoint uses seconds rather than milliseconds.
        timestamp = time.unix_epoch_to_datetime(payload["timestamp"], is_millis=False)

        if "guild_id" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])
            member = self._app.entity_factory.deserialize_member(payload["member"], guild_id=guild_id)
            return typing_events.GuildTypingEvent(
                shard=shard,
                channel_id=channel_id,
                guild_id=guild_id,
                timestamp=timestamp,
                member=member,
            )

        user_id = snowflakes.Snowflake(payload["user_id"])
        return typing_events.DMTypingEvent(
            app=self._app, shard=shard, channel_id=channel_id, user_id=user_id, timestamp=timestamp
        )

    ################
    # GUILD EVENTS #
    ################

    def deserialize_guild_available_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildAvailableEvent:
        guild_information = self._app.entity_factory.deserialize_gateway_guild(payload)
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

    def deserialize_guild_join_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildJoinEvent:
        guild_information = self._app.entity_factory.deserialize_gateway_guild(payload)
        assert guild_information.channels is not None
        assert guild_information.members is not None
        assert guild_information.presences is not None
        assert guild_information.voice_states is not None
        return guild_events.GuildJoinEvent(
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
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_guild: typing.Optional[guild_models.GatewayGuild],
    ) -> guild_events.GuildUpdateEvent:
        guild_information = self._app.entity_factory.deserialize_gateway_guild(payload)
        return guild_events.GuildUpdateEvent(
            shard=shard,
            guild=guild_information.guild,
            emojis=guild_information.emojis,
            roles=guild_information.roles,
            old_guild=old_guild,
        )

    def deserialize_guild_leave_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_guild: typing.Optional[guild_models.GatewayGuild],
    ) -> guild_events.GuildLeaveEvent:
        return guild_events.GuildLeaveEvent(
            app=self._app, shard=shard, guild_id=snowflakes.Snowflake(payload["id"]), old_guild=old_guild
        )

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
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            user=self._app.entity_factory.deserialize_user(payload["user"]),
        )

    def deserialize_guild_ban_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanDeleteEvent:
        return guild_events.BanDeleteEvent(
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            user=self._app.entity_factory.deserialize_user(payload["user"]),
        )

    def deserialize_guild_emojis_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_emojis: typing.Optional[typing.Sequence[emojis_models.KnownCustomEmoji]],
    ) -> guild_events.EmojisUpdateEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        emojis = [
            self._app.entity_factory.deserialize_known_custom_emoji(emoji, guild_id=guild_id)
            for emoji in payload["emojis"]
        ]
        return guild_events.EmojisUpdateEvent(
            app=self._app, shard=shard, guild_id=guild_id, emojis=emojis, old_emojis=old_emojis
        )

    def deserialize_integration_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationCreateEvent:
        return guild_events.IntegrationCreateEvent(
            app=self._app, shard=shard, integration=self._app.entity_factory.deserialize_integration(payload)
        )

    def deserialize_integration_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationDeleteEvent:
        application_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_application_id := payload.get("application_id")) is not None:
            application_id = snowflakes.Snowflake(raw_application_id)

        return guild_events.IntegrationDeleteEvent(
            id=snowflakes.Snowflake(payload["id"]),
            app=self._app,
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            application_id=application_id,
        )

    def deserialize_integration_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationUpdateEvent:
        return guild_events.IntegrationUpdateEvent(
            app=self._app, shard=shard, integration=self._app.entity_factory.deserialize_integration(payload)
        )

    def deserialize_presence_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_presence: typing.Optional[presences_models.MemberPresence],
    ) -> guild_events.PresenceUpdateEvent:
        presence = self._app.entity_factory.deserialize_member_presence(payload)

        user_payload = payload["user"]
        user: typing.Optional[user_models.PartialUser] = None
        # Here we're told that the only guaranteed field is "id", so if we only get 1 field in the user payload then
        # then we've only got an ID and there's no reason to form a user object.
        if len(user_payload) > 1:
            # PartialUser
            discriminator = user_payload.get("discriminator", undefined.UNDEFINED)
            flags: undefined.UndefinedOr[user_models.UserFlag] = undefined.UNDEFINED
            if "public_flags" in user_payload:
                flags = user_models.UserFlag(user_payload["public_flags"])

            accent_color: undefined.UndefinedNoneOr[colors.Color] = undefined.UNDEFINED
            if "accent_color" in user_payload:
                raw_accent_color = user_payload["accent_color"]
                accent_color = colors.Color(raw_accent_color) if raw_accent_color is not None else raw_accent_color

            user = user_models.PartialUserImpl(
                app=self._app,
                id=snowflakes.Snowflake(user_payload["id"]),
                discriminator=discriminator,
                username=user_payload.get("username", undefined.UNDEFINED),
                avatar_hash=user_payload.get("avatar", undefined.UNDEFINED),
                banner_hash=user_payload.get("banner", undefined.UNDEFINED),
                accent_color=accent_color,
                is_bot=user_payload.get("bot", undefined.UNDEFINED),
                is_system=user_payload.get("system", undefined.UNDEFINED),
                flags=flags,
            )
        return guild_events.PresenceUpdateEvent(shard=shard, presence=presence, user=user, old_presence=old_presence)

    ######################
    # INTERACTION EVENTS #
    ######################

    def deserialize_interaction_create_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
    ) -> interaction_events.InteractionCreateEvent:
        return interaction_events.InteractionCreateEvent(
            shard=shard,
            interaction=self._app.entity_factory.deserialize_interaction(payload),
        )

    #################
    # MEMBER EVENTS #
    #################

    def deserialize_guild_member_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberCreateEvent:
        member = self._app.entity_factory.deserialize_member(payload)
        return member_events.MemberCreateEvent(shard=shard, member=member)

    def deserialize_guild_member_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_member: typing.Optional[guild_models.Member],
    ) -> member_events.MemberUpdateEvent:
        member = self._app.entity_factory.deserialize_member(payload)
        return member_events.MemberUpdateEvent(shard=shard, member=member, old_member=old_member)

    def deserialize_guild_member_remove_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_member: typing.Optional[guild_models.Member],
    ) -> member_events.MemberDeleteEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        user = self._app.entity_factory.deserialize_user(payload["user"])
        return member_events.MemberDeleteEvent(shard=shard, guild_id=guild_id, user=user, old_member=old_member)

    ###############
    # ROLE EVENTS #
    ###############

    def deserialize_guild_role_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleCreateEvent:
        role = self._app.entity_factory.deserialize_role(
            payload["role"],
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
        )
        return role_events.RoleCreateEvent(shard=shard, role=role)

    def deserialize_guild_role_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_role: typing.Optional[guild_models.Role],
    ) -> role_events.RoleUpdateEvent:
        role = self._app.entity_factory.deserialize_role(
            payload["role"],
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
        )
        return role_events.RoleUpdateEvent(shard=shard, role=role, old_role=old_role)

    def deserialize_guild_role_delete_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_role: typing.Optional[guild_models.Role],
    ) -> role_events.RoleDeleteEvent:
        return role_events.RoleDeleteEvent(
            app=self._app,
            shard=shard,
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            role_id=snowflakes.Snowflake(payload["role_id"]),
            old_role=old_role,
        )

    ###################
    # LIFETIME EVENTS #
    ###################

    def deserialize_starting_event(self) -> lifetime_events.StartingEvent:
        return lifetime_events.StartingEvent(app=self._app)

    def deserialize_started_event(self) -> lifetime_events.StartedEvent:
        return lifetime_events.StartedEvent(app=self._app)

    def deserialize_stopping_event(self) -> lifetime_events.StoppingEvent:
        return lifetime_events.StoppingEvent(app=self._app)

    def deserialize_stopped_event(self) -> lifetime_events.StoppedEvent:
        return lifetime_events.StoppedEvent(app=self._app)

    ##################
    # MESSAGE EVENTS #
    ##################

    def deserialize_message_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageCreateEvent:
        message = self._app.entity_factory.deserialize_message(payload)

        if message.guild_id is None:
            return message_events.DMMessageCreateEvent(shard=shard, message=message)

        return message_events.GuildMessageCreateEvent(shard=shard, message=message)

    def deserialize_message_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_message: typing.Optional[messages_models.PartialMessage],
    ) -> message_events.MessageUpdateEvent:
        message = self._app.entity_factory.deserialize_partial_message(payload)

        if message.guild_id is None:
            return message_events.DMMessageUpdateEvent(shard=shard, message=message, old_message=old_message)

        return message_events.GuildMessageUpdateEvent(shard=shard, message=message, old_message=old_message)

    def deserialize_message_delete_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_message: typing.Optional[messages_models.Message],
    ) -> message_events.MessageDeleteEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["id"])

        if "guild_id" in payload:
            return message_events.GuildMessageDeleteEvent(
                app=self._app,
                shard=shard,
                channel_id=channel_id,
                message_id=message_id,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                old_message=old_message,
            )

        return message_events.DMMessageDeleteEvent(
            app=self._app,
            shard=shard,
            channel_id=channel_id,
            message_id=message_id,
            old_message=old_message,
        )

    def deserialize_guild_message_delete_bulk_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        old_messages: typing.Mapping[snowflakes.Snowflake, messages_models.Message],
    ) -> message_events.GuildBulkMessageDeleteEvent:
        return message_events.GuildBulkMessageDeleteEvent(
            app=self._app,
            shard=shard,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            message_ids=collections.SnowflakeSet(*(snowflakes.Snowflake(message_id) for message_id in payload["ids"])),
            old_messages=old_messages,
        )

    ###################
    # REACTION EVENTS #
    ###################

    def deserialize_message_reaction_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionAddEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])

        emoji_payload = payload["emoji"]
        raw_emoji_id = emoji_payload.get("id")
        emoji_id = snowflakes.Snowflake(raw_emoji_id) if raw_emoji_id else None
        is_animated = bool(emoji_payload.get("animated", False))
        emoji_name = emojis_models.UnicodeEmoji(emoji_payload["name"]) if not emoji_id else emoji_payload["name"]

        if "member" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])
            member = self._app.entity_factory.deserialize_member(payload["member"], guild_id=guild_id)
            return reaction_events.GuildReactionAddEvent(
                shard=shard,
                member=member,
                channel_id=channel_id,
                message_id=message_id,
                emoji_id=emoji_id,
                emoji_name=emoji_name,
                is_animated=is_animated,
            )

        user_id = snowflakes.Snowflake(payload["user_id"])
        return reaction_events.DMReactionAddEvent(
            app=self._app,
            shard=shard,
            channel_id=channel_id,
            message_id=message_id,
            user_id=user_id,
            emoji_id=emoji_id,
            emoji_name=emoji_name,
            is_animated=is_animated,
        )

    def _split_reaction_emoji(
        self, emoji_payload: data_binding.JSONObject, /
    ) -> typing.Tuple[typing.Optional[snowflakes.Snowflake], typing.Union[str, emojis_models.UnicodeEmoji, None]]:
        if (emoji_id := emoji_payload.get("id")) is not None:
            return snowflakes.Snowflake(emoji_id), emoji_payload["name"]

        return None, emojis_models.UnicodeEmoji(emoji_payload["name"])

    def deserialize_message_reaction_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])
        user_id = snowflakes.Snowflake(payload["user_id"])
        emoji_id, emoji_name = self._split_reaction_emoji(payload["emoji"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteEvent(
                app=self._app,
                shard=shard,
                user_id=user_id,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
                emoji_id=emoji_id,
                emoji_name=emoji_name,
            )

        return reaction_events.DMReactionDeleteEvent(
            app=self._app,
            shard=shard,
            user_id=user_id,
            channel_id=channel_id,
            message_id=message_id,
            emoji_id=emoji_id,
            emoji_name=emoji_name,
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

        return reaction_events.DMReactionDeleteAllEvent(
            app=self._app,
            shard=shard,
            channel_id=channel_id,
            message_id=message_id,
        )

    def deserialize_message_reaction_remove_emoji_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEmojiEvent:
        channel_id = snowflakes.Snowflake(payload["channel_id"])
        message_id = snowflakes.Snowflake(payload["message_id"])
        emoji_id, emoji_name = self._split_reaction_emoji(payload["emoji"])

        if "guild_id" in payload:
            return reaction_events.GuildReactionDeleteEmojiEvent(
                app=self._app,
                shard=shard,
                emoji_id=emoji_id,
                emoji_name=emoji_name,
                guild_id=snowflakes.Snowflake(payload["guild_id"]),
                channel_id=channel_id,
                message_id=message_id,
            )

        return reaction_events.DMReactionDeleteEmojiEvent(
            app=self._app,
            shard=shard,
            emoji_id=emoji_id,
            emoji_name=emoji_name,
            channel_id=channel_id,
            message_id=message_id,
        )

    ################
    # SHARD EVENTS #
    ################

    def deserialize_shard_payload_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject, *, name: str
    ) -> shard_events.ShardPayloadEvent:
        payload = types.MappingProxyType(payload)
        return shard_events.ShardPayloadEvent(app=self._app, shard=shard, payload=payload, name=name)

    def deserialize_ready_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.ShardReadyEvent:
        gateway_version = int(payload["v"])
        my_user = self._app.entity_factory.deserialize_my_user(payload["user"])
        unavailable_guilds = [snowflakes.Snowflake(guild["id"]) for guild in payload["guilds"]]
        session_id = payload["session_id"]

        return shard_events.ShardReadyEvent(
            shard=shard,
            actual_gateway_version=gateway_version,
            session_id=session_id,
            my_user=my_user,
            unavailable_guilds=unavailable_guilds,
            application_id=snowflakes.Snowflake(payload["application"]["id"]),
            application_flags=application_models.ApplicationFlags(int(payload["application"]["flags"])),
        )

    def deserialize_connected_event(self, shard: gateway_shard.GatewayShard) -> shard_events.ShardConnectedEvent:
        return shard_events.ShardConnectedEvent(app=self._app, shard=shard)

    def deserialize_disconnected_event(self, shard: gateway_shard.GatewayShard) -> shard_events.ShardDisconnectedEvent:
        return shard_events.ShardDisconnectedEvent(app=self._app, shard=shard)

    def deserialize_resumed_event(self, shard: gateway_shard.GatewayShard) -> shard_events.ShardResumedEvent:
        return shard_events.ShardResumedEvent(app=self._app, shard=shard)

    def deserialize_guild_member_chunk_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.MemberChunkEvent:
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        index = int(payload["chunk_index"])
        count = int(payload["chunk_count"])
        members = {
            snowflakes.Snowflake(m["user"]["id"]): self._app.entity_factory.deserialize_member(m, guild_id=guild_id)
            for m in payload["members"]
        }
        # Note, these IDs may be returned as ints or strings based on whether they're over a certain value.
        not_found = [snowflakes.Snowflake(sn) for sn in payload["not_found"]] if "not_found" in payload else []

        if presence_payloads := payload.get("presences"):
            presences = {
                snowflakes.Snowflake(p["user"]["id"]): self._app.entity_factory.deserialize_member_presence(
                    p, guild_id=guild_id
                )
                for p in presence_payloads
            }
        else:
            presences = {}

        return shard_events.MemberChunkEvent(
            app=self._app,
            shard=shard,
            guild_id=guild_id,
            members=members,
            chunk_index=index,
            chunk_count=count,
            not_found=not_found,
            presences=presences,
            nonce=payload.get("nonce"),
        )

    ###############
    # USER EVENTS #
    ###############

    def deserialize_own_user_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_user: typing.Optional[user_models.OwnUser],
    ) -> user_events.OwnUserUpdateEvent:
        return user_events.OwnUserUpdateEvent(
            shard=shard, user=self._app.entity_factory.deserialize_my_user(payload), old_user=old_user
        )

    ################
    # VOICE EVENTS #
    ################

    def deserialize_voice_state_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_state: typing.Optional[voices_models.VoiceState],
    ) -> voice_events.VoiceStateUpdateEvent:
        state = self._app.entity_factory.deserialize_voice_state(payload)
        return voice_events.VoiceStateUpdateEvent(shard=shard, state=state, old_state=old_state)

    def deserialize_voice_server_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        token = payload["token"]
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        raw_endpoint = payload["endpoint"]
        return voice_events.VoiceServerUpdateEvent(
            app=self._app, shard=shard, guild_id=guild_id, token=token, raw_endpoint=raw_endpoint
        )

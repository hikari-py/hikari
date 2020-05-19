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
import contextlib
import datetime

import mock
import pytest

from hikari.events import message
from hikari.internal import conversions
from hikari.models import applications
from hikari.models import embeds
from hikari.models import emojis
from hikari.models import guilds
from hikari.models import messages
from hikari.models import unset
from hikari.models import users
from tests.hikari import _helpers


@pytest.fixture()
def test_emoji_payload():
    return {"id": "4242", "name": "blahblah", "animated": True}


@pytest.fixture()
def test_user_payload():
    return {"id": "2929292", "username": "agent 69", "discriminator": "4444", "avatar": "9292929292929292"}


@pytest.fixture()
def test_member_payload(test_user_payload):
    return {
        "user": test_user_payload,
        "nick": "Agent 42",
        "roles": [],
        "joined_at": "2015-04-26T06:26:56.936000+00:00",
        "premium_since": "2019-05-17T06:26:56.936000+00:00",
        "deaf": True,
        "mute": False,
    }


@pytest.fixture()
def test_channel_payload():
    return {"id": "393939", "name": "a channel", "type": 2}


# Doesn't declare any new fields.
class TestMessageCreateEvent:
    ...


class TestMessageUpdateEvent:
    @pytest.fixture()
    def test_attachment_payload(self):
        return {
            "id": "4242",
            "filename": "nyaa.png",
            "size": 1024,
            "url": "heck.heck",
            "_proxy_url": "proxy.proxy?heck",
            "height": 42,
            "width": 84,
        }

    @pytest.fixture()
    def test_embed_payload(self):
        return {"title": "42", "description": "blah blah blah"}

    @pytest.fixture()
    def test_reaction_payload(self):
        return {"count": 69, "me": True, "emoji": "🤣"}

    @pytest.fixture()
    def test_activity_payload(self):
        return {"type": 1, "party_id": "spotify:23123123"}

    @pytest.fixture()
    def test_application_payload(self):
        return {"id": "292929", "icon": None, "description": "descript", "name": "A name"}

    @pytest.fixture()
    def test_reference_payload(self):
        return {"channel": "432341231231"}

    @pytest.fixture()
    def test_message_update_payload(
        self,
        test_user_payload,
        test_member_payload,
        test_attachment_payload,
        test_embed_payload,
        test_reaction_payload,
        test_activity_payload,
        test_application_payload,
        test_reference_payload,
        test_channel_payload,
    ):
        return {
            "id": "3939399393",
            "channel": "93939393939",
            "guild_id": "66557744883399",
            "author": test_user_payload,
            "member": test_member_payload,
            "content": "THIS IS A CONTENT",
            "timestamp": "2019-05-17T06:26:56.936000+00:00",
            "edited_timestamp": "2019-05-17T06:58:56.936000+00:00",
            "tts": True,
            "mention_everyone": True,
            "mentions": [test_user_payload],
            "mention_roles": ["123"],
            "mention_channels": [test_channel_payload],
            "attachments": [test_attachment_payload],
            "embeds": [test_embed_payload],
            "reactions": [test_reaction_payload],
            "nonce": "6454345345345345",
            "pinned": True,
            "webhook_id": "212231231232123",
            "type": 2,
            "activity": test_activity_payload,
            "application": test_application_payload,
            "message_reference": test_reference_payload,
            "flags": 3,
        }

    def test_deserialize(
        self,
        test_message_update_payload,
        test_user_payload,
        test_member_payload,
        test_activity_payload,
        test_application_payload,
        test_reference_payload,
        test_attachment_payload,
        test_embed_payload,
        test_reaction_payload,
    ):
        mock_author = mock.MagicMock(users.User)
        mock_member = mock.MagicMock(guilds.GuildMember)
        mock_timestamp = mock.MagicMock(datetime.datetime)
        mock_edited_timestamp = mock.MagicMock(datetime.datetime)
        mock_attachment = mock.MagicMock(messages.Attachment)
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_reaction = mock.MagicMock(messages.Reaction)
        mock_activity = mock.MagicMock(messages.MessageActivity)
        mock_application = mock.MagicMock(applications.Application)
        mock_reference = mock.MagicMock(messages.MessageCrosspost)
        stack = contextlib.ExitStack()
        patched_author_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent, "author", deserializer=users.User.deserialize, return_value=mock_author
            )
        )
        patched_member_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent,
                "member",
                deserializer=guilds.GuildMember.deserialize,
                return_value=mock_member,
            )
        )
        patched_timestamp_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent,
                "timestamp",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_timestamp,
            )
        )
        patched_edit_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent,
                "edited_timestamp",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_edited_timestamp,
            )
        )
        patched_activity_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent,
                "activity",
                deserializer=messages.MessageActivity.deserialize,
                return_value=mock_activity,
            )
        )
        patched_application_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent,
                "application",
                deserializer=applications.Application.deserialize,
                return_value=mock_application,
            )
        )
        patched_reference_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageUpdateEvent,
                "message_reference",
                deserializer=messages.MessageCrosspost.deserialize,
                return_value=mock_reference,
            )
        )
        stack.enter_context(mock.patch.object(messages.Attachment, "deserialize", return_value=mock_attachment))
        stack.enter_context(mock.patch.object(embeds.Embed, "deserialize", return_value=mock_embed))
        stack.enter_context(mock.patch.object(messages.Reaction, "deserialize", return_value=mock_reaction))
        with stack:
            message_update_payload = message.MessageUpdateEvent.deserialize(test_message_update_payload)
            messages.Reaction.deserialize.assert_called_once_with(test_reaction_payload)
            embeds.Embed.deserialize.assert_called_once_with(test_embed_payload)
            messages.Attachment.deserialize.assert_called_once_with(test_attachment_payload)
            patched_reference_deserializer.assert_called_once_with(test_reference_payload)
            patched_application_deserializer.assert_called_once_with(test_application_payload)
            patched_activity_deserializer.assert_called_once_with(test_activity_payload)
            patched_edit_deserializer.assert_called_once_with("2019-05-17T06:58:56.936000+00:00")
            patched_timestamp_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
            patched_member_deserializer.assert_called_once_with(test_member_payload)
            patched_author_deserializer.assert_called_once_with(test_user_payload)
        assert message_update_payload.channel_id == 93939393939
        assert message_update_payload.guild_id == 66557744883399
        assert message_update_payload.author is mock_author
        assert message_update_payload.member is mock_member
        assert message_update_payload.content == "THIS IS A CONTENT"
        assert message_update_payload.timestamp is mock_timestamp
        assert message_update_payload.edited_timestamp is mock_edited_timestamp
        assert message_update_payload.is_tts is True
        assert message_update_payload.is_mentioning_everyone is True
        assert message_update_payload.user_mentions == {2929292}
        assert message_update_payload.role_mentions == {123}
        assert message_update_payload.channel_mentions == {393939}
        assert message_update_payload.attachments == [mock_attachment]
        assert message_update_payload.embeds == [mock_embed]
        assert message_update_payload.reactions == [mock_reaction]
        assert message_update_payload.is_pinned is True
        assert message_update_payload.webhook_id == 212231231232123
        assert message_update_payload.type is messages.MessageType.RECIPIENT_REMOVE
        assert message_update_payload.activity is mock_activity
        assert message_update_payload.application is mock_application
        assert message_update_payload.message_reference is mock_reference
        assert message_update_payload.flags == messages.MessageFlag.CROSSPOSTED | messages.MessageFlag.IS_CROSSPOST
        assert message_update_payload.nonce == "6454345345345345"

    def test_partial_message_update(self):
        message_update_obj = message.MessageUpdateEvent.deserialize({"id": "393939", "channel": "434949"})
        for key in message_update_obj.__slots__:
            if key in ("id", "channel"):
                continue
            assert getattr(message_update_obj, key) is unset.UNSET
        assert message_update_obj.id == 393939
        assert message_update_obj.channel_id == 434949


class TestMessageDeleteEvent:
    @pytest.fixture()
    def test_message_delete_payload(self):
        return {"channel": "20202020", "id": "2929", "guild_id": "1010101"}

    def test_deserialize(self, test_message_delete_payload):
        message_delete_obj = message.MessageDeleteEvent.deserialize(test_message_delete_payload)
        assert message_delete_obj.channel_id == 20202020
        assert message_delete_obj.message_id == 2929
        assert message_delete_obj.guild_id == 1010101


class TestMessageDeleteBulkEvent:
    @pytest.fixture()
    def test_message_delete_bulk_payload(self):
        return {"channel": "20202020", "ids": ["2929", "4394"], "guild_id": "1010101"}

    def test_deserialize(self, test_message_delete_bulk_payload):
        message_delete_bulk_obj = message.MessageDeleteBulkEvent.deserialize(test_message_delete_bulk_payload)
        assert message_delete_bulk_obj.channel_id == 20202020
        assert message_delete_bulk_obj.guild_id == 1010101
        assert message_delete_bulk_obj.message_ids == {2929, 4394}


class TestMessageReactionAddEvent:
    @pytest.fixture()
    def test_message_reaction_add_payload(self, test_member_payload, test_emoji_payload):
        return {
            "user_id": "9494949",
            "channel": "4393939",
            "message_id": "2993993",
            "guild_id": "49494949",
            "member": test_member_payload,
            "emoji": test_emoji_payload,
        }

    def test_deserialize(self, test_message_reaction_add_payload, test_member_payload, test_emoji_payload):
        mock_member = mock.MagicMock(guilds.GuildMember)
        mock_emoji = mock.MagicMock(emojis.CustomEmoji)
        stack = contextlib.ExitStack()
        patched_member_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageReactionAddEvent,
                "member",
                deserializer=guilds.GuildMember.deserialize,
                return_value=mock_member,
            )
        )
        patched_emoji_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                message.MessageReactionAddEvent,
                "emoji",
                deserializer=emojis.deserialize_reaction_emoji,
                return_value=mock_emoji,
            )
        )
        with stack:
            message_reaction_add_obj = message.MessageReactionAddEvent.deserialize(test_message_reaction_add_payload)
            patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
            patched_member_deserializer.assert_called_once_with(test_member_payload)
        assert message_reaction_add_obj.user_id == 9494949
        assert message_reaction_add_obj.channel_id == 4393939
        assert message_reaction_add_obj.message_id == 2993993
        assert message_reaction_add_obj.guild_id == 49494949
        assert message_reaction_add_obj.member is mock_member
        assert message_reaction_add_obj.emoji is mock_emoji


class TestMessageReactionRemoveEvent:
    @pytest.fixture()
    def test_message_reaction_remove_payload(self, test_emoji_payload):
        return {
            "user_id": "9494949",
            "channel": "4393939",
            "message_id": "2993993",
            "guild_id": "49494949",
            "emoji": test_emoji_payload,
        }

    def test_deserialize(self, test_message_reaction_remove_payload, test_emoji_payload):
        mock_emoji = mock.MagicMock(emojis.CustomEmoji)
        with _helpers.patch_marshal_attr(
            message.MessageReactionRemoveEvent,
            "emoji",
            deserializer=emojis.deserialize_reaction_emoji,
            return_value=mock_emoji,
        ) as patched_emoji_deserializer:
            message_reaction_remove_obj = message.MessageReactionRemoveEvent.deserialize(
                test_message_reaction_remove_payload
            )
            patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
        assert message_reaction_remove_obj.user_id == 9494949
        assert message_reaction_remove_obj.channel_id == 4393939
        assert message_reaction_remove_obj.message_id == 2993993
        assert message_reaction_remove_obj.guild_id == 49494949
        assert message_reaction_remove_obj.emoji is mock_emoji


class TestMessageReactionRemoveAllEvent:
    @pytest.fixture()
    def test_reaction_remove_all_payload(self):
        return {"channel": "3493939", "message_id": "944949", "guild_id": "49494949"}

    def test_deserialize(self, test_reaction_remove_all_payload):
        message_reaction_remove_all_obj = message.MessageReactionRemoveAllEvent.deserialize(
            test_reaction_remove_all_payload
        )
        assert message_reaction_remove_all_obj.channel_id == 3493939
        assert message_reaction_remove_all_obj.message_id == 944949
        assert message_reaction_remove_all_obj.guild_id == 49494949


class TestMessageReactionRemoveEmojiEvent:
    @pytest.fixture()
    def test_message_reaction_remove_emoji_payload(self, test_emoji_payload):
        return {"channel": "4393939", "message_id": "2993993", "guild_id": "49494949", "emoji": test_emoji_payload}

    def test_deserialize(self, test_message_reaction_remove_emoji_payload, test_emoji_payload):
        mock_emoji = mock.MagicMock(emojis.CustomEmoji)
        with _helpers.patch_marshal_attr(
            message.MessageReactionRemoveEmojiEvent,
            "emoji",
            deserializer=emojis.deserialize_reaction_emoji,
            return_value=mock_emoji,
        ) as patched_emoji_deserializer:
            message_reaction_remove_emoji_obj = message.MessageReactionRemoveEmojiEvent.deserialize(
                test_message_reaction_remove_emoji_payload
            )
            patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
        assert message_reaction_remove_emoji_obj.channel_id == 4393939
        assert message_reaction_remove_emoji_obj.message_id == 2993993
        assert message_reaction_remove_emoji_obj.guild_id == 49494949
        assert message_reaction_remove_emoji_obj.emoji is mock_emoji

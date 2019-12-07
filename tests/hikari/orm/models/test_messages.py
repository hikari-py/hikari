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
import datetime
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import channels
from hikari.orm.models import guilds
from hikari.orm.models import messages
from tests.hikari import _helpers


@pytest.fixture()
def mock_user():
    return {"id": "1234", "username": "potato"}


@pytest.fixture()
def mock_message(mock_user):
    return {
        "type": 0,
        "id": "12345",
        "channel_id": "67890",
        "guild_id": None,
        "author": mock_user,
        "edited_timestamp": None,
        "tts": True,
        "mention_everyone": False,
        "attachments": [],
        "embeds": [],
        "pinned": False,
        "application": None,
        "activity": None,
        "content": "ayyyyyyy lmao",
        "flags": 7,
    }


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model
class TestMessage:
    def test_Message_parsing_User(self, mock_message, mock_user, fabric_obj):
        assert "webhook_id" not in mock_message, "this test needs a mock message with no webhook id set :("
        messages.Message(fabric_obj, mock_message)
        fabric_obj.state_registry.parse_user.assert_called_with(mock_user)
        fabric_obj.state_registry.parse_member.assert_not_called()
        fabric_obj.state_registry.parse_webhook.assert_not_called()

    def test_Message_parsing_Member(self, mock_message, mock_user, fabric_obj):
        mock_message["guild_id"] = "909090"
        mock_message["member"] = {"foo": "bar", "baz": "bork"}
        mock_message["author"] = {"ayy": "lmao"}
        guild_obj = _helpers.mock_model(guilds.Guild, id=909090)
        fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        messages.Message(fabric_obj, mock_message)
        fabric_obj.state_registry.parse_partial_member.assert_called_with(
            {"foo": "bar", "baz": "bork"}, {"ayy": "lmao"}, guild_obj
        )
        fabric_obj.state_registry.parse_webhook.assert_not_called()

    def test_Message_parsing_Webhook(self, mock_message, mock_user, fabric_obj):
        mock_message["guild_id"] = "909090"
        mock_message["webhook_id"] = object()  # we don't care what this really is
        messages.Message(fabric_obj, mock_message)
        fabric_obj.state_registry.parse_webhook.assert_called_with(mock_user)
        fabric_obj.state_registry.parse_user.assert_not_called()
        fabric_obj.state_registry.parse_member.assert_not_called()

    def test_Message_simple_test_data(self, mock_message, mock_user, fabric_obj):
        message_obj = messages.Message(fabric_obj, mock_message)

        assert message_obj.type is messages.MessageType.DEFAULT
        assert message_obj.id == 12345
        assert message_obj.channel_id == 67890
        assert message_obj.guild_id is None
        assert message_obj.edited_at is None
        assert message_obj.is_tts is True
        assert message_obj.is_mentioning_everyone is False
        assert len(message_obj.attachments) == 0
        assert len(message_obj.embeds) == 0
        assert message_obj.is_pinned is False
        assert message_obj.application is None
        assert message_obj.activity is None
        assert message_obj.content == "ayyyyyyy lmao"
        assert message_obj.flags & messages.MessageFlag.CROSSPOSTED
        assert message_obj.flags & messages.MessageFlag.IS_CROSSPOST
        assert message_obj.flags & messages.MessageFlag.SUPPRESS_EMBEDS
        fabric_obj.state_registry.parse_user.assert_called_with(mock_user)

    def test_Message_update_state_with_no_payload(self, mock_message, fabric_obj):
        initial = messages.Message(fabric_obj, mock_message)
        updated = messages.Message(fabric_obj, mock_message)
        updated.update_state({})
        assert initial.author == updated.author
        assert initial.edited_at == updated.edited_at
        assert initial.is_mentioning_everyone == updated.is_mentioning_everyone
        assert initial.attachments == updated.attachments
        assert initial.embeds == updated.embeds
        assert initial.is_pinned == updated.is_pinned
        assert initial.application == updated.application
        assert initial.activity == updated.activity
        assert initial.content == updated.content
        assert initial.reactions == updated.reactions

    def test_Message_update_state_reactions(self, mock_message, fabric_obj):
        message_obj = messages.Message(fabric_obj, mock_message)
        # noinspection PyTypeChecker
        message_obj.update_state({"reactions": [{"id": None, "value": "\N{OK HAND SIGN}"}]})
        fabric_obj.state_registry.parse_reaction.assert_called_once_with({"id": None, "value": "\N{OK HAND SIGN}"})

    def test_Message_complex_test_data(self, mock_user, fabric_obj):
        message_obj = messages.Message(
            fabric_obj,
            {
                "author": mock_user,
                "type": 10,
                "id": "12345",
                "channel_id": "67890",
                "guild_id": "102234",
                "edited_timestamp": "2019-10-10T05:22:33.023456+02:30",
                "tts": False,
                "mention_everyone": True,
                "attachments": [
                    {
                        "id": "5555555555555555",
                        "filename": "catto.png",
                        "size": 180,
                        "url": "http://c.at",
                        "proxy_url": "http://c.at/?proxy",
                        "width": 92,
                        "height": 69,
                    }
                ],
                "embeds": [
                    {
                        "type": "whelp",
                        "title": "hello, world",
                        "description": "ayyy lmao",
                        "fields": [{"name": "ping", "value": "pong", "inline": True}],
                        "thumbnail": {"url": "hello", "proxy_url": "world"},
                    },
                    {"type": "something", "title": "hello, world, again."},
                ],
                "pinned": True,
                "application": {
                    "id": "969696",
                    "cover_image": "123454",
                    "description": "this is a description",
                    "icon": "900",
                    "name": "fubar",
                },
                "activity": {"type": 2, "party_id": "44332211"},
                "content": "some pointless text",
                "message_reference": {
                    "channel_id": "278325129692446722",
                    "guild_id": "278325129692446720",
                    "message_id": "306588351130107906",
                },
                "something_we_didnt_account_for": "meh, it is fine to ignore it.",
            },
        )

        assert message_obj.type is messages.MessageType.USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2
        assert message_obj.id == 12345
        assert message_obj.channel_id == 67890
        assert message_obj.guild_id == 102234
        assert message_obj.edited_at == datetime.datetime(
            2019, 10, 10, 5, 22, 33, 23456, tzinfo=datetime.timezone(datetime.timedelta(hours=2, minutes=30))
        )
        assert message_obj.is_tts is False
        assert message_obj.is_mentioning_everyone is True
        assert message_obj.is_pinned is True
        assert message_obj.content == "some pointless text"
        message_obj.__repr__()

        assert len(message_obj.attachments) == 1
        assert len(message_obj.embeds) == 2
        assert message_obj.application is not None
        assert message_obj.activity is not None

        attachment0 = message_obj.attachments[0]

        assert attachment0.id == 5555555555555555
        assert attachment0.filename == "catto.png"
        assert attachment0.size == 180
        assert attachment0.url == "http://c.at"
        assert attachment0.proxy_url == "http://c.at/?proxy"
        assert attachment0.width == 92
        assert attachment0.height == 69

        embed0, embed1 = message_obj.embeds[0], message_obj.embeds[1]
        assert embed0.type == "whelp"
        assert embed0.title == "hello, world"
        assert embed0.description == "ayyy lmao"
        assert len(embed0.fields) == 1
        embed0field0 = embed0.fields[0]
        assert embed0field0.name == "ping"
        assert embed0field0.value == "pong"
        assert embed0field0.inline is True
        assert embed1.title == "hello, world, again."
        assert embed1.type == "something"

        assert message_obj.application.id == 969696
        assert message_obj.application.cover_image_id == 123454
        assert message_obj.application.description == "this is a description"
        assert message_obj.application.icon_image_id == 900
        assert message_obj.application.name == "fubar"

        assert message_obj.activity.type == messages.MessageActivityType.SPECTATE
        assert message_obj.activity.party_id == 44332211

        assert message_obj.crosspost_of.channel_id == 278325129692446722
        assert message_obj.crosspost_of.message_id == 306588351130107906
        assert message_obj.crosspost_of.guild_id == 278325129692446720

    def test_Message_guild_if_guild_message(self, mock_message, fabric_obj):
        mock_message["guild_id"] = "91827"
        message_obj = messages.Message(fabric_obj, mock_message)

        guild = mock.MagicMock()
        fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild)

        g = message_obj.guild
        assert g is guild

        fabric_obj.state_registry.get_guild_by_id.assert_called_with(91827)

    def test_Message_guild_if_dm_message(self, mock_message, fabric_obj):
        message_obj = messages.Message(fabric_obj, mock_message)
        assert message_obj.guild is None

        fabric_obj.state_registry.get_guild_by_id.assert_not_called()

    def test_Message_channel_if_guild_message(self, mock_message, fabric_obj):
        mock_message["guild_id"] = "5432"
        mock_message["channel_id"] = "1234"
        guild = mock.MagicMock(spec_set=guilds.Guild)
        guild.channels = {1234: mock.MagicMock(), 1235: mock.MagicMock()}
        message_obj = messages.Message(fabric_obj, mock_message)
        fabric_obj.state_registry.get_channel_by_id = mock.MagicMock(return_value=message_obj.channel)
        guild.channels[1234] = message_obj.channel
        c = message_obj.channel
        assert c is guild.channels[1234]

    def test_Message_channel_if_dm_message(self, mock_message, fabric_obj):
        mock_message["channel_id"] = "1234"
        channel = mock.MagicMock(spec_set=channels.Channel)
        fabric_obj.state_registry.get_channel_by_id = mock.MagicMock(return_value=channel)

        obj = messages.Message(fabric_obj, mock_message)

        c = obj.channel
        fabric_obj.state_registry.get_channel_by_id.assert_called_with(1234)
        assert c is channel


@pytest.mark.model
def test_MessageActivity():
    ma = messages.MessageActivity({"type": 3, "party_id": "999"})

    assert ma.type == messages.MessageActivityType.LISTEN
    assert ma.party_id == 999
    ma.__repr__()


@pytest.mark.model
def test_MessageApplication():
    ma = messages.MessageApplication(
        {"id": "19", "cover_image": "112233", "description": "potato", "icon": "332211", "name": "poof"}
    )

    assert ma.id == 19
    assert ma.icon_image_id == 332211
    assert ma.cover_image_id == 112233
    assert ma.description == "potato"
    assert ma.name == "poof"
    ma.__repr__()


@pytest.mark.model
def test_MessageCrosspost():
    mcp = messages.MessageCrosspost(
        {"channel_id": "278325129692446722", "guild_id": "278325129692446720", "message_id": "306588351130107906"}
    )

    assert mcp.channel_id == 278325129692446722
    assert mcp.message_id == 306588351130107906
    assert mcp.guild_id == 278325129692446720
    mcp.__repr__()

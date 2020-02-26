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
from hikari.orm.http import base_http_adapter

from hikari.orm import fabric
from hikari.orm.models import channels
from hikari.orm.models import guilds
from hikari.orm.models import members
from hikari.orm.models import messages
from hikari.orm.models import users
from hikari.orm.models import webhooks
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture
def mock_user():
    return {"id": "1234", "username": "potato"}


@pytest.fixture
def mock_message_payload(mock_user):
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


@pytest.fixture
def mock_state_registry():
    return _helpers.create_autospec(base_registry.BaseRegistry)


@pytest.fixture
def mock_http_adapter():
    return _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)


@pytest.fixture
def fabric_obj(mock_state_registry, mock_http_adapter):
    mock_obj = mock.create_autospec(fabric.Fabric, spec_set=True)
    mock_obj.state_registry = mock_state_registry
    mock_obj.http_adapter = mock_http_adapter
    return mock_obj


@pytest.mark.model
class TestMessage:
    def test_parsing_User(self, mock_message_payload, mock_user, fabric_obj):
        assert "webhook_id" not in mock_message_payload, "this test needs a mock message with no webhook id set :("
        messages.Message(fabric_obj, mock_message_payload)
        fabric_obj.state_registry.parse_user.assert_called_with(mock_user)
        fabric_obj.state_registry.parse_member.assert_not_called()
        fabric_obj.state_registry.parse_webhook.assert_not_called()

    def test_parsing_Member(self, mock_message_payload, mock_user, fabric_obj):
        mock_message_payload["guild_id"] = "909090"
        mock_message_payload["member"] = {"foo": "bar", "baz": "bork"}
        mock_message_payload["author"] = {"ayy": "lmao"}
        guild_obj = _helpers.mock_model(guilds.Guild, id=909090)
        fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        messages.Message(fabric_obj, mock_message_payload)
        fabric_obj.state_registry.parse_partial_member.assert_called_with(
            {"foo": "bar", "baz": "bork"}, {"ayy": "lmao"}, guild_obj
        )
        fabric_obj.state_registry.parse_webhook.assert_not_called()

    def test_parsing_Webhook(self, mock_message_payload, mock_user, fabric_obj):
        mock_message_payload["guild_id"] = "909090"
        mock_message_payload["webhook_id"] = object()  # we don't care what this really is
        messages.Message(fabric_obj, mock_message_payload)
        fabric_obj.state_registry.parse_webhook_user.assert_called_with(mock_user)
        fabric_obj.state_registry.parse_user.assert_not_called()
        fabric_obj.state_registry.parse_member.assert_not_called()

    def test_simple_test_data(self, mock_message_payload, mock_user, fabric_obj):
        message_obj = messages.Message(fabric_obj, mock_message_payload)

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

    def test_update_state_with_no_payload(self, mock_message_payload, fabric_obj):
        initial = messages.Message(fabric_obj, mock_message_payload)
        updated = messages.Message(fabric_obj, mock_message_payload)
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

    def test_update_state_reactions(self, mock_message_payload, fabric_obj):
        message_obj = messages.Message(fabric_obj, mock_message_payload)
        # noinspection PyTypeChecker
        message_obj.update_state({"reactions": [{"id": None, "value": "\N{OK HAND SIGN}"}]})
        fabric_obj.state_registry.parse_reaction.assert_called_once_with(
            {"id": None, "value": "\N{OK HAND SIGN}"}, 12345, 67890
        )

    @pytest.mark.parametrize(
        ("is_webhook", "user_type"),
        [(True, webhooks.WebhookUser), (False, users.User), (False, users.OAuth2User), (False, members.Member),],
    )
    def test_is_webhook(self, mock_message_payload, fabric_obj, is_webhook, user_type):
        message_obj = messages.Message(fabric_obj, mock_message_payload)
        message_obj.author = _helpers.mock_model(user_type)
        assert message_obj.is_webhook is is_webhook

    def test_complex_test_data(self, mock_user, fabric_obj):
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

    def test_guild_if_guild_message(self, mock_message_payload, fabric_obj):
        mock_message_payload["guild_id"] = "91827"
        message_obj = messages.Message(fabric_obj, mock_message_payload)

        guild = mock.MagicMock()
        fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(return_value=guild)

        g = message_obj.guild
        assert g is guild

        fabric_obj.state_registry.get_guild_by_id.assert_called_with(91827)

    def test_guild_if_dm_message(self, mock_message_payload, fabric_obj):
        message_obj = messages.Message(fabric_obj, mock_message_payload)
        assert message_obj.guild is None

        fabric_obj.state_registry.get_guild_by_id.assert_not_called()

    def test_channel_if_guild_message(self, mock_message_payload, fabric_obj):
        mock_message_payload["guild_id"] = "5432"
        mock_message_payload["channel_id"] = "1234"
        guild = _helpers.create_autospec(guilds.Guild)
        guild.channels = {1234: mock.MagicMock(), 1235: mock.MagicMock()}
        message_obj = messages.Message(fabric_obj, mock_message_payload)
        fabric_obj.state_registry.get_channel_by_id = mock.MagicMock(return_value=message_obj.channel)
        guild.channels[1234] = message_obj.channel
        c = message_obj.channel
        assert c is guild.channels[1234]

    def test_channel_if_dm_message(self, mock_message_payload, fabric_obj):
        mock_message_payload["channel_id"] = "1234"
        channel = _helpers.create_autospec(channels.Channel)
        fabric_obj.state_registry.get_mandatory_channel_by_id = mock.MagicMock(return_value=channel)

        obj = messages.Message(fabric_obj, mock_message_payload)

        c = obj.channel
        fabric_obj.state_registry.get_mandatory_channel_by_id.assert_called_with(1234)
        assert c is channel

    def test_repr(self):
        assert repr(
            _helpers.mock_model(
                messages.Message,
                id=42,
                author=_helpers.mock_model(users.User, __repr__=users.User.__repr__),
                type=messages.MessageType.DEFAULT,
                is_tts=True,
                created_at=datetime.datetime.fromtimestamp(69).replace(tzinfo=datetime.timezone.utc),
                edited_at=datetime.datetime.fromtimestamp(101).replace(tzinfo=datetime.timezone.utc),
                __repr__=messages.Message.__repr__,
            )
        )

    @pytest.mark.asyncio
    async def test_delete(self, mock_message_payload, fabric_obj):
        obj = messages.Message(fabric_obj, mock_message_payload)

        await obj.delete()
        fabric_obj.http_adapter.delete_messages.assert_awaited_once_with(obj)


@pytest.mark.model
def test_MessageActivity():
    ma = messages.MessageActivity({"type": 3, "party_id": "999"})

    assert ma.type == messages.MessageActivityType.LISTEN
    assert ma.party_id == 999


@pytest.mark.model
def test_MessageActivity___repr__():
    assert repr(
        _helpers.mock_model(
            messages.MessageActivity,
            type=messages.MessageActivityType.NONE,
            party_id=42,
            __repr__=messages.MessageActivity.__repr__,
        )
    )


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


@pytest.mark.model
def test_MessageApplication___repr__():
    assert repr(
        _helpers.mock_model(
            messages.MessageApplication, id=42, name="foo", __repr__=messages.MessageApplication.__repr__
        )
    )


@pytest.mark.model
def test_MessageCrosspost():
    mcp = messages.MessageCrosspost(
        {"channel_id": "278325129692446722", "guild_id": "278325129692446720", "message_id": "306588351130107906"}
    )

    assert mcp.channel_id == 278325129692446722
    assert mcp.message_id == 306588351130107906
    assert mcp.guild_id == 278325129692446720


@pytest.mark.model
def test_MessageCrosspost___repr__():
    assert repr(
        _helpers.mock_model(
            messages.MessageCrosspost,
            message_id=42,
            guild_id=69,
            channel_id=101,
            __repr__=messages.MessageCrosspost.__repr__,
        )
    )

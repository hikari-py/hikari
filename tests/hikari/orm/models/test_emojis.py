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
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm.state import base_registry
from hikari.orm.models import emojis
from hikari.orm.models import guilds
from tests.hikari import _helpers


@pytest.fixture
def mock_state():
    return mock.MagicMock(spec_set=base_registry.BaseRegistry)


@pytest.fixture
def fabric_obj(mock_state):
    return fabric.Fabric(None, mock_state)


@pytest.fixture
def unicode_emoji_payload():
    return {"name": "\N{OK HAND SIGN}"}


@pytest.fixture
def unknown_emoji_payload():
    return {"name": "asshat123", "id": "100000000001110010"}


@pytest.fixture
def user_payload():
    return {
        "username": "Luigi",
        "discriminator": "0002",
        "id": "96008815106887111",
        "avatar": "5500909a3274e1812beb4e8de6631111",
    }


@pytest.fixture
def guild_emoji_payload(user_payload):
    return {
        "id": "41771983429993937",
        "name": "LUL",
        "roles": ["41771983429993000", "41771983429993111"],
        "user": user_payload,
        "require_colons": True,
        "managed": False,
        "animated": False,
    }


@pytest.mark.model
def test_UnicodeEmoji___init__(unicode_emoji_payload):
    assert emojis.UnicodeEmoji(unicode_emoji_payload).value == "\N{OK HAND SIGN}"
    emojis.UnicodeEmoji(unicode_emoji_payload).__repr__()


@pytest.mark.model
def test_UnicodeEmoji___eq__(unicode_emoji_payload):
    assert emojis.UnicodeEmoji(unicode_emoji_payload) == "\N{OK HAND SIGN}"
    assert emojis.UnicodeEmoji(unicode_emoji_payload).value == emojis.UnicodeEmoji(
        {"name": "\N{OK HAND SIGN}", "id": None}
    )


@pytest.mark.model
def test_UnicodeEmoji___ne__(unicode_emoji_payload):
    assert emojis.UnicodeEmoji(unicode_emoji_payload) != "\N{AUBERGINE}"
    assert emojis.UnicodeEmoji(unicode_emoji_payload).value != emojis.UnicodeEmoji(
        {"name": "\N{AUBERGINE}", "id": None}
    )


@pytest.mark.model
def test_UnicodeEmoji___str__(unicode_emoji_payload):
    assert str(emojis.UnicodeEmoji(unicode_emoji_payload)) == "\N{OK HAND SIGN}"


@pytest.mark.model
def test_UnicodeEmoji_url_name(unicode_emoji_payload):
    assert emojis.UnicodeEmoji(unicode_emoji_payload).url_name == "\N{OK HAND SIGN}"


@pytest.mark.model
def test_UnicodeEmoji_mention(unicode_emoji_payload):
    assert emojis.UnicodeEmoji(unicode_emoji_payload).mention == "\N{OK HAND SIGN}"


@pytest.mark.model
def test_UnicodeEmoji___repr__():
    assert repr(
        _helpers.mock_model(emojis.UnicodeEmoji, value="\N{OK HAND SIGN}", __repr__=emojis.UnicodeEmoji.__repr__)
    )


@pytest.mark.model
def test_UnicodeEmoji___repr__():
    assert repr(_helpers.mock_model(emojis.UnicodeEmoji, value="\N{OK HAND SIGN}"))


@pytest.mark.model
def test_UnknownEmoji___init__(unknown_emoji_payload):
    e = emojis.UnknownEmoji(unknown_emoji_payload)
    assert e.id == 100000000001110010
    assert e.name == "asshat123"
    assert e.url_name == "asshat123:100000000001110010"
    try:
        e.mention
        assert False, "Expected AttributeError."
    except AttributeError:
        pass


@pytest.mark.model
def test_UnknownEmoji___repr__():
    assert repr(_helpers.mock_model(emojis.UnknownEmoji, id=42, name="foo", __repr__=emojis.UnknownEmoji.__repr__))


@pytest.mark.model
def test_GuildEmoji___init__(mock_state, fabric_obj, guild_emoji_payload, user_payload):
    user = mock.MagicMock()
    mock_state.parse_user = mock.MagicMock(return_value=user)
    e = emojis.GuildEmoji(fabric_obj, guild_emoji_payload, 98765)

    assert e.id == 41771983429993937
    assert e.name == "LUL"
    assert e._role_ids == [41771983429993000, 41771983429993111]
    assert e.user is user
    assert e.is_requiring_colons is True
    assert e.is_managed is False
    assert e.is_animated is False
    assert e._guild_id == 98765
    assert e.url_name == "LUL:41771983429993937"
    assert e.mention == "<:LUL:41771983429993937>"
    mock_state.parse_user.assert_called_with(user_payload)


@pytest.mark.model
def test_GuildEmomji___str__(unicode_emoji_payload, fabric_obj):
    assert str(emojis.GuildEmoji(fabric_obj, {"id": "1231", "name": "An_emoji"}, 123)) == "<:An_emoji:1231>"


@pytest.mark.model
def test_GuildEmoji_mention_when_not_animated(mock_state, fabric_obj, guild_emoji_payload):
    mock_state.parse_user = mock.MagicMock()
    guild_emoji_payload["animated"] = True
    e = emojis.GuildEmoji(fabric_obj, guild_emoji_payload, 98765)
    assert e.mention == "<a:LUL:41771983429993937>"


@pytest.mark.model
def test_GuildEmoji___repr__():
    assert repr(
        _helpers.mock_model(emojis.GuildEmoji, id=42, name="foo", is_animated=True, __repr__=emojis.GuildEmoji.__repr__)
    )


@pytest.mark.model
def test_GuildEmoji___repr__():
    assert repr(_helpers.mock_model(emojis.GuildEmoji, id=42, name="foo", is_animated=True))


@pytest.mark.model
def test_emoji_from_dict_with_unicode_emoji(fabric_obj, unicode_emoji_payload):
    assert isinstance(emojis.parse_emoji(fabric_obj, unicode_emoji_payload), emojis.UnicodeEmoji)


@pytest.mark.model
def test_emoji_from_dict_with_unknown_emoji(fabric_obj, unknown_emoji_payload):
    e = emojis.parse_emoji(fabric_obj, unknown_emoji_payload)
    assert isinstance(e, emojis.UnknownEmoji)
    assert not isinstance(e, emojis.GuildEmoji)


@pytest.mark.model
def test_emoji_from_dict_with_guild_emoji_but_no_guild(fabric_obj, guild_emoji_payload):
    e = emojis.parse_emoji(fabric_obj, guild_emoji_payload, None)
    assert isinstance(e, emojis.UnknownEmoji)
    assert not isinstance(e, emojis.GuildEmoji)


@pytest.mark.model
def test_emoji_from_dict_with_guild_emoji_and_passed_guild_id(fabric_obj, guild_emoji_payload):
    e = emojis.parse_emoji(fabric_obj, guild_emoji_payload, 1234)
    assert isinstance(e, emojis.GuildEmoji)


@pytest.mark.model
def test_UnicodeEmoji_is_unicode(unicode_emoji_payload):
    assert emojis.UnicodeEmoji(unicode_emoji_payload).is_unicode


@pytest.mark.model
def test_UnknownEmoji_is_unicode(unknown_emoji_payload):
    assert not emojis.UnknownEmoji(unknown_emoji_payload).is_unicode


@pytest.mark.model
def test_GuildEmoji_is_unicode(fabric_obj, guild_emoji_payload):
    assert not emojis.GuildEmoji(fabric_obj, guild_emoji_payload, 98765).is_unicode


@pytest.mark.model
def test_GuildEmoji_guild_property(fabric_obj, mock_state, guild_emoji_payload):
    guild = mock.MagicMock(spec_state=guilds.Guild)
    guild.id = 1234
    emoji = emojis.GuildEmoji(fabric_obj, guild_emoji_payload, guild.id)
    mock_state.get_guild_by_id = mock.MagicMock(return_value=guild)
    assert emoji.guild is guild
    mock_state.get_guild_by_id.assert_called_once_with(1234)


@pytest.mark.model
def test_UnknownEmoji___hash__(unknown_emoji_payload):
    e = emojis.UnknownEmoji(unknown_emoji_payload)
    assert hash(e) == hash(e.id)


@pytest.mark.model
def test_GuildEmoji___hash__(fabric_obj, guild_emoji_payload):
    e = emojis.GuildEmoji(fabric_obj, guild_emoji_payload, 1234)
    assert hash(e) == hash(e.id)

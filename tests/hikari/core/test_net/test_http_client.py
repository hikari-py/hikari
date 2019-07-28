#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
#
# Big text is from: http://patorjk.com/software/taag/#p=display&f=Big&t=Gateway
# Adding new categories? Keep it consistent, bud.
import io
import json

import asynctest
import pytest

from hikari.core.net import http_client as _http_client
from hikari.core.utils import unspecified

r"""
PyTest Fixtures
  _____    _______        _     ______ _      _                       
 |  __ \  |__   __|      | |   |  ____(_)    | |                      
 | |__) |   _| | ___  ___| |_  | |__   ___  _| |_ _   _ _ __ ___  ___ 
 |  ___/ | | | |/ _ \/ __| __| |  __| | \ \/ / __| | | | '__/ _ \/ __|
 | |   | |_| | |  __/\__ \ |_  | |    | |>  <| |_| |_| | | |  __/\__ \
 |_|    \__, |_|\___||___/\__| |_|    |_/_/\_\\__|\__,_|_|  \___||___/
         __/ |                                                        
        |___/                                                         
"""


class ClientMock(_http_client.HTTPClient):
    """
    Useful for HTTP client calls that need to mock the HTTP connection quickly in a fixture.

    .. code-block::
        @pytest.fixture()
        async def http_client(event_loop):
            from hikari_tests.test_net.test_http import ClientMock
            return ClientMock(token="foobarsecret", loop=event_loop)

                async def test_that_something_does_a_thing(self, http_client):
            http_client.request = asynctest.CoroutineMock(return_value=69)
            assert await http_client.something() == 69

    """

    def __init__(self, *args, **kwargs):
        with asynctest.patch("aiohttp.ClientSession", new=asynctest.MagicMock()):
            super().__init__(*args, **kwargs)

    async def request(self, method, path, params=None, **kwargs):
        pass


@pytest.fixture()
async def http_client(event_loop):
    token = "thisisafaketoken:3"
    return ClientMock(token=token, loop=event_loop)


r"""
Constructor Unit Tests
   _____                _                   _             
  / ____|              | |                 | |            
 | |     ___  _ __  ___| |_ _ __ _   _  ___| |_ ___  _ __ 
 | |    / _ \| '_ \/ __| __| '__| | | |/ __| __/ _ \| '__|
 | |___| (_) | | | \__ \ |_| |  | |_| | (__| || (_) | |   
  \_____\___/|_| |_|___/\__|_|   \__,_|\___|\__\___/|_|   
"""


@pytest.mark.asyncio
class TestConstructor:
    async def test_initialize_http_behaves_as_expected_and_does_not_fail(self, event_loop):
        c = _http_client.HTTPClient(loop=event_loop, token="1a2b3c4d.1a2b3c4d")
        assert c is not None


r"""
Audit Log Unit Tests
                    _ _ _     _                 
     /\            | (_) |   | |                
    /  \  _   _  __| |_| |_  | |     ___   __ _ 
   / /\ \| | | |/ _` | | __| | |    / _ \ / _` |
  / ____ \ |_| | (_| | | |_  | |___| (_) | (_| |
 /_/    \_\__,_|\__,_|_|\__| |______\___/ \__, |
                                           __/ |
                                          |___/ 
"""


@pytest.mark.asyncio
@pytest.mark.auditlog
class TestAuditLog:
    async def test_audit_log_request_layout(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"foo": "bar"})

        result = await http_client.get_guild_audit_log("1234", user_id="5678", action_type=20, limit=18)

        http_client.request.assert_awaited_once_with(
            "get",
            "/guilds/{guild_id}/audit-logs",
            query={"user_id": "5678", "action_type": 20, "limit": 18},
            guild_id="1234",
        )

        assert result == {"foo": "bar"}

    async def test_audit_log_request_default_args(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"foo": "bar"})

        result = await http_client.get_guild_audit_log("1234")

        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/audit-logs", guild_id="1234", query={})

        assert result == {"foo": "bar"}


r"""
Channel Unit Tests
   _____ _                            _ 
  / ____| |                          | |
 | |    | |__   __ _ _ __  _ __   ___| |
 | |    | '_ \ / _` | '_ \| '_ \ / _ \ |
 | |____| | | | (_| | | | | | | |  __/ |
  \_____|_| |_|\__,_|_| |_|_| |_|\___|_|

"""


@pytest.mark.asyncio
@pytest.mark.channel
class TestChannel:
    async def test_add_pinned_channel_message(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.add_pinned_channel_message("12345", "54321")
        http_client.request.assert_awaited_once_with(
            "put", "/channels/{channel_id}/pins/{message_id}", channel_id="12345", message_id="54321"
        )

    async def test_bulk_delete_messages(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.bulk_delete_messages("69", ["192", "168", "0", "1"])
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/messages/bulk-delete",
            channel_id="69",
            json={"messages": ["192", "168", "0", "1"]},
        )

    async def test_create_channel_invite_without_optional_args_has_empty_payload(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_channel_invite("696969")
        http_client.request.assert_awaited_once_with(
            "post", "/channels/{channel_id}/invites", channel_id="696969", json={}, reason=unspecified.UNSPECIFIED
        )

    async def test_create_channel_invite_with_max_age(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_channel_invite("696969", max_age=10)
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/invites",
            channel_id="696969",
            json={"max_age": 10},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_channel_invite_with_max_uses(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_channel_invite("696969", max_uses=10)
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/invites",
            channel_id="696969",
            json={"max_uses": 10},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_channel_invite_with_temporary(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_channel_invite("696969", temporary=True)
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/invites",
            channel_id="696969",
            json={"temporary": True},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_channel_invite_with_unique(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_channel_invite("696969", unique=True)
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/invites",
            channel_id="696969",
            json={"unique": True},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_channel_invite_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_channel_invite("696969", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_create_message_performs_a_post_request(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456")

        args, kwargs = http_client.request.await_args
        assert "post" in args

    async def test_create_message_sends_to_expected_endpoint(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456")

        args, kwargs = http_client.request.await_args
        assert "/channels/{channel_id}/messages" in args
        assert kwargs["channel_id"] == "123456"

    async def test_create_message_tts_flag_unspecified_will_be_false(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456")

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": False}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_tts_flag_false_will_be_false(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", tts=False)

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": False}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_tts_flag_true_will_be_true(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", tts=True)

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": True}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_specifying_content_allows_content_to_be_specified(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", content="ayy")

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": False, "content": "ayy"}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_specifying_nonce_allows_nonce_to_be_specified(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", nonce="91827")

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": False, "nonce": "91827"}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_specifying_embed_allows_embed_to_be_specified(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", embed={"foo": "bar"})

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": False, "embed": {"foo": "bar"}}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_specifying_all_payload_json_fields(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", embed={"foo": "bar"}, nonce="69", content="ayy lmao", tts=True)

        args, kwargs = http_client.request.await_args
        form = kwargs["data"]
        field_dict, headers, payload = form._fields[0]
        assert json.loads(payload) == {"tts": True, "embed": {"foo": "bar"}, "nonce": "69", "content": "ayy lmao"}
        assert headers == {"Content-Type": "application/json"}

    async def test_create_message_passing_bytes_as_file_converts_it_correctly_to_BytesIO(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", files=[("foo.png", b"1a2b3c")])
        args, kwargs = http_client.request.await_args
        assert len(kwargs["re_seekable_resources"]) == 1
        form = kwargs["data"]
        fields = form._fields
        field_dict, headers, payload = fields[1]
        assert "foo.png" == field_dict["filename"]
        assert "file0" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == b"1a2b3c"

    async def test_create_message_passing_bytearray_as_file_converts_it_correctly_to_BytesIO(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message("123456", files=[("foo.png", bytearray((0x9, 0x18, 0x27)))])
        args, kwargs = http_client.request.await_args
        assert len(kwargs["re_seekable_resources"]) == 1
        form = kwargs["data"]
        fields = form._fields
        field_dict, headers, payload = fields[1]
        assert "foo.png" == field_dict["filename"]
        assert "file0" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == b"\x09\x18\x27"

    async def test_create_message_passing_memoryview_as_file_converts_it_correctly_to_BytesIO(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        obj = b"Hello, World!"
        view = memoryview(obj)

        await http_client.create_message("123456", files=[("foo.png", view)])
        args, kwargs = http_client.request.await_args
        assert len(kwargs["re_seekable_resources"]) == 1
        form = kwargs["data"]
        fields = form._fields
        field_dict, headers, payload = fields[1]
        assert "foo.png" == field_dict["filename"]
        assert "file0" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == b"Hello, World!"

    async def test_create_message_passing_str_as_file_converts_it_correctly_to_StringIO(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        obj = "Hello, World!"

        await http_client.create_message("123456", files=[("foo.txt", obj)])
        args, kwargs = http_client.request.await_args
        assert len(kwargs["re_seekable_resources"]) == 1
        form = kwargs["data"]
        fields = form._fields
        field_dict, headers, payload = fields[1]
        assert "foo.txt" == field_dict["filename"]
        assert "file0" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == "Hello, World!"

    async def test_create_message_passing_io_as_file_converts_it_correctly_to_StringIO(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        file = io.StringIO("blah")

        await http_client.create_message("123456", files=[("foo.txt", file)])
        args, kwargs = http_client.request.await_args
        assert len(kwargs["re_seekable_resources"]) == 1
        form = kwargs["data"]
        fields = form._fields
        field_dict, headers, payload = fields[1]
        assert "foo.txt" == field_dict["filename"]
        assert "file0" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == "blah"

    async def test_create_message_passing_several_files_adds_several_files(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

        await http_client.create_message(
            "123456", files=[("foo.png", b"1a2b3c"), ("bar.png", b""), ("baz.png", b"blep")]
        )
        args, kwargs = http_client.request.await_args
        assert len(kwargs["re_seekable_resources"]) == 3
        form = kwargs["data"]
        fields = form._fields
        assert len(fields[1:]) == 3

        field_dict, headers, payload = fields[1]
        assert "foo.png" == field_dict["filename"]
        assert "file0" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == b"1a2b3c"

        field_dict, headers, payload = fields[2]
        assert "bar.png" == field_dict["filename"]
        assert "file1" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == b""

        field_dict, headers, payload = fields[3]
        assert "baz.png" == field_dict["filename"]
        assert "file2" == field_dict["name"]
        assert headers == {"Content-Type": "application/octet-stream"}
        assert isinstance(payload, io.IOBase)
        assert payload in kwargs["re_seekable_resources"]
        payload.seek(0)
        assert payload.readline() == b"blep"

    async def test_create_reaction(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_reaction("696969", "12", "\N{OK HAND SIGN}")
        http_client.request.assert_awaited_once_with(
            "put",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id="696969",
            message_id="12",
            emoji="\N{OK HAND SIGN}",
        )

    async def test_delete_all_reactions(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_all_reactions("696969", "12")
        http_client.request.assert_awaited_once_with(
            "delete", "/channels/{channel_id}/messages/{message_id}/reactions", channel_id="696969", message_id="12"
        )

    async def test_delete_channel_permission(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_channel_permission("696969", "123456")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id="696969",
            overwrite_id="123456",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_delete_channel_permission_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_channel_permission("696969", "123456", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_delete_close_channel(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_close_channel("12345")
        http_client.request.assert_awaited_once_with(
            "delete", "/channels/{channel_id}", channel_id="12345", reason=unspecified.UNSPECIFIED
        )

    async def test_delete_close_channel_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_close_channel("696969", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_delete_message(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_message("123456", "420420420")
        http_client.request.assert_awaited_once_with(
            "delete", "/channels/{channel_id}/messages/{message_id}", channel_id="123456", message_id="420420420"
        )

    async def test_delete_own_reaction(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_own_reaction("696969", "12", "\N{OK HAND SIGN}")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id="696969",
            message_id="12",
            emoji="\N{OK HAND SIGN}",
        )

    async def test_delete_pinned_channel_message(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_pinned_channel_message("12345", "54321")
        http_client.request.assert_awaited_once_with(
            "delete", "/channels/{channel_id}/pins/{message_id}", channel_id="12345", message_id="54321"
        )

    async def test_delete_user_reaction(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_user_reaction("696969", "12", "\N{OK HAND SIGN}", "101")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}",
            channel_id="696969",
            message_id="12",
            emoji="\N{OK HAND SIGN}",
            user_id="101",
        )

    async def test_edit_channel_permissions(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.edit_channel_permissions("69", "420", allow=192, deny=168, type_="member")
        http_client.request.assert_awaited_once_with(
            "put",
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id="69",
            overwrite_id="420",
            json={"allow": 192, "deny": 168, "type": "member"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_edit_channel_permissions_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.edit_channel_permissions(
            "696969", "123456", allow=123, deny=456, type_="me", reason="because i can"
        )
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_edit_message_no_changes(self, http_client):
        # not sure if this is even valid, TODO: verify this
        http_client.request = asynctest.CoroutineMock()
        await http_client.edit_message("123456", "6789012")
        http_client.request.assert_awaited_once_with(
            "patch", "/channels/{channel_id}/messages/{message_id}", channel_id="123456", message_id="6789012", json={}
        )

    async def test_edit_message_content(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.edit_message("123456", "6789012", content="ayy lmao im a duck")
        http_client.request.assert_awaited_once_with(
            "patch",
            "/channels/{channel_id}/messages/{message_id}",
            channel_id="123456",
            message_id="6789012",
            json={"content": "ayy lmao im a duck"},
        )

    async def test_edit_message_embed(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.edit_message("123456", "6789012", embed={"title": "ayy lmao im a duck"})
        http_client.request.assert_awaited_once_with(
            "patch",
            "/channels/{channel_id}/messages/{message_id}",
            channel_id="123456",
            message_id="6789012",
            json={"embed": {"title": "ayy lmao im a duck"}},
        )

    async def test_edit_message_embed_and_content(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.edit_message("123456", "6789012", embed={"title": "ayy lmao im a duck"}, content="quack")
        http_client.request.assert_awaited_once_with(
            "patch",
            "/channels/{channel_id}/messages/{message_id}",
            channel_id="123456",
            message_id="6789012",
            json={"embed": {"title": "ayy lmao im a duck"}, "content": "quack"},
        )

    async def test_edit_message_return_value(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"...": "..."})
        result = await http_client.edit_message(
            "123456", "6789012", embed={"title": "ayy lmao im a duck"}, content="quack"
        )
        http_client.request.assert_awaited_once_with(
            "patch",
            "/channels/{channel_id}/messages/{message_id}",
            channel_id="123456",
            message_id="6789012",
            json={"embed": {"title": "ayy lmao im a duck"}, "content": "quack"},
        )
        assert result == {"...": "..."}

    async def test_get_channel(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"id": "696969", "name": "bobs and v"})
        channel = await http_client.get_channel("696969")
        http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}", channel_id="696969")
        assert channel == {"id": "696969", "name": "bobs and v"}

    async def test_get_channel_invites(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"...": "..."})
        result = await http_client.get_channel_invites("123456")
        http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}/invites", channel_id="123456")
        assert result == {"...": "..."}

    async def test_get_channel_message(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_message("696969", "12")
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages/{message_id}", channel_id="696969", message_id="12"
        )

    async def test_get_channel_messages_no_kwargs(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969")
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={}
        )

    async def test_get_channel_messages_with_limit(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", limit=12)
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"limit": 12}
        )

    async def test_get_channel_messages_with_before(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", before="12")
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"before": "12"}
        )

    async def test_get_channel_messages_with_after(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", after="12")
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"after": "12"}
        )

    async def test_get_channel_messages_with_around(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", around="12")
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"around": "12"}
        )

    async def test_get_channel_messages_with_before_and_limit(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", before="12", limit=12)
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"before": "12", "limit": 12}
        )

    async def test_get_channel_messages_with_after_and_limit(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", after="12", limit=12)
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"after": "12", "limit": 12}
        )

    async def test_get_channel_messages_with_around_and_limit(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_messages("696969", around="12", limit=12)
        http_client.request.assert_awaited_once_with(
            "get", "/channels/{channel_id}/messages", channel_id="696969", json={"around": "12", "limit": 12}
        )

    async def test_get_pinned_messages(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_pinned_messages("12345")
        http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}/pins", channel_id="12345")

    async def test_get_reactions_no_kwargs(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_reactions("12345", "54321", "99887766")
        http_client.request.assert_awaited_once_with(
            "get",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id="12345",
            message_id="54321",
            emoji="99887766",
            json={},
        )

    async def test_get_reactions_before(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_reactions("12345", "54321", "99887766", before="707")
        http_client.request.assert_awaited_once_with(
            "get",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id="12345",
            message_id="54321",
            emoji="99887766",
            json={"before": "707"},
        )

    async def test_get_reactions_after(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_reactions("12345", "54321", "99887766", after="707")
        http_client.request.assert_awaited_once_with(
            "get",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id="12345",
            message_id="54321",
            emoji="99887766",
            json={"after": "707"},
        )

    async def test_get_reactions_limit(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_reactions("12345", "54321", "99887766", limit=10)
        http_client.request.assert_awaited_once_with(
            "get",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id="12345",
            message_id="54321",
            emoji="99887766",
            json={"limit": 10},
        )

    async def test_get_reactions_limit_and_before(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_reactions("12345", "54321", "99887766", limit=10, before="707")
        http_client.request.assert_awaited_once_with(
            "get",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id="12345",
            message_id="54321",
            emoji="99887766",
            json={"limit": 10, "before": "707"},
        )

    async def test_get_reactions_limit_and_after(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_reactions("12345", "54321", "99887766", limit=10, after="707")
        http_client.request.assert_awaited_once_with(
            "get",
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id="12345",
            message_id="54321",
            emoji="99887766",
            json={"limit": 10, "after": "707"},
        )

    async def test_modify_channel_no_kwargs(self, http_client):
        # Not sure if this is even valid TODO: verify
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_channel("12345")
        http_client.request.assert_awaited_once_with(
            "patch", "/channels/{channel_id}", channel_id="12345", json={}, reason=unspecified.UNSPECIFIED
        )

    @pytest.mark.parametrize(
        ["name", "value"],
        [
            ("position", 10),
            ("topic", "eating donkey"),
            ("nsfw", True),
            ("rate_limit_per_user", 420),
            ("bitrate", 69_000),
            ("user_limit", 69),
            ("parent_id", "999999"),
            (
                "permission_overwrites",
                [{"id": "919191", "allow": 0, "deny": 180}, {"id": "191919", "allow": 10, "deny": 19}],
            ),
        ],
    )
    async def test_modify_channel_with_one_kwarg(self, http_client, name, value):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_channel("12345", **{name: value})
        http_client.request.assert_awaited_once_with(
            "patch", "/channels/{channel_id}", channel_id="12345", json={name: value}, reason=unspecified.UNSPECIFIED
        )

    async def test_modify_channel_with_many_kwargs(self, http_client):
        test_data_kwargs = [
            ("position", 10),
            ("topic", "eating donkey"),
            ("nsfw", True),
            ("rate_limit_per_user", 420),
            ("bitrate", 69_000),
            ("user_limit", 69),
            (
                "permission_overwrites",
                [{"id": "919191", "allow": 0, "deny": 180}, {"id": "191919", "allow": 10, "deny": 19}],
            ),
            ("parent_id", "999999"),
        ]

        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_channel("12345", **{name: value for name, value in test_data_kwargs})
        http_client.request.assert_awaited_once_with(
            "patch",
            "/channels/{channel_id}",
            channel_id="12345",
            json={name: value for name, value in test_data_kwargs},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_channel_return_value(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"...": "..."})
        result = await http_client.modify_channel("12345")
        assert result == {"...": "..."}

    async def test_modify_channel_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_channel("696969", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_trigger_typing_indicator(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.trigger_typing_indicator("12345")
        http_client.request.assert_awaited_once_with("post", "/channels/{channel_id}/typing", channel_id="12345")


r"""
Emoji Unit Tests
  ______                 _ _ 
 |  ____|               (_|_)
 | |__   _ __ ___   ___  _ _ 
 |  __| | '_ ` _ \ / _ \| | |
 | |____| | | | | | (_) | | |
 |______|_| |_| |_|\___/| |_|
                       _/ |  
                      |__/   
"""


@pytest.mark.asyncio
@pytest.mark.emoji
class TestEmoji:
    async def test_create_guild_emoji(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_emoji("424242", "asdf", b"", [])
        http_client.request.assert_awaited_once_with(
            "post",
            "/guilds/{guild_id}/emojis",
            guild_id="424242",
            json={"name": "asdf", "image": b"", "roles": []},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_guild_emoji_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_emoji("696969", "123456", b"", [], reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_delete_guild_emoji(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild_emoji("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/guilds/{guild_id}/emojis/{emoji_id}",
            guild_id="424242",
            emoji_id="696969",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_delete_guild_emoji_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild_emoji("696969", "123456", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_get_guild_emoji(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_emoji("424242", "404101")
        http_client.request.assert_awaited_once_with(
            "get", "/guilds/{guild_id}/emojis/{emoji_id}", guild_id="424242", emoji_id="404101"
        )

    async def test_list_guild_emojis(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.list_guild_emojis("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/emojis", guild_id="424242")

    async def test_modify_guild_emoji(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_emoji("424242", "696969", "asdf", [])
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/emojis/{emoji_id}",
            guild_id="424242",
            emoji_id="696969",
            json={"name": "asdf", "roles": []},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_emoji_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_emoji("696969", "123456", "asdf", [], reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"


r"""
Gateway Endpoint Unit Tests
   _____       _                           
  / ____|     | |                          
 | |  __  __ _| |_ _____      ____ _ _   _ 
 | | |_ |/ _` | __/ _ \ \ /\ / / _` | | | |
 | |__| | (_| | ||  __/\ V  V / (_| | |_| |
  \_____|\__,_|\__\___| \_/\_/ \__,_|\__, |
                                      __/ |
                                     |___/ 
"""


@pytest.mark.asyncio
@pytest.mark.gateway
class TestGateway:
    async def test_get_gateway(self, http_client):
        http_client.request = asynctest.CoroutineMock(return_value={"url": "http://somehost.com"})
        url = await http_client.get_gateway()
        http_client.request.assert_awaited_once_with("get", "/gateway")
        assert url == "http://somehost.com"

    async def test_get_gateway_bot(self, http_client):
        payload = {
            "url": "http://somehost.com",
            "shards": 123,
            "session_start_limit": {"total": 1000, "remaining": 999, "reset_after": 14400000},
        }
        http_client.request = asynctest.CoroutineMock(return_value=payload)
        obj = await http_client.get_gateway_bot()
        http_client.request.assert_awaited_once_with("get", "/gateway/bot")
        assert obj == payload


r"""
Guild Unit Tests
   _____       _ _     _ 
  / ____|     (_) |   | |
 | |  __ _   _ _| | __| |
 | | |_ | | | | | |/ _` |
 | |__| | |_| | | | (_| |
  \_____|\__,_|_|_|\__,_|
                                                  
"""


@pytest.mark.asyncio
@pytest.mark.guild
class TestGuild:
    async def test_add_guild_member_role(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.add_guild_member_role("424242", "696969", "404101")
        http_client.request.assert_awaited_once_with(
            "put",
            "/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            guild_id="424242",
            user_id="696969",
            role_id="404101",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_add_guild_member_role_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.add_guild_member_role("424242", "696969", "404101", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_begin_guild_prune(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.begin_guild_prune("424242", 10, False)
        http_client.request.assert_awaited_once_with(
            "post",
            "/guilds/{guild_id}/prune",
            guild_id="424242",
            query={"days": 10, "compute_prune_count": False},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_begin_guild_prune_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.begin_guild_prune("424242", 10, False, reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_create_guild(self, http_client):
        test_all_args = {
            "name": "asdf",
            "region": "eu-west",
            "icon": b"",
            "verification_level": 1,
            "default_message_notifications": 1,
            "explicit_content_filter": 1,
            "roles": [{}, {"id": "424242", "color": 404, "hoist": True}],
            "channels": [
                {
                    "name": "general",
                    "type": 0,
                    "permission_overwrites": [{"id": "424242", "type": "role", "allow": 101}],
                }
            ],
        }

        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild(**test_all_args)
        http_client.request.assert_awaited_once_with("post", "/guilds", json=test_all_args)

    async def test_create_guild_ban_no_message_deletion(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_ban("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "put", "/guilds/{guild_id}/bans/{user_id}", guild_id="424242", user_id="696969", query={}
        )

    async def test_create_guild_ban_with_message_deletion(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_ban("424242", "696969", delete_message_days=10)
        http_client.request.assert_awaited_once_with(
            "put",
            "/guilds/{guild_id}/bans/{user_id}",
            guild_id="424242",
            user_id="696969",
            query={"delete_message_days": 10},
        )

    async def test_create_guild_ban_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_ban("424242", "696969", reason="baz")
        http_client.request.assert_awaited_once_with(
            "put", "/guilds/{guild_id}/bans/{user_id}", guild_id="424242", user_id="696969", query={"reason": "baz"}
        )
        # args, kwargs = http_client.request.call_args
        # assert kwargs["reason"] == "baz"

    async def test_create_guild_channel_no_kwars(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_channel("424242", "asdf")
        http_client.request.assert_awaited_once_with(
            "post",
            "/guilds/{guild_id}/channels",
            guild_id="424242",
            json={"name": "asdf"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_guild_channel_all_kwars(self, http_client):
        test_args = {
            "topic": "I like trains.",
            "bitrate": 64000,
            "user_limit": 10,
            "rate_limit_per_user": 100,
            "position": 2,
            "permission_overwrites": [{"id": "404101", "type": "role", "allow": 666, "deny": 911}],
            "parent_id": 404,
            "nsfw": True,
        }

        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_channel("424242", "asdf", type_=1, **test_args)
        http_client.request.assert_awaited_once_with(
            "post",
            "/guilds/{guild_id}/channels",
            guild_id="424242",
            json=dict(name="asdf", type=1, **test_args),
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_guild_channel_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_channel("424242", "asdf", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_create_guild_integration(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_integration("424242", "twitch", "696969")
        http_client.request.assert_awaited_once_with(
            "post",
            "/guilds/{guild_id}/integrations",
            guild_id="424242",
            json={"type": "twitch", "id": "696969"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_guild_integration_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_integration("424242", "twitch", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_create_guild_role_no_kwargs(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_role("424242")
        http_client.request.assert_awaited_once_with(
            "post", "/guilds/{guild_id}/roles", guild_id="424242", json={}, reason=unspecified.UNSPECIFIED
        )

    async def test_create_guild_role_many_kwargs(self, http_client):
        test_many_args = {"name": "asdf", "permissions": 404, "hoist": True}

        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_role("424242", **test_many_args)
        http_client.request.assert_awaited_once_with(
            "post", "/guilds/{guild_id}/roles", guild_id="424242", json=test_many_args, reason=unspecified.UNSPECIFIED
        )

    async def test_create_guild_role_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_guild_role("424242", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_delete_guild(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild("424242")
        http_client.request.assert_awaited_once_with("delete", "/guilds/{guild_id}", guild_id="424242")

    async def test_delete_guild_integration(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild_integration("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/guilds/{guild_id}/integrations/{integration_id}",
            guild_id="424242",
            integration_id="696969",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_delete_guild_integration_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild_integration("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_delete_guild_role(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild_role("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/guilds/{guild_id}/roles/{role_id}",
            guild_id="424242",
            role_id="696969",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_delete_guild_role_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_guild_role("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_get_guild(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}", guild_id="424242")

    async def test_get_guild_ban(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_ban("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "get", "/guilds/{guild_id}/bans/{user_id}", guild_id="424242", user_id="696969"
        )

    async def test_get_guild_bans(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_bans("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/bans", guild_id="424242")

    async def test_get_guild_channels(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_channels("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/channels", guild_id="424242")

    async def test_get_guild_embed(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_embed("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/embed", guild_id="424242")

    async def test_get_guild_integrations(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_integrations("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/integrations", guild_id="424242")

    async def test_get_guild_invites(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_invites("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/invites", guild_id="424242")

    async def test_get_guild_member(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_member("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "get", "/guilds/{guild_id}/members/{user_id}", guild_id="424242", user_id="696969"
        )

    async def test_get_guild_prune_count(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_prune_count("424242", days=10)
        http_client.request.assert_awaited_once_with(
            "get", "/guilds/{guild_id}/prune", guild_id="424242", query={"days": 10}
        )

    async def test_get_guild_roles(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_roles("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/roles", guild_id="424242")

    async def test_get_guild_vanity_url(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_vanity_url("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/vanity-url", guild_id="424242")

    async def test_get_guild_voice_regions(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_voice_regions("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/regions", guild_id="424242")

    async def test_get_guild_widget_image(self, http_client):
        http_client.base_uri = "https://potato.com/api/v12"
        assert (
            http_client.get_guild_widget_image("1234", style="banner3")
            == "https://potato.com/api/v12/guilds/1234/widget.png?style=banner3"
        )

    async def test_list_guild_members_no_args(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.list_guild_members("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/members", guild_id="424242", json={})

    async def test_list_guild_members_with_args(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.list_guild_members("424242", limit=10, after="696969")
        http_client.request.assert_awaited_once_with(
            "get", "/guilds/{guild_id}/members", guild_id="424242", json={"limit": 10, "after": "696969"}
        )

    async def test_modify_current_user_nick_to_string(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_current_user_nick("424242", "asdf")
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/members/@me/nick",
            guild_id="424242",
            json={"nick": "asdf"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_current_user_nick_to_none(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_current_user_nick("424242", None)
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/members/@me/nick",
            guild_id="424242",
            json={"nick": None},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_current_user_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_current_user_nick("424242", "adsf", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_no_kwargs(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild("424242")
        http_client.request.assert_awaited_once_with(
            "patch", "/guilds/{guild_id}", guild_id="424242", json={}, reason=unspecified.UNSPECIFIED
        )

    async def test_modify_guild_all_kwargs(self, http_client):
        test_all_kwargs = {
            "name": "asdf",
            "region": "eu-west",
            "verification_level": 1,
            "default_message_notifications": 1,
            "explicit_content_filter": 1,
            "afk_channel_id": "404101",
            "afk_timeout": 10,
            "icon": b"",
            "owner_id": "696969",
            "splash": b"",
            "system_channel_id": "112",
        }

        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild("424242", **test_all_kwargs)
        http_client.request.assert_awaited_once_with(
            "patch", "/guilds/{guild_id}", guild_id="424242", json=test_all_kwargs, reason=unspecified.UNSPECIFIED
        )

    async def test_modify_guild_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild("424242", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_channel_positions(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_channel_positions("424242", ("696969", 1), ("404101", 2))
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/channels",
            guild_id="424242",
            json=[{"id": "696969", "position": 1}, {"id": "404101", "position": 2}],
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_channel_positions_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_channel_positions("424242", ("696969", 1), ("404101", 2), reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_integration(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_integration(
            "424242", "696969", expire_behaviour=1, expire_grace_period=10, enable_emoticons=True
        )
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/integrations/{integration_id}",
            guild_id="424242",
            integration_id="696969",
            json={"expire_behaviour": 1, "expire_grace_period": 10, "enable_emoticons": True},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_integration_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_integration(
            "424242", "696969", expire_behaviour=1, expire_grace_period=10, enable_emoticons=True, reason="baz"
        )
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_member_no_kwargs(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_member("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/members/{user_id}",
            guild_id="424242",
            user_id="696969",
            json={},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_member_all_kwargs(self, http_client):
        test_args = {"nick": "asdf", "roles": ["404101"], "mute": True, "deaf": True, "channel_id": None}

        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_member("424242", "696969", **test_args)
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/members/{user_id}",
            guild_id="424242",
            user_id="696969",
            json=test_args,
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_member_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_member("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_role_no_kwargs(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_role("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/roles/{role_id}",
            guild_id="424242",
            role_id="696969",
            json={},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_role_all_kwargs(self, http_client):
        test_args = {"name": "asdf", "permissions": 404, "color": 101, "hoist": True, "mentionable": False}

        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_role("424242", "696969", **test_args)
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/roles/{role_id}",
            guild_id="424242",
            role_id="696969",
            json=test_args,
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_role_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_role("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_role_positions(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_role_positions("424242", ("696969", 1), ("404101", 2))
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/roles",
            guild_id="424242",
            json=[{"id": "696969", "position": 1}, {"id": "404101", "position": 2}],
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_role_positions_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_role_positions("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_modify_guild_embed_empty_embed_provided(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_embed("424242", {})
        http_client.request.assert_awaited_once_with(
            "patch", "/guilds/{guild_id}/embed", guild_id="424242", json={}, reason=unspecified.UNSPECIFIED
        )

    async def test_modify_guild_embed_all_args(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_embed("424242", {"enabled": True, "channel_id": "696969"})
        http_client.request.assert_awaited_once_with(
            "patch",
            "/guilds/{guild_id}/embed",
            guild_id="424242",
            json={"enabled": True, "channel_id": "696969"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_guild_embed_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_guild_embed("424242", {"enabled": True, "channel_id": "696969"}, reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_remove_guild_ban(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.remove_guild_ban("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/guilds/{guild_id}/bans/{user_id}",
            guild_id="424242",
            user_id="696969",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_remove_guild_ban_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.remove_guild_ban("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_remove_guild_member(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.remove_guild_member("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/guilds/{guild_id}/members/{user_id}",
            guild_id="424242",
            user_id="696969",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_remove_guild_member_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.remove_guild_member("424242", "696969", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_remove_guild_member_role(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.remove_guild_member_role("424242", "696969", "404101")
        http_client.request.assert_awaited_once_with(
            "delete",
            "/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            guild_id="424242",
            user_id="696969",
            role_id="404101",
            reason=unspecified.UNSPECIFIED,
        )

    async def test_remove_guild_member_role_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.remove_guild_member_role("424242", "696969", "404101", reason="baz")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "baz"

    async def test_sync_guild_integration(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.sync_guild_integration("424242", "696969")
        http_client.request.assert_awaited_once_with(
            "post", "/guilds/{guild_id}/integrations/{integration_id}/sync", guild_id="424242", integration_id="696969"
        )


r"""
Invite Unit Tests
  _____            _ _       
 |_   _|          (_) |      
   | |  _ ____   ___| |_ ___ 
   | | | '_ \ \ / / | __/ _ \
  _| |_| | | \ V /| | ||  __/
 |_____|_| |_|\_/ |_|\__\___|

"""


@pytest.mark.asyncio
@pytest.mark.invite
class TestInvite:
    async def test_delete_invite(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_invite("424242")
        http_client.request.assert_awaited_once_with(
            "delete", "/invites/{invite_code}", invite_code="424242", reason=unspecified.UNSPECIFIED
        )

    async def test_delete_invite_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_invite("696969", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_get_invite_without_counts(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_invite("424242")
        http_client.request.assert_awaited_once_with("get", "/invites/{invite_code}", invite_code="424242", query={})

    async def test_get_invite_with_counts(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_invite("424242", with_counts=True)
        http_client.request.assert_awaited_once_with(
            "get", "/invites/{invite_code}", invite_code="424242", query={"with_counts": True}
        )


r"""
Oauth2 Unit Tests
   ____               _   _     ___  
  / __ \   /\        | | | |   |__ \ 
 | |  | | /  \  _   _| |_| |__    ) |
 | |  | |/ /\ \| | | | __| '_ \  / / 
 | |__| / ____ \ |_| | |_| | | |/ /_ 
  \____/_/    \_\__,_|\__|_| |_|____|
  
"""


@pytest.mark.asyncio
@pytest.mark.oauth2
class TestOauth2:
    async def test_get_current_application_info(self, http_client):
        resp = {
            "id": "9182736",
            "name": "hikari",
            "icon": "1a2b3c4d",
            "description": "a sane discord api",
            "rpc_origins": ["http://foo", "http://bar", "http://baz"],
            "bot_public": True,
            "bot_require_code_grant": False,
            "owner": {"username": "nekoka.tt", "discriminator": "1234", "id": "123456789", "avatar": None},
        }
        http_client.request = asynctest.CoroutineMock(return_value=resp)

        info = await http_client.get_current_application_info()
        assert info == resp


r"""
User Unit Tests
  _    _               
 | |  | |              
 | |  | |___  ___ _ __ 
 | |  | / __|/ _ \ '__|
 | |__| \__ \  __/ |   
  \____/|___/\___|_|   
                       
"""


@pytest.mark.asyncio
@pytest.mark.user
class TestUser:
    async def test_create_dm(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_dm("424242")
        http_client.request.assert_awaited_once_with("post", "/users/@me/channels", json={"recipient_id": "424242"})

    async def test_get_current_user(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_current_user()
        http_client.request.assert_awaited_once_with("get", "/users/@me")

    async def test_get_current_user_guilds_no_args(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_current_user_guilds()
        http_client.request.assert_awaited_once_with("get", "/users/@me/guilds", query={})

    async def test_get_current_user_guilds_with_before(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_current_user_guilds(before="424242")
        http_client.request.assert_awaited_once_with("get", "/users/@me/guilds", query={"before": "424242"})

    async def test_get_current_user_guilds_with_after(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_current_user_guilds(after="696969")
        http_client.request.assert_awaited_once_with("get", "/users/@me/guilds", query={"after": "696969"})

    async def test_get_current_user_guilds_with_limit(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_current_user_guilds(limit=10)
        http_client.request.assert_awaited_once_with("get", "/users/@me/guilds", query={"limit": 10})

    async def test_get_user(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_user("424242")
        http_client.request.assert_awaited_once_with("get", "/users/{user_id}", user_id="424242")

    async def test_leave_guild(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.leave_guild("424242")
        http_client.request.assert_awaited_once_with("delete", "/users/@me/guilds/{guild_id}", guild_id="424242")

    async def test_modify_current_user_no_args(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_current_user()
        http_client.request.assert_awaited_once_with("patch", "/users/@me", json={})

    async def test_modify_current_user_all_args(self, http_client):
        test_args = {"username": "asdf", "avatar": b""}
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_current_user(**test_args)
        http_client.request.assert_awaited_once_with("patch", "/users/@me", json=test_args)


r"""
Voice Endpoint Unit Tests
 __      __   _          
 \ \    / /  (_)         
  \ \  / /__  _  ___ ___ 
   \ \/ / _ \| |/ __/ _ \
    \  / (_) | | (_|  __/
     \/ \___/|_|\___\___|
                         
"""


@pytest.mark.asyncio
@pytest.mark.voice
class TestVoice:
    async def test_list_guild_regions(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.list_voice_regions()
        http_client.request.assert_awaited_once_with("get", "/voice/regions")


r"""
Webhook Unit Tests
 __          __  _     _                 _    
 \ \        / / | |   | |               | |   
  \ \  /\  / /__| |__ | |__   ___   ___ | | __
   \ \/  \/ / _ \ '_ \| '_ \ / _ \ / _ \| |/ /
    \  /\  /  __/ |_) | | | | (_) | (_) |   < 
     \/  \/ \___|_.__/|_| |_|\___/ \___/|_|\_\

"""


@pytest.mark.asyncio
@pytest.mark.webhook
class TestWebhook:
    async def test_create_webhook_without_avatar(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_webhook("424242", "asdf")
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/webhooks",
            channel_id="424242",
            json={"name": "asdf"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_webhook_with_avatar(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_webhook("424242", "asdf", avatar=b"")
        http_client.request.assert_awaited_once_with(
            "post",
            "/channels/{channel_id}/webhooks",
            channel_id="424242",
            json={"name": "asdf", "avatar": b""},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_create_webhook_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.create_webhook("696969", "123456", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_delete_webhook(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_webhook("424242")
        http_client.request.assert_awaited_once_with(
            "delete", "/webhooks/{webhook_id}", webhook_id="424242", reason=unspecified.UNSPECIFIED
        )

    async def test_delete_webhook_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.delete_webhook("696969", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

    async def test_get_channel_webhooks(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_channel_webhooks("424242")
        http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}/webhooks", channel_id="424242")

    async def test_get_guild_webhooks(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_guild_webhooks("424242")
        http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/webhooks", guild_id="424242")

    async def test_get_webhook(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.get_webhook("424242")
        http_client.request.assert_awaited_once_with("get", "/webhooks/{webhook_id}", webhook_id="424242")

    async def test_modify_webhook(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_webhook("424242", "asdf", b"", "696969")
        http_client.request.assert_awaited_once_with(
            "patch",
            "/webhooks/{webhook_id}",
            webhook_id="424242",
            json={"name": "asdf", "avatar": b"", "channel_id": "696969"},
            reason=unspecified.UNSPECIFIED,
        )

    async def test_modify_webhook_with_optional_reason(self, http_client):
        http_client.request = asynctest.CoroutineMock()
        await http_client.modify_webhook("696969", "123456", b"", "1234", reason="because i can")
        args, kwargs = http_client.request.call_args
        assert kwargs["reason"] == "because i can"

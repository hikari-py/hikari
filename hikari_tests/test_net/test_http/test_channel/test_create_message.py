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

import io
import json

import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_create_message_performs_a_post_request(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456")

    args, kwargs = http_client.request.await_args
    assert "post" in args


@pytest.mark.asyncio
async def test_create_message_sends_to_expected_endpoint(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456")

    args, kwargs = http_client.request.await_args
    assert "/channels/{channel_id}/messages" in args
    assert kwargs["channel_id"] == "123456"


@pytest.mark.asyncio
async def test_tts_flag_unspecified_will_be_false(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456")

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": False}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_tts_flag_false_will_be_false(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", tts=False)

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": False}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_tts_flag_true_will_be_true(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", tts=True)

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": True}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_specifying_content_allows_content_to_be_specified(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", content="ayy")

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": False, "content": "ayy"}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_specifying_nonce_allows_nonce_to_be_specified(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", nonce="91827")

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": False, "nonce": "91827"}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_specifying_embed_allows_embed_to_be_specified(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", embed={"foo": "bar"})

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": False, "embed": {"foo": "bar"}}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_specifying_all_payload_json_fields(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", embed={"foo": "bar"}, nonce="69", content="ayy lmao", tts=True)

    args, kwargs = http_client.request.await_args
    form = kwargs["data"]
    field_dict, headers, payload = form._fields[0]
    assert json.loads(payload) == {"tts": True, "embed": {"foo": "bar"}, "nonce": "69", "content": "ayy lmao"}
    assert headers == {"Content-Type": "application/json"}


@pytest.mark.asyncio
async def test_passing_bytes_as_file_converts_it_correctly_to_BytesIO(http_client):
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


@pytest.mark.asyncio
async def test_passing_bytearray_as_file_converts_it_correctly_to_BytesIO(http_client):
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


@pytest.mark.asyncio
async def test_passing_memoryview_as_file_converts_it_correctly_to_BytesIO(http_client):
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


@pytest.mark.asyncio
async def test_passing_str_as_file_converts_it_correctly_to_StringIO(http_client):
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


@pytest.mark.asyncio
async def test_passing_io_as_file_converts_it_correctly_to_StringIO(http_client):
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


@pytest.mark.asyncio
async def test_passing_several_files_adds_several_files(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., ...))

    await http_client.create_message("123456", files=[("foo.png", b"1a2b3c"), ("bar.png", b""), ("baz.png", b"blep")])
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

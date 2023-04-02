# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
import asyncio
import contextlib
import re
import threading

import aiohttp
import aiohttp.abc
import aiohttp.web
import aiohttp.web_runner
import mock
import multidict

from hikari import files

try:
    import nacl.exceptions
    import nacl.signing

    nacl_present = True
except ModuleNotFoundError:
    nacl_present = False

import pytest

from hikari import errors
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import interaction_server as interaction_server_impl
from hikari.impl import rest as rest_impl
from hikari.interactions import base_interactions
from tests.hikari import hikari_test_helpers


class MockWriter(aiohttp.abc.AbstractStreamWriter):
    def __init__(self):
        self.payload = bytearray()

    async def write(self, chunk: bytes) -> None:
        self.payload.extend(chunk)

    async def write_eof(self, chunk: bytes = b"") -> None:
        pass

    async def drain(self) -> None:
        pass

    def enable_compression(self, encoding: str = "deflate") -> None:
        pass

    def enable_chunking(self) -> None:
        pass

    async def write_headers(self, status_line: str, headers: "multidict.CIMultiDict[str]") -> None:
        pass


@pytest.mark.asyncio()
class TestConsumeGeneratorListener:
    async def test_normal_behaviour(self):
        async def mock_generator_listener():
            nonlocal g_continued

            yield

            g_continued = True

        g_continued = False
        generator = mock_generator_listener()
        # The function expects the generator to have already yielded once
        await generator.__anext__()

        await interaction_server_impl._consume_generator_listener(generator)

        assert g_continued is True

    async def test_when_more_than_one_yield(self):
        async def mock_generator_listener():
            nonlocal g_continued

            yield

            g_continued = True

            yield

        g_continued = False
        generator = mock_generator_listener()
        # The function expects the generator to have already yielded once
        await generator.__anext__()

        loop = mock.Mock()
        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            await interaction_server_impl._consume_generator_listener(generator)

        assert g_continued is True
        args, _ = loop.call_exception_handler.call_args_list[0]
        exception = args[0]["exception"]
        assert isinstance(exception, RuntimeError)
        assert exception.args == ("Generator listener yielded more than once, expected only one yield",)

    async def test_when_exception(self):
        async def mock_generator_listener():
            nonlocal g_continued, exception

            yield

            g_continued = True

            raise exception

        g_continued = False
        exception = ValueError("Some random exception")
        generator = mock_generator_listener()
        # The function expects the generator to have already yielded once
        await generator.__anext__()

        loop = mock.Mock()
        with mock.patch.object(asyncio, "get_running_loop", return_value=loop):
            await interaction_server_impl._consume_generator_listener(generator)

        assert g_continued is True
        args, _ = loop.call_exception_handler.call_args_list[0]
        assert args[0]["exception"] is exception


@pytest.fixture()
def valid_edd25519():
    body = (
        b'{"application_id":"658822586720976907","channel_id":"938391701561679903","data":{"id":"870616445036421159","'
        b'name":"ping","type":1},"guild_id":"561884984214814744","guild_locale":"en-GB","id":"938421734825140264","loc'
        b'ale":"en-GB","member":{"avatar":null,"communication_disabled_until":null,"deaf":false,"is_pending":false,"jo'
        b'ined_at":"2019-03-31T12:10:19.616000+00:00","mute":false,"nick":"Snab","pending":false,"permissions":"219902'
        b'3255551","premium_since":null,"roles":["561885635074457600"],"user":{"avatar":"2549318b6a5f514a6c4a4379ed89a'
        b'469","discriminator":"6127","id":"115590097100865541","public_flags":131072,"username":"Faster Speeding"}},"'
        b'token":"aW50ZXJhY3Rpb246OTM4NDIxNzM0ODI1MTQwMjY0Ok1pR0t6dGt3T1Q4SkhHMnREQmJ2RXI4Vk5vaXZ0UzVMRTBqdVRLcmhnd1dY'
        b"dEd6d2dlTUZGMlNQRkRybGZJaHVuWHZva2lKaWQzcjh1ZEt5NzJtVTFKNzdGOVREOWtoNE5BYnlCdGlGaEZDMDVMY3VhbkF1a0ZZMnhGeU9q"
        b'OHY4","type":2,"version":1}'
    )
    signature = (
        b"\x8c*\xb2\x9e\x05\x0cSgc\xc9}A\xbd\x02.'-[\xb0\xa9\xbegN\xd5Z\x12\xa6 \xc5\x0b!\xd8c"
        b"B\x99\xf5W\x80\x07\xf2\x97\xba\x97\xcc\x17 L\xc53kG\xa0\x1c\x11\x8e|X\x05P\x81@.\xb5\x04"
    )
    timestamp = b"1643807576"
    return (body, signature, timestamp)


@pytest.fixture()
def valid_payload():
    return {
        "application_id": "658822586720976907",
        "channel_id": "938391701561679903",
        "data": {"id": "870616445036421159", "name": "ping", "type": 1},
        "guild_id": "561884984214814744",
        "guild_locale": "en-GB",
        "id": "938421734825140264",
        "locale": "en-GB",
        "member": {
            "avatar": None,
            "communication_disabled_until": None,
            "deaf": False,
            "is_pending": False,
            "joined_at": "2019-03-31T12:10:19.616000+00:00",
            "mute": False,
            "nick": "Snab",
            "pending": False,
            "permissions": "2199023255551",
            "premium_since": None,
            "roles": ["561885635074457600"],
            "user": {
                "avatar": "2549318b6a5f514a6c4a4379ed89a469",
                "discriminator": "6127",
                "id": "115590097100865541",
                "public_flags": 131072,
                "username": "Faster Speeding",
            },
        },
        "token": (
            "aW50ZXJhY3Rpb246OTM4NDIxNzM0ODI1MTQwMjY0Ok1pR0t6dGt3T1Q4SkhHMnREQmJ2RXI"
            "4Vk5vaXZ0UzVMRTBqdVRLcmhnd1dYdEd6d2dlTUZGMlNQRkRybGZJaHVuWHZva2lKaWQzc"
            "jh1ZEt5NzJtVTFKNzdGOVREOWtoNE5BYnlCdGlGaEZDMDVMY3VhbkF1a0ZZMnhGeU9qOHY4"
        ),
        "type": 2,
        "version": 1,
    }


@pytest.fixture()
def invalid_ed25519():
    body = (
        b'{"application_id":"658822586720976907","id":"838085779104202754","token":"aW50ZXJhY3Rpb246ODM4MDg1Nzc5MTA0MjA'
        b"yNzU0OmNhSk9QUU4wa1BKV21nTjFvSGhIbUp0QnQ1NjNGZFRtMlJVRlNjR0ttaDhtUGJrWUNvcmxYZnd2NTRLeUQ2c0hGS1YzTU03dFJ0V0s5"
        b'RWRBY0ltZTRTS0NneFFSYW1BbDZxSkpnMkEwejlkTldXZUh2OGwzbnBrMzhscURIMXUz","type":1,"user":{"avatar":"b333580bd947'
        b'4630226ff7b0a9696231","discriminator":"6127","id":"115590097100865541","public_flags":13'
        b'1072,"username":"Faster Speeding"},"version":1}'
    )
    signature = (
        b"\x0c4\xda!\xd9\xd5\x08<{a\x0c\xfa\xe6\xd2\x9e\xb3\xe0\x17r\x83\xa8\xb5\xda\xaa\x97\n\xb5\xe1\x92A|\x94\xbb"
        b"\x8aGu\xdb\xd6\x19\xd5\x94\x98\x08\xb4\x1a\xfaF@\xbbx\xc9\xa3\x8f\x1f\x13\t\xd81\xa3:\xa9%p\x0c"
    )
    timestamp = b"1619885620"
    return (body, signature, timestamp)


@pytest.fixture()
def public_key():
    return b"\x12-\xdfX\xa8\x95\xd7\xe1\xb7o\xf5\xd0q\xb0\xaa\xc9\xb7v^*\xb5\x15\xe1\x1b\x7f\xca\xf9d\xdbT\x90\xc6"


@pytest.mark.skipif(nacl_present, reason="PyNacl is present")
def test_interaction_server_init_when_no_pynacl():
    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "You must install the optional `hikari[server]` dependencies to use the default interaction server."
        ),
    ):
        interaction_server_impl.InteractionServer(entity_factory=mock.Mock(), rest_client=mock.Mock())


@pytest.mark.skipif(not nacl_present, reason="PyNacl not present")
class TestInteractionServer:
    @pytest.fixture()
    def mock_entity_factory(self):
        return mock.Mock(entity_factory_impl.EntityFactoryImpl)

    @pytest.fixture()
    def mock_rest_client(self):
        return mock.Mock(rest_impl.RESTClientImpl)

    @pytest.fixture()
    def mock_interaction_server(
        self, mock_entity_factory: interaction_server_impl.InteractionServer, mock_rest_client: rest_impl.RESTClientImpl
    ):
        cls = hikari_test_helpers.mock_class_namespace(interaction_server_impl.InteractionServer, slots_=False)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl", return_value=mock_rest_client))

        with stack:
            return cls(entity_factory=mock_entity_factory, rest_client=mock_rest_client)

    def test___init__(
        self, mock_rest_client: rest_impl.RESTClientImpl, mock_entity_factory: entity_factory_impl.EntityFactoryImpl
    ):
        mock_dumps = object()
        mock_loads = object()

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))

        with stack:
            result = interaction_server_impl.InteractionServer(
                dumps=mock_dumps,
                entity_factory=mock_entity_factory,
                loads=mock_loads,
                rest_client=mock_rest_client,
                public_key=None,
            )

        assert result._dumps is mock_dumps
        assert result._entity_factory is mock_entity_factory
        assert result._loads is mock_loads
        assert result._rest_client is mock_rest_client
        assert result._public_key is None

    def test___init___with_public_key(
        self, mock_rest_client: rest_impl.RESTClientImpl, mock_entity_factory: entity_factory_impl.EntityFactoryImpl
    ):
        mock_dumps = object()
        mock_loads = object()

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))

        with stack:
            result = interaction_server_impl.InteractionServer(
                dumps=mock_dumps,
                entity_factory=mock_entity_factory,
                loads=mock_loads,
                rest_client=mock_rest_client,
                public_key=None,
            )

        assert result._public_key is None

    def test_is_alive_property_when_inactive(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        assert mock_interaction_server.is_alive is False

    def test_is_alive_property_when_active(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_interaction_server._server = object()

        assert mock_interaction_server.is_alive is True

    @pytest.mark.asyncio()
    async def test___fetch_public_key_when_lock_is_None_gets_new_lock_and_doesnt_overwrite_existing_ones(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_rest_client: rest_impl.RESTClientImpl,
    ):
        mock_rest_client.token_type = "Bot"
        mock_interaction_server._application_fetch_lock = None
        mock_rest_client.fetch_application.return_value.public_key = (
            b"e\xb9\xf8\xac]eH\xb1\xe1D\xafaW\xdd\x1c.\xc1s\xfd<\x82\t\xeaO\xd4w\xaf\xc4\x1b\xd0\x8f\xc5"
        )
        results = []

        with mock.patch.object(asyncio, "Lock") as lock_class:
            # Run some times to make sure it does not overwrite it
            for _ in range(5):
                results.append(await mock_interaction_server._fetch_public_key())

        assert results[0] == nacl.signing.VerifyKey(mock_rest_client.fetch_application.return_value.public_key)
        assert all(result is results[0] for result in results)
        assert mock_interaction_server._application_fetch_lock is lock_class.return_value
        lock_class.assert_called_once_with()
        lock_class.return_value.__aenter__.assert_has_awaits([mock.call() for _ in range(5)])
        lock_class.return_value.__aexit__.assert_has_awaits([mock.call(None, None, None) for _ in range(5)])

    @pytest.mark.asyncio()
    async def test__fetch_public_key_with_bearer_token(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_rest_client: rest_impl.RESTClientImpl,
    ):
        mock_rest_client.token_type = "Bearer"
        mock_interaction_server._application_fetch_lock = mock.AsyncMock()
        mock_rest_client.fetch_authorization.return_value.application.public_key = (
            b'\x81\xa9\xc0\xee"\xf0%\xd1CF\x82Uh\x16.>\x9b\xcf[\x1f\xa4\xfcsb\xc3\xf4x\xf9\xe0z\xad\xed'
        )

        result = await mock_interaction_server._fetch_public_key()

        assert result == nacl.signing.VerifyKey(
            mock_rest_client.fetch_authorization.return_value.application.public_key
        )
        mock_rest_client.fetch_authorization.assert_awaited_once()
        mock_rest_client.fetch_application.assert_not_called()
        mock_interaction_server._application_fetch_lock.__aenter__.assert_awaited_once()
        mock_interaction_server._application_fetch_lock.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test__fetch_public_key_fetch_with_bot_token(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_rest_client: rest_impl.RESTClientImpl,
    ):
        mock_rest_client.token_type = "Bot"
        mock_interaction_server._application_fetch_lock = mock.AsyncMock()
        mock_rest_client.fetch_application.return_value.public_key = (
            b"\xf3\xfd\xfc\x81\xfcU\x00\xe5;V\x15\xc6H\xab4Ip\x07\x1bR\xc2b9\x86\xa9\\e\xfa\xcbw\xd7\x0b"
        )

        result = await mock_interaction_server._fetch_public_key()

        assert result == nacl.signing.VerifyKey(mock_rest_client.fetch_application.return_value.public_key)
        mock_rest_client.fetch_authorization.assert_not_called()
        mock_rest_client.fetch_application.assert_awaited_once()
        mock_interaction_server._application_fetch_lock.__aenter__.assert_awaited_once()
        mock_interaction_server._application_fetch_lock.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test__fetch_public_key_when_public_key_already_set(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_lock = mock.AsyncMock()
        mock_public_key = object()
        mock_interaction_server._application_fetch_lock = mock_lock
        mock_interaction_server._public_key = mock_public_key

        assert await mock_interaction_server._fetch_public_key() is mock_public_key

        mock_lock.__aenter__.assert_awaited_once()
        mock_lock.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_aiohttp_hook(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_interaction_server.on_interaction = mock.AsyncMock(
            return_value=mock.Mock(
                payload=b"abody",
                files=[],
                status_code=200,
                headers={"header1": "ok"},
                content_type="ooga/booga",
                charset=None,
            )
        )
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(return_value=b"bfddasdasd"),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        mock_interaction_server.on_interaction.assert_awaited_once_with(
            body=b"bfddasdasd", signature=b"troekpewieojksi9", timestamp=b"123123"
        )
        assert result.body == b"abody"
        assert result.content_type == "ooga/booga"
        assert result.headers == {"header1": "ok", "Content-Type": "ooga/booga"}
        assert result.status == 200

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_when_no_other_headers(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_interaction_server.on_interaction = mock.AsyncMock(
            return_value=mock.Mock(
                payload=b"abody", files=[], headers=None, status_code=200, content_type="ooga/booga", charset=None
            )
        )
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(return_value=b"bfddasdasd"),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        mock_interaction_server.on_interaction.assert_awaited_once_with(
            body=b"bfddasdasd", signature=b"troekpewieojksi9", timestamp=b"123123"
        )
        assert result.body == b"abody"
        assert result.content_type == "ooga/booga"
        assert result.headers == {"Content-Type": "ooga/booga"}
        assert result.status == 200

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_when_files(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_interaction_server.on_interaction = mock.AsyncMock(
            return_value=mock.Mock(
                payload=b"abody",
                files=[files.Bytes("x" * 329, "meow.txt"), files.Bytes("y" * 124, "nyaa.txt")],
                status_code=200,
                headers={"header1": "ok"},
                content_type="ooga/booga",
            )
        )
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(return_value=b"bfddasdasd"),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        mock_interaction_server.on_interaction.assert_awaited_once_with(
            body=b"bfddasdasd", signature=b"troekpewieojksi9", timestamp=b"123123"
        )
        assert isinstance(result.body, aiohttp.MultipartWriter)
        assert result.content_type == "multipart/form-data"
        assert result.headers == {
            "header1": "ok",
            "Content-Type": f"multipart/form-data; boundary={result.body.boundary}",
        }
        assert result.status == 200

        mock_writer = MockWriter()
        await result.body.write(mock_writer)

        boundary = result.body.boundary.encode()
        assert mock_writer.payload == (
            b"--" + boundary + b"""\r\nContent-Type: ooga/booga\r\nContent-Disposition: form-data; name="payload_json"""
            b""""\r\nContent-Length: 5\r\n\r\nabody\r\n--""" + boundary + b"""\r\nContent-Type: text/plain\r\nConten"""
            b"""t-Disposition: form-data; name="files[0]"; filename="meow.txt"\r\n\r\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"""
            b"""xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"""
            b"""xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"""
            b"""xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"""
            b"""\r\n--""" + boundary + b"""\r\nContent-Type: text/plain\r\nContent-Disposition: form-data; name="fil"""
            b"""es[1]"; filename="nyaa.txt"\r\n\r\nyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"""
            b"""yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy\r\n--""" + boundary + b"""--\r\n"""
        )

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_for_unsupported_media_type(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        request = mock.Mock(aiohttp.web.Request, content_type="notjson")

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Unsupported Media Type"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 415

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_with_missing_ed25519_header(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        request = mock.Mock(aiohttp.web.Request, content_type="application/json", headers={"X-Signature-Timestamp": ""})

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Missing or invalid required request signature header(s)"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_with_missing_timestamp_header(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        request = mock.Mock(aiohttp.web.Request, content_type="application/json", headers={"X-Signature-Ed25519": ""})

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Missing or invalid required request signature header(s)"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_with_invalid_ed25519_header(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "'#';[][];['345", "X-Signature-Timestamp": ""},
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Missing or invalid required request signature header(s)"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_when_payload_too_large(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(side_effect=aiohttp.web.HTTPRequestEntityTooLarge(123, 321)),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Payload too large"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 413

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_when_no_body(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(return_value=""),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"POST request must have a body"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_close(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_runner = mock.AsyncMock()
        mock_event = mock.Mock()
        mock_interaction_server._is_closing = False
        mock_interaction_server._server = mock_runner
        mock_interaction_server._close_event = mock_event
        generator_listener_1 = mock.Mock()
        generator_listener_2 = mock.Mock()
        generator_listener_3 = mock.Mock()
        generator_listener_4 = mock.Mock()
        mock_interaction_server._running_generator_listeners = [
            generator_listener_1,
            generator_listener_2,
            generator_listener_3,
            generator_listener_4,
        ]

        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()) as gather:
            await mock_interaction_server.close()

        mock_runner.shutdown.assert_awaited_once()
        mock_runner.cleanup.assert_awaited_once()
        mock_event.set.assert_called_once()
        assert mock_interaction_server._is_closing is False
        assert mock_interaction_server._running_generator_listeners == []
        gather.assert_awaited_once_with(
            generator_listener_1, generator_listener_2, generator_listener_3, generator_listener_4
        )

    @pytest.mark.asyncio()
    async def test_close_when_closing(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_runner = mock.AsyncMock()
        mock_event = mock.Mock()
        mock_interaction_server._server = mock_runner
        mock_interaction_server._close_event = mock_event
        mock_interaction_server._is_closing = True
        mock_interaction_server.join = mock.AsyncMock()
        mock_listener = object()
        mock_interaction_server._running_generator_listeners = [mock_listener]

        await mock_interaction_server.close()

        mock_runner.shutdown.assert_not_called()
        mock_runner.cleanup.assert_not_called()
        mock_event.set.assert_not_called()
        mock_interaction_server.join.assert_awaited_once()
        assert mock_interaction_server._running_generator_listeners == [mock_listener]

    @pytest.mark.asyncio()
    async def test_close_when_not_running(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        with pytest.raises(errors.ComponentStateConflictError):
            await mock_interaction_server.close()

    @pytest.mark.asyncio()
    async def test_join(self, mock_interaction_server):
        mock_event = mock.AsyncMock()
        mock_interaction_server._server = object()
        mock_interaction_server._close_event = mock_event

        await mock_interaction_server.join()

        mock_event.wait.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_join_when_not_running(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        with pytest.raises(errors.ComponentStateConflictError):
            await mock_interaction_server.join()

    @pytest.mark.asyncio()
    async def test_on_interaction(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
        public_key: bytes,
        valid_edd25519: bytes,
        valid_payload: bytes,
    ):
        mock_interaction_server._public_key = nacl.signing.VerifyKey(public_key)
        mock_file_1 = mock.Mock()
        mock_file_2 = mock.Mock()
        mock_entity_factory.deserialize_interaction.return_value = base_interactions.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock(return_value=({"ok": "No boomer"}, [mock_file_1, mock_file_2])))
        mock_listener = mock.AsyncMock(return_value=mock_builder)
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, mock_listener)

        result = await mock_interaction_server.on_interaction(*valid_edd25519)

        mock_listener.assert_awaited_once_with(mock_entity_factory.deserialize_interaction.return_value)
        mock_builder.build.assert_called_once_with(mock_entity_factory)
        mock_entity_factory.deserialize_interaction.assert_called_once_with(valid_payload)
        assert result.content_type == "application/json"
        assert result.charset == "UTF-8"
        assert result.files == [mock_file_1, mock_file_2]
        assert result.headers is None
        assert result.payload == b'{"ok":"No boomer"}'
        assert result.status_code == 200

    @pytest.mark.asyncio()
    async def test_on_interaction_with_generator_listener(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
        public_key: bytes,
        valid_edd25519: bytes,
        valid_payload: bytes,
    ):
        async def mock_generator_listener(event):
            nonlocal g_called, g_complete

            g_called = True
            assert event is mock_entity_factory.deserialize_interaction.return_value

            yield mock_builder

            g_complete = True

        mock_interaction_server._public_key = nacl.signing.VerifyKey(public_key)
        mock_file_1 = mock.Mock()
        mock_file_2 = mock.Mock()
        mock_entity_factory.deserialize_interaction.return_value = base_interactions.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock(return_value=({"ok": "No boomer"}, [mock_file_1, mock_file_2])))
        g_called = False
        g_complete = False
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, mock_generator_listener)

        result = await mock_interaction_server.on_interaction(*valid_edd25519)

        mock_builder.build.assert_called_once_with(mock_entity_factory)
        mock_entity_factory.deserialize_interaction.assert_called_once_with(valid_payload)
        assert result.content_type == "application/json"
        assert result.charset == "UTF-8"
        assert result.files == [mock_file_1, mock_file_2]
        assert result.headers is None
        assert result.payload == b'{"ok":"No boomer"}'
        assert result.status_code == 200

        assert g_called is True
        assert g_complete is False
        assert len(mock_interaction_server._running_generator_listeners) != 0
        # Give some time for the task to complete
        await asyncio.sleep(hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME)

        assert g_complete is True
        assert len(mock_interaction_server._running_generator_listeners) == 0

    @pytest.mark.asyncio()
    async def test_on_interaction_calls__fetch_public_key(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_fetcher = mock.AsyncMock(
            return_value=mock.Mock(verify=mock.Mock(side_effect=nacl.exceptions.BadSignatureError))
        )
        mock_interaction_server._public_key = None
        mock_interaction_server._fetch_public_key = mock_fetcher

        result = await mock_interaction_server.on_interaction(b"body", b"signature", b"timestamp")

        mock_fetcher.assert_awaited_once()
        mock_fetcher.return_value.verify.assert_called_once_with(b"timestampbody", b"signature")
        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Invalid request signature"
        assert result.status_code == 400

    @pytest.mark.asyncio()
    async def test_on_interaction_when_public_key_mismatch(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        public_key: bytes,
        invalid_ed25519: bytes,
    ):
        mock_interaction_server._public_key = nacl.signing.VerifyKey(public_key)

        result = await mock_interaction_server.on_interaction(*invalid_ed25519)

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Invalid request signature"
        assert result.status_code == 400

    @pytest.mark.parametrize("body", [b"not a json", b"\x80abc"])
    @pytest.mark.asyncio()
    async def test_on_interaction_when_bad_body(
        self, mock_interaction_server: interaction_server_impl.InteractionServer, body: bytes
    ):
        mock_interaction_server._public_key = mock.Mock()

        result = await mock_interaction_server.on_interaction(body, b"signature", b"timestamp")

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Invalid JSON body"
        assert result.status_code == 400

    @pytest.mark.asyncio()
    async def test_on_interaction_when_missing_type_key(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_interaction_server._public_key = mock.Mock()

        result = await mock_interaction_server.on_interaction(b'{"key": "OK"}', b"signature", b"timestamp")

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Missing required 'type' field in payload"
        assert result.status_code == 400

    @pytest.mark.asyncio()
    async def test_on_interaction_on_ping(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_interaction_server._public_key = mock.Mock()

        result = await mock_interaction_server.on_interaction(b'{"type":1}', b"signature", b"timestamp")

        assert result.content_type == "application/json"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b'{"type":1}'
        assert result.status_code == 200

    @pytest.mark.asyncio()
    async def test_on_interaction_on_deserialize_unrecognised_entity_error(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
    ):
        mock_interaction_server._public_key = mock.Mock()
        mock_entity_factory.deserialize_interaction.side_effect = errors.UnrecognisedEntityError("blah")

        result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Interaction type not implemented"
        assert result.status_code == 501

    @pytest.mark.asyncio()
    async def test_on_interaction_on_failed_deserialize(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
    ):
        mock_interaction_server._public_key = mock.Mock()
        mock_exception = TypeError("OK")
        mock_entity_factory.deserialize_interaction.side_effect = mock_exception

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction deserialization", "exception": mock_exception}
            )

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Exception occurred during interaction deserialization"
        assert result.status_code == 500

    @pytest.mark.asyncio()
    async def test_on_interaction_on_dispatch_error(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
    ):
        mock_interaction_server._public_key = mock.Mock()
        mock_exception = TypeError("OK")
        mock_entity_factory.deserialize_interaction.return_value = base_interactions.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_interaction_server.set_listener(
            base_interactions.PartialInteraction, mock.Mock(side_effect=mock_exception)
        )

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction dispatch", "exception": mock_exception}
            )

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Exception occurred during interaction dispatch"
        assert result.status_code == 500

    @pytest.mark.asyncio()
    async def test_on_interaction_when_response_builder_error(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
    ):
        mock_interaction_server._public_key = mock.Mock()
        mock_exception = TypeError("OK")
        mock_entity_factory.deserialize_interaction.return_value = base_interactions.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock(side_effect=mock_exception))
        mock_interaction_server.set_listener(
            base_interactions.PartialInteraction, mock.AsyncMock(return_value=mock_builder)
        )

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction dispatch", "exception": mock_exception}
            )

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Exception occurred during interaction dispatch"
        assert result.status_code == 500

    @pytest.mark.asyncio()
    async def test_on_interaction_when_json_encode_fails(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
    ):
        mock_interaction_server._public_key = mock.Mock()
        mock_exception = TypeError("OK")
        mock_interaction_server._dumps = mock.Mock(side_effect=mock_exception)
        mock_entity_factory.deserialize_interaction.return_value = base_interactions.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock(return_value=({"ok": "No"}, [])))
        mock_interaction_server.set_listener(
            base_interactions.PartialInteraction, mock.AsyncMock(return_value=mock_builder)
        )

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction dispatch", "exception": mock_exception}
            )

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Exception occurred during interaction dispatch"
        assert result.status_code == 500

    @pytest.mark.asyncio()
    async def test_on_interaction_when_no_registered_listener(
        self,
        mock_interaction_server: interaction_server_impl.InteractionServer,
        mock_entity_factory: entity_factory_impl.EntityFactoryImpl,
    ):
        mock_interaction_server._public_key = mock.Mock()

        result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

        assert result.content_type == "text/plain"
        assert result.charset == "UTF-8"
        assert result.files == ()
        assert result.headers is None
        assert result.payload == b"Handler not set for this interaction type"
        assert result.status_code == 501

    @pytest.mark.asyncio()
    async def test_start(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_context = object()
        mock_socket = object()
        mock_interaction_server._is_closing = True
        mock_interaction_server._fetch_public_key = mock.AsyncMock()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "UnixSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "SockSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))
        stack.enter_context(mock.patch.object(asyncio, "Event"))

        with stack:
            await mock_interaction_server.start(
                backlog=123123,
                host="hoototototo",
                port=123123123,
                path="hshshshshsh",
                reuse_address=True,
                reuse_port=False,
                socket=mock_socket,
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
            )

            mock_interaction_server._fetch_public_key.assert_awaited_once_with()

            aiohttp.web.Application.assert_called_once_with()
            aiohttp.web.Application.return_value.add_routes.assert_called_once_with(
                [aiohttp.web.post("/", mock_interaction_server.aiohttp_hook)]
            )
            aiohttp.web_runner.AppRunner.assert_called_once_with(
                aiohttp.web.Application.return_value, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                "hoototototo",
                port=123123123,
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
                backlog=123123,
                reuse_address=True,
                reuse_port=False,
            )
            aiohttp.web.UnixSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                "hshshshshsh",
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
                backlog=123123,
            )
            aiohttp.web.SockSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                mock_socket,
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
                backlog=123123,
            )
            aiohttp.web.TCPSite.return_value.start.assert_awaited_once()
            aiohttp.web.UnixSite.return_value.start.assert_awaited_once()
            aiohttp.web.SockSite.return_value.start.assert_awaited_once()
            assert mock_interaction_server._close_event is asyncio.Event.return_value
            assert mock_interaction_server._is_closing is False

    @pytest.mark.asyncio()
    async def test_start_with_default_behaviour(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_context = object()
        mock_interaction_server._fetch_public_key = mock.AsyncMock()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))

        with stack:
            await mock_interaction_server.start(ssl_context=mock_context)

            mock_interaction_server._fetch_public_key.assert_awaited_once_with()

            aiohttp.web.Application.assert_called_once_with()
            aiohttp.web.Application.return_value.add_routes.assert_called_once_with(
                [aiohttp.web.post("/", mock_interaction_server.aiohttp_hook)]
            )
            aiohttp.web_runner.AppRunner.assert_called_once_with(
                aiohttp.web.Application.return_value, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                port=None,
                shutdown_timeout=60.0,
                ssl_context=mock_context,
                backlog=128,
                reuse_address=None,
                reuse_port=None,
            )
            aiohttp.web.TCPSite.return_value.start.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_start_with_default_behaviour_and_not_main_thread(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_context = object()
        mock_interaction_server._fetch_public_key = mock.AsyncMock()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))
        stack.enter_context(mock.patch.object(threading, "current_thread"))

        with stack:
            await mock_interaction_server.start(ssl_context=mock_context)

            mock_interaction_server._fetch_public_key.assert_awaited_once_with()

            aiohttp.web.Application.assert_called_once_with()
            aiohttp.web.Application.return_value.add_routes.assert_called_once_with(
                [aiohttp.web.post("/", mock_interaction_server.aiohttp_hook)]
            )
            aiohttp.web_runner.AppRunner.assert_called_once_with(
                aiohttp.web.Application.return_value, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                port=None,
                shutdown_timeout=60.0,
                ssl_context=mock_context,
                backlog=128,
                reuse_address=None,
                reuse_port=None,
            )
            aiohttp.web.TCPSite.return_value.start.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_start_with_multiple_hosts(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_context = object()
        mock_interaction_server._fetch_public_key = mock.AsyncMock()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))

        with stack:
            await mock_interaction_server.start(ssl_context=mock_context, host=["123", "4312"], port=453123)

            mock_interaction_server._fetch_public_key.assert_awaited_once_with()

            aiohttp.web.Application.assert_called_once_with()
            aiohttp.web.Application.return_value.add_routes.assert_called_once_with(
                [aiohttp.web.post("/", mock_interaction_server.aiohttp_hook)]
            )
            aiohttp.web_runner.AppRunner.assert_called_once_with(
                aiohttp.web.Application.return_value, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_has_calls(
                [
                    mock.call(
                        aiohttp.web_runner.AppRunner.return_value,
                        "123",
                        port=453123,
                        shutdown_timeout=60.0,
                        ssl_context=mock_context,
                        backlog=128,
                        reuse_address=None,
                        reuse_port=None,
                    ),
                    mock.call(
                        aiohttp.web_runner.AppRunner.return_value,
                        "4312",
                        port=453123,
                        shutdown_timeout=60.0,
                        ssl_context=mock_context,
                        backlog=128,
                        reuse_address=None,
                        reuse_port=None,
                    ),
                ]
            )
            aiohttp.web.TCPSite.return_value.start.assert_has_awaits([mock.call(), mock.call()])

    @pytest.mark.asyncio()
    async def test_start_when_no_tcp_sites(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_socket = object()
        mock_context = object()
        mock_interaction_server._fetch_public_key = mock.AsyncMock()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "Application"))
        stack.enter_context(mock.patch.object(aiohttp.web, "SockSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "UnixSite", return_value=mock.AsyncMock()))

        with stack:
            await mock_interaction_server.start(ssl_context=mock_context, socket=mock_socket)

            mock_interaction_server._fetch_public_key.assert_awaited_once_with()

            aiohttp.web.Application.assert_called_once_with()
            aiohttp.web.Application.return_value.add_routes.assert_called_once_with(
                [aiohttp.web.post("/", mock_interaction_server.aiohttp_hook)]
            )
            aiohttp.web_runner.AppRunner.assert_called_once_with(
                aiohttp.web.Application.return_value, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_not_called()
            aiohttp.web.UnixSite.assert_not_called()
            aiohttp.web.SockSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                mock_socket,
                shutdown_timeout=60.0,
                ssl_context=mock_context,
                backlog=128,
            )
            aiohttp.web.SockSite.return_value.start.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_start_when_already_running(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_interaction_server._server = object()

        with pytest.raises(errors.ComponentStateConflictError):
            await mock_interaction_server.start()

    def test_get_listener_when_unknown(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        assert mock_interaction_server.get_listener(base_interactions.PartialInteraction) is None

    def test_get_listener_when_registered(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_listener = object()
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, mock_listener)

        assert mock_interaction_server.get_listener(base_interactions.PartialInteraction) is mock_listener

    def test_set_listener(self, mock_interaction_server: interaction_server_impl.InteractionServer):
        mock_listener = object()

        mock_interaction_server.set_listener(base_interactions.PartialInteraction, mock_listener)

        assert mock_interaction_server.get_listener(base_interactions.PartialInteraction) is mock_listener

    def test_set_listener_when_already_registered_without_replace(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, object())

        with pytest.raises(TypeError):
            mock_interaction_server.set_listener(base_interactions.PartialInteraction, object())

    def test_set_listener_when_already_registered_with_replace(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_listener = object()
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, object())

        mock_interaction_server.set_listener(base_interactions.PartialInteraction, mock_listener, replace=True)

        assert mock_interaction_server.get_listener(base_interactions.PartialInteraction) is mock_listener

    def test_set_listener_when_removing_listener(
        self, mock_interaction_server: interaction_server_impl.InteractionServer
    ):
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, object())
        mock_interaction_server.set_listener(base_interactions.PartialInteraction, None)

        assert mock_interaction_server.get_listener(base_interactions.PartialInteraction) is None

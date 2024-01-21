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
import logging
import time

from aiohttp import web

logging.basicConfig(level="DEBUG")


host = "localhost"
port = 8080

gateway_route_v8 = "/gateway/v8"
gateway_uri_v8 = f"ws://{host}:{port}{gateway_route_v8}"
heartbeat_interval = 5_000

me_user_id = "1234567890"
me_username = "nekokatt"
me_global_name = None
me_discriminator = "6945"
me_avatar = None
me_bot = True
me_mfa = False
me_locale = "en_GB"
me_verified = False
me_email = "guesswhat@example.com"
me_flags = 0
me_premium_type = 0
me_public_flags = 0

route_table = web.RouteTableDef()


@route_table.get("/api/v8/gateway")
def v8_get_gateway(_):
    return web.json_response({"url": gateway_uri_v8})


@route_table.get("/api/v8/gateway/bot")
def v8_get_gateway_bot(_):
    return web.json_response(
        {
            "url": gateway_uri_v8,
            "shards": 1,
            "session_start_limit": {"total": 1000, "remaining": 1000, "reset_after": 1},
        }
    )


@route_table.get("/api/v8/users/@me")
def v8_get_my_user(_):
    body = {
        "id": me_user_id,
        "username": me_username,
        "global_name": me_global_name,
        "discriminator": me_discriminator,
        "avatar": me_avatar,
        "bot": me_bot,
        "mfa_enabled": me_mfa,
        "locale": me_locale,
        "verified": me_verified,
        "email": me_email,
        "flags": me_flags,
        "premium_type": me_premium_type,
        "public_flags": me_public_flags,
    }
    return web.json_response(body)


@route_table.get(gateway_route_v8)
async def gateway_v8(req):
    res = web.WebSocketResponse()
    await res.prepare(req)
    await GatewayV8(res).run()
    return res


class GatewayV8:
    def __init__(self, ws: web.WebSocketResponse):
        self.ws = ws
        self.last_heartbeat = float("nan")
        self.seq = 0

    async def run(self):
        await self.send_hello()
        await self.receive_identify()
        while True:
            print("received payload", await self.poll_messages())
        print("Closed")

    async def send_hello(self):
        await self.ws.send_json({"op": 10, "d": {"heartbeat_interval": heartbeat_interval}})

    async def receive_identify(self):
        payload = await self.poll_messages()
        if payload["op"] != 2:
            print("Expected IDENTIFY, got", payload)
            await self.ws.close(code=4003, message=b"not authenticated")
        else:
            print("received IDENTIFY", payload)

    async def poll_messages(self):
        while True:
            payload = await self.ws.receive_json()
            op = payload["op"]

            if op == 1:
                print("Recv heartbeat, seq =", payload["d"])
                self.last_heartbeat = time.perf_counter()
                print("Sending heartbeat ack")
                await self.ws.send_json({"op": 11, "d": None})
                continue

            if op == 11:
                print("Recv Heartbeat ACK")
                continue

            return payload


server = web.Application()
server.add_routes(route_table)
web.run_app(server, host=host, port=port)

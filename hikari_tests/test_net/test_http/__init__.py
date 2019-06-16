#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest

from hikari.net import opcodes
from hikari.net.http import client
from hikari.net.http.base import _RequestReturnSignature


class ClientMock(client.HTTPClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_response()

    async def request(self, method, path, params=None, **kwargs) -> _RequestReturnSignature:
        pass

    def set_response(self, status=opcodes.HTTPStatus.OK, headers=..., body=...) -> None:
        if headers is ...:
            headers = {}
        if body is ...:
            body = {}
        # noinspection PyAttributeOutsideInit
        self.request = asynctest.CoroutineMock(return_value=(status, headers, body))

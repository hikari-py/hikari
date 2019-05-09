#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import textwrap

import asynctest
import pytest

from hikari.net import debug


@pytest.mark.asyncio
async def test_get_debug_data():
    with asynctest.patch("aiohttp.request", new=prepare_mock_response()):
        data = await debug.get_debug_data()
        assert data.fl == "abc123"
        assert data.ip == "127.0.0.1"
        assert data.h == "discordapp.com"
        assert data.visit_scheme == "https"
        assert data.uag == "ayylmao browser inc"
        assert data.http == "2"
        assert data.tls == "henlo yes ssl here"
        assert data.sni == "plaintext"
        assert data.warp == "back to the futureee"

        ts = data.ts
        assert ts.day == 8
        assert ts.month == 5
        assert ts.year == 2019
        assert ts.hour == 18
        assert ts.minute == 0

        airport = data.colo
        assert airport.airport == "Heathrow Airport"
        assert airport.iata_code == "LHR"
        assert airport.country == "England"
        assert airport.location == "London"


def prepare_mock_response():
    class Response:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def __init__(self, text):
            self.text = asyncio.coroutine(lambda: text)
            self.raise_for_status = lambda: None

    request_method = asynctest.Mock(
        side_effect=[
            Response(
                textwrap.dedent(
                    """
                fl=abc123
                ip=127.0.0.1
                ts=1557338434
                h=discordapp.com

                visit_scheme=https
                uag=ayylmao browser inc
                colo=LHR
                http=2
                loc=gb
                tls=henlo yes ssl here
                sni=plaintext
                warp=back to the futureee
            """
                )
            ),
            Response(
                textwrap.dedent(
                    """
                <!doctype html>
                <html>
                    <head>
                        <meta charset="utf-8" />
                        <title>Some Response</title>
                    </head>
                    <body>
                        <table>
                            <tr><td>foo</td><td>bar</td></tr>
                            <tr><td>foo</td><td>bar</td></tr>
                            <tr><td>foo</td><td>bar</td></tr>
                            <tr><td>Location:</td><td>London</td></tr>
                            <tr><td>foo</td><td>bar</td></tr>
                            <tr><td>Airport:</td><td>Heathrow Airport</td></tr>
                            <tr><td>Country:</td><td>England</td></tr>
                        </table>
                    </body>
                </html>
            """
                )
            ),
        ]
    )

    return request_method

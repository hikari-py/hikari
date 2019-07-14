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

import textwrap

import asynctest
import pytest

from hikari.net import server_debug
from hikari_tests import _helpers


def teardown_function():
    _helpers.purge_loop()


@pytest.mark.asyncio
async def test_get_debug_data(event_loop):
    with asynctest.patch("aiohttp.request", new=prepare_mock_response()):
        data = await server_debug.get_debug_data()
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

        assert str(airport) == f"{airport.airport} ({airport.iata_code}), {airport.location}, {airport.country}"


def prepare_mock_response():
    class Response:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def __init__(self, text):
            async def text_getter():
                return text

            self.text = text_getter
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

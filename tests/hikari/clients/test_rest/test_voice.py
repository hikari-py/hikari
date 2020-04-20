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
import mock
import pytest

from hikari import voices
from hikari.clients.rest import voice
from hikari.net import rest


class TestRESTUserLogic:
    @pytest.fixture()
    def rest_voice_logic_impl(self):
        mock_low_level_restful_client = mock.MagicMock(rest.REST)

        class RESTVoiceLogicImpl(voice.RESTVoiceComponent):
            def __init__(self):
                super().__init__(mock_low_level_restful_client)

        return RESTVoiceLogicImpl()

    @pytest.mark.asyncio
    async def test_fetch_voice_regions(self, rest_voice_logic_impl):
        mock_voice_payload = {"id": "LONDON", "name": "london"}
        mock_voice_obj = mock.MagicMock(voices.VoiceRegion)
        rest_voice_logic_impl._session.list_voice_regions.return_value = [mock_voice_payload]
        with mock.patch.object(voices.VoiceRegion, "deserialize", return_value=mock_voice_obj):
            assert await rest_voice_logic_impl.fetch_voice_regions() == [mock_voice_obj]
            rest_voice_logic_impl._session.list_voice_regions.assert_called_once()
            voices.VoiceRegion.deserialize.assert_called_once_with(mock_voice_payload)

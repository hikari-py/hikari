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

from hikari.models import invites
from hikari.components import application
from hikari.rest import invite
from hikari.rest import session


class TestRESTInviteLogic:
    @pytest.fixture()
    def rest_invite_logic_impl(self):
        mock_components = mock.MagicMock(application.Application)
        mock_low_level_restful_client = mock.MagicMock(session.RESTSession)

        class RESTInviteLogicImpl(invite.RESTInviteComponent):
            def __init__(self):
                super().__init__(mock_components, mock_low_level_restful_client)

        return RESTInviteLogicImpl()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invite", [mock.MagicMock(invites.Invite, code="AAAAAAAAAAAAAAAA"), "AAAAAAAAAAAAAAAA"])
    async def test_fetch_invite_with_counts(self, rest_invite_logic_impl, invite):
        mock_invite_payload = {"code": "AAAAAAAAAAAAAAAA", "guild": {}, "channel": {}}
        mock_invite_obj = mock.MagicMock(invites.Invite)
        rest_invite_logic_impl._session.get_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.Invite, "deserialize", return_value=mock_invite_obj):
            assert await rest_invite_logic_impl.fetch_invite(invite, with_counts=True) is mock_invite_obj
            rest_invite_logic_impl._session.get_invite.assert_called_once_with(
                invite_code="AAAAAAAAAAAAAAAA", with_counts=True,
            )
            invites.Invite.deserialize.assert_called_once_with(
                mock_invite_payload, components=rest_invite_logic_impl._components
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invite", [mock.MagicMock(invites.Invite, code="AAAAAAAAAAAAAAAA"), "AAAAAAAAAAAAAAAA"])
    async def test_fetch_invite_without_counts(self, rest_invite_logic_impl, invite):
        mock_invite_payload = {"code": "AAAAAAAAAAAAAAAA", "guild": {}, "channel": {}}
        mock_invite_obj = mock.MagicMock(invites.Invite)
        rest_invite_logic_impl._session.get_invite.return_value = mock_invite_payload
        with mock.patch.object(invites.Invite, "deserialize", return_value=mock_invite_obj):
            assert await rest_invite_logic_impl.fetch_invite(invite) is mock_invite_obj
            rest_invite_logic_impl._session.get_invite.assert_called_once_with(
                invite_code="AAAAAAAAAAAAAAAA", with_counts=...,
            )
            invites.Invite.deserialize.assert_called_once_with(
                mock_invite_payload, components=rest_invite_logic_impl._components
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invite", [mock.MagicMock(invites.Invite, code="AAAAAAAAAAAAAAAA"), "AAAAAAAAAAAAAAAA"])
    async def test_delete_invite(self, rest_invite_logic_impl, invite):
        rest_invite_logic_impl._session.delete_invite.return_value = ...
        assert await rest_invite_logic_impl.delete_invite(invite) is None
        rest_invite_logic_impl._session.delete_invite.assert_called_once_with(invite_code="AAAAAAAAAAAAAAAA")

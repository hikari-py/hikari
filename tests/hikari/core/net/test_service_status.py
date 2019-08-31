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

import dataclasses

import asynctest
import pytest

from hikari.core.model import service_status as status_model
from hikari.core.net import service_status
from tests.hikari.core.testdata import *

_base = "https://status.discordapp.com/api/v2"


def _get_data(name):
    return with_test_data(raw(f"service_status_{name}.json"))


endpoints = {
    f"{_base}/scheduled-maintenances/active.json": _get_data("active_scheduled_maintenances"),
    f"{_base}/components.json": _get_data("components"),
    f"{_base}/incidents.json": _get_data("incidents"),
    f"{_base}/scheduled-maintenances.json": _get_data("scheduled_maintenances"),
    f"{_base}/status.json": _get_data("status"),
    f"{_base}/summary.json": _get_data("summary"),
    f"{_base}/incidents/unresolved.json": _get_data("unresolved"),
    f"{_base}/scheduled-maintenances/upcoming.json": _get_data("upcoming"),
    f"{_base}/subscribers.json": _get_data("subscriber"),
    f"{_base}/subscribers/1a2b3c.json": _get_data("subscriber"),
    f"{_base}/subscriptions/1a2b3c/resend_confirmation": "{}",
}


@dataclasses.dataclass
class Response:
    body: str

    async def json(self):
        return libjson.loads(self.body)

    def raise_for_status(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class Router:
    def __call__(self, method, uri, **kwargs):
        return Response(endpoints[uri])


@pytest.fixture
def patched_request():
    # Forces us to use a dummy router rather than hitting discord directly.
    router = Router()
    with asynctest.patch("aiohttp.request", new=router):
        yield router


@pytest.mark.asyncio
@pytest.mark.model
class TestServiceStatus:
    async def test_get_status(self, patched_request):
        assert isinstance(await service_status.get_status(), status_model.Status)

    async def test_get_summary(self, patched_request):
        assert isinstance(await service_status.get_summary(), status_model.Summary)

    async def test_get_components(self, patched_request):
        assert isinstance(await service_status.get_components(), status_model.Components)

    async def test_get_all_incidents(self, patched_request):
        assert isinstance(await service_status.get_all_incidents(), status_model.Incidents)

    async def test_get_unresolved_incidents(self, patched_request):
        assert isinstance(await service_status.get_unresolved_incidents(), status_model.Incidents)

    async def test_get_all_scheduled_maintenances(self, patched_request):
        assert isinstance(await service_status.get_all_scheduled_maintenances(), status_model.ScheduledMaintenances)

    async def test_get_upcoming_scheduled_maintenances(self, patched_request):
        assert isinstance(
            await service_status.get_upcoming_scheduled_maintenances(), status_model.ScheduledMaintenances
        )

    async def test_get_active_scheduled_maintenances(self, patched_request):
        assert isinstance(await service_status.get_active_scheduled_maintenances(), status_model.ScheduledMaintenances)

    async def test_subscribe_email_to_all_incidents(self, patched_request):
        assert isinstance(await service_status.subscribe_email_to_all_incidents("foo@bar.com"), status_model.Subscriber)

    async def test_subscribe_email_to_incidents(self, patched_request):
        subscription = await service_status.subscribe_email_to_incident("foo@bar.com", "1a2b3c")
        assert isinstance(subscription, status_model.Subscriber)

    async def test_subscribe_webhook_to_all_incidents(self, patched_request):
        assert isinstance(
            await service_status.subscribe_webhook_to_all_incidents("foo@bar.com", "localhost:8080/lol"),
            status_model.Subscriber,
        )

    async def test_subscribe_webhook_to_incidents(self, patched_request):
        assert isinstance(
            await service_status.subscribe_webhook_to_incident("foo@bar.com", "localhost:8080/lol", "1a2b3c"),
            status_model.Subscriber,
        )

    async def test_unsubscribe(self, patched_request):
        assert await service_status.unsubscribe_from("1a2b3c") is None

    async def test_resend_confirmation_email(self, patched_request):
        assert await service_status.resend_confirmation_email("1a2b3c") is None

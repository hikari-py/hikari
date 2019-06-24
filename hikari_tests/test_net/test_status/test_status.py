#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dataclasses
import json
import os

import asynctest
import pytest

from hikari.net import status


def _parse(path):
    with open(os.path.join("hikari_tests", "test_net", "test_status", path)) as fp:
        return fp.read()


endpoints = {
    "https://status.discordapp.com/api/v2/scheduled-maintenances/active.json": _parse("active.json"),
    "https://status.discordapp.com/api/v2/components.json": _parse("components.json"),
    "https://status.discordapp.com/api/v2/incidents.json": _parse("incidents.json"),
    "https://status.discordapp.com/api/v2/scheduled-maintenances.json": _parse("scheduled-maintenances.json"),
    "https://status.discordapp.com/api/v2/status.json": _parse("status.json"),
    "https://status.discordapp.com/api/v2/summary.json": _parse("summary.json"),
    "https://status.discordapp.com/api/v2/incidents/unresolved.json": _parse("unresolved.json"),
    "https://status.discordapp.com/api/v2/scheduled-maintenances/upcoming.json": _parse("upcoming.json"),
    "https://status.discordapp.com/api/v2/subscribers.json": _parse("subscriber.json"),
    "https://status.discordapp.com/api/v2/subscribers/1a2b3c.json": _parse("subscriber.json"),
    "https://status.discordapp.com/api/v2/subscriptions/1a2b3c/resend_confirmation": "{}",
}


@dataclasses.dataclass
class Response:
    body: str

    async def json(self):
        return json.loads(self.body)

    def raise_for_status(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class Router:
    def __call__(self, method, uri, **kwargs):
        print("(MOCKED)", method.upper(), uri, "w kwargs", kwargs)
        return Response(endpoints[uri])


@pytest.fixture
def patched_request():
    # Forces us to use a dummy router rather than hitting discord directly.
    router = Router()
    with asynctest.patch("aiohttp.request", new=router):
        yield router


# If dacite can parse the responses, we don't care. Everything else is validated already.


@pytest.mark.asyncio
async def test_get_status(patched_request):
    assert isinstance(await status.get_status(), status.Status)


@pytest.mark.asyncio
async def test_get_summary(patched_request):
    assert isinstance(await status.get_summary(), status.Summary)


@pytest.mark.asyncio
async def test_get_components(patched_request):
    assert isinstance(await status.get_components(), status.Components)


@pytest.mark.asyncio
async def test_get_all_incidents(patched_request):
    assert isinstance(await status.get_all_incidents(), status.Incidents)


@pytest.mark.asyncio
async def test_get_unresolved_incidents(patched_request):
    assert isinstance(await status.get_unresolved_incidents(), status.Incidents)


@pytest.mark.asyncio
async def test_get_all_scheduled_maintenances(patched_request):
    assert isinstance(await status.get_all_scheduled_maintenances(), status.ScheduledMaintenances)


@pytest.mark.asyncio
async def test_get_upcoming_scheduled_maintenances(patched_request):
    assert isinstance(await status.get_upcoming_scheduled_maintenances(), status.ScheduledMaintenances)


@pytest.mark.asyncio
async def test_get_active_scheduled_maintenances(patched_request):
    assert isinstance(await status.get_active_scheduled_maintenances(), status.ScheduledMaintenances)


@pytest.mark.asyncio
async def test_get_active_scheduled_maintenances(patched_request):
    assert isinstance(await status.get_active_scheduled_maintenances(), status.ScheduledMaintenances)


@pytest.mark.asyncio
async def test_subscribe_email_to_all_incidents(patched_request):
    assert isinstance(await status.subscribe_email_to_all_incidents("foo@bar.com"), status.Subscriber)


@pytest.mark.asyncio
async def test_subscribe_email_to_incidents(patched_request):
    assert isinstance(await status.subscribe_email_to_incident("foo@bar.com", "1a2b3c"), status.Subscriber)


@pytest.mark.asyncio
async def test_subscribe_webhook_to_all_incidents(patched_request):
    assert isinstance(
        await status.subscribe_webhook_to_all_incidents("foo@bar.com", "localhost:8080/lol"), status.Subscriber
    )


@pytest.mark.asyncio
async def test_subscribe_webhook_to_incidents(patched_request):
    assert isinstance(
        await status.subscribe_webhook_to_incident("foo@bar.com", "localhost:8080/lol", "1a2b3c"), status.Subscriber
    )


@pytest.mark.asyncio
async def test_unsubscribe(patched_request):
    assert await status.unsubscribe_from("1a2b3c") is None


@pytest.mark.asyncio
async def test_resend_confirmation_email(patched_request):
    assert await status.resend_confirmation_email("1a2b3c") is None

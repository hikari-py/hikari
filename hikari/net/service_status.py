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
"""
Retrieves the status of Discord systems, and can subscribe to update lists via Email and webhooks.

Note:
    This API is not overly well documented, and the API documentation does not directly tarry up with the API
    specification. Thus, some details may be undocumented or omitted or incorrect.

See:
    https://status.discordapp.com/api/v2
"""
from __future__ import annotations

import typing

import aiohttp

from hikari.model import service_status

_BASE_URI = "https://status.discordapp.com/api/v2"


def _parse(data, to):
    if to is not None:
        return to.from_dict(data)
    return None


def _get_as_id_or_get_id(obj: typing.Any):
    return obj if isinstance(obj, str) else obj.id


async def _request(method, path, to, data=None):
    async with aiohttp.request(method, _BASE_URI + path, data=data) as resp:
        resp.raise_for_status()
        return _parse(await resp.json(), to)


async def _get(path, to):
    return await _request("get", path, to)


async def _post(path, to, data):
    return await _request("post", path, to, data)


async def _delete(path, to):
    return await _request("delete", path, to)


async def get_summary() -> service_status.Summary:
    """
    Returns:
        The overall API summary.
    """
    return await _get("/summary.json", service_status.Summary)


async def get_status() -> service_status.Status:
    """
    Returns:
        The overall API status.
    """
    return await _get("/status.json", service_status.Status)


async def get_components() -> service_status.Components:
    """
    Returns:
        The status of any components.
    """
    return await _get("/components.json", service_status.Components)


async def get_all_incidents() -> service_status.Incidents:
    """
    Returns:
        The status of all incidents.
    """
    return await _get("/incidents.json", service_status.Incidents)


async def get_unresolved_incidents() -> service_status.Incidents:
    """
    Returns:
        The status of any unresolved incidents.
    """
    return await _get("/incidents/unresolved.json", service_status.Incidents)


async def get_all_scheduled_maintenances() -> service_status.ScheduledMaintenances:
    """
    Returns:
        All scheduled maintenances.
    """
    return await _get("/scheduled-maintenances.json", service_status.ScheduledMaintenances)


async def get_upcoming_scheduled_maintenances() -> service_status.ScheduledMaintenances:
    """
    Returns:
        All upcoming scheduled maintenances.
    """
    return await _get("/scheduled-maintenances/upcoming.json", service_status.ScheduledMaintenances)


async def get_active_scheduled_maintenances() -> service_status.ScheduledMaintenances:
    """
    Returns:
        All active scheduled maintenances.
    """
    return await _get("/scheduled-maintenances/active.json", service_status.ScheduledMaintenances)


async def subscribe_email_to_all_incidents(email: str) -> service_status.Subscriber:
    """
    Subscribe an email address to all ongoing incidents.

    Args:
        email:
            the owner's email.
        incident:
            the incident or incident ID.

    Returns:
        A :class:`Subscription`.

    Note:
        If the result specifies that you need to confirm your email address, any other requests will return a
        `422 Unprocessable Entity` which will result in an `aiohttp.ClientResponseError` being raised.
    """
    result = await _post("/subscribers.json", service_status.Subscription, {"subscriber[email]": email})
    return result.subscriber


async def subscribe_email_to_incident(
    email: str, incident: typing.Union[str, service_status.Incident, service_status.ScheduledMaintenance]
) -> service_status.Subscriber:
    """
    Subscribe an email address to a given incident.

    Args:
        email:
            the owner's email.
        incident:
            the incident or incident ID.

    Returns:
        A :class:`Subscription`.

    Note:
        If the result specifies that you need to confirm your email address, any other requests will return a
        `422 Unprocessable Entity` which will result in an `aiohttp.ClientResponseError` being raised.
    """
    incident = _get_as_id_or_get_id(incident)
    result = await _post(
        "/subscribers.json", service_status.Subscription, {"subscriber[email]": email, "subscriber[incident]": incident}
    )
    return result.subscriber


async def subscribe_webhook_to_all_incidents(email: str, endpoint: str) -> service_status.Subscriber:
    """
    Subscribe a webhook to all ongoing incidents.

    Args:
        email:
            the owner's email.
        endpoint:
            the endpoint webhook to send to.

    Returns:
        A :class:`Subscription`.

    Note:
        If the result specifies that you need to confirm your email address, any other requests will return a
        `422 Unprocessable Entity` which will result in an `aiohttp.ClientResponseError` being raised.
    """
    result = await _post(
        "/subscribers.json", service_status.Subscription, {"subscriber[email]": email, "subscriber[endpoint]": endpoint}
    )
    return result.subscriber


async def subscribe_webhook_to_incident(
    email: str, endpoint: str, incident: typing.Union[str, service_status.Incident, service_status.ScheduledMaintenance]
) -> service_status.Subscriber:
    """
    Subscribe a webhook to a given incident.

    Args:
        email:
            the owner's email.
        endpoint:
            the endpoint webhook to send to.
        incident:
            the incident or incident ID.

    Returns:
        A :class:`Subscription`.

    Note:
        If the result specifies that you need to confirm your email address, any other requests will return a
        `422 Unprocessable Entity` which will result in an `aiohttp.ClientResponseError` being raised.
    """
    incident = _get_as_id_or_get_id(incident)
    result = await _post(
        "/subscribers.json",
        service_status.Subscription,
        {"subscriber[email]": email, "subscriber[incident]": incident, "subscriber[endpoint]": endpoint},
    )
    return result.subscriber


async def unsubscribe_from(subscriber: typing.Union[str, service_status.Subscriber]) -> None:
    """
    Unsubscribe from the given subscription ID or object.
    """
    subscriber = _get_as_id_or_get_id(subscriber)
    await _delete(f"/subscribers/{subscriber}.json", None)


async def resend_confirmation_email(subscriber: typing.Union[str, service_status.Subscriber]) -> None:
    """
    Request that the confirmation for the given subscription ID or object is resent.
    """
    subscriber = _get_as_id_or_get_id(subscriber)
    await _post(f"/subscriptions/{subscriber}/resend_confirmation", None, None)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retrieves the status of Discord systems, and can subscribe to update lists via Email and webhooks.

Note:
    This API is not overly well documented, and the API documentation does not directly tarry up with the API
    specification. Thus, some details may be undocumented or omitted or incorrect.

See:
    https://status.discordapp.com/api/v2
"""
import abc
import dataclasses
import datetime
import typing

import aiohttp
import dacite
import dateutil.parser

_BASE_URI = "https://status.discordapp.com/api/v2"


class _AnyID(metaclass=abc.ABCMeta):
    """
    Base class for anything with an ID.
    """

    id: str


@dataclasses.dataclass(frozen=True)
class Subscriber(_AnyID):
    """
    A subscription to an incident.
    """

    email: str
    mode: str
    quarantined_at: typing.Optional[datetime.datetime] = None
    incident: typing.Optional[str] = None
    skip_confirmation_notification: typing.Optional[bool] = None
    purge_at: typing.Optional[datetime.datetime] = None


@dataclasses.dataclass(frozen=True)
class _Subscription:
    subscriber: Subscriber


@dataclasses.dataclass(frozen=True)
class Page(_AnyID):
    """
    A page element.
    """

    name: str
    url: str
    updated_at: datetime.datetime


@dataclasses.dataclass(frozen=True)
class Status:
    """
    A status description.
    """

    indicator: typing.Optional[str] = None
    description: typing.Optional[str] = None


@dataclasses.dataclass(frozen=True)
class Component(_AnyID):
    """
    A component description.
    """

    name: str
    created_at: datetime.datetime
    page_id: str
    position: int
    updated_at: datetime.datetime
    description: typing.Optional[str] = None


@dataclasses.dataclass(frozen=True)
class Components:
    """
    A collection of :class:`Component` objects.
    """

    page: Page
    components: typing.List[Component]


@dataclasses.dataclass(frozen=True)
class IncidentUpdate:
    """
    An informative status update for a specific incident.
    """

    body: str
    created_at: datetime.datetime
    display_at: typing.Optional[datetime.datetime]
    incident_id: str
    status: str
    id: str
    updated_at: typing.Optional[datetime.datetime]


@dataclasses.dataclass(frozen=True)
class Incident(_AnyID):
    """
    An incident.
    """

    name: str
    impact: str
    incident_updates: typing.List[IncidentUpdate]
    monitoring_at: typing.Optional[datetime.datetime]
    page_id: str
    resolved_at: typing.Optional[datetime.datetime]
    shortlink: str
    status: str
    updated_at: datetime.datetime


@dataclasses.dataclass(frozen=True)
class Incidents:
    """
    A collection of :class:`Incident` objects.
    """

    page: Page
    incidents: typing.List[Incident]


@dataclasses.dataclass(frozen=True)
class ScheduledMaintenance(_AnyID):
    """
    A description of a maintenance that is scheduled to be performed.
    """

    name: str
    impact: str
    incident_updates: typing.List[IncidentUpdate]
    monitoring_at: typing.Optional[datetime.datetime]
    name: str
    page_id: str
    resolved_at: typing.Optional[datetime.datetime]
    scheduled_for: typing.Optional[datetime.datetime]
    scheduled_until: typing.Optional[datetime.datetime]
    status: str
    updated_at: datetime.datetime


@dataclasses.dataclass(frozen=True)
class ScheduledMaintenances:
    """
    A collection of maintenance events.
    """

    page: Page
    scheduled_maintenances: typing.List[ScheduledMaintenance]


@dataclasses.dataclass(frozen=True)
class Summary:
    """
    A description of the overall API status.
    """

    page: Page
    status: Status
    components: typing.List[Component]
    incidents: typing.List[Incident]
    scheduled_maintenances: typing.List[ScheduledMaintenance]


def _parse(data, to):
    if to is not None:
        config = dacite.Config(
            type_hooks={
                # pypi doesn't support datetime.datetime.fromisoformat, nor does python3.6
                datetime.datetime: dateutil.parser.parse
            }
        )
        return dacite.from_dict(to, data, config=config)
    return None


def _get_as_id_or_get_id(obj: typing.Union[str, _AnyID]):
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


async def get_summary() -> Summary:
    """
    Returns:
        The overall API summary.
    """
    return await _get("/summary.json", Summary)


async def get_status() -> Status:
    """
    Returns:
        The overall API status.
    """
    return await _get("/status.json", Status)


async def get_components() -> Components:
    """
    Returns:
        The status of any components.
    """
    return await _get("/components.json", Components)


async def get_all_incidents() -> Incidents:
    """
    Returns:
        The status of all incidents.
    """
    return await _get("/incidents.json", Incidents)


async def get_unresolved_incidents() -> Incidents:
    """
    Returns:
        The status of any unresolved incidents.
    """
    return await _get("/incidents/unresolved.json", Incidents)


async def get_all_scheduled_maintenances() -> ScheduledMaintenances:
    """
    Returns:
        All scheduled maintenances.
    """
    return await _get("/scheduled-maintenances.json", ScheduledMaintenances)


async def get_upcoming_scheduled_maintenances() -> ScheduledMaintenances:
    """
    Returns:
        All upcoming scheduled maintenances.
    """
    return await _get("/scheduled-maintenances/upcoming.json", ScheduledMaintenances)


async def get_active_scheduled_maintenances() -> ScheduledMaintenances:
    """
    Returns:
        All active scheduled maintenances.
    """
    return await _get("/scheduled-maintenances/active.json", ScheduledMaintenances)


async def subscribe_email_to_all_incidents(email: str) -> Subscriber:
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
    result = await _post("/subscribers.json", _Subscription, {"subscriber[email]": email})
    return result.subscriber


async def subscribe_email_to_incident(
    email: str, incident: typing.Union[str, Incident, ScheduledMaintenance]
) -> Subscriber:
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
        "/subscribers.json", _Subscription, {"subscriber[email]": email, "subscriber[incident]": incident}
    )
    return result.subscriber


async def subscribe_webhook_to_all_incidents(email: str, endpoint: str) -> Subscriber:
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
        "/subscribers.json", _Subscription, {"subscriber[email]": email, "subscriber[endpoint]": endpoint}
    )
    return result.subscriber


async def subscribe_webhook_to_incident(
    email: str, endpoint: str, incident: typing.Union[str, Incident, ScheduledMaintenance]
) -> Subscriber:
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
        _Subscription,
        {"subscriber[email]": email, "subscriber[incident]": incident, "subscriber[endpoint]": endpoint},
    )
    return result.subscriber


async def unsubscribe_from(subscriber: typing.Union[str, Subscriber]) -> None:
    """
    Unsubscribe from the given subscription ID or object.
    """
    subscriber = _get_as_id_or_get_id(subscriber)
    await _delete(f"/subscribers/{subscriber}.json", None)


async def resend_confirmation_email(subscriber: typing.Union[str, Subscriber]) -> None:
    """
    Request that the confirmation for the given subscription ID or object is resent.
    """
    subscriber = _get_as_id_or_get_id(subscriber)
    await _post(f"/subscriptions/{subscriber}/resend_confirmation", None, None)

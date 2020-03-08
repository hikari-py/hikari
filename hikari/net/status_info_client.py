#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""API status information.

Retrieves the status of Discord systems, and can subscribe to update lists via
Email and webhooks.

Notes
-----
    This API is not overly well documented on a low level, and the API
    documentation often does not directly tarry up with the underlying
    specification. Thus, some details may be undocumented or omitted or
    incorrect. If you notice anything that may be erroneous, please file a
    ticket on the bug tracker at https://gitlab.com/nekokatt/hikari/issues.

See
---
https://status.discordapp.com/api/v2
"""
from __future__ import annotations

__all__ = [
    "Subscriber",
    "Page",
    "Status",
    "Component",
    "ComponentsPage",
    "IncidentUpdate",
    "Incident",
    "IncidentsPage",
    "ScheduledMaintenance",
    "ScheduledMaintenancesPage",
    "Summary",
    "StatusPage",
    "StatusInfoClient",
]

import dataclasses
import typing

from hikari.internal_utilities import cache
from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.internal_utilities import transformations
from hikari.internal_utilities import type_hints
from hikari.net import base_http_client

if typing.TYPE_CHECKING:
    import asyncio
    import datetime
    import ssl

    import aiohttp.typedefs

T = typing.TypeVar("T")


@dataclasses.dataclass()
class Subscriber:
    """A subscription to an incident."""

    __slots__ = (
        "id",
        "email",
        "mode",
        "created_at",
        "quarantined_at",
        "incident",
        "is_skipped_confirmation_notification",
        "purge_at",
    )

    #: The ID of the subscriber.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str

    #: The email address of the subscription.
    #:
    #: :type: :class:`str`
    email: str

    #: The mode of the subscription.
    #:
    #: :type: :class:`str`
    mode: str

    #: The date/time the description was created at.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: The date/time the description was quarantined at, if applicable.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    quarantined_at: typing.Optional[datetime.datetime]

    #: The optional incident that this subscription is for.
    #:
    #: :type: :class:`hikari.core.models.Incident` or `None`
    incident: typing.Optional[Incident]

    #: True if the confirmation notification is skipped.
    #:
    #: :type: :class:`bool` or `None`
    is_skipped_confirmation_notification: typing.Optional[bool]

    #: The optional date/time to stop the subscription..
    #:
    #: :type: :class:`datetime.datetime` or `None`
    purge_at: typing.Optional[datetime.datetime]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> Subscriber:
        payload = payload["subscriber"]

        return Subscriber(
            id=payload["id"],
            email=payload["email"],
            mode=payload["mode"],
            created_at=dates.parse_iso_8601_ts(payload["created_at"]),
            quarantined_at=transformations.nullable_cast(payload.get("quarantined_at"), dates.parse_iso_8601_ts),
            incident=transformations.nullable_cast(payload.get("incident"), Incident.from_dict),
            is_skipped_confirmation_notification=transformations.nullable_cast(
                payload.get("skip_confirmation_notification"), bool
            ),
            purge_at=transformations.nullable_cast(payload.get("purge_at"), dates.parse_iso_8601_ts),
        )


@dataclasses.dataclass()
class Page:
    """
    A page element.
    """

    __slots__ = ("id", "name", "url", "updated_at")

    #: The ID of the page.
    #:
    #: :type: :class:`str`
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str

    #: The name of the page.
    #:
    #: :type: :class:`str`
    name: str

    #: A permalink to the page.
    #:
    #: :type: :class:`str`
    url: str

    #: The date and time that the page was last updated at.
    #:
    #: :type: :class:`datetime.datetime`
    updated_at: datetime.datetime

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> Page:
        return Page(
            id=payload["id"],
            name=payload["name"],
            url=payload["url"],
            updated_at=transformations.nullable_cast(payload.get("updated_at"), dates.parse_iso_8601_ts),
        )


@dataclasses.dataclass()
class Status:
    """
    A status description.
    """

    __slots__ = ("indicator", "description")

    #: The indicator that specifies the state of the service.
    #:
    #: :type: :class:`str` or `None`
    indicator: typing.Optional[str]

    #: The optional description of the service state.
    #:
    #: :type: :class:`str` or `None`
    description: typing.Optional[str]

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> Status:
        return Status(indicator=payload.get("indicator"), description=payload.get("description"))


@dataclasses.dataclass()
class Component:
    """A component description."""

    __slots__ = ("id", "name", "created_at", "page_id", "position", "updated_at", "description", "status")

    #: The ID of the component.
    #:
    #: :type: :class:`str` or `None`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str

    #: The name of the component.
    #:
    #: :type: :class:`str`
    name: str

    #: The date and time the component came online for the first time.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: The ID of the status page for this component.
    #:
    #: :type: :class:`str`
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    page_id: str

    #: The position of the component in the list of components.
    #:
    #: :type: :class:`int`
    position: int

    #: The date/time that this component last was updated at.
    #:
    #: :type: :class:`datetime.datetime`
    updated_at: datetime.datetime

    #: The optional description of the component.
    #:
    #: :type: :class:`str` or `None`
    description: typing.Optional[str]

    #: The status of this component.
    #:
    #: :type: :class:`str` or `None`
    status: typing.Optional[str]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> Component:
        return Component(
            id=payload["id"],
            name=payload["name"],
            created_at=transformations.nullable_cast(payload.get("created_at"), dates.parse_iso_8601_ts),
            page_id=payload["page_id"],
            position=transformations.nullable_cast(payload.get("position"), int),
            updated_at=transformations.nullable_cast(payload.get("updated_at"), dates.parse_iso_8601_ts),
            description=payload.get("description"),
            status=payload.get("status"),
        )


@dataclasses.dataclass()
class ComponentsPage:
    """A collection of :class:`Component` objects."""

    __slots__ = ("page", "components")

    #: The page for this list of components.
    #:
    #: :type: :class:`Page`
    page: Page

    #: The list of components.
    #:
    #: :type: :class:`typing.Sequence` of :class:`Component`
    components: typing.Sequence[Component]

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> ComponentsPage:
        return ComponentsPage(
            page=Page.from_dict(payload["page"]),
            components=[Component.from_dict(c) for c in payload.get("components", [])],
        )


@dataclasses.dataclass()
class IncidentUpdate:
    """
    An informative status update for a specific incident.
    """

    __slots__ = ("body", "created_at", "display_at", "incident_id", "status", "id", "updated_at")

    #: The ID of this incident update.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str

    #: The content in this update.
    #:
    #: :type: :class:`str`
    body: str

    #: Time and date the incident update was made at.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: The date/time to display the update at.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    display_at: typing.Optional[datetime.datetime]

    #: The ID of the corresponding incident.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    incident_id: str

    #: The status of the service during this incident update.
    #:
    #: :type: :class:`str`
    status: str

    #: The date/time that the update was last changed.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    updated_at: typing.Optional[datetime.datetime]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> IncidentUpdate:
        return IncidentUpdate(
            id=payload["id"],
            body=payload["body"],
            created_at=transformations.nullable_cast(payload.get("created_at"), dates.parse_iso_8601_ts),
            display_at=transformations.nullable_cast(payload.get("display_at"), dates.parse_iso_8601_ts),
            incident_id=payload["incident_id"],
            status=payload["status"],
            updated_at=transformations.nullable_cast(payload.get("updated_at"), dates.parse_iso_8601_ts),
        )


@dataclasses.dataclass()
class Incident:
    """An incident."""

    __slots__ = (
        "id",
        "name",
        "impact",
        "incident_updates",
        "created_at",
        "monitoring_at",
        "page_id",
        "resolved_at",
        "shortlink",
        "status",
        "updated_at",
        "started_at",
    )

    #: The ID of the incident.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str

    #: The name of the incident.
    #:
    #: :type: :class:`str`
    name: str

    #: The impact of the incident.
    #:
    #: :type: :class:`str`
    impact: str

    #: A mapping of zero or more updates to the status of this incident. This maps the
    #: update ID to the update data.
    #:
    #: :type: :class:`typing.Mapping` [ :obj:`str`, :obj:`IncidentUpdate` ]
    incident_updates: typing.Mapping[str, IncidentUpdate]

    #: The date and time, if applicable, that the faulty component(s) were created at.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: The date and time, if applicable, that the faulty component(s) were being monitored at.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    monitoring_at: typing.Optional[datetime.datetime]

    #: The ID of the page describing this incident.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    page_id: str

    #: The date and time that the incident finished, if applicable.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    resolved_at: typing.Optional[datetime.datetime]

    #: A short permalink to the page describing the incident.
    #:
    #: :type: :class:`str`
    shortlink: str

    #: The incident status.
    #:
    #: :type: :class:`str`
    status: str

    #: The last time the status of the incident was updated.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    updated_at: typing.Optional[datetime.datetime]

    #: The date and time, if applicable, that the faulty component(s) began to malfunction.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    started_at: typing.Optional[datetime.datetime]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> Incident:
        updates = (IncidentUpdate.from_dict(i) for i in payload.get("incident_updates", containers.EMPTY_SEQUENCE))

        return Incident(
            id=payload["id"],
            name=payload["name"],
            status=payload["status"],
            created_at=transformations.try_cast(payload["created_at"], dates.parse_iso_8601_ts),
            updated_at=transformations.try_cast(payload.get("updated_at"), dates.parse_iso_8601_ts),
            incident_updates={u.id: u for u in updates},
            monitoring_at=transformations.try_cast(payload.get("monitoring_at"), dates.parse_iso_8601_ts),
            resolved_at=transformations.try_cast(payload.get("resolved_at"), dates.parse_iso_8601_ts),
            shortlink=payload["shortlink"],
            page_id=payload["page_id"],
            impact=payload["impact"],
            started_at=transformations.try_cast(payload.get("started_at"), dates.parse_iso_8601_ts),
        )


@dataclasses.dataclass()
class IncidentsPage:
    """A collection of :class:`Incident` objects."""

    __slot__ = ("page", "incidents", "_cp_unresolved_incidents", "_cp_resolved_incidents")

    #: The page listing the incidents.
    #:
    #: :type: :class:`Page`
    page: Page

    #: The incidents on the page.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`str`, :obj:`Incident` ]
    incidents: typing.Mapping[str, Incident]

    @cache.cached_property()
    def unresolved_incidents(self) -> typing.Mapping[str, Incident]:
        return {
            i.id: i
            for i in self.incidents.values()
            if i.status.lower() in ("investigating", "identified", "monitoring")
        }

    @cache.cached_property()
    def resolved_incidents(self) -> typing.Mapping[str, Incident]:
        return {i.id: i for i in self.incidents.values() if i.status.lower() in ("resolved", "postmortem")}

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> IncidentsPage:
        incidents = (Incident.from_dict(i) for i in payload["incidents"])
        return IncidentsPage(Page.from_dict(payload["page"]), {incident.id: incident for incident in incidents})


@dataclasses.dataclass()
class ScheduledMaintenance:
    """A description of a maintenance that is scheduled to be performed."""

    __slots__ = (
        "id",
        "name",
        "impact",
        "incident_updates",
        "created_at",
        "monitoring_at",
        "page_id",
        "resolved_at",
        "scheduled_for",
        "scheduled_until",
        "status",
        "updated_at",
        "started_at",
        "shortlink",
    )

    #: The ID of the entry.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str

    #: The name of the entry.
    #:
    #: :type: :class:`str`
    name: str

    #: The impact of the entry.
    #:
    #: :type: :class:`str`
    impact: str

    #: Zero or more updates to this event. This maps the update ID to the update data.
    #:
    #: :type: :obj:`typing.Mapping` [ `:obj:`str`, :obj:`IncidentUpdate` ]
    incident_updates: typing.Mapping[str, IncidentUpdate]

    #: The date and time the event was created at.
    #:
    #: :type: :class:`datetime.datetime`
    created_at: datetime.datetime

    #: The date and time the event was being monitored since, if applicable.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    monitoring_at: typing.Optional[datetime.datetime]

    #: The ID of the page describing this event.
    #:
    #: :type: :class:`str`
    #:
    #: Warning:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    page_id: str

    #: The optional date/time the event finished at.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    resolved_at: typing.Optional[datetime.datetime]

    #: The date/time that the event was scheduled for.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    scheduled_for: typing.Optional[datetime.datetime]

    #: The date/time that the event was scheduled until.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    scheduled_until: typing.Optional[datetime.datetime]

    #: The status of the event.
    #:
    #: :type: :class:`str`
    status: str

    #: The date/time that the event was last updated at.
    #:
    #: :type: :class:`datetime.datetime`
    updated_at: datetime.datetime

    #: The URL to the status page for more details.
    #:
    #: :type: :class:`str`
    shortlink: str

    #: The date and time, if applicable, that the event began.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    started_at: typing.Optional[datetime.datetime]

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> ScheduledMaintenance:
        updates = (IncidentUpdate.from_dict(iu) for iu in payload.get("incident_updates", containers.EMPTY_SEQUENCE))

        return ScheduledMaintenance(
            id=payload["id"],
            name=payload["name"],
            impact=payload["impact"],
            incident_updates={u.id: u for u in updates},
            monitoring_at=transformations.try_cast(payload.get("monitoring_at"), dates.parse_iso_8601_ts),
            page_id=payload["page_id"],
            resolved_at=transformations.try_cast(payload.get("resolved_at"), dates.parse_iso_8601_ts),
            scheduled_for=transformations.try_cast(payload.get("scheduled_for"), dates.parse_iso_8601_ts),
            scheduled_until=transformations.try_cast(payload.get("scheduled_until"), dates.parse_iso_8601_ts),
            status=payload["status"],
            updated_at=transformations.try_cast(payload.get("updated_at"), dates.parse_iso_8601_ts),
            created_at=transformations.try_cast(payload["created_at"], dates.parse_iso_8601_ts),
            shortlink=payload["shortlink"],
            started_at=transformations.try_cast(payload["started_at"], dates.parse_iso_8601_ts),
        )


@dataclasses.dataclass()
class ScheduledMaintenancesPage:
    """A collection of maintenance events."""

    __slots__ = ("page", "scheduled_maintenances")

    #: The page containing this information.
    #:
    #: :type: :class:`Page`
    page: Page

    #: The maintenance items on the page. Maps the entry ID to the information
    #: associated with it.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`str`, :class:`ScheduledMaintenance` ]
    scheduled_maintenances: typing.Mapping[str, ScheduledMaintenance]

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> ScheduledMaintenancesPage:
        maintenances = (ScheduledMaintenance.from_dict(sm) for sm in payload["scheduled_maintenances"])
        return ScheduledMaintenancesPage(
            page=Page.from_dict(payload["page"]), scheduled_maintenances={m.id: m for m in maintenances},
        )


@dataclasses.dataclass()
class StatusPage:
    """
    A description of the overall API status.
    """

    __slots__ = ("page", "status")

    #: The page describing this summary.
    #:
    #: :type: :class:`Page`
    page: Page

    #: The overall system status.
    #:
    #: :type: :class:`Status`
    status: Status

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> StatusPage:
        return StatusPage(page=Page.from_dict(payload["page"]), status=Status.from_dict(payload["status"]),)


@dataclasses.dataclass()
class Summary:
    """
    A summary of the API status.
    """

    __slots__ = (
        "page",
        "components",
        "incidents",
        "scheduled_maintenances",
        "_cp_unresolved_incidents",
        "_cp_resolved_incidents",
        "_cp_upcoming_scheduled_maintenances",
        "_cp_ongoing_scheduled_maintenances",
        "_cp_completed_scheduled_maintenances",
    )

    #: The page describing this summary.
    #:
    #: :type: :class:`Page`
    page: Page

    #: The status of each component in the system.
    #:
    #: :type: :class:`typing.Sequence` [ :class:`Component` ]
    components: typing.Sequence[Component]

    #: The list of incidents that have occurred/are occurring to components in this system.
    #:
    #: :type: :class:`typing.Sequence` [ :class:`Incident` ]
    incidents: typing.Sequence[Incident]

    #: A list of maintenance tasks that have been/will be undertaken.
    #:
    #: :type: :class:`typing.Sequence` [ :class:`ScheduledMaintenance` ]
    scheduled_maintenances: typing.Sequence[ScheduledMaintenance]

    @cache.cached_property()
    def unresolved_incidents(self) -> typing.Mapping[str, Incident]:
        look_for = ("investigating", "identified", "monitoring")
        return {i.id: i for i in self.incidents if i.status.lower() in look_for}

    @cache.cached_property()
    def resolved_incidents(self) -> typing.Mapping[str, Incident]:
        look_for = ("resolved", "postmortem")
        return {i.id: i for i in self.incidents if i.status.lower() in look_for}

    @cache.cached_property()
    def upcoming_scheduled_maintenances(self) -> typing.Mapping[str, ScheduledMaintenance]:
        look_for = ("scheduled",)
        return {sm.id: sm for sm in self.scheduled_maintenances if sm.status.lower() in look_for}

    @cache.cached_property()
    def ongoing_scheduled_maintenances(self) -> typing.Mapping[str, ScheduledMaintenance]:
        look_for = ("in progress", "verifying")
        return {sm.id: sm for sm in self.scheduled_maintenances if sm.status.lower() in look_for}

    @cache.cached_property()
    def completed_scheduled_maintenances(self) -> typing.Mapping[str, ScheduledMaintenance]:
        look_for = ("completed",)
        return {sm.id: sm for sm in self.scheduled_maintenances if sm.status.lower() in look_for}

    @staticmethod
    def from_dict(payload: type_hints.JSONObject) -> Summary:
        return Summary(
            page=Page.from_dict(payload["page"]),
            scheduled_maintenances=[
                ScheduledMaintenance.from_dict(sm)
                for sm in payload.get("scheduled_maintenances", containers.EMPTY_SEQUENCE)
            ],
            incidents=[Incident.from_dict(i) for i in payload.get("incidents", containers.EMPTY_SEQUENCE)],
            components=[Component.from_dict(c) for c in payload.get("components", containers.EMPTY_SEQUENCE)],
        )


class StatusInfoClient(base_http_client.BaseHTTPClient):
    """A generic client to allow you to check the current status of Discord's
    services.

    Warnings
    --------
    This must be initialized within a coroutine while an event loop is active
    and registered to the current thread.
    """

    __slots__ = ("url",)

    @typing.overload
    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop = None,
        allow_redirects: bool = False,
        max_retries: int = 5,
        base_uri: str = None,
        json_unmarshaller: typing.Callable = None,
        connector: aiohttp.BaseConnector = None,
        proxy_headers: aiohttp.typedefs.LooseHeaders = None,
        proxy_auth: aiohttp.BasicAuth = None,
        proxy_url: str = None,
        ssl_context: ssl.SSLContext = None,
        verify_ssl: bool = True,
        timeout: float = None,
    ) -> None:
        ...

    def __init__(self, **kwargs):
        """
        Args:
            allow_redirects:
                defaults to False for security reasons. If you find you are receiving multiple redirection responses
                causing requests to fail, it is probably worth enabling this.
            base_uri:
                optional HTTP API base URI to hit. If unspecified, this defaults to Discord's API URI. This exists for
                the purpose of mocking for functional testing. Any URI should NOT end with a trailing forward slash, and
                any instance of `{VERSION}` in the URL will be replaced.
            connector:
                the :class:`aiohttp.BaseConnector` to use for the client session, or `None` if you wish to use the
                default instead.
            json_unmarshaller:
                a callable that consumes a JSON-encoded string and returns a Python object.
                This defaults to :func:`json.loads`.
            loop:
                the asyncio event loop to run on.
            max_retries:
                The max number of times to retry in certain scenarios before giving up on making the request.
            proxy_auth:
                optional proxy authentication to use.
            proxy_headers:
                optional proxy headers to pass.
            proxy_url:
                optional proxy URL to use.
            ssl_context:
                optional SSL context to use.
            verify_ssl:
                defaulting to True, setting this to false will disable SSL verification.
            timeout:
                optional timeout to apply to individual HTTP requests.
            url:
                the URL to use for StatusPage's API to. If unspecified, it uses the default URL you generally want
                to be using.
        """
        self.url = f"https://status.discordapp.com/api/v{self.version}" if "url" not in kwargs else kwargs.pop("url")
        super().__init__(**kwargs)

    @property
    def version(self) -> int:
        return 2

    async def _perform_request(self, route: str, cast: typing.Optional[typing.Type[T]], data=None, method=None) -> T:
        coro = super()._request(method or self.GET, self.url + route, data=data)

        async with coro as resp:
            self.logger.debug(
                "%s %s returned %s %s type %s", method, resp.real_url, resp.status, resp.reason, resp.content_type,
            )
            # TODO: use errors types instead of aiohttp ones.
            resp.raise_for_status()
            data = await resp.json()

        return cast.from_dict(data) if cast else None

    async def fetch_summary(self) -> Summary:
        """Fetch the overall service summary."""
        return await self._perform_request("/summary.json", Summary)

    async def fetch_status(self) -> StatusPage:
        """Fetch the overall service status."""
        return await self._perform_request("/status.json", StatusPage)

    async def fetch_components(self) -> ComponentsPage:
        """Fetch information on the status of all API components."""
        return await self._perform_request("/components.json", ComponentsPage)

    async def fetch_all_incidents(self) -> IncidentsPage:
        """Fetch information on all incidents both past and present."""
        return await self._perform_request("/incidents.json", IncidentsPage)

    async def fetch_unresolved_incidents(self) -> IncidentsPage:
        """Fetch information on all incidents that are ongoing."""
        return await self._perform_request("/incidents/unresolved.json", IncidentsPage)

    async def fetch_all_scheduled_maintenances(self) -> ScheduledMaintenancesPage:
        """Fetch information on all scheduled maintenances both past, present, and future."""
        return await self._perform_request("/scheduled-maintenances.json", ScheduledMaintenancesPage)

    async def fetch_upcoming_scheduled_maintenances(self) -> ScheduledMaintenancesPage:
        """Fetch information on scheduled maintenances that are upcoming."""
        return await self._perform_request("/scheduled-maintenances/upcoming.json", ScheduledMaintenancesPage)

    async def fetch_active_scheduled_maintenances(self) -> ScheduledMaintenancesPage:
        """Fetch information on all ongoing scheduled maintenances."""
        return await self._perform_request("/scheduled-maintenances/active.json", ScheduledMaintenancesPage)

    async def subscribe_email_to_incidents(
        self, email: str, incident: typing.Optional[typing.Union[str, Incident]] = None,
    ) -> Subscriber:
        """
        Subscribe to a specific incident or all incidents for email updates.

        Args:
            email:
                The email address to send updates to.
            incident:
                If `None`, all updates for any incident will be sent. If an incident or incident ID,
                then only updates for that incident will be sent.

        Returns:
            a subscription definition that can be used later to unsubscribe from that update
            programmatically.
        """

        body = {"subscriber[email]": email}

        if incident is not None:
            body["subscriber[incident]"] = incident.id if isinstance(incident, Incident) else incident

        return await self._perform_request("/subscribers.json", Subscriber, body, self.POST)

    async def subscribe_webhook_to_incidents(
        self, url: str, incident: typing.Optional[typing.Union[str, Incident]] = None,
    ) -> Subscriber:
        """
        Subscribe to a specific incident or all incidents for webhook updates. This means the given
        webhook will be hit when an update occurs.

        Args:
            url:
                The webhook to hit.
            incident:
                If `None`, all updates for any incident will be sent. If an incident or incident ID,
                then only updates for that incident will be sent.

        Returns:
            a subscription definition that can be used later to unsubscribe from that update
            programmatically.
        """
        body = {"subscriber[endpoint]": url}

        if incident is not None:
            body["subscriber[incident]"] = incident.id if isinstance(incident, Incident) else incident

        return await self._perform_request("/subscribers.json", Subscriber, body, self.POST)

    async def unsubscribe(self, subscriber: typing.Union[str, Subscriber]) -> None:
        """
        Unsubscribe from a given subscription described by a subscription ID or subscriber object.

        Args:
            subscriber:
                Either a subscription ID or subscriber object.
        """
        sub_id = subscriber.id if isinstance(subscriber, Subscriber) else subscriber
        await self._perform_request(f"/subscribers/{sub_id}.json", None, None, self.DELETE)

    async def resend_confirmation_email(self, subscriber: typing.Union[str, Subscriber]) -> None:
        """
        Resend the confirmation email for a given subscriber ID or subscriber object.


        """
        sub_id = subscriber.id if isinstance(subscriber, Subscriber) else subscriber
        await self._perform_request(f"/subscribers/{sub_id}/resend_confirmation", None, None, self.POST)

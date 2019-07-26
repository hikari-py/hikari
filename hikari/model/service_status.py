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
Models for the Status API.
"""
from __future__ import annotations

__all__ = (
    "Subscriber",
    "Subscription",
    "Page",
    "Status",
    "Component",
    "Components",
    "IncidentUpdate",
    "Incident",
    "Incidents",
    "ScheduledMaintenance",
    "ScheduledMaintenances",
    "Summary",
)

import dataclasses
import datetime
import typing

from hikari.utils import dateutils, maps


@dataclasses.dataclass()
class Subscriber:
    """
    A subscription to an incident.
    """

    __slots__ = ("id", "email", "mode", "quarantined_at", "incident", "skip_confirmation_notification", "purge_at")

    #: The ID of the subscriber.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str
    #: The email address of the subscription.
    email: str
    #: The mode of the subscription.
    mode: str
    #: The date/time the description was quarantined at.
    quarantined_at: typing.Optional[datetime.datetime]
    #: The optional incident that this subscription is for.
    incident: typing.Optional[Incident]
    #: True if the confirmation notification is skipped.
    skip_confirmation_notification: typing.Optional[bool]
    #: The optional date/time to stop the subscription..
    purge_at: typing.Optional[datetime.datetime]

    @staticmethod
    def from_dict(payload):
        return Subscriber(
            id=payload["id"],
            email=payload["email"],
            mode=payload["mode"],
            quarantined_at=maps.get_from_map_as(payload, "quarantined_at", dateutils.parse_iso_8601_datetime),
            incident=maps.get_from_map_as(payload, "incident", Incident.from_dict),
            skip_confirmation_notification=maps.get_from_map_as(payload, "skip_confirmation_notification", bool),
            purge_at=maps.get_from_map_as(payload, "purge_at", dateutils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Subscription:
    """
    A subscription to an incident.
    """

    __slots__ = ("subscriber",)

    #: The subscription body.
    subscriber: Subscriber

    @staticmethod
    def from_dict(payload):
        return Subscription(subscriber=Subscriber.from_dict(payload["subscriber"]))


@dataclasses.dataclass()
class Page:
    """
    A page element.
    """

    __slots__ = ("id", "name", "url", "updated_at")

    #: The ID of the page.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str
    #: The name of the page.
    name: str
    #: A permalink to the page.
    url: str
    #: The date and time that the page was last updated at.
    updated_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return Page(
            id=payload["id"],
            name=payload["name"],
            url=payload["url"],
            updated_at=maps.get_from_map_as(payload, "updated_at", dateutils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Status:
    """
    A status description.
    """

    __slots__ = ("indicator", "description")

    #: The indicator that specifies the state of the service.
    indicator: typing.Optional[str]
    #: The optional description of the service state.
    description: typing.Optional[str]

    @staticmethod
    def from_dict(payload):
        return Status(indicator=payload.get("indicator"), description=payload.get("description"))


@dataclasses.dataclass()
class Component:
    """
    A component description.
    """

    __slots__ = ("id", "name", "created_at", "page_id", "position", "updated_at", "description")

    #: The ID of the component.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str
    #: The name of the component.
    name: str
    #: The date and time the component came online for the first time.
    created_at: datetime.datetime
    #: The ID of the status page for this component.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    page_id: str
    #: The position of the component in the list of components.
    position: int
    #: The date/time that this component last was updated at.
    updated_at: datetime.datetime
    #: The optional description of the component.
    description: typing.Optional[str]

    @staticmethod
    def from_dict(payload):
        return Component(
            id=payload["id"],
            name=payload["name"],
            created_at=maps.get_from_map_as(payload, "created_at", dateutils.parse_iso_8601_datetime),
            page_id=payload["page_id"],
            position=maps.get_from_map_as(payload, "position", int),
            updated_at=maps.get_from_map_as(payload, "updated_at", dateutils.parse_iso_8601_datetime),
            description=payload.get("description"),
        )


@dataclasses.dataclass()
class Components:
    """
    A collection of :class:`Component` objects.
    """

    __slots__ = ("page", "components")

    #: The page for this list of components.
    page: Page
    #: The list of components.
    components: typing.List[Component]

    @staticmethod
    def from_dict(payload):
        return Components(
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
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str
    #: The content in this update.
    body: str
    #: Time and date the incident update was made at.
    created_at: datetime.datetime
    #: The date/time to display the update at.
    display_at: typing.Optional[datetime.datetime]
    #: The ID of the corresponding incident.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    incident_id: str
    #: The status of the service during this incident update.
    status: str
    #: The date/time that the update was last changed.
    updated_at: typing.Optional[datetime.datetime]

    @staticmethod
    def from_dict(payload):
        return IncidentUpdate(
            id=payload["id"],
            body=payload["body"],
            created_at=maps.get_from_map_as(payload, "created_at", dateutils.parse_iso_8601_datetime),
            display_at=maps.get_from_map_as(payload, "display_at", dateutils.parse_iso_8601_datetime),
            incident_id=payload["incident_id"],
            status=payload["status"],
            updated_at=maps.get_from_map_as(payload, "updated_at", dateutils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Incident:
    """
    An incident.
    """

    __slots__ = (
        "id",
        "name",
        "impact",
        "incident_updates",
        "monitoring_at",
        "page_id",
        "resolved_at",
        "shortlink",
        "status",
        "updated_at",
    )

    #: The ID of the incident.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str
    #: The name of the incident.
    name: str
    #: The impact of the incident.
    impact: str
    #: A list of zero or more updates to the status of this incident.
    incident_updates: typing.List[IncidentUpdate]
    #: The date and time, if applicable, that the faulty component(s) were being monitored at.
    monitoring_at: typing.Optional[datetime.datetime]
    #: The ID of the page describing this incident.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    page_id: str
    #: The date and time that the incident finished, if applicable.
    resolved_at: typing.Optional[datetime.datetime]
    #: A short permalink to the page describing the incident.
    shortlink: str
    #: The incident status.
    status: str
    #: The last time the status of the incident was updated.
    updated_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return Incident(
            id=payload["id"],
            name=payload["name"],
            status=payload["status"],
            updated_at=maps.get_from_map_as(
                payload, "updated_at", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            incident_updates=[IncidentUpdate.from_dict(i) for i in payload.get("incident_updates", [])],
            monitoring_at=maps.get_from_map_as(
                payload, "monitoring_at", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            resolved_at=maps.get_from_map_as(
                payload, "resolved_at", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            shortlink=payload["shortlink"],
            page_id=payload["page_id"],
            impact=payload["impact"],
        )


@dataclasses.dataclass()
class Incidents:
    """
    A collection of :class:`Incident` objects.
    """

    __slot__ = ("page", "incidents")

    #: The page listing the incidents.
    page: Page
    #: The list of incidents on the page.
    incidents: typing.List[Incident]

    @staticmethod
    def from_dict(payload):
        return Incidents(Page.from_dict(payload["page"]), [Incident.from_dict(i) for i in payload["incidents"]])


@dataclasses.dataclass()
class ScheduledMaintenance:
    """
    A description of a maintenance that is scheduled to be performed.
    """

    __slots__ = (
        "id",
        "name",
        "impact",
        "incident_updates",
        "monitoring_at",
        "page_id",
        "resolved_at",
        "scheduled_for",
        "scheduled_until",
        "status",
        "updated_at",
    )

    #: The ID of the entry.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    id: str
    #: The name of the entry.
    name: str
    #: The impact of the entry.
    impact: str
    #: Zero or more updates to this event.
    incident_updates: typing.List[IncidentUpdate]
    #: The date and time the event was being monitored since, if applicable.
    monitoring_at: typing.Optional[datetime.datetime]
    #: The ID of the page describing this event.
    #:
    #: Note:
    #:     Unlike the rest of this API, this ID is a :class:`str` and *not* an :class:`int` type.
    page_id: str
    #: The optional date/time the event finished at.
    resolved_at: typing.Optional[datetime.datetime]
    #: The date/time that the event was scheduled for.
    scheduled_for: typing.Optional[datetime.datetime]
    #: The date/time that the event was scheduled until.
    scheduled_until: typing.Optional[datetime.datetime]
    #: The status of the event.
    status: str
    #: The date/time that the event was last updated at.
    updated_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return ScheduledMaintenance(
            id=payload["id"],
            name=payload["name"],
            impact=payload["impact"],
            incident_updates=[IncidentUpdate.from_dict(iu) for iu in payload.get("incident_updates", [])],
            monitoring_at=maps.get_from_map_as(
                payload, "monitoring_at", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            page_id=payload["page_id"],
            resolved_at=maps.get_from_map_as(
                payload, "resolved_at", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            scheduled_for=maps.get_from_map_as(
                payload, "scheduled_for", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            scheduled_until=maps.get_from_map_as(
                payload, "scheduled_until", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
            status=payload["status"],
            updated_at=maps.get_from_map_as(
                payload, "updated_at", dateutils.parse_iso_8601_datetime, default_on_error=True
            ),
        )


@dataclasses.dataclass()
class ScheduledMaintenances:
    """
    A collection of maintenance events.
    """

    __slots__ = ("page", "scheduled_maintenances")

    #: The page containing this information.
    page: Page
    #: The list of items on the page.
    scheduled_maintenances: typing.List[ScheduledMaintenance]

    @staticmethod
    def from_dict(payload):
        return ScheduledMaintenances(
            page=Page.from_dict(payload["page"]),
            scheduled_maintenances=[ScheduledMaintenance.from_dict(sm) for sm in payload["scheduled_maintenances"]],
        )


@dataclasses.dataclass()
class Summary:
    """
    A description of the overall API status.
    """

    __slots__ = ("page", "status", "components", "incidents", "scheduled_maintenances")

    #: The page describing this summary.
    page: Page
    #: The overall system status.
    status: Status
    #: The status of each component in the system.
    components: typing.List[Component]
    #: The list of incidents that have occurred/are occurring to components in this system.
    incidents: typing.List[Incident]
    #: A list of maintenance tasks that have been/will be undertaken.
    scheduled_maintenances: typing.List[ScheduledMaintenance]

    @staticmethod
    def from_dict(payload):
        return Summary(
            page=Page.from_dict(payload["page"]),
            scheduled_maintenances=[ScheduledMaintenance.from_dict(sm) for sm in payload["scheduled_maintenances"]],
            incidents=[Incident.from_dict(i) for i in payload["incidents"]],
            components=[Component.from_dict(c) for c in payload["components"]],
            status=Status.from_dict(payload["status"]),
        )

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

import datetime
import typing

import dataclasses

from hikari import utils


@dataclasses.dataclass()
class Subscriber:
    """
    A subscription to an incident.
    """

    __slots__ = ("id", "email", "mode", "quarantined_at", "incident", "skip_confirmation_notification", "purge_at")

    id: str
    email: str
    mode: str
    quarantined_at: typing.Optional[datetime.datetime]
    incident: typing.Optional[str]
    skip_confirmation_notification: typing.Optional[bool]
    purge_at: typing.Optional[datetime.datetime]

    @staticmethod
    def from_dict(payload: utils.DiscordObject):
        return Subscriber(
            id=payload["id"],
            email=payload["email"],
            mode=payload["mode"],
            quarantined_at=utils.get_from_map_as(payload, "quarantined_at", utils.parse_iso_8601_datetime),
            incident=utils.get_from_map_as(payload, "incident", Incident.from_dict),
            skip_confirmation_notification=utils.get_from_map_as(payload, "skip_confirmation_notification", bool),
            purge_at=utils.get_from_map_as(payload, "purge_at", utils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Subscription:
    """
    A subscription to an incident.
    """

    __slots__ = ("subscriber",)

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

    id: str
    name: str
    url: str
    updated_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return Page(
            id=payload["id"],
            name=payload["name"],
            url=payload["url"],
            updated_at=utils.get_from_map_as(payload, "updated_at", utils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Status:
    """
    A status description.
    """

    __slots__ = ("indicator", "description")

    indicator: typing.Optional[str]
    description: typing.Optional[str]

    @staticmethod
    def from_dict(payload: utils.DiscordObject):
        return Status(indicator=payload.get("indicator"), description=payload.get("description"))


@dataclasses.dataclass()
class Component:
    """
    A component description.
    """

    __slots__ = ("id", "name", "created_at", "page_id", "position", "updated_at", "description")

    id: str
    name: str
    created_at: datetime.datetime
    page_id: str
    position: int
    updated_at: datetime.datetime
    description: typing.Optional[str]

    @staticmethod
    def from_dict(payload: utils.DiscordObject):
        return Component(
            id=payload["id"],
            name=payload["name"],
            created_at=utils.get_from_map_as(payload, "created_at", utils.parse_iso_8601_datetime),
            page_id=payload["page_id"],
            position=utils.get_from_map_as(payload, "position", int),
            updated_at=utils.get_from_map_as(payload, "updated_at", utils.parse_iso_8601_datetime),
            description=payload.get("description"),
        )


@dataclasses.dataclass()
class Components:
    """
    A collection of :class:`Component` objects.
    """

    __slots__ = ("page", "components")

    page: Page
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

    body: str
    created_at: datetime.datetime
    display_at: typing.Optional[datetime.datetime]
    incident_id: str
    status: str
    id: str
    updated_at: typing.Optional[datetime.datetime]

    @staticmethod
    def from_dict(payload):
        return IncidentUpdate(
            id=payload["id"],
            body=payload["body"],
            created_at=utils.get_from_map_as(payload, "created_at", utils.parse_iso_8601_datetime),
            display_at=utils.get_from_map_as(payload, "display_at", utils.parse_iso_8601_datetime),
            incident_id=payload["incident_id"],
            status=payload["status"],
            updated_at=utils.get_from_map_as(payload, "updated_at", utils.parse_iso_8601_datetime),
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

    id: str
    name: str
    impact: str
    incident_updates: typing.List[IncidentUpdate]
    monitoring_at: typing.Optional[datetime.datetime]
    page_id: str
    resolved_at: typing.Optional[datetime.datetime]
    shortlink: str
    status: str
    updated_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return Incident(
            id=payload["id"],
            name=payload["name"],
            status=payload["status"],
            updated_at=utils.get_from_map_as(
                payload, "updated_at", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            incident_updates=[IncidentUpdate.from_dict(i) for i in payload.get("incident_updates", [])],
            monitoring_at=utils.get_from_map_as(
                payload, "monitoring_at", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            resolved_at=utils.get_from_map_as(
                payload, "resolved_at", utils.parse_iso_8601_datetime, default_on_error=True
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

    page: Page
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

    id: str
    name: str
    impact: str
    incident_updates: typing.List[IncidentUpdate]
    monitoring_at: typing.Optional[datetime.datetime]
    page_id: str
    resolved_at: typing.Optional[datetime.datetime]
    scheduled_for: typing.Optional[datetime.datetime]
    scheduled_until: typing.Optional[datetime.datetime]
    status: str
    updated_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return ScheduledMaintenance(
            id=payload["id"],
            name=payload["name"],
            impact=payload["impact"],
            incident_updates=[IncidentUpdate.from_dict(iu) for iu in payload.get("incident_updates", [])],
            monitoring_at=utils.get_from_map_as(
                payload, "monitoring_at", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            page_id=payload["page_id"],
            resolved_at=utils.get_from_map_as(
                payload, "resolved_at", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            scheduled_for=utils.get_from_map_as(
                payload, "scheduled_for", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            scheduled_until=utils.get_from_map_as(
                payload, "scheduled_until", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            status=payload["status"],
            updated_at=utils.get_from_map_as(
                payload, "updated_at", utils.parse_iso_8601_datetime, default_on_error=True
            ),
        )


@dataclasses.dataclass()
class ScheduledMaintenances:
    """
    A collection of maintenance events.
    """

    __slots__ = ("page", "scheduled_maintenances")

    page: Page
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

    page: Page
    status: Status
    components: typing.List[Component]
    incidents: typing.List[Incident]
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

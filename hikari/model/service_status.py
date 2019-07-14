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

from hikari import utils
from . import base


# TODO: slot these classes.


@dataclasses.dataclass()
class Subscriber(base.Model):
    """
    A subscription to an incident.
    """

    id: str
    email: str
    mode: str
    quarantined_at: typing.Optional[datetime.datetime] = None
    incident: typing.Optional[str] = None
    skip_confirmation_notification: typing.Optional[bool] = None
    purge_at: typing.Optional[datetime.datetime] = None

    @classmethod
    def from_dict(cls: Subscriber, payload: utils.DiscordObject, state=NotImplemented) -> Subscriber:
        return cls(
            state,
            id=payload["id"],
            email=payload["email"],
            mode=payload["mode"],
            quarantined_at=utils.get_from_map_as(payload, "quarantined_at", utils.parse_iso_8601_datetime),
            incident=utils.get_from_map_as(payload, "incident", Incident.from_dict),
            skip_confirmation_notification=utils.get_from_map_as(payload, "skip_confirmation_notification", bool),
            purge_at=utils.get_from_map_as(payload, "purge_at", utils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Subscription(base.Model):
    subscriber: Subscriber

    @classmethod
    def from_dict(cls: Subscription, payload: utils.DiscordObject, state=NotImplemented) -> Subscription:
        return cls(state, subscriber=Subscriber.from_dict(payload["subscriber"], state))


@dataclasses.dataclass()
class Page(base.Model):
    """
    A page element.
    """

    id: str
    name: str
    url: str
    updated_at: datetime.datetime

    @classmethod
    def from_dict(cls: Page, payload: utils.DiscordObject, state=NotImplemented) -> Page:
        return cls(
            state,
            id=payload["id"],
            name=payload["name"],
            url=payload["url"],
            updated_at=utils.get_from_map_as(payload, "updated_at", utils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Status(base.Model):
    """
    A status description.
    """

    indicator: typing.Optional[str] = None
    description: typing.Optional[str] = None

    @classmethod
    def from_dict(cls: Status, payload: utils.DiscordObject, state=NotImplemented) -> Status:
        return Status(state, indicator=payload.get("indicator"), description=payload.get("description"))


@dataclasses.dataclass()
class Component(base.Model):
    """
    A component description.
    """

    id: str
    name: str
    created_at: datetime.datetime
    page_id: str
    position: int
    updated_at: datetime.datetime
    description: typing.Optional[str] = None

    @classmethod
    def from_dict(cls: Component, payload: utils.DiscordObject, state=NotImplemented) -> Component:
        return cls(
            state,
            id=payload["id"],
            name=payload["name"],
            created_at=utils.get_from_map_as(payload, "created_at", utils.parse_iso_8601_datetime),
            page_id=payload["page_id"],
            position=utils.get_from_map_as(payload, "position", int),
            updated_at=utils.get_from_map_as(payload, "updated_at", utils.parse_iso_8601_datetime),
            description=payload.get("description"),
        )


@dataclasses.dataclass()
class Components(base.Model):
    """
    A collection of :class:`Component` objects.
    """

    page: Page
    components: typing.List[Component]

    @classmethod
    def from_dict(cls: Components, payload: utils.DiscordObject, state=NotImplemented) -> Components:
        return cls(
            state,
            page=Page.from_dict(payload["page"], state),
            components=[Component.from_dict(c, state) for c in payload.get("components", [])],
        )


@dataclasses.dataclass()
class IncidentUpdate(base.Model):
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

    @classmethod
    def from_dict(cls: IncidentUpdate, payload: utils.DiscordObject, state=NotImplemented) -> IncidentUpdate:
        return cls(
            state,
            id=payload["id"],
            body=payload["body"],
            created_at=utils.get_from_map_as(payload, "created_at", utils.parse_iso_8601_datetime),
            display_at=utils.get_from_map_as(payload, "display_at", utils.parse_iso_8601_datetime),
            incident_id=payload["incident_id"],
            status=payload["status"],
            updated_at=utils.get_from_map_as(payload, "updated_at", utils.parse_iso_8601_datetime),
        )


@dataclasses.dataclass()
class Incident(base.Model):
    """
    An incident.
    """

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

    @classmethod
    def from_dict(cls: Incident, payload: utils.DiscordObject, state=NotImplemented) -> Incident:
        return cls(
            state,
            id=payload["id"],
            name=payload["name"],
            status=payload["status"],
            updated_at=utils.get_from_map_as(
                payload, "updated_at", utils.parse_iso_8601_datetime, default_on_error=True
            ),
            incident_updates=[IncidentUpdate.from_dict(i, state) for i in payload.get("incident_updates", [])],
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
class Incidents(base.Model):
    """
    A collection of :class:`Incident` objects.
    """

    page: Page
    incidents: typing.List[Incident]

    # TODO: def from_dict()


@dataclasses.dataclass()
class ScheduledMaintenance(base.Model):
    """
    A description of a maintenance that is scheduled to be performed.
    """

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

    # TODO: def from_dict()


@dataclasses.dataclass()
class ScheduledMaintenances(base.Model):
    """
    A collection of maintenance events.
    """

    page: Page
    scheduled_maintenances: typing.List[ScheduledMaintenance]

    # TODO: def from_dict()


@dataclasses.dataclass()
class Summary(base.Model):
    """
    A description of the overall API status.
    """

    page: Page
    status: Status
    components: typing.List[Component]
    incidents: typing.List[Incident]
    scheduled_maintenances: typing.List[ScheduledMaintenance]

    # TODO: def from_dict()

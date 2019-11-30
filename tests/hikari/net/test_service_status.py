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

from hikari.net import service_status


@pytest.fixture()
def active_scheduled_maintenances_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "scheduled_maintenances": [],
    }


@pytest.fixture()
def components_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "components": [
            {
                "id": "rhznvxg4v7yh",
                "name": "API",
                "status": "operational",
                "created_at": "2015-07-30T18:55:43.739-07:00",
                "updated_at": "2019-05-31T15:49:13.651-07:00",
                "position": 1,
                "description": None,
                "showcase": True,
                "group_id": None,
                "page_id": "srhpyqt94yxb",
                "group": False,
                "only_show_if_degraded": False,
            },
            {
                "id": "0cwvg0jp5cbg",
                "name": "EU West",
                "status": "operational",
                "created_at": "2015-07-30T20:36:41.891-07:00",
                "updated_at": "2018-07-17T13:00:35.378-07:00",
                "position": 1,
                "description": None,
                "showcase": False,
                "group_id": "jk03xttfcz9b",
                "page_id": "srhpyqt94yxb",
                "group": False,
                "only_show_if_degraded": False,
            },
            {
                "id": "jk03xttfcz9b",
                "name": "Voice",
                "status": "operational",
                "created_at": "2015-07-30T20:39:36.003-07:00",
                "updated_at": "2017-09-29T06:48:54.042-07:00",
                "position": 5,
                "description": None,
                "showcase": False,
                "group_id": None,
                "page_id": "srhpyqt94yxb",
                "group": True,
                "only_show_if_degraded": False,
                "components": [
                    "0cwvg0jp5cbg",
                    "fc8y53dfg85y",
                    "q0lbnfc59j35",
                    "qbt7ryjc5tcd",
                    "nhlpbmmcffcl",
                    "kdz8bp5dp08v",
                    "gmppldfdghcd",
                    "334vzyzzwlfs",
                    "sg02vq1rbfrr",
                    "0ysw0jy8hnsr",
                    "ccgfj3l84lvt",
                    "xggnf9hnngkt",
                    "b5v9r9bdppvm",
                ],
            },
        ],
    }


@pytest.fixture()
def incidents_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "incidents": [
            {
                "id": "2gztsrksff0v",
                "name": "Global Unavailability",
                "status": "investigating",
                "created_at": "2019-06-24T05:25:57.666-07:00",
                "updated_at": "2019-06-24T06:07:14.465-07:00",
                "monitoring_at": None,
                "resolved_at": None,
                "impact": "none",
                "shortlink": "http://stspg.io/15e073752",
                "started_at": "2019-06-24T05:25:57.659-07:00",
                "page_id": "srhpyqt94yxb",
                "incident_updates": [
                    {
                        "id": "xxqwgv42dnx5",
                        "status": "investigating",
                        "body": "We are working on resolving some internal technical problems now.",
                        "incident_id": "2gztsrksff0v",
                        "created_at": "2019-06-24T06:07:14.463-07:00",
                        "updated_at": "2019-06-24T06:07:14.463-07:00",
                        "display_at": "2019-06-24T06:07:14.463-07:00",
                        "affected_components": None,
                        "deliver_notifications": False,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                    {
                        "id": "jvrfncktc4yp",
                        "status": "investigating",
                        "body": "Discord is affected by the general internet outage. Hang tight.  Pet your cats.",
                        "incident_id": "2gztsrksff0v",
                        "created_at": "2019-06-24T05:25:57.698-07:00",
                        "updated_at": "2019-06-24T05:25:57.698-07:00",
                        "display_at": "2019-06-24T05:25:57.698-07:00",
                        "affected_components": None,
                        "deliver_notifications": False,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                ],
                "components": [],
            }
        ],
    }


@pytest.fixture()
def scheduled_maintenances_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "scheduled_maintenances": [
            {
                "id": "ymm0202y77k6",
                "name": "Potentially Disruptive Upgrade",
                "status": "completed",
                "created_at": "2016-10-16T16:57:33.416-07:00",
                "updated_at": "2016-10-19T02:39:00.299-07:00",
                "monitoring_at": None,
                "resolved_at": "2016-10-19T02:39:00.274-07:00",
                "impact": "maintenance",
                "shortlink": "http://stspg.io/4ERc",
                "started_at": "2016-10-16T16:57:00.000-07:00",
                "page_id": "srhpyqt94yxb",
                "incident_updates": [
                    {
                        "id": "ptphhdp7zzy8",
                        "status": "completed",
                        "body": "The maintenance has completed as planned with no outage or service interruption.\r\n\r\nNothing broke. Nothing caught fire. Everything is OK.",
                        "incident_id": "ymm0202y77k6",
                        "created_at": "2016-10-19T02:39:00.274-07:00",
                        "updated_at": "2016-10-19T02:39:00.274-07:00",
                        "display_at": "2016-10-19T02:39:00.274-07:00",
                        "affected_components": [{"name": "No components were affected by this update."}],
                        "deliver_notifications": True,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                    {
                        "id": "jd5jjsflj0x5",
                        "status": "in_progress",
                        "body": "This maintenance is currently in progress.",
                        "incident_id": "ymm0202y77k6",
                        "created_at": "2016-10-19T02:07:00.712-07:00",
                        "updated_at": "2016-10-19T02:07:00.712-07:00",
                        "display_at": "2016-10-19T02:07:00.712-07:00",
                        "affected_components": [{"name": "No components were affected by this update."}],
                        "deliver_notifications": True,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                    {
                        "id": "vw800012grtl",
                        "status": "scheduled",
                        "body": 'On September 23rd we attempted to release a code upgrade that involved some of our real-time servers that we upgrade without disruption using a method called "handoffs." After over a year of working fine, Discord\'s growth revealed flaws in the handoff implementation at our current scale. We have implemented changes in the handoff system and will attempt to do a code upgrade without disruption, but if something goes wrong we might have to force everyone to reconnect which can cause up to 30 minutes of disruption.',
                        "incident_id": "ymm0202y77k6",
                        "created_at": "2016-10-16T16:57:33.923-07:00",
                        "updated_at": "2016-10-16T16:59:23.526-07:00",
                        "display_at": "2016-10-16T16:57:00.000-07:00",
                        "affected_components": [{"name": "No components were affected by this update."}],
                        "deliver_notifications": True,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                ],
                "components": [],
                "scheduled_for": "2016-10-19T02:00:00.000-07:00",
                "scheduled_until": "2016-10-19T03:00:00.000-07:00",
            },
        ],
    }


@pytest.fixture()
def subscriber_pl():
    return {
        "subscriber": {
            "created_at": "2019-06-24T07:29:43.684-07:00",
            "skip_confirmation_notification": False,
            "quarantined_at": None,
            "id": "82kp04j58dhm",
            "mode": "email",
            "purge_at": None,
            "email": "xxx@yyy.com",
        }
    }


@pytest.fixture()
def summary_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "components": [
            {
                "id": "rhznvxg4v7yh",
                "name": "API",
                "status": "operational",
                "created_at": "2015-07-30T18:55:43.739-07:00",
                "updated_at": "2019-05-31T15:49:13.651-07:00",
                "position": 1,
                "description": None,
                "showcase": True,
                "group_id": None,
                "page_id": "srhpyqt94yxb",
                "group": False,
                "only_show_if_degraded": False,
            },
            {
                "id": "0cwvg0jp5cbg",
                "name": "EU West",
                "status": "operational",
                "created_at": "2015-07-30T20:36:41.891-07:00",
                "updated_at": "2018-07-17T13:00:35.378-07:00",
                "position": 1,
                "description": None,
                "showcase": False,
                "group_id": "jk03xttfcz9b",
                "page_id": "srhpyqt94yxb",
                "group": False,
                "only_show_if_degraded": False,
            },
            {
                "id": "fc8y53dfg85y",
                "name": "EU Central",
                "status": "operational",
                "created_at": "2015-12-10T23:45:29.114-08:00",
                "updated_at": "2018-12-03T09:58:22.515-08:00",
                "position": 2,
                "description": None,
                "showcase": False,
                "group_id": "jk03xttfcz9b",
                "page_id": "srhpyqt94yxb",
                "group": False,
                "only_show_if_degraded": False,
            },
        ],
    }


@pytest.fixture()
def unresolved_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "incidents": [
            {
                "id": "2gztsrksff0v",
                "name": "Global Unavailability",
                "status": "investigating",
                "created_at": "2019-06-24T05:25:57.666-07:00",
                "updated_at": "2019-06-24T06:07:14.465-07:00",
                "monitoring_at": None,
                "resolved_at": None,
                "impact": "none",
                "shortlink": "http://stspg.io/15e073752",
                "started_at": "2019-06-24T05:25:57.659-07:00",
                "page_id": "srhpyqt94yxb",
                "incident_updates": [
                    {
                        "id": "xxqwgv42dnx5",
                        "status": "investigating",
                        "body": "We are working on resolving some internal technical problems now.",
                        "incident_id": "2gztsrksff0v",
                        "created_at": "2019-06-24T06:07:14.463-07:00",
                        "updated_at": "2019-06-24T06:07:14.463-07:00",
                        "display_at": "2019-06-24T06:07:14.463-07:00",
                        "affected_components": None,
                        "deliver_notifications": False,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                    {
                        "id": "jvrfncktc4yp",
                        "status": "investigating",
                        "body": "Discord is affected by the general internet outage. Hang tight.  Pet your cats.",
                        "incident_id": "2gztsrksff0v",
                        "created_at": "2019-06-24T05:25:57.698-07:00",
                        "updated_at": "2019-06-24T05:25:57.698-07:00",
                        "display_at": "2019-06-24T05:25:57.698-07:00",
                        "affected_components": None,
                        "deliver_notifications": False,
                        "custom_tweet": None,
                        "tweet_id": None,
                    },
                ],
                "components": [],
            }
        ],
    }


@pytest.fixture()
def upcoming_scheduled_maintenances_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "scheduled_maintenances": [],
    }


@pytest.fixture()
def status_pl():
    return {
        "page": {
            "id": "srhpyqt94yxb",
            "name": "Discord",
            "url": "http://status.discordapp.com",
            "time_zone": "America/Tijuana",
            "updated_at": "2019-06-24T06:07:14.473-07:00",
        },
        "status": {"indicator": "none", "description": "All Systems Operational"},
    }

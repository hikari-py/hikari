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
import asyncio

import aiohttp
import async_timeout
import cymock as mock
import pytest

from hikari.net import ratelimits
from hikari.net import status_info_client
from hikari.orm import api_status_checker
from tests.hikari import _helpers


@pytest.fixture()
def mock_log_initial_state():
    with mock.patch.object(api_status_checker, "_log_initial_state", spec_set=True, autospec=True) as mocked:
        yield mocked


@pytest.fixture()
def mock_change_in_status():
    with mock.patch.object(api_status_checker, "_log_change_in_status", spec_set=True, autospec=True) as mocked:
        yield mocked


@pytest.fixture()
def mock_everything(mock_log_initial_state, mock_change_in_status):
    yield object()  # sentinel


class LazyForeverSideEffect:
    def __init__(self, iterate_these, and_then_repeat_this):
        self.first_iter = iterate_these
        self.then_iter = and_then_repeat_this

    def __iter__(self):
        yield from self.first_iter
        while True:
            yield self.then_iter


@pytest.mark.asyncio
async def test_log_api_incidents_logs_initial_api_state_once(mock_everything, mock_log_initial_state):
    fetch_return = mock.MagicMock()
    with mock.patch.object(api_status_checker, "_fetch_latest", spec_set=True, return_value=fetch_return) as fl:
        try:
            async with async_timeout.timeout(0.2):
                await api_status_checker.log_api_incidents(mock.MagicMock(), period=0.01)
        except asyncio.TimeoutError:
            pass

        fl.assert_awaited()
        mock_log_initial_state.assert_called_once_with(fetch_return)


@pytest.mark.asyncio
async def test_log_api_incidents_logs_change_in_status(mock_everything, mock_change_in_status):
    first_status = mock.MagicMock()
    second_status = mock.MagicMock()
    more_status = mock.MagicMock()
    side_effect = LazyForeverSideEffect((first_status, second_status), more_status)

    with mock.patch.object(api_status_checker, "_fetch_latest", spec_set=True, side_effect=side_effect) as fl:
        try:
            async with async_timeout.timeout(0.2):
                await api_status_checker.log_api_incidents(mock.MagicMock(), period=0.01)

        except asyncio.TimeoutError:
            pass

        fl.assert_awaited()
        api_status_checker._log_change_in_status.assert_any_call(first_status, second_status)
        api_status_checker._log_change_in_status.assert_any_call(second_status, more_status)
        api_status_checker._log_change_in_status.assert_any_call(more_status, more_status)


@pytest.mark.asyncio
async def test_log_api_incidents_when_cancelled(mock_everything, event_loop):
    client = mock.create_autospec(status_info_client.StatusInfoClient, spec_set=True)
    task = event_loop.create_task(api_status_checker.log_api_incidents(client, period=0.01))
    await asyncio.sleep(0.5)
    task.cancel()
    await asyncio.sleep(0.1)
    assert task.done()
    assert await task is None


def test_log_initial_state():
    with mock.patch.object(api_status_checker, "logger") as logger:
        status = mock.MagicMock()
        api_status_checker._log_initial_state(status)

    logger.info.assert_called_once()
    (string, current_status, updated_at, description, url), kwargs = logger.info.call_args
    assert current_status is status.status.indicator
    assert updated_at is status.page.updated_at
    assert description is status.status.description
    assert url is status.page.url


def test_log_change_in_status_when_changed():
    with mock.patch.object(api_status_checker, "logger") as logger:
        status1 = mock.MagicMock()
        status2 = mock.MagicMock()
        api_status_checker._log_change_in_status(status1, status2)

    logger.warning.assert_called_once()
    (string, previous_status, current_status, updated_at, description, url), kwargs = logger.warning.call_args
    assert previous_status is status1.status.indicator
    assert current_status is status2.status.indicator
    assert updated_at is status2.page.updated_at
    assert description is status2.status.description
    assert url is status2.page.url


def test_log_change_in_status_when_not_changed():
    with mock.patch.object(api_status_checker, "logger") as logger:
        status1 = mock.MagicMock()
        status2 = status1
        api_status_checker._log_change_in_status(status1, status2)

    logger.warning.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_latest_success_case():
    mock_client = mock.create_autospec(status_info_client.StatusInfoClient, spec_set=True)
    status = _helpers.mock_model(status_info_client.StatusPage)
    mock_client.fetch_status = mock.AsyncMock(return_value=status)
    backoff = ratelimits.ExponentialBackOff(base=1.1, maximum=5, jitter_multiplier=0)
    assert await api_status_checker._fetch_latest(mock_client, backoff) is status


@pytest.mark.asyncio
async def test_fetch_latest_failure_case_with_backoff():
    mock_client = mock.create_autospec(status_info_client.StatusInfoClient, spec_set=True)
    status = _helpers.mock_model(status_info_client.StatusPage)
    mock_client.fetch_status = mock.AsyncMock(side_effect=[aiohttp.ClientError(), aiohttp.ClientError(), status])
    backoff = ratelimits.ExponentialBackOff(base=1.1, maximum=5, jitter_multiplier=0)
    assert await api_status_checker._fetch_latest(mock_client, backoff) is status

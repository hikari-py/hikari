# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
import contextlib
import distutils.version

import aiohttp
import mock
import pytest

from hikari import _about
from hikari.utilities import version_sniffer
from tests.hikari import client_session_stub


@pytest.mark.asyncio
class TestFetchAllReleases:
    @pytest.fixture
    def pypi_update_payload(self):
        return {
            "info": ...,
            "releases": {
                "0.0.1": [{"yanked": False}],
                "0.0.1.dev1": [{"yanked": True}, {"yanked": False}],
                "0.0.1.dev2": [{"yanked": True}, {"yanked": True}],
                "0.0.1.dev3": [{"yanked": False}],
                "0.0.1.dev4": [{"yanked": False}],
                "0.0.1.dev5": [{"yanked": False}],
            },
        }

    @pytest.fixture
    def client_session_mock(self, pypi_update_payload):
        stub = client_session_stub.ClientSessionStub()
        stub.response_stub.json = mock.AsyncMock(return_value=pypi_update_payload)

        with mock.patch.object(aiohttp, "ClientSession", return_value=stub):
            yield stub

    async def test_request_is_made(self, client_session_mock):
        await version_sniffer._fetch_all_releases()
        client_session_mock.request.assert_called_once_with(
            "get", "https://pypi.org/pypi/hikari/json", raise_for_status=True, timeout=aiohttp.ClientTimeout(total=3.0),
        )

    async def test_response_is_populated_with_loose_versions(self, client_session_mock):
        releases = await version_sniffer._fetch_all_releases()

        assert len(releases) > 1

        for i, release in enumerate(await version_sniffer._fetch_all_releases()):
            assert isinstance(release, distutils.version.LooseVersion), f"{i}, release: {release}, {type(release)}"

    async def test_responses_have_non_yanked_releases(self, client_session_mock):
        releases = await version_sniffer._fetch_all_releases()

        for v in ("0.0.1", "0.0.1.dev3", "0.0.1.dev4", "0.0.1.dev5"):
            assert distutils.version.LooseVersion(v) in releases

    async def test_responses_have_partially_yanked_releases(self, client_session_mock):
        releases = await version_sniffer._fetch_all_releases()

        assert distutils.version.LooseVersion("0.0.1.dev1") in releases

    async def test_responses_do_not_have_totally_yanked_releases(self, client_session_mock):
        releases = await version_sniffer._fetch_all_releases()

        assert distutils.version.LooseVersion("0.0.1.dev2") not in releases

    async def test_responses_are_sorted(self, client_session_mock):
        releases = await version_sniffer._fetch_all_releases()
        assert sorted(releases) == releases


@pytest.mark.asyncio
class TestFetchVersionInfoFromPyPI:
    async def test_fetch_all_releases_invoked(self):
        stack = contextlib.ExitStack()
        fetch_all_releases_mock = stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases"))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.1"))
        stack.enter_context(contextlib.suppress(BaseException))

        with stack:
            await version_sniffer.fetch_version_info_from_pypi()
            fetch_all_releases_mock.assert_awaited_once()

    async def test_this_version(self):
        pl = [
            distutils.version.LooseVersion(v)
            for v in (
                "0.0.1",
                "0.0.1.dev9",
                "0.999.999",
                "1.0.0",
                "1.0.0.dev16",
                "1.0.1",
                "1.0.1.dev2",
                "1.0.2",
                "1.0.2.dev2",
                "1.1.0",
                "1.1.0.dev9",
                "1.2.0",
                "1.2.0.dev8",
                "2.0.0",
                "2.0.0.dev37",
                "2.0.1.dev3",
            )
        ]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases", return_value=pl))
        mock_api_version = stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.1"))
        with stack:
            result = await version_sniffer.fetch_version_info_from_pypi()
            assert result.this == distutils.version.LooseVersion(mock_api_version)

    async def test_only_newer_compatible_version_given_when_not_a_dev_release(self):
        pl = [
            distutils.version.LooseVersion(v)
            for v in (
                "0.0.1",
                "0.0.1.dev9",
                "0.999.999",
                "1.0.0",
                "1.0.0.dev16",
                "1.0.1",
                "1.0.1.dev2",
                "1.0.2",
                "1.0.2.dev2",
                "1.0.7.dev3",
                "1.0.7",
                "1.0.8.dev4",
                "1.1.0",
                "1.1.0.dev9",
                "1.2.0",
                "1.2.0.dev8",
                "2.0.0",
                "2.0.0.dev37",
                "2.0.1.dev3",
            )
        ]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases", return_value=pl))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.1"))
        with stack:
            result = await version_sniffer.fetch_version_info_from_pypi()
            assert result.latest_compatible == distutils.version.LooseVersion("1.0.7")

    async def test_latest_version_given_when_not_a_dev_release(self):
        pl = [
            distutils.version.LooseVersion(v)
            for v in (
                "0.0.1",
                "0.0.1.dev9",
                "0.999.999",
                "1.0.0",
                "1.0.0.dev16",
                "1.0.1",
                "1.0.1.dev2",
                "1.0.2",
                "1.0.2.dev2",
                "1.0.7.dev3",
                "1.0.7",
                "1.0.8.dev4",
                "1.1.0",
                "1.1.0.dev9",
                "1.2.0",
                "1.2.0.dev8",
                "2.0.0",
                "2.0.0.dev37",
                "2.0.1.dev3",
            )
        ]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases", return_value=pl))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.1"))
        with stack:
            result = await version_sniffer.fetch_version_info_from_pypi()
            assert result.latest == distutils.version.LooseVersion("2.0.0")

    async def test_only_newer_compatible_version_given_when_dev_release(self):
        pl = [
            distutils.version.LooseVersion(v)
            for v in (
                "0.0.1",
                "0.0.1.dev9",
                "0.999.999",
                "1.0.0",
                "1.0.0.dev16",
                "1.0.1",
                "1.0.1.dev2",
                "1.0.2",
                "1.0.2.dev2",
                "1.0.7.dev3",
                "1.0.7",
                "1.0.8.dev4",
                "1.1.0",
                "1.1.0.dev9",
                "1.2.0",
                "1.2.0.dev8",
                "2.0.0",
                "2.0.0.dev37",
                "2.0.1.dev3",
            )
        ]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases", return_value=pl))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.1.dev1"))
        with stack:
            result = await version_sniffer.fetch_version_info_from_pypi()
            assert result.latest_compatible == distutils.version.LooseVersion("1.0.8.dev4")

    async def test_latest_version_given_when_dev_release(self):
        pl = [
            distutils.version.LooseVersion(v)
            for v in (
                "0.0.1",
                "0.0.1.dev9",
                "0.999.999",
                "1.0.0",
                "1.0.0.dev16",
                "1.0.1",
                "1.0.1.dev2",
                "1.0.2",
                "1.0.2.dev2",
                "1.1.0",
                "1.1.0.dev9",
                "1.2.0",
                "1.2.0.dev8",
                "2.0.0",
                "2.0.0.dev37",
                "2.0.1.dev3",
            )
        ]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases", return_value=pl))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.1.dev1"))
        with stack:
            result = await version_sniffer.fetch_version_info_from_pypi()
            assert result.latest == distutils.version.LooseVersion("2.0.1.dev3")

    @pytest.mark.parametrize("this_version", ["1.0.2", "1.0.2.dev4"])
    async def test_no_versions_given(self, this_version):
        pl = []

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(version_sniffer, "_fetch_all_releases", return_value=pl))
        stack.enter_context(mock.patch.object(_about, "__version__", new=this_version))
        with stack:
            result = await version_sniffer.fetch_version_info_from_pypi()
            assert result.this == distutils.version.LooseVersion(this_version)
            assert result.latest_compatible == distutils.version.LooseVersion(this_version)
            assert result.latest == distutils.version.LooseVersion(this_version)

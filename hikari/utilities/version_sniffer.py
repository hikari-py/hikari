# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Checks PyPI for a newer release of the library."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = []

import typing
from distutils import version as distutils_version

import aiohttp
import attr

from hikari import _about

if typing.TYPE_CHECKING:
    from hikari.utilities import data_binding


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VersionInfo:
    """PyPI release info."""

    this: distutils_version.LooseVersion = attr.ib()
    """This version."""

    latest_compatible: distutils_version.LooseVersion = attr.ib()
    """Latest compatible version with no breaking API changes."""

    latest: distutils_version.LooseVersion = attr.ib()
    """Latest version. May contain breaking API changes."""

    is_official: bool = attr.ib(default=_about.__is_official_distributed_release__)
    """True if this library version is a valid PyPI release.

    This will be False for non-release versions (e.g. cloned from version
    control, on forks, or not released using the Hikari CI pipeline).
    """


async def _fetch_all_releases() -> typing.Sequence[distutils_version.LooseVersion]:
    # Make a client session, it is easier to stub.
    async with aiohttp.ClientSession() as cs:
        async with cs.get(
            "https://pypi.org/pypi/hikari/json", raise_for_status=True, timeout=aiohttp.ClientTimeout(total=3.0),
        ) as resp:
            data: data_binding.JSONObject = await resp.json()

    releases: typing.List[distutils_version.LooseVersion] = []

    for release_string, artifacts in data["releases"].items():
        if not all(artifact["yanked"] for artifact in artifacts):
            releases.append(distutils_version.LooseVersion(release_string))

    releases.sort()

    return releases


async def fetch_version_info_from_pypi() -> VersionInfo:
    """Fetch the info about updates to this library on PyPI.

    If this is a development release, then development releases will be taken
    into account when collecting this data. Otherwise, development releases
    will be ignored.

    Returns
    -------
    VersionInfo
        Version information.
    """
    releases = await _fetch_all_releases()

    this = distutils_version.LooseVersion(_about.__version__)

    same_compatible_releases = [v for v in releases if v.version[:2] == this.version[:2] and v > this] or [this]

    if "dev" not in this.vstring:
        # Remove dev releases if we are not on a dev release.
        same_compatible_releases = [v for v in same_compatible_releases if "dev" not in v.version] or [this]
        newer_releases = [v for v in releases if "dev" not in v.version if v > this] or [this]
        latest = max(newer_releases)
    else:
        latest = max(releases) if releases else this

    latest_compatible = max(same_compatible_releases)

    return VersionInfo(this=this, latest_compatible=latest_compatible, latest=latest,)

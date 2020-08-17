# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Checks PyPI for a newer release of the library."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "VersionInfo",
    "fetch_version_info_from_pypi",
    "log_available_updates",
]

import logging
import typing
from distutils import version as distutils_version

import aiohttp
import attr

from hikari import _about
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    from hikari.utilities import data_binding


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VersionInfo:
    """PyPI release info."""

    this: distutils_version.LooseVersion = attr.ib()
    """This version."""

    latest_compatible: distutils_version.LooseVersion = attr.ib()
    """Latest compatible version with no breaking API changes."""

    latest: distutils_version.LooseVersion = attr.ib()
    """Latest version. May contain breaking API changes."""


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


async def log_available_updates(logger: logging.Logger) -> None:
    """Log if any updates are available for the library.

    Parameters
    ----------
    logger : logging.Logger
        The logger to write to.
    """
    try:
        if _about.__git_sha1__.casefold() == "head":
            return

        version_info = await fetch_version_info_from_pypi()

        if version_info.this == version_info.latest:
            logger.info("package is up to date!")
            return

        if version_info.this != version_info.latest_compatible:
            logger.warning(
                "non-breaking updates are available for hikari, update from v%s to v%s!",
                version_info.this,
                version_info.latest_compatible,
            )
            return

        # We can only get here if there are breaking changes available
        logger.info(
            "breaking updates are available for hikari, consider upgrading from v%s to v%s!",
            version_info.this,
            version_info.latest,
        )

    except Exception as ex:
        logger.debug("Error occurred fetching version info", exc_info=ex)

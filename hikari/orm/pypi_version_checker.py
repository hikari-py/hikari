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
"""
A helper utility class that checks PyPI for the latest stable version of the package.
"""
import contextlib
import functools

import aiohttp

from hikari import _about
from hikari.internal_utilities import loggers

logger = loggers.get_named_logger(__name__)


@functools.total_ordering
class _Version:
    def __init__(self, version):
        self.major, _, rest = version.partition(".")
        self.major = int(self.major)
        self.minor, _, rest = rest.partition(".")
        self.minor = int(self.minor)
        self.micro, _, rest = rest.partition(".")
        self.micro = int(self.micro)
        self.dev = "dev" not in rest

    def to_tuple(self):
        return self.major, self.minor, self.micro, self.dev

    def __lt__(self, other):
        return self.__class__ == other.__class__ and self.to_tuple() < other.to_tuple()


async def check_package_version() -> None:
    """Check PyPI for latest stable version of the package.

    Polls the PyPI API to check if there is a new version of the package and logs if so.
    """
    logger.debug("fetching package info off PyPI")

    with contextlib.suppress(aiohttp.ClientError):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pypi.python.org/pypi/hikari/json") as resp:
                pypi_version = _Version((await resp.json())["info"]["version"])

        installed_version = _Version(_about.__version__)

        if installed_version < pypi_version:
            logger.warning(
                "you are on version %s but the latest stable is %s. "
                "Please consider updating since a newer version might include bug fixes or breaking API changes. "
                "To update do `python -m pip install -U hikari`",
                installed_version,
                pypi_version,
            )

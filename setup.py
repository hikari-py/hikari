#!/usr/bin/env python3
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

import setuptools

__version__ = "0.0.70"


def long_description():
    with open("README.md") as fp:
        return fp.read()


def parse_requirements():
    with open("requirements.txt") as fp:
        dependencies = (d.strip() for d in fp.read().split("\n") if d.strip())
        return [d for d in dependencies if not d.startswith("#")]


setuptools.setup(
    name="hikari",
    version=__version__,
    description="A sane Discord API for Python 3 built on asyncio and good intentions",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    author="Nekokatt",
    author_email="nekoka.tt@outlook.com",
    license="LGPL-3.0-ONLY",
    url="https://gitlab.com/nekokatt/hikari",
    packages=setuptools.find_namespace_packages(include=["hikari*"]),
    python_requires=">=3.8.0,<3.10",
    install_requires=parse_requirements(),
    include_package_data=True,
    test_suite="tests",
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
)

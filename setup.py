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
from distutils import log
from distutils import errors
import os
import re
import types

import setuptools
from setuptools.command import build_ext

name = "hikari"


class Accelerator(setuptools.Extension):
    def __init__(self, name, sources, **kwargs):
        super().__init__(name, sources, **kwargs)


class BuildCommand(build_ext.build_ext):
    def build_extensions(self):
        for ext in self.extensions:
            if isinstance(ext, Accelerator):
                self.build_accelerator(ext)
            else:
                self.build_extension(ext)

    def build_accelerator(self, ext):
        try:
            self.build_extension(ext)
        except errors.CompileError as ex:
            log.warn("Compilation of %s failed, so this module will not be accelerated: %s", ext, ex)
        except errors.LinkError as ex:
            log.warn("Linking of %s failed, so this module will not be accelerated: %s", ext, ex)


def long_description():
    with open("README.md") as fp:
        return fp.read()


def parse_meta():
    with open(os.path.join(name, "_about.py")) as fp:
        code = fp.read()

    token_pattern = re.compile(r"^__(?P<key>\w+)?__\s*=\s*(?P<quote>(?:'{3}|\"{3}|'|\"))(?P<value>.*?)(?P=quote)", re.M)

    groups = {}

    for match in token_pattern.finditer(code):
        group = match.groupdict()
        groups[group["key"]] = group["value"]

    return types.SimpleNamespace(**groups)


def parse_requirements():
    with open("requirements.txt") as fp:
        dependencies = (d.strip() for d in fp.read().split("\n") if d.strip())
        return [d for d in dependencies if not d.startswith("#")]


metadata = parse_meta()

extensions = [Accelerator("hikari.internal.marshaller", ["hikari/internal/marshaller.cpp"])]

setuptools.setup(
    name=name,
    version=metadata.version,
    description="A sane Discord API for Python 3 built on asyncio and good intentions",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    author=metadata.author,
    author_email=metadata.email,
    license=metadata.license,
    url=metadata.url,
    packages=setuptools.find_namespace_packages(include=[name + "*"]),
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
    # Uncomment this to enable compilation of accelerated modules.
    # ext_modules=extensions,
    # cmdclass={
    #    "build_ext": BuildCommand,
    # }
)

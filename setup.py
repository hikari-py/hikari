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

import os
import re
import types

import setuptools

name = "hikari"

# """Acceleration stuff for the future."""
#
# from distutils import ccompiler
# from distutils import log
# from distutils import errors
# from setuptools.command import build_ext
#
# should_accelerate = "ACCELERATE_HIKARI" in os.environ
#
#
# class Accelerator(setuptools.Extension):
#     def __init__(self, name, sources, **kwargs):
#         super().__init__(name, sources, **kwargs)
#
#
# class BuildCommand(build_ext.build_ext):
#     def build_extensions(self):
#         if should_accelerate:
#             for ext in self.extensions:
#                 if isinstance(ext, Accelerator):
#                     self.build_accelerator(ext)
#                 else:
#                     self.build_extension(ext)
#
#     def build_accelerator(self, ext):
#         try:
#             self.build_extension(ext)
#         except errors.CompileError as ex:
#             log.warn("Compilation of %s failed, so this module will not be accelerated: %s", ext, ex)
#         except errors.LinkError as ex:
#             log.warn("Linking of %s failed, so this module will not be accelerated: %s", ext, ex)
#
#
# if should_accelerate:
#     log.warn("!!!!!!!!!!!!!!!!!!!!EXPERIMENTAL!!!!!!!!!!!!!!!!!!!!")
#     log.warn("HIKARI ACCELERATION SUPPORT IS ENABLED: YOUR MILEAGE MAY VARY :^)")
#
#     extensions = [Accelerator("hikari.internal.marshaller", ["hikari/internal/marshaller.cpp"], **cxx_compile_kwargs)]
#
#     cxx_spec = "c++17"
#     compiler_type = ccompiler.get_default_compiler()
#
#     if compiler_type in ("unix", "cygwin", "mingw32"):
#         log.warn("using unix-style compiler toolchain: %s", compiler_type)
#         cxx_debug_flags = f"-Wall -Wextra -Wpedantic -std={cxx_spec} -ggdb -DDEBUG -O0".split()
#         cxx_release_flags = f"-Wall -Wextra -Wpedantic -std={cxx_spec} -O3 -DNDEBUG".split()
#         cxx_debug_linker_flags = []
#         cxx_release_linker_flags = []
#     elif compiler_type == "msvc":
#         # compiler flags:
#         # https://docs.microsoft.com/en-us/cpp/build/reference/compiler-options-listed-alphabetically?view=vs-2019
#         # linker flags:
#         # https://docs.microsoft.com/en-us/cpp/build/reference/opt-optimizations?view=vs-2019
#         log.warn("using Microsoft Visual C/C++ compiler toolchain: %s", compiler_type)
#         cxx_debug_flags = f"/D DEBUG=1 /Od /Wall /std:{cxx_spec}".split()
#         cxx_release_flags = f"/D NDEBUG=1 /O2 /Qspectre /Wall /std:{cxx_spec}".split()
#         cxx_debug_linker_flags = "/DEBUG /OPT:NOREF,NOICF,NOLBR".split()
#         cxx_release_linker_flags = "/OPT:REF,ICF,LBR".split()
#
#     if "DEBUG_HIKARI" in os.environ:
#         cxx_compile_kwargs = dict(
#             extra_compile_args=cxx_debug_flags, extra_link_args=cxx_debug_linker_flags, language="c++",
#         )
#     else:
#         cxx_compile_kwargs = dict(
#             extra_compile_args=cxx_release_flags, extra_link_args=cxx_release_linker_flags, language="c++",
#         )
#
#     log.warn("Building c++ with opts: %s", cxx_compile_kwargs)
#
#     log.warn("!!!!!!!!!!!!!!!!!!!!EXPERIMENTAL!!!!!!!!!!!!!!!!!!!!")
# else:
#     log.warn("skipping building of accelerators for %s", name)
#     extensions = []


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
    project_urls={
        "Documentation": metadata.docs,
        "Source": metadata.url,
        "CI": metadata.ci,
        "Tracker": metadata.issue_tracker,
        "Discord": metadata.discord_invite,
    },
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
        # "Programming Language :: C",
        # "Programming Language :: C++",
        "Programming Language :: Python :: Implementation :: CPython",
        # "Programming Language :: Python :: Implementation :: Stackless",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    entry_points={"console_scripts": ["hikari = hikari.__main__:main", "hikari-test = hikari.clients.test:main",]},
    provides="hikari",
    # """Acceleration stuff for the future."""
    # ext_modules=extensions,
    # cmdclass={"build_ext": BuildCommand},
)

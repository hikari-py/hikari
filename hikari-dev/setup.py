# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""This is a mock package to install the dev requirements for hikari."""
import pathlib

import setuptools


def parse_requirements_file(path):
    with open(path) as fp:
        raw_dependencies = fp.readlines()

    dependencies = []
    for dependency in raw_dependencies:
        comment_index = dependency.find("#")
        if comment_index == 0:
            continue

        if comment_index != -1:  # Remove any comments after the requirement
            dependency = dependency[:comment_index]

        if d := dependency.strip():
            dependencies.append(d)

    return dependencies


all_requirement_files_path = pathlib.Path(".").glob("*-requirements.txt")

all_extras = []
extras = {"all": all_extras}
magic_len = len("-requirements.txt")
for path in all_requirement_files_path:
    name = str(path)[:-magic_len]

    requirements = parse_requirements_file(path)
    all_extras.extend(requirements)
    extras[name] = requirements

setuptools.setup(name="hikari-dev", extras_require=extras)

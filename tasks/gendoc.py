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
"""
Generates module documentation for me. Turns out Sphinx is a pain for doing this in a "simple" way. All the stuff on
PyPi for doing this has annoying quirks that I don't care for, like not supporting asyncio, or only working on a Tuesday
or during a full moon, and it is just angering.

Arg1 = package to document
Arg2 = templates dir for gendoc
Arg3 = path to write index.rst to
Arg4 = path to write module rst files to
"""
import os
import sys

import jinja2


def is_valid_python_file(path):
    base = os.path.basename(path)
    return not base.startswith("__") and (os.path.isdir(path) or base.endswith(".py"))


def to_module_name(base):
    bits = base.split("/")
    bits[-1], _ = os.path.splitext(bits[-1])
    return ".".join(bits)


def iter_all_module_paths_in(base):
    stack = [os.path.join(base)]
    while stack:
        next_path = stack.pop()

        yield next_path

        if os.path.isdir(next_path):
            children = os.listdir(next_path)

            for f in children:
                next_file = os.path.join(next_path, f)
                if is_valid_python_file(next_file):
                    if os.path.isdir(next_file):
                        stack.append(next_file)
                    elif os.path.isfile(next_file):
                        yield next_file


def main(*argv):
    base = argv[0].replace('.', '/')
    template_dir = argv[1]
    index_file = argv[2]
    documentation_path = argv[3]

    modules = [to_module_name(module_path) for module_path in sorted(iter_all_module_paths_in(base))]
    print(f"Found {len(modules)} modules to document:", *modules, sep="\n   - ")

    with open(os.path.join(template_dir, "index.rst")) as fp:
        print("Reading", fp.name)
        index_template = jinja2.Template(fp.read())

    with open(index_file, "w") as fp:
        print("Writing", fp.name)
        fp.write(index_template.render(modules=modules, documentation_path=documentation_path))

    with open(os.path.join(template_dir, "module.rst")) as fp:
        print("Reading", fp.name)
        module_template = jinja2.Template(fp.read())

    os.makedirs(documentation_path, 0o1777, exist_ok=True)

    for m in modules:
        with open(os.path.join(documentation_path, m + ".rst"), "w") as fp:
            submodules = [sm for sm in modules if sm.startswith(m) and sm != m]

            print("Writing", fp.name)

            fp.write(module_template.render(module=m, rule=len(m) * "#", submodules=submodules))


if __name__ == "__main__":
    os.chdir(sys.argv[1])
    main(*sys.argv[2:])

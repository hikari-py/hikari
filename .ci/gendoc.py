#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

import jinja2


def remove_base_path(base, path):
    base = os.path.abspath(os.path.join(base, ".."))
    path = os.path.abspath(path)
    truncated = path[len(base):]
    return truncated[1:] if truncated.startswith("/") or truncated.startswith("\\") else truncated


def is_valid_python_file(path):
    base = os.path.basename(path)
    return not base.startswith('__') and (os.path.isdir(path) or base.endswith('.py'))


def to_module_name(rel_path, base):
    rel_path = remove_base_path(base, rel_path)
    bits = rel_path.split('/')
    bits[-1], _ = os.path.splitext(bits[-1])
    return '.'.join(bits)


def iter_all_module_paths_in(base):
    stack = [base]
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
    base = argv[0]
    modules = [to_module_name(module_path, base) for module_path in sorted(iter_all_module_paths_in(base))]
    print(f"Found {len(modules)} modules to document:", *modules, sep='\n   - ')

    tempalate_dir = argv[1]

    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(tempalate_dir))

    index_template = environment.get_template('index.rst')
    module_template = jinja2.Template('module.rst')
    class_template = jinja2.Template('class.rst')
    function_template = jinja2.Template('function.rst')
    variable_template = jinja2.Template('variable.rst')

    documentation_path = argv[2]
    os.makedirs(documentation_path, 0o644, exist_ok=True)


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    main(*sys.argv[1:])

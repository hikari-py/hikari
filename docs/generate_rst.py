#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A jJavadoc-like tool for Python that wasn't a massive headache to use and configure, didn't have a billion dependencies,
and had sane defaults would be awesome, but whatever. Until that magical day comes I guess this will do.
"""
import importlib
import os
import pkgutil
import sys
import textwrap
import traceback


def parse_argv():
    if len(sys.argv) != 5:
        raise RuntimeError("Usage: <working_dir> <package_name> <output_dir> <toc_file>")

    working_dir, package, output_dir, toc_file = sys.argv[1:5]
    print('Introspecting', package, 'in', working_dir, 'and producing docs in', output_dir, 'and TOC file', toc_file)

    assert os.path.isdir(os.path.join(working_dir, package)) or os.path.isfile(
        os.path.join(working_dir, package + '.py'))

    if not os.path.exists(output_dir):
        print('Creating', output_dir, 'as it does not exist')
        os.mkdir(output_dir)

    print('Adding', working_dir, 'to PYTHON_PATH')
    sys.path.append(working_dir)

    return package, output_dir, toc_file


def mk_tree(pkg):
    # modules = collections.OrderedDict()
    # If someone finds it amusing to add a symbolic link, then the joke is on them, it won't do anything.
    considered = set()
    stack = [pkg]

    print('Producing pkg tree')
    while stack:
        target = stack.pop()
        print((len(stack) + 1) * '>', target)

        # Make Sphinx ignore it if it is fubared.
        try:
            m = importlib.import_module(target)
            considered.add(target)
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)  # verbose way doesn't cause a PEP8 violation.
            continue

        # modules[target] = m
        yield target

        if hasattr(m, '__path__'):
            print((len(stack) + 1) * '!', 'Queueing', target, 'child nodes')
            next_target = m.__path__[0] if isinstance(m.__path__, list) else m.__path__
            next_target = next_target[2:] if next_target.startswith('./') else next_target
            children = {f'{next_target}/{name}' for _, name, _ in pkgutil.walk_packages([next_target])} - considered
            children = (c.replace('\\', '/').replace('/', '.') for c in children)
            stack += children
    # return modules


def auto_doc(out_dir, name):
    path = os.path.join(out_dir, name + '.rst')
    print('Generating', path)
    with open(path, 'w') as fp:
        content = textwrap.dedent(f'''
            {name}
            {"=" * len(name)}
            
            .. automodule:: {name}
                :members:
        ''')

        print('Wrote', fp.write(content), 'bytes to', path)

        return name


def make_toc(toc_file, entries):
    print('Creating TOC', toc_file)

    with open(toc_file, 'w') as fp:
        fp.write(textwrap.dedent('''
            hikari technical documentation
            ##############################
            
            .. toctree::
                :maxdepth: 8
                :caption: Contents:
        '''))

        for entry in entries:
            print('Dumping entry', entry, 'to TOC')
            fp.write(f'\n    {entry}')

        fp.write(textwrap.dedent('''
        
            Indices and tables
            ------------------

            * :ref:`genindex`
            * :ref:`modindex`
            * :ref:`search`
        '''))

    print('TOC complete.')


pkg, out, toc_file = parse_argv()
make_toc(toc_file, (auto_doc(out, src_file) for src_file in mk_tree(pkg)))

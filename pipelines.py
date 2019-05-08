#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Makes running stuff on CI and locally in the same way easier for me.
"""
import importlib
import os
import sys


PACKAGE = 'hikari'
COVERAGE_ARGS = f'--branch --concurrency=thread --source={PACKAGE} --timid -m'
PYTEST_ARGS = '-l -v --color=yes tests/'

dispatcher = {}


def splash():
    import hikari

    print('HIKARI', f'v{hikari.__version__}', 'CI helper')
    print(f'\t{hikari.__copyright__}')
    print(f'\tLICENSED UNDER {hikari.__license__}')
    print(f'\tTHANKS TO {", ".join(hikari.__contributors__)}')
    print()


def option(description):
    def decorator(function):
        dispatcher[function.__name__.lower()] = (function, description)
        return function
    return decorator


def sp_run(executable):
    print('$', executable)
    os.system(executable)


def pip(package, *args):
    try:
        importlib.import_module(package)
        print('Found', package)
    except ImportError:
        sp_run('python -m pip ' + ' '.join(args))
    finally:
        return importlib.import_module(package)


@option("Run unit tests only")
def uts(*_):
    sp_run(f'coverage run {COVERAGE_ARGS} pytest --deselect tests/integration {PYTEST_ARGS}')
    sp_run('coverage report -m')


@option("Run integration tests only")
def its(*_):
    sp_run(f'coverage run {COVERAGE_ARGS} pytest --deselect tests/unit {PYTEST_ARGS}')
    sp_run('coverage report -m')


@option("Run unit tests and integration tests")
def tests(*_):
    sp_run(f'coverage run {COVERAGE_ARGS} pytest {PYTEST_ARGS}')
    sp_run('coverage report -m --fail-under=90')


@option("Run black code formatter. Pass --check to only check, not fix.")
def black(*args):
    if '--check' in args:
        flags = '--check'
    else:
        flags = ''
    pip('black', 'install', 'black')
    sp_run(f'python -m black {PACKAGE} --verbose {flags}')


@option("Create Sphinx documentation")
def docs(*_):
    pip('sphinx', 'install', 'sphinx')
    pip('sphinx_autodoc_typehints', 'install', 'sphinx-autodoc-typehints')
    pip('sphinxcontrib.asyncio', 'install', 'sphinxcontrib-asyncio')
    pip('sphinx_bootstrap_theme', 'install', 'sphinx_bootstrap_theme')
    sp_run(f'python docs/generate_rst.py . {PACKAGE} docs/source docs/source/index.rst')
    sp_run('cd docs && make clean html && cd ..')


@option("Run static code analysis")
def sast(*_):
    pip('bandit', 'install', 'bandit')
    sp_run(f'bandit -r {PACKAGE} -n 3')


if __name__ == '__main__':
    try:
        task = sys.argv[1].lower()
        if task in ('help', 'usage', '-h', '--help', '/?'):
            print('USAGE:', sys.argv[0], '<OPTION> [arg1 arg2 ... argn]')
            print('  Options:')
            for name, (_, description) in sorted(dispatcher.items(), key=lambda pair: pair[0]):
                print(' ' * 3, name, '-', description)
        else:
            splash()
            dispatcher[task][0](*sys.argv[2:])
    except KeyError:
        raise SystemExit("ERR: Invalid option provided")
    except IndexError:
        raise SystemExit("ERR: No arguments provided. Run with --help for usage information")
    except Exception:
        raise SystemExit("ERR: Unexpected error occurred")

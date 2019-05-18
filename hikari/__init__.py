#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A lightweight, flexible, customizable Discord API wrapper for Python.
"""
import setuptools_scm as __setuptools_scm

__author__ = "Nekokatt"
__copyright__ = f"© 2019 {__author__}"
__license__ = "zlib"
__version__ = __setuptools_scm.get_version(version_scheme=__setuptools_scm.version.guess_next_dev_version)
__contributors__ = {"LunarCoffee"}

# Apply compatibility monkey patching.
from . import _compat

#!/usr/bin/env python
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
Black uses a multiprocessing Lock, which is fine until the
platform doesn't support sem_open syscalls, then all hell
breaks loose. This should allow it to fail silently :-)
"""
import multiprocessing
import os
import sys

try:
    multiprocessing.Lock()
except ImportError as ex:
    print("Will not run black because", str(ex).lower())
    print("Exiting with success code anyway")
    exit(0)
else:
    os.system(f'black {" ".join(sys.argv[1:])}')

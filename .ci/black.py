#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

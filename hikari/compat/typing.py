#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type checking compatibility.
"""
import typing as _typing

# noinspection PyUnresolvedReferences
from typing import *

#: Not implemented by PyPy3.6
NoReturn = getattr(_typing, "NoReturn", None)

try:
    raise RuntimeError
except RuntimeError as __ex:
    #: Type of a traceback.
    TracebackType = type(__ex.__traceback__)
    del __ex

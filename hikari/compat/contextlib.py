#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contextlib compatibility methods.
"""
# noinspection PyUnresolvedReferences
from contextlib import *


#: Not implemented in Python3.6, this one will provide aenter and aexit by default if unspecified.
class AbstractAsyncContextManager:
    """An abstract base class for asynchronous context managers."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

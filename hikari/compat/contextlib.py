#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contextlib compatibility methods.
"""
import abc as _abc

# noinspection PyUnresolvedReferences
from contextlib import *


#: Not implemented in Python3.6
class AbstractAsyncContextManager(_abc.ABC):
    """An abstract base class for asynchronous context managers."""

    async def __aenter__(self):
        return self

    @_abc.abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

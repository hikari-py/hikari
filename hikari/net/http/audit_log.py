#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP component implementation for handling Audit Logs.
"""
import abc

from . import base


class AuditLogMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows interaction with the Audit Log API.
    """

    __slots__ = []

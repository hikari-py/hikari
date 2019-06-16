#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Invitation API.
"""
import abc

from . import base


class InviteMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows interaction with the Invitation HTTP API.
    """

    __slots__ = []

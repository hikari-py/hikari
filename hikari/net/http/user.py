#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP User API (inspecting users, sending DMs, etc).
"""
import abc

from . import base


class UserMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows interaction with the HTTP User API.
    """

    __slots__ = []

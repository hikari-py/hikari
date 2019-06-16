#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Guild API.
"""
import abc

from . import base


class GuildMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows interaction with the Guild HTTP API.
    """

    __slots__ = []

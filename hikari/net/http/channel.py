#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP messaging and channel handling API.
"""
import abc

from . import base


class ChannelMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows interaction with the Channels and Messages APIs.
    """

    __slots__ = []

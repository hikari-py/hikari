#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP webhook API with rate limiting.
"""
import abc

from . import base


class WebhookMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows for the creation of webhooks.
    """

    __slots__ = []

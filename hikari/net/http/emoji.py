#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Emoji API.
"""
import abc

from . import base


class EmojiMixin(base.MixinBase, abc.ABC):
    """
    HTTP component that allows interaction with the Emoji API.
    """

    __slots__ = []

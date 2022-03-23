# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Enum of Discord locales."""
from __future__ import annotations

__all__ = [
    "Locale",
]

import typing

from hikari.internal import enums


@typing.final
class Locale(str, enums.Enum):
    """Possible user/guild locales."""

    DA = "da"
    """Language is Danish (da)"""

    DE = "de"
    """Language is German (de)"""

    EN_GB = "en-GB"
    """Language is English, UK (en-GB)"""

    EN_US = "en-US"
    """Language is English, US (en-US)"""

    ES_ES = "es-ES"
    """Language is Spanish (es-ES)"""

    FR = "fr"
    """Language is French (fr)"""

    HR = "hr"
    """Language is Croatian (hr)"""

    IT = "it"
    """Language is Italian (it)"""

    LT = "lt"
    """Language is Lithuanian (lt)"""

    HU = "hu"
    """Language is Hungarian (hu)"""

    NL = "nl"
    """Language is Dutch (nl)"""

    NO = "no"
    """Language is Norwegian (no)"""

    OL = "pl"
    """Language is Polish (pl)"""

    PT_BR = "pt-BR"
    """Language is Portuguese, Bralizian (pt-BR)"""

    RO = "ro"
    """Language is Romian (ro)"""

    FI = "fi"
    """Language is Finnish (fi)"""

    SV_SE = "sv-SE"
    """Language is Swedish (sv-SE)"""

    VI = "vi"
    """Language is Vietnamese (vi)"""

    TR = "tr"
    """Language is Turkish (tr)"""

    CS = "cs"
    """Language is Czech (cs)"""

    EL = "el"
    """Language is Greek (el)"""

    BG = "bg"
    """Language is Bulgarian (bg)"""

    RU = "ru"
    """Language is Russian (ru)"""

    UK = "uk"
    """Language is Ukrainian (uk)"""

    HI = "hi"
    """Language is Hindi (hi)"""

    TH = "th"
    """Language is Thai (th)"""

    ZH_CN = "zh-CN"
    """Language is Chinese, China (zh-CN)"""

    JA = "ja"
    """Language is Japanese (ja)"""

    ZH_TW = "zh-TW"
    """Language is Chinese, Taiwan (zh-TW)"""

    KO = "ko"
    """Language is Korean (ko)"""

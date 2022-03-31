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
"""Enum of Discord accepted locales."""
from __future__ import annotations

__all__ = ["Locale"]

import typing

from hikari.internal import enums


@typing.final
class Locale(str, enums.Enum):
    """Possible user/guild locales."""

    DA = "da"
    """Danish"""

    DE = "de"
    """German"""

    EN_GB = "en-GB"
    """English, UK"""

    EN_US = "en-US"
    """English, US"""

    ES_ES = "es-ES"
    """Spanish"""

    FR = "fr"
    """French"""

    HR = "hr"
    """Croatian"""

    IT = "it"
    """Italian"""

    LT = "lt"
    """Lithuanian"""

    HU = "hu"
    """Hungarian"""

    NL = "nl"
    """Dutch"""

    NO = "no"
    """Norwegian"""

    OL = "pl"
    """Polish"""

    PT_BR = "pt-BR"
    """Portuguese, Bralizian"""

    RO = "ro"
    """Romian"""

    FI = "fi"
    """Finnish"""

    SV_SE = "sv-SE"
    """Swedish"""

    VI = "vi"
    """Vietnamese"""

    TR = "tr"
    """Turkish"""

    CS = "cs"
    """Czech"""

    EL = "el"
    """Greek"""

    BG = "bg"
    """Bulgarian"""

    RU = "ru"
    """Russian"""

    UK = "uk"
    """Ukrainian"""

    HI = "hi"
    """Hindi"""

    TH = "th"
    """Thai"""

    ZH_CN = "zh-CN"
    """Chinese, China"""

    JA = "ja"
    """Japanese"""

    ZH_TW = "zh-TW"
    """Chinese, Taiwan"""

    KO = "ko"
    """Korean"""

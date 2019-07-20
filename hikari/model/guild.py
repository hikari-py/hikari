#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
Guild models.
"""
from __future__ import annotations

__all__ = ()

import enum
from hikari.model import base


class PartialGuild(base.Snowflake):
    """Returned if the guild is not available yet..."""

    __slots__ = ()


class Guild(PartialGuild):
    __slots__ = ()


class DefaultMessageNotificationLevel(enum.IntEnum):
    ...


class ExplicitContentFilterLevel(enum.IntEnum):
    ...


class MFALevel(enum.IntEnum):
    ...


class VerificationLevel(enum.IntEnum):
    ...


class PremiumTier(enum.IntEnum):
    ...


class GuildEmbed(base.Snowflake):
    __slots__ = ()


class Ban(base.StatefulModel):
    __slots__ = ()

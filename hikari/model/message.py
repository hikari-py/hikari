#!/usr/bin/env python
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
Messages and attachments.
"""
from __future__ import annotations

__all__ = ()

import enum

from hikari.model import base


class MessageType(enum.IntEnum):
    ...


class MessageActivityType(enum.IntEnum):
    ...


class Message(base.Snowflake):
    __slots__ = ()


class MessageActivity(base.Model):
    __slots__ = ()


class MessageApplication(base.Model):
    __slots__ = ()


class Attachment(base.Snowflake):
    __slots__ = ()

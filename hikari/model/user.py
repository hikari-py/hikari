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
Generic users not bound to a guild, and guild-bound member definitions.
"""
__all__ = ("User", "Member")

import dataclasses

from hikari.model import base
from hikari.utils import delegate


@dataclasses.dataclass()
class User(base.SnowflakeMixin):
    __slots__ = ("id", "username", "discriminator", "avatar", "bot")

    id: int
    username: str
    discriminator: int
    avatar: bytes
    bot: bool


class Member(base.SnowflakeMixin, metaclass=delegate.DelegatedMeta, delegate_to=(User, "_user")):
    """
    A specialization of a user which provides
    """
    __slots__ = ("_user",)

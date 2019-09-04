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
Permission overwrites.
"""
from __future__ import annotations

import enum

from hikari.core.model import base
from hikari.core.model import permission
from hikari.core.model import role
from hikari.core.model import user
from hikari.core.utils import transform


class OverwriteEntityType(base.NamedEnum, enum.Enum):
    """
    The type of "thing" that a permission overwrite sets the permissions for.

    These values act as types, so you can write expressions such as:

    .. code-block:: python

        if isinstance(user_or_role, overwrite.type):
            ...

    ...should you desire to do so.
    """

    #: A member.
    MEMBER = user.Member
    #: A role.
    ROLE = role.Role

    def __instancecheck__(self, instance):
        return isinstance(instance, self.value)

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self.value)


@base.dataclass()
class Overwrite(base.Snowflake):
    """
    Representation of some permissions that have been explicitly allowed or denied as an override from the defaults.
    """

    __slots__ = ("id", "type", "allow", "deny")

    #: The ID of this overwrite.
    #:
    #: :type: :class:`int`
    id: int

    #: The type of entity that was changed.
    #:
    #: :type: :class:`hikari.core.model.overwrite.OverwriteEntityType`
    type: OverwriteEntityType

    #: The bitfield of permissions explicitly allowed.
    #:
    #: :type: :class:`hikari.core.model.permission.Permission`
    allow: permission.Permission

    #: The bitfield of permissions explicitly denied.
    #:
    #: :type: :class:`hikari.core.model.permission.Permission`
    deny: permission.Permission

    @property
    def default(self) -> permission.Permission:
        """
        Returns:
            The bitfield of all permissions that were not changed in this overwrite.
        """
        # noinspection PyTypeChecker
        return permission.Permission(permission.Permission.all() ^ (self.allow | self.deny))

    def __init__(self, payload):
        self.id = transform.get_cast(payload, "id", int)
        self.type = transform.get_cast_or_raw(payload, "type", OverwriteEntityType.from_discord_name)
        self.allow = transform.get_cast_or_raw(payload, "allow", permission.Permission)
        self.deny = transform.get_cast_or_raw(payload, "deny", permission.Permission)


__all__ = ["Overwrite", "OverwriteEntityType"]

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

import dataclasses
import enum

from hikari.core.models import base
from hikari.core.models import permissions
from hikari.core.models import roles
from hikari.core.models import users
from hikari.core.utils import transform, auto_repr


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
    MEMBER = users.Member
    #: A role.
    ROLE = roles.Role

    def __instancecheck__(self, instance):
        return isinstance(instance, self.value)

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self.value)


@dataclasses.dataclass()
class Overwrite(base.HikariModel, base.Snowflake):
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
    #: :type: :class:`hikari.core.models.overwrite.OverwriteEntityType`
    type: OverwriteEntityType

    #: The bitfield of permissions explicitly allowed.
    #:
    #: :type: :class:`hikari.core.models.permission.Permission`
    allow: permissions.Permission

    #: The bitfield of permissions explicitly denied.
    #:
    #: :type: :class:`hikari.core.models.permission.Permission`
    deny: permissions.Permission

    __repr__ = auto_repr.repr_of("id", "type", "allow", "deny", "default")

    @property
    def default(self) -> permissions.Permission:
        """
        Returns:
            The bitfield of all permissions that were not changed in this overwrite.
        """
        # noinspection PyTypeChecker
        return permissions.Permission(permissions.Permission.all() ^ (self.allow | self.deny))

    def __init__(self, payload):
        self.id = int(payload["id"])
        self.type = OverwriteEntityType.from_discord_name(payload["type"])
        self.allow = transform.try_cast(payload["allow"], permissions.Permission)
        self.deny = transform.try_cast(payload["deny"], permissions.Permission)


__all__ = ["Overwrite", "OverwriteEntityType"]

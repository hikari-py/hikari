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
__all__ = ("Overwrite", "OverwriteEntityType")

import dataclasses

from hikari.model import base
from hikari.model import permission
from hikari.model import role
from hikari.model import user
from hikari.utils import transform



class OverwriteEntityType(base.NamedEnum):
    MEMBER = user.Member
    ROLE = role.Role

    def __instancecheck__(self, instance):
        return isinstance(instance, self.value)

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self.value)


@dataclasses.dataclass()
class Overwrite(base.SnowflakeMixin):
    """
    Representation of some permissions that have been explicitly allowed or denied as an override from the defaults.
    """
    __slots__ = ("id", "type", "allow", "deny")

    #: The ID of this overwrite.
    id: int
    #: The type of entity that was changed.
    type: OverwriteEntityType
    #: The bitfield of permissions explicitly allowed.
    allow: permission.Permission
    #: The bitfield of permissions explicitly denied.
    deny: permission.Permission

    @property
    def default(self) -> permission.Permission:
        """
        Returns:
            The bitfield of all permissions that were not changed in this overwrite.
        """
        return permission.Permission(permission.Permission.all() ^ (self.allow | self.deny))

    @staticmethod
    def from_dict(payload):
        return Overwrite(
            id=transform.get_cast(payload, "id", int),
            type=transform.get_cast_or_raw(payload, "type", OverwriteEntityType.from_discord_name),
            allow=transform.get_cast_or_raw(payload, "allow", permission.Permission),
            deny=transform.get_cast_or_raw(payload, "deny", permission.Permission),
        )

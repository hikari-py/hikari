#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import transformations
from hikari.orm.models import interfaces
from hikari.orm.models import members
from hikari.orm.models import permissions
from hikari.orm.models import roles


class OverwriteEntityType(interfaces.INamedEnum, enum.Enum):
    """
    The type of "thing" that a permission overwrite sets the permissions for.

    These values act as types, so you can write expressions such as:

    .. code-block:: python

        if isinstance(user_or_role, overwrite.type):
            ...

    ...should you desire to do so.
    """

    #: A member.
    MEMBER = members.Member
    #: A role.
    ROLE = roles.Role

    def __instancecheck__(self, instance: typing.Any) -> bool:
        return isinstance(instance, self.value)

    def __subclasscheck__(self, subclass: typing.Type) -> bool:
        return issubclass(subclass, self.value)


class Overwrite(interfaces.ISnowflake):
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
    #: :type: :class:`hikari.orm.models.overwrites.OverwriteEntityType`
    type: OverwriteEntityType

    #: The bitfield of permissions explicitly allowed.
    #:
    #: :type: :class:`hikari.orm.models.permissions.Permission`
    allow: permissions.Permission

    #: The bitfield of permissions explicitly denied.
    #:
    #: :type: :class:`hikari.orm.models.permissions.Permission`
    deny: permissions.Permission

    __repr__ = auto_repr.repr_of("id", "type", "allow", "deny", "default")

    @property
    def default(self) -> permissions.Permission:
        """
        Returns:
            The bitfield of all permissions that were not changed in this overwrite.
        """
        # noinspection PyTypeChecker
        all_perms = ~permissions.NONE
        return permissions.Permission(all_perms ^ (self.allow | self.deny))

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.type = OverwriteEntityType.from_discord_name(payload["type"])
        self.allow = transformations.try_cast(payload["allow"], permissions.Permission)
        self.deny = transformations.try_cast(payload["deny"], permissions.Permission)


#: A :class:`Overwrite`, or an :class:`int`/:class:`str` ID of one.
OverwriteLikeT = typing.Union[interfaces.RawSnowflakeT, Overwrite]


__all__ = ["Overwrite", "OverwriteEntityType"]

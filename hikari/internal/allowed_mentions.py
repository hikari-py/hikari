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
"""Logic for generating a allowed mentions dict objects.

|internal|
"""

__all__ = ["generate_allowed_mentions"]

import typing

from hikari import bases
from hikari import guilds
from hikari import users
from hikari.internal import assertions
from hikari.internal import more_collections


def generate_allowed_mentions(
    mentions_everyone: bool,
    user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool],
    role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool],
) -> typing.Dict[str, typing.Sequence[str]]:
    """Generate an allowed mentions object based on input mention rules.

    Parameters
    ----------
    mentions_everyone : :obj:`~bool`
        Whether ``@everyone`` and ``@here`` mentions should be resolved by
        discord and lead to actual pings.
    user_mentions : :obj:`~typing.Union` [ :obj:`~typing.Collection` [ :obj:`~typing.Union` [ :obj:`~hikari.users.User`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ], :obj:`~bool` ]
        Either an array of user objects/IDs to allow mentions for,
        :obj:`~True` to allow all user mentions or :obj:`~False` to block all
        user mentions from resolving.
    role_mentions : :obj:`~typing.Union` [ :obj:`~typing.Collection` [ :obj:`~typing.Union` [ :obj:`~hikari.guilds.GuildRole`, :obj:`~hikari.entities.Snowflake`, :obj:`~int` ] ], :obj:`~bool` ]
        Either an array of guild role objects/IDs to allow mentions for,
        :obj:`~True` to allow all role mentions or :obj:`~False` to block all
        role mentions from resolving.

    Returns
    -------
    :obj:`~typing.Dict` [ :obj:`~str`, :obj:`~typing.Sequence` [ :obj:`~str` ] ]
        The resulting allowed mentions dict object.

    Raises
    ------
    :obj:`~ValueError`
        If more than 100 unique objects/entities are passed for
        ``role_mentions`` or ``user_mentions.
    """
    parsed_mentions = []
    allowed_mentions = {}
    if mentions_everyone is True:
        parsed_mentions.append("everyone")
    if user_mentions is True:
        parsed_mentions.append("users")
    # This covers both `False` and an array of IDs/objs by using `user_mentions or EMPTY_SEQUENCE`, where a
    # resultant empty list will mean that all user mentions are blacklisted.
    else:
        allowed_mentions["users"] = list(
            # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
            dict.fromkeys(
                str(user.id if isinstance(user, bases.UniqueEntity) else int(user))
                for user in user_mentions or more_collections.EMPTY_SEQUENCE
            )
        )
        assertions.assert_that(len(allowed_mentions["users"]) <= 100, "Only up to 100 users can be provided.")
    if role_mentions is True:
        parsed_mentions.append("roles")
    # This covers both `False` and an array of IDs/objs by using `user_mentions or EMPTY_SEQUENCE`, where a
    # resultant empty list will mean that all role mentions are blacklisted.
    else:
        allowed_mentions["roles"] = list(
            # dict.fromkeys is used to remove duplicate entries that would cause discord to return an error.
            dict.fromkeys(
                str(role.id if isinstance(role, bases.UniqueEntity) else int(role))
                for role in role_mentions or more_collections.EMPTY_SEQUENCE
            )
        )
        assertions.assert_that(len(allowed_mentions["roles"]) <= 100, "Only up to 100 roles can be provided.")
    allowed_mentions["parse"] = parsed_mentions
    # As a note, discord will also treat an empty `allowed_mentions` object as if it wasn't passed at all, so we
    # want to use empty lists for blacklisting elements rather than just not including blacklisted elements.
    return allowed_mentions

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""General helper functions and classes that are not categorised elsewhere."""

from __future__ import annotations

__all__ = ["warning"]

import textwrap
import typing
import warnings

from hikari import bases
from hikari.internal import assertions
from hikari.internal import more_collections

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import users
    from hikari.internal import more_typing


def warning(message: str, category: typing.Type[Warning], stack_level: int = 1) -> None:
    """Generate a warning in a style consistent for this library.

    Parameters
    ----------
    message : str
        The message to display.
    category : typing.Type[Warning]
        The type of warning to raise.
    stack_level : int
        How many stack frames to go back to find the user's invocation.

    """
    warnings.warn("\n\n" + textwrap.indent(message, " " * 2), category, stacklevel=stack_level + 1)


def generate_allowed_mentions(
    mentions_everyone: bool,
    user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool],
    role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool],
) -> typing.Dict[str, typing.Sequence[str]]:
    """Generate an allowed mentions object based on input mention rules.

    Parameters
    ----------
    mentions_everyone : bool
        Whether `@everyone` and `@here` mentions should be resolved by
        discord and lead to actual pings.
    user_mentions : typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]] OR bool
        Either an array of user objects/IDs to allow mentions for,
        `True` to allow all user mentions or `False` to block all
        user mentions from resolving.
    role_mentions : typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]] OR bool
        Either an array of guild role objects/IDs to allow mentions for,
        `True` to allow all role mentions or `False` to block all
        role mentions from resolving.

    Returns
    -------
    typing.Dict[str, typing.Sequence[str]]
        The resulting allowed mentions dict object.

    Raises
    ------
    ValueError
        If more than 100 unique objects/entities are passed for
        `role_mentions` or `user_mentions.
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


# pylint: disable=too-many-arguments
async def pagination_handler(
    deserializer: typing.Callable[[typing.Any], typing.Any],
    direction: typing.Union[typing.Literal["before"], typing.Literal["after"]],
    request: typing.Callable[..., more_typing.Coroutine[typing.Any]],
    reversing: bool,
    start: str,
    maximum_limit: int,
    limit: typing.Optional[int] = None,
    id_getter: typing.Callable[[typing.Any], str] = lambda entity: str(entity.id),
) -> typing.AsyncIterator[typing.Any]:
    """Generate an async iterator for handling paginated endpoints.

    This will handle Discord's `before` and `after` pagination.

    Parameters
    ----------
    deserializer : typing.Callable[[typing.Any], typing.Any]
        The deserializer to use to deserialize raw elements.
    direction : typing.Union[`"before"`, `"after"`]
        The direction that this paginator should go in.
    request : typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]]
        The `hikari.net.rest.REST` method that should be
        called to make requests for this paginator.
    reversing : bool
        Whether the retrieved array of objects should be reversed before
        iterating through it, this is needed for certain endpoints like
        `fetch_messages_before` where the order is static regardless of
        if you're using `before` or `after`.
    start : int
        The snowflake ID that this paginator should start at, `0` may be
        passed for `forward` pagination to start at the first created
        entity and `9223372036854775807` may be passed for `before` pagination
        to start at the newest entity (based on it's snowflake timestamp).
    maximum_limit : int
        The highest number that `limit` can be set to in a request for this
        specific endpoint.
    limit : int, optional
        The amount of deserialized entities that the iterator should return
        total, will be unlimited if set to `None`.
    id_getter : typing.Callable[[typing.Any], str]

    Returns
    -------
    typing.AsyncIterator[typing.Any]
        An async iterator of the found deserialized found objects.
    """
    while payloads := await request(
        limit=maximum_limit if limit is None or limit > maximum_limit else limit, **{direction: start},
    ):
        if reversing:
            payloads.reverse()
        if limit is not None:
            limit -= len(payloads)

        for payload in payloads:
            entity = deserializer(payload)
            yield entity
        if limit == 0:
            break
        start = id_getter(entity)

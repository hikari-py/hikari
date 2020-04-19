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
"""Logic for handling Discord's generic paginated endpoints.

|internal|
"""

__all__ = ["pagination_handler"]

import typing

from hikari.internal import more_typing


async def pagination_handler(
    deserializer: typing.Callable[[typing.Any], typing.Any],
    direction: typing.Union[typing.Literal["before"], typing.Literal["after"]],
    request: typing.Callable[..., more_typing.Coroutine[typing.Any]],
    reversing: bool,
    start: typing.Union[str, None],
    limit: typing.Optional[int] = None,
    id_getter: typing.Callable[[typing.Any], str] = lambda entity: str(entity.id),
    **kwargs,
) -> typing.AsyncIterator[typing.Any]:
    """Generate an async iterator for handling paginated endpoints.

    This will handle Discord's ``before`` and ``after`` pagination.

    Parameters
    ----------
    deserializer : :obj:`~typing.Callable` [ [ :obj:`~typing.Any` ], :obj:`~typing.Any` ]
        The deserializer to use to deserialize raw elements.
    direction : :obj:`~typing.Union` [ ``"before"``, ``"after"`` ]
        The direction that this paginator should go in.
    request : :obj:`~typing.Callable` [ ``...``, :obj:`~typing.Coroutine` [ :obj:`~typing.Any`, :obj:`~typing.Any`, :obj:`~typing.Any` ] ]
        The :obj:`hikari.net.rest_sessions.LowLevelRestfulClient` method that should be
        called to make requests for this paginator.
    reversing : :obj:`~bool`
        Whether the retrieved array of objects should be reversed before
        iterating through it, this is needed for certain endpoints like
        ``fetch_messages_before`` where the order is static regardless of
        if you're using ``before`` or ``after``.
    start : :obj:`~int`, optional
        The snowflake ID that this paginator should start at, ``0`` may be
        passed for ``forward`` pagination to start at the first created
        entity and :obj:`~None` may be passed for ``before`` pagination to
        start at the newest entity (based on when it's snowflake timestamp).
    limit : :obj:`~int`, optional
        The amount of deserialized entities that the iterator should return
        total, will be unlimited if set to :obj:`~None`.
    id_getter : :obj:`~typing.Callable` [ [ :obj:`~typing.Any` ], :obj:`~str` ]
    **kwargs
        Kwargs to pass through to ``request`` for every request made along
        with the current decided limit and direction snowflake.

    Returns
    -------
    :obj:`~typing.AsyncIterator` [ :obj:`~typing.Any` ]
        An async iterator of the found deserialized found objects.

    """
    while payloads := await request(
        limit=100 if limit is None or limit > 100 else limit,
        **{direction: start if start is not None else ...},
        **kwargs,
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
        # TODO: @FasterSpeeding: can `payloads` ever be empty, leading this to be undefined?
        start = id_getter(entity)

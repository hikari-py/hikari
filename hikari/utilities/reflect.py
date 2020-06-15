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
"""Reflection utilities."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["resolve_signature", "EMPTY", "get_logger"]

import inspect
import logging
import typing

EMPTY: typing.Final[inspect.Parameter.empty] = inspect.Parameter.empty
"""A singleton that empty annotations will be set to in `resolve_signature`."""


def resolve_signature(func: typing.Callable[..., typing.Any]) -> inspect.Signature:
    """Get the `inspect.Signature` of `func` with resolved forward annotations.

    Parameters
    ----------
    func : typing.Callable[[...], ...]
        The function to get the resolved annotations from.

    !!! warning
        This will use `eval` to resolve string typehints and forward references.
        This has a slight performance overhead, so attempt to cache this info
        as much as possible.

    Returns
    -------
    typing.Signature
        A `typing.Signature` object with all forward reference annotations
        resolved.
    """
    signature = inspect.signature(func)
    resolved_typehints = typing.get_type_hints(func)
    params = []

    none_type = type(None)
    for name, param in signature.parameters.items():
        if isinstance(param.annotation, str):
            param = param.replace(annotation=resolved_typehints[name] if name in resolved_typehints else EMPTY)
        if param.annotation is none_type:
            param = param.replace(annotation=None)
        params.append(param)

    return_annotation = resolved_typehints.get("return", EMPTY)
    if return_annotation is none_type:
        return_annotation = None

    return signature.replace(parameters=params, return_annotation=return_annotation)


def get_logger(obj: typing.Union[typing.Type[typing.Any], typing.Any], *additional_args: str) -> logging.Logger:
    """Get an appropriately named logger for the given class or object.

    Parameters
    ----------
    obj : typing.Type or object
        A type or instance of a type to make a logger in the name of.
    *additional_args : str
        Additional tokens to append onto the logger name, separated by `.`.
        This is useful in some places to append info such as shard ID to each
        logger to enable shard-specific logging, for example.

    Returns
    -------
    logging.Logger
        The logger to use.
    """
    if isinstance(obj, str):
        return logging.getLogger(obj)

    obj = obj if isinstance(obj, type) else type(obj)
    return logging.getLogger(".".join((obj.__module__, obj.__qualname__, *additional_args)))

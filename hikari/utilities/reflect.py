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
"""Reflection utilities."""

from __future__ import annotations

__all__ = ["resolve_signature", "EMPTY"]

import inspect
import typing

EMPTY: typing.Final[inspect.Parameter.empty] = inspect.Parameter.empty
"""A singleton that empty annotations will be set to in `resolve_signature`."""


def resolve_signature(func: typing.Callable) -> inspect.Signature:
    """Get the `inspect.Signature` of `func` with resolved forward annotations.

    Parameters
    ----------
    func : typing.Callable[[...], ...]
        The function to get the resolved annotations from.

    Returns
    -------
    typing.Signature
        A `typing.Signature` object with all forward reference annotations
        resolved.
    """
    signature = inspect.signature(func)
    resolved_type_hints = None
    parameters = []
    for key, value in signature.parameters.items():
        if isinstance(value.annotation, str):
            if resolved_type_hints is None:
                resolved_type_hints = typing.get_type_hints(func)
            value = value.replace(annotation=resolved_type_hints[key])

        if value is type(None):
            value = None

        parameters.append(value)
    signature = signature.replace(parameters=parameters)

    if isinstance(signature.return_annotation, str):
        if resolved_type_hints is None:
            return_annotation = typing.get_type_hints(func)["return"]
        else:
            return_annotation = resolved_type_hints["return"]

        if return_annotation is type(None):
            return_annotation = None

        signature = signature.replace(return_annotation=return_annotation)

    return signature

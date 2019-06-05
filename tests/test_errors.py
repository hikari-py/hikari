#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http
import logging
import traceback

import pytest

from hikari import errors
from hikari.net import opcodes


_LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "ex",
    [
        errors.DiscordGatewayError(opcodes.GatewayServerExit(4003), "broken"),
        errors.DiscordGatewayError(opcodes.GatewayServerExit.SHARDING_REQUIRED, "Shard me"),
        errors.DiscordUnauthorized(http.HTTPStatus.UNAUTHORIZED, opcodes.JSONErrorCode.UNAUTHORIZED, "Bad token"),
        errors.DiscordForbidden(http.HTTPStatus.FORBIDDEN, opcodes.JSONErrorCode.MISSING_PERMISSIONS, "Forbidden"),
        errors.DiscordBadRequest(http.HTTPStatus.BAD_REQUEST, opcodes.JSONErrorCode.INVALID_FORM_BODY, "Bad form body"),
        errors.DiscordHTTPError(http.HTTPStatus.NOT_FOUND, opcodes.JSONErrorCode.UNKNOWN_CHANNEL, "Channel not found"),
        errors.DiscordHTTPError(http.HTTPStatus.BAD_REQUEST, opcodes.JSONErrorCode.INVALID_FORM_BODY, "Bad form body"),
        errors.HikariError("eee"),
        errors.ClientError("aaa"),
    ],
    ids=lambda ex: type(ex),
)
def test_error(ex):
    try:
        raise ex
    except type(ex) as ex:
        traceback.format_exception(type(ex), ex, ex.__traceback__)
        assert repr(ex) != ""
        assert str(ex) != ""

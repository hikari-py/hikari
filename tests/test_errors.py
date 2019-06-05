#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        errors.DiscordGatewayError(opcodes.GatewayServerExit.SHARDING_REQUIRED, "Shard plez"),
        errors.DiscordUnauthorized("you cant do that u are not allowed"),
        errors.DiscordForbidden("idfk where it is fam"),
        errors.DiscordBadRequest("fix yo code fam"),
        errors.DiscordHTTPError(404, "Not found innit"),
        errors.DiscordHTTPError(None, "Something unspecified occurred"),
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

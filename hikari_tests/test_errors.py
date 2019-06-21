#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import traceback
from http import HTTPStatus as HTTP

import pytest

from hikari import errors
from hikari import _utils
from hikari.net.opcodes import GatewayClosure as GSE
from hikari.net.opcodes import JSONErrorCode as JSON

_LOGGER = logging.getLogger(__name__)

res = _utils.Resource("http://you.local", "get", "/it/now")


@pytest.mark.parametrize(
    "ex",
    [
        errors.GatewayError(GSE(4000), "broken"),
        errors.GatewayError(GSE.SHARDING_REQUIRED, "Shard me"),
        errors.ServerError(res, HTTP.SERVICE_UNAVAILABLE),
        errors.ServerError(res, HTTP.SERVICE_UNAVAILABLE, "Service Unavailable!"),
        errors.ClientError(res, HTTP.TOO_MANY_REQUESTS, None, "You are being rate limited"),
        errors.BadRequest(res, JSON.INVALID_FORM_BODY, "Bad body"),
        errors.Unauthorized(res, JSON.UNAUTHORIZED, "Who are you"),
        errors.Forbidden(res, JSON.MISSING_PERMISSIONS, "You cant do this"),
        errors.NotFound(res, JSON.UNKNOWN_CHANNEL, "Channel was not found"),
    ],
    ids=type,
)
def test_error(ex):
    try:
        raise ex
    except type(ex) as ex:
        traceback.format_exception(type(ex), ex, ex.__traceback__)
        assert repr(ex) != ""
        assert str(ex) != ""


@pytest.mark.parametrize("ex_t", [errors.HikariError, errors.DiscordError, errors.HTTPError], ids=lambda t: t.__name__)
def test_cannot_initialize_base_exception(ex_t):
    try:
        ex_t()
        assert False, "No error was raised"
    except NotImplementedError:
        pass

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
"""Provides logging support for HTTP requests internally."""
from __future__ import annotations

__all__ = ["BaseTracer", "CFRayTracer", "DebugTracer"]

import functools
import logging
import time
import uuid

import aiohttp


class BaseTracer:
    """Base type for tracing HTTP requests."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    @functools.cached_property
    def trace_config(self):
        """Generate a trace config for aiohttp."""
        tc = aiohttp.TraceConfig()

        for name in dir(self):
            if name.startswith("on_") and name in dir(tc):
                getattr(tc, name).append(getattr(self, name))

        return tc


class CFRayTracer(BaseTracer):
    """Regular debug logging of requests to a Cloudflare resource.

    Logs information about endpoints being hit, response latency, and any
    Cloudflare rays in the response.
    """

    async def on_request_start(self, _, ctx, params):
        """Log an outbound request."""
        ctx.identifier = f"uuid4:{uuid.uuid4()}"
        ctx.start_time = time.perf_counter()

        self.logger.debug(
            "[%s] %s %s [content-type:%s, accept:%s]",
            ctx.identifier,
            params.method,
            params.url,
            params.headers.get("content-type"),
            params.headers.get("accept"),
        )

    async def on_request_end(self, _, ctx, params):
        """Log an inbound response."""
        latency = round((time.perf_counter() - ctx.start_time) * 1_000, 1)
        response = params.response
        self.logger.debug(
            "[%s] %s %s after %sms [content-type:%s, size:%s, cf-ray:%s, cf-request-id:%s]",
            ctx.identifier,
            response.status,
            response.reason,
            latency,
            response.headers.get("content-type"),
            response.headers.get("content-length", 0),
            response.headers.get("cf-ray"),
            response.headers.get("cf-request-id"),
        )


class DebugTracer(BaseTracer):
    """Provides verbose debug logging of requests.

    This logs several pieces of information during an AIOHTTP request such as
    request headers and body chunks, response headers, response body chunks,
    and other events such as DNS cache hits/misses, connection pooling events,
    and other pieces of information that can be incredibly useful for debugging
    performance issues and API issues.

    !!! warn
        This may log potentially sensitive information such as authorization
        tokens, so ensure those are removed from debug logs before proceeding
        to send logs to anyone.
    """

    async def on_request_start(self, _, ctx, params):
        """Log an outbound request."""
        ctx.identifier = f"uuid4:{uuid.uuid4()}"
        ctx.start_time = time.perf_counter()

        self.logger.debug(
            "[%s] %s %s\n  request headers: %s\n  request body: %s",
            ctx.identifier,
            params.method,
            params.url,
            params.headers,
            getattr(ctx.trace_request_ctx, "request_body", "<unknown>"),
        )

    async def on_request_end(self, _, ctx, params):
        """Log an inbound response."""
        latency = round((time.perf_counter() - ctx.start_time) * 1_000, 2)
        response = params.response
        self.logger.debug(
            "[%s] %s %s %s after %sms\n  response headers: %s\n  response body: %s",
            ctx.identifier,
            response.real_url,
            response.status,
            response.reason,
            latency,
            response.raw_headers,
            await response.read(),
        )

    async def on_request_exception(self, _, ctx, params):
        """Log an error while making a request."""
        self.logger.debug("[%s] encountered exception", ctx.identifier, exc_info=params.exception)

    async def on_connection_queued_start(self, _, ctx, __):
        """Log when we have to wait for a new connection in the pool."""
        self.logger.debug("[%s] is waiting for a connection", ctx.identifier)

    async def on_connection_reuseconn(self, _, ctx, __):
        """Log when we re-use an existing connection in the pool."""
        self.logger.debug("[%s] has acquired an existing connection", ctx.identifier)

    async def on_connection_create_end(self, _, ctx, __):
        """Log when we create a new connection in the pool."""
        self.logger.debug("[%s] has created a new connection", ctx.identifier)

    async def on_dns_cache_hit(self, _, ctx, params):
        """Log when we reuse the DNS cache and do not have to look up an IP."""
        self.logger.debug("[%s] has retrieved the IP of %s from the DNS cache", ctx.identifier, params.host)

    async def on_dns_cache_miss(self, _, ctx, params):
        """Log when we have to query a DNS server for an IP address."""
        self.logger.debug("[%s] will perform DNS lookup of new host %s", ctx.identifier, params.host)

    async def on_dns_resolvehost_start(self, _, ctx, __):
        """Store the time the DNS lookup started at."""
        ctx.dns_start_time = time.perf_counter()

    async def on_dns_resolvehost_end(self, _, ctx, params):
        """Log how long a DNS lookup of an IP took to perform."""
        latency = round((time.perf_counter() - ctx.dns_start_time) * 1_000, 2)
        self.logger.debug("[%s] DNS lookup of host %s took %sms", ctx.identifier, params.host, latency)

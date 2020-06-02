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
import io
import logging
import time
import uuid

import aiohttp.abc


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
    """Regular _debug logging of requests to a Cloudflare resource.

    Logs information about endpoints being hit, response latency, and any
    Cloudflare rays in the response.
    """

    async def on_request_start(self, _, ctx, params):
        """Log an outbound request."""
        ctx.identifier = f"request_id:{uuid.uuid4()}"
        ctx.start_time = time.perf_counter()

        self.logger.debug(
            "%s %s [content-type:%s, accept:%s] [%s]",
            params.method,
            params.url,
            params.headers.get("content-type"),
            params.headers.get("accept"),
            ctx.identifier,
        )

    async def on_request_end(self, _, ctx, params):
        """Log an inbound response."""
        latency = round((time.perf_counter() - ctx.start_time) * 1_000, 1)
        response = params.response
        self.logger.debug(
            "%s %s after %sms [content-type:%s, size:%s, cf-ray:%s, cf-request-id:%s] [%s]",
            response.status,
            response.reason,
            latency,
            response.headers.get("content-type"),
            response.headers.get("content-length", 0),
            response.headers.get("cf-ray"),
            response.headers.get("cf-request-id"),
            ctx.identifier,
        )


class _ByteStreamWriter(io.BytesIO, aiohttp.abc.AbstractStreamWriter):
    async def write(self, data) -> None:
        io.BytesIO.write(self, data)

    write_eof = NotImplemented
    drain = NotImplemented
    enable_compression = NotImplemented
    enable_chunking = NotImplemented
    write_headers = NotImplemented


class DebugTracer(BaseTracer):
    """Provides verbose _debug logging of requests.

    This logs several pieces of information during an AIOHTTP request such as
    request headers and body chunks, response headers, response body chunks,
    and other events such as DNS cache hits/misses, connection pooling events,
    and other pieces of information that can be incredibly useful for debugging
    performance issues and API issues.

    !!! warning
        This may log potentially sensitive information such as authorization
        tokens, so ensure those are removed from _debug logs before proceeding
        to send logs to anyone.
    """

    @staticmethod
    async def _format_body(body):
        if isinstance(body, aiohttp.FormData):
            # We have to either copy the internal multipart writer, or we have
            # to make a dummy second instance and read from that. I am putting
            # my bets on the second option, simply because it reduces the
            # risk of screwing up the original payload in some weird edge case.
            # These objects have stateful stuff somewhere by the looks.
            copy_of_data = aiohttp.FormData()
            setattr(copy_of_data, "_fields", getattr(copy_of_data, "_fields"))
            byte_writer = _ByteStreamWriter()
            await copy_of_data().write(byte_writer)
            return repr(byte_writer.read())
        return repr(body)

    async def on_request_start(self, _, ctx, params):
        """Log an outbound request."""
        ctx.identifier = f"request_id:{uuid.uuid4()}"
        ctx.start_time = time.perf_counter()

        body = (
            await self._format_body(ctx.trace_request_ctx.request_body)
            if hasattr(ctx.trace_request_ctx, "request_body")
            else "<???>"
        )

        self.logger.debug(
            "%s %s [%s]\n  request headers: %s\n  request body: %s",
            params.method,
            params.url,
            ctx.identifier,
            dict(params.headers),
            body,
        )

    async def on_request_end(self, _, ctx, params):
        """Log an inbound response."""
        latency = round((time.perf_counter() - ctx.start_time) * 1_000, 2)
        response = params.response
        self.logger.debug(
            "%s %s %s after %sms [%s]\n  response headers: %s\n  response body: %s",
            response.real_url,
            response.status,
            response.reason,
            latency,
            ctx.identifier,
            dict(response.headers),
            await self._format_body(await response.read()) if "content-type" in response.headers else "<no content>",
        )

    async def on_request_exception(self, _, ctx, params):
        """Log an error while making a request."""
        self.logger.debug("encountered exception [%s]", ctx.identifier, exc_info=params.exception)

    async def on_connection_queued_start(self, _, ctx, __):
        """Log when we have to wait for a new connection in the pool."""
        self.logger.debug("is waiting for a connection [%s]", ctx.identifier)

    async def on_connection_reuseconn(self, _, ctx, __):
        """Log when we re-use an existing connection in the pool."""
        self.logger.debug("has acquired an existing connection [%s]", ctx.identifier)

    async def on_connection_create_end(self, _, ctx, __):
        """Log when we create a new connection in the pool."""
        self.logger.debug("has created a new connection [%s]", ctx.identifier)

    async def on_dns_cache_hit(self, _, ctx, params):
        """Log when we reuse the DNS cache and do not have to look up an IP."""
        self.logger.debug("has retrieved the IP of %s from the DNS cache [%s]", params.host, ctx.identifier)

    async def on_dns_cache_miss(self, _, ctx, params):
        """Log when we have to query a DNS server for an IP address."""
        self.logger.debug("will perform DNS lookup of new host %s  [%s]", params.host, ctx.identifier)

    # noinspection PyMethodMayBeStatic
    async def on_dns_resolvehost_start(self, _, ctx, __):
        """Store the time the DNS lookup started at."""
        ctx.dns_start_time = time.perf_counter()

    async def on_dns_resolvehost_end(self, _, ctx, params):
        """Log how long a DNS lookup of an IP took to perform."""
        latency = round((time.perf_counter() - ctx.dns_start_time) * 1_000, 2)
        self.logger.debug("DNS lookup of host %s took %sms [%s]", params.host, latency, ctx.identifier)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite of tests that spins up a fake websocket server to perform higher-level black box testing. This also acts as a
sanity check that websockets is working correctly.

Skip these tests with the `--deselect tests/net/integration` flag for PyTest.
"""
import warnings

# /usr/local/lib/python3.7/site-packages/websockets/protocol.py:911:
#       DeprecationWarning: 'with (yield from lock)' is  deprecated
#       use 'async with lock' instead
#   with (yield from self._drain_lock):
warnings.filterwarnings("ignore", category=DeprecationWarning)

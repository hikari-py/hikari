# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Helper classes used for handling EdDSA cryptography in the interaction server."""

from __future__ import annotations

__all__: typing.List[str] = ["VerifyBuilderT", "VerifierT", "build_ed25519_verifier"]

import typing

from pure25519 import ed25519_oop as _pure_ed25519  # type: ignore[import]

VerifierT = typing.Callable[[bytes, bytes, bytes], bool]
"""A callable used to verify an interaction payload received from Discord.

Parameters
----------
body : builtins.bytes
    The interaction payload.
signature : builtins.bytes
    Value of the `"X-Signature-Ed25519"` header.
timestamp : builtins.bytes
    Value of the `"X-Signature-Timestamp"` header.

Returns
-------
builtins.bool
    Whether the provided arguments match this public key.
"""


VerifyBuilderT = typing.Callable[[bytes], VerifierT]
"""Build a callable used to verify an interaction payload received from Discord.

Parameters
----------
public_key : builtins.bytes
    The public key to use to verify received interaction requests against.

Returns
-------
VerifierT
    The callable used to verify interaction requests.
"""


def _build_verifier(call: typing.Callable[[bytes, bytes], None], exc: typing.Type[Exception]) -> VerifierT:
    def verify(body: bytes, signature: bytes, timestamp: bytes, /) -> bool:
        try:
            call(signature, timestamp + body)
            return True

        except exc:
            return False

    return verify


def _verify_key(public_key: bytes, /) -> None:
    if not isinstance(public_key, bytes):
        raise ValueError("Invalid type passed for public key")

    if len(public_key) != 32:
        raise ValueError("Invalid public key passed")


def build_slow_ed25519_verifier(public_key: bytes, /) -> VerifierT:
    """`VerifyBuilderT` implementation which will always be present."""
    _verify_key(public_key)
    return _build_verifier(_pure_ed25519.VerifyingKey(public_key).verify, _pure_ed25519.BadSignatureError)


build_fast_ed25519_verifier: typing.Optional[VerifyBuilderT]
"""`VerifyBuilderT` implementation which relies on a speedup requirement."""

try:
    import ed25519 as _ed25519  # type: ignore[import]

    def _build_fast_ed25519_verifier(public_key: bytes, /) -> VerifierT:
        _verify_key(public_key)
        return _build_verifier(_ed25519.VerifyingKey(public_key).verify, _ed25519.BadSignatureError)

    build_fast_ed25519_verifier = _build_fast_ed25519_verifier

except ImportError:
    build_fast_ed25519_verifier = None

build_ed25519_verifier: typing.Final[VerifyBuilderT] = build_fast_ed25519_verifier or build_slow_ed25519_verifier
"""Main implementation of `VerifyBuilderT` used within Hikari."""

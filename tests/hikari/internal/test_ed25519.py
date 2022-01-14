# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
import pytest

from hikari.internal import ed25519


@pytest.fixture()
def valid_edd25519():
    body = (
        b'{"application_id":"658822586720976907","id":"838085779104202753","token":"aW50ZXJhY3Rpb246ODM4MDg1Nzc5MTA0MjA'
        b"yNzUzOmd3MG5nSmpDck9UcWtWc3lsUERFbWx6MEt6bnVUb1Bjc0pNN2FCMVZ3TVJOeVdudUk5R2t4Q0EwSG1LWUVzQkMza0IyR2I3dEtRWHhn"
        b'TlRTYmRxZlgzMFRvZW5CTmVIWDUyZ2Q1NEFmWllueXJhVjBCSVhlQzZyMVpxQloyT20y","type":1,"user":{"avatar":"b333580bd947'
        b'4630226ff7b0a9696231","discriminator":"6127","id":"115590097100865541","public_flags":131072,"username":"Fast'
        b'er Speeding"},"version":1}'
    )
    signature = (
        b"\xb4*\x91w\xf8\xfa{\x8f\xdf\xc3%\xaa\x81nl\xdej\x9aS\xdeq\xe5\x97\xb8$\x8f\xc6\xd4?Y\x1c\x85+\xcf\x93\xc1\xd5"
        b"\xea-\xfe-\x97s\xe04\xb6a:k\xbb\x12\xa4\xa0\x19\xb1P\xf6s\x8e\r'\xab\xbe\x07"
    )
    timestamp = b"1619885621"
    return (body, signature, timestamp)


@pytest.fixture()
def invalid_ed25519():
    body = (
        b'{"application_id":"658822586720976907","id":"838085779104202754","token":"aW50ZXJhY3Rpb246ODM4MDg1Nzc5MTA0MjA'
        b"yNzU0OmNhSk9QUU4wa1BKV21nTjFvSGhIbUp0QnQ1NjNGZFRtMlJVRlNjR0ttaDhtUGJrWUNvcmxYZnd2NTRLeUQ2c0hGS1YzTU03dFJ0V0s5"
        b'RWRBY0ltZTRTS0NneFFSYW1BbDZxSkpnMkEwejlkTldXZUh2OGwzbnBrMzhscURIMXUz","type":1,"user":{"avatar":"b333580bd947'
        b'4630226ff7b0a9696231","discriminator":"6127","id":"115590097100865541","public_flags":13'
        b'1072,"username":"Faster Speeding"},"version":1}'
    )
    signature = (
        b"\x0c4\xda!\xd9\xd5\x08<{a\x0c\xfa\xe6\xd2\x9e\xb3\xe0\x17r\x83\xa8\xb5\xda\xaa\x97\n\xb5\xe1\x92A|\x94\xbb"
        b"\x8aGu\xdb\xd6\x19\xd5\x94\x98\x08\xb4\x1a\xfaF@\xbbx\xc9\xa3\x8f\x1f\x13\t\xd81\xa3:\xa9%p\x0c"
    )
    timestamp = b"1619885620"
    return (body, signature, timestamp)


@pytest.fixture()
def public_key():
    return b"\x12-\xdfX\xa8\x95\xd7\xe1\xb7o\xf5\xd0q\xb0\xaa\xc9\xb7v^*\xb5\x15\xe1\x1b\x7f\xca\xf9d\xdbT\x90\xc6"


class TestSlowED25519Verifier:
    @pytest.mark.parametrize(
        ("key", "message"),
        [
            ("okokokokokokokokokokokokokokokok", "Invalid type passed for public key"),
            (b"NO", "Invalid public key passed"),
        ],
    )
    def test_handles_invalid_public_key(self, key, message):
        with pytest.raises(ValueError, match=message):
            ed25519.build_slow_ed25519_verifier(key)

    def test_verify_matches(self, valid_edd25519, public_key):
        verifier = ed25519.build_slow_ed25519_verifier(public_key)
        assert verifier(*valid_edd25519) is True

    def test_verify_rejects(self, invalid_ed25519, public_key):
        verifier = ed25519.build_slow_ed25519_verifier(public_key)
        assert verifier(*invalid_ed25519) is False


@pytest.mark.skipif(ed25519.build_fast_ed25519_verifier is None, reason="Fast ed25519 verifier impl not present")
class TestFastED25519Verifier:
    @pytest.mark.parametrize(
        ("key", "message"),
        [
            ("okokokokokokokokokokokokokokokok", "Invalid type passed for public key"),
            (b"NO", "Invalid public key passed"),
        ],
    )
    def test_handles_invalid_public_key(self, key, message):
        with pytest.raises(ValueError, match=message):
            ed25519.build_fast_ed25519_verifier(key)

    def test_verify_matches(self, valid_edd25519, public_key):
        verifier = ed25519.build_fast_ed25519_verifier(public_key)
        assert verifier(*valid_edd25519) is True

    def test_verify_rejects(self, invalid_ed25519, public_key):
        verifier = ed25519.build_fast_ed25519_verifier(public_key)
        assert verifier(*invalid_ed25519) is False


@pytest.mark.skipif(ed25519.build_fast_ed25519_verifier is not None, reason="Fast ed25519 verifier impl not present")
def test_build_ed25519_verifier_set_as_fast_impl():
    assert ed25519.build_ed25519_verifier is ed25519.build_slow_ed25519_verifier


@pytest.mark.skipif(ed25519.build_fast_ed25519_verifier is None, reason="Fast ed25519 verifier impl present")
def test_build_ed25519_verifier_set_as_slow_impl():
    assert ed25519.build_ed25519_verifier is ed25519.build_fast_ed25519_verifier

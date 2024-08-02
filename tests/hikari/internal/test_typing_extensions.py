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
import contextlib
import typing

import mock
import pytest

from hikari.internal import fast_protocol


class TestCheckIfIgnored:
    def test_when_startswith_abc(self):
        mock_string = mock.Mock(startswith=mock.Mock(return_value=True))

        assert fast_protocol._check_if_ignored(mock_string) is True

        mock_string.startswith.assert_called_once_with("_abc_")

    def test_when_in_IGNORED_ATTRS(self):
        with mock.patch.object(
            fast_protocol, "_IGNORED_ATTRS", new=mock.Mock(__contains__=mock.Mock(return_value=True))
        ) as mock_list:
            assert fast_protocol._check_if_ignored("testing") is True

            mock_list.__contains__.assert_called_once_with("testing")

    def test_when_not_ignored(self):
        mock_string = mock.Mock(startswith=mock.Mock(return_value=False))
        with mock.patch.object(
            fast_protocol, "_IGNORED_ATTRS", new=mock.Mock(__contains__=mock.Mock(return_value=False))
        ) as mock_list:
            assert fast_protocol._check_if_ignored(mock_string) is False

            mock_list.__contains__.assert_called_once_with(mock_string)


class TestFastProtocolChecking:
    def test_new_when_first_protocol_not_FastProtocolChecking(self):
        stack = contextlib.ExitStack()
        stack.enter_context(
            pytest.raises(TypeError, match=r"First instance of _FastProtocolChecking must be FastProtocolChecking")
        )
        stack.enter_context(mock.patch.object(fast_protocol, "_Protocol", new=NotImplemented))

        with stack:

            class NotProtocol(metaclass=fast_protocol._FastProtocolChecking): ...

    def test_new_when_first_protocol_is_FastProtocolChecking(self):
        with mock.patch.object(fast_protocol, "_Protocol", new=NotImplemented):

            class FastProtocolChecking(metaclass=fast_protocol._FastProtocolChecking): ...

            assert fast_protocol._Protocol is FastProtocolChecking

        assert FastProtocolChecking._attributes_ == ()

    def test_new_when_bases_not_fastprotocols(self):
        with pytest.raises(
            TypeError,
            match=r"FastProtocolChecking can only inherit from other fast checking protocols, got <class 'object'>",
        ):

            class MyProtocol(object, fast_protocol.FastProtocolChecking, typing.Protocol): ...

    def test_new_when_fastprotocolchecking_in_bases_but_not_protocol(self):
        with pytest.raises(TypeError, match=r"FastProtocolChecking can only be used with protocols"):

            class MyProtocol(fast_protocol.FastProtocolChecking): ...

    def test_new(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
            def test1(): ...

        class OtherProtocol(MyProtocol, fast_protocol.FastProtocolChecking, typing.Protocol):
            def test2(): ...

        assert sorted(OtherProtocol._attributes_) == ["test1", "test2"]

    def test_init_subclass_does_not_overwrite_subclasshoook(self):
        def subclass_hook(): ...

        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
            __subclasshook__ = subclass_hook

        assert MyProtocol.__subclasshook__ is subclass_hook

    def test_isinstance_when_not_protocol(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol): ...

        class Class: ...

        MyProtocol._is_protocol = False
        class_instance = Class()

        with mock.patch.object(type(typing.Protocol), "__instancecheck__", return_value=True) as instance_check:
            assert isinstance(class_instance, MyProtocol) is True

            instance_check.assert_called_once_with(class_instance)

    def test_isinstance_fastfail(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
            def test(): ...

        class Class: ...

        assert isinstance(Class(), MyProtocol) is False

    def test_isinstance(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
            def test(): ...

        class Class:
            def test(): ...

        assert isinstance(Class(), MyProtocol) is True

    def test_issubclass_when_not_protocol(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol): ...

        class Class: ...

        with mock.patch.object(type(typing.Protocol), "__subclasscheck__", return_value=True) as subclass_check:
            assert issubclass(Class, MyProtocol) is True

            subclass_check.assert_called_once_with(Class)

    def test_issubclass_fastfail(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
            def test(): ...

        class Class: ...

        assert issubclass(Class, MyProtocol) is False

    def test_issubclass(self):
        class MyProtocol(fast_protocol.FastProtocolChecking, typing.Protocol):
            def test(): ...

        class Class:
            def test(): ...

        assert issubclass(Class, MyProtocol) is True

# -*- coding: utf-8 -*-
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
import abc
import contextlib

import mock
import pytest

from hikari.internal import protocol as protocol_impl


class TestCheckIfIgnored:
    def test_when_startswith_abc(self):
        mock_string = mock.Mock(startswith=mock.Mock(return_value=True))

        assert protocol_impl._check_if_ignored(mock_string) is True

        mock_string.startswith.assert_called_once_with("_abc_")

    def test_when_in_IGNORED_ATTRS(self):
        with mock.patch.object(
            protocol_impl, "IGNORED_ATTRS", new=mock.Mock(__contains__=mock.Mock(return_value=True))
        ) as mock_list:
            assert protocol_impl._check_if_ignored("testing") is True

            mock_list.__contains__.assert_called_once_with("testing")

    def test_when_not_ignored(self):
        mock_string = mock.Mock(startswith=mock.Mock(return_value=False))
        with mock.patch.object(
            protocol_impl, "IGNORED_ATTRS", new=mock.Mock(__contains__=mock.Mock(return_value=False))
        ) as mock_list:
            assert protocol_impl._check_if_ignored(mock_string) is False

            mock_list.__contains__.assert_called_once_with(mock_string)


class TestNoInit:
    @pytest.fixture()
    def mock_class(self):
        class MockClass:
            _is_protocol = NotImplemented

        return MockClass

    def test_no_init_when_protocol(self, mock_class):
        mock_class._is_protocol = True
        with pytest.raises(TypeError, match=r"Protocols cannot be instantiated"):
            protocol_impl._no_init(mock_class())

    def test_no_init_when_not_protocol(self, mock_class):
        mock_class._is_protocol = False
        protocol_impl._no_init(mock_class())


class TestFastProtocol:
    def test_new_when_first_protocol_not_Protocol(self):
        stack = contextlib.ExitStack()
        stack.enter_context(pytest.raises(TypeError, match=r"First instance of _FastProtocol must be Protocol"))
        stack.enter_context(mock.patch.object(protocol_impl, "_Protocol", new=NotImplemented))

        with stack:

            class NotProtocol(metaclass=protocol_impl._FastProtocol):
                ...

    def test_new_when_first_protocol_is_Protocol(self):
        with mock.patch.object(protocol_impl, "_Protocol", new=NotImplemented):

            class Protocol(metaclass=protocol_impl._FastProtocol):
                ...

            assert protocol_impl._Protocol is Protocol

        assert Protocol._is_protocol is True
        assert Protocol._attributes_ == ()
        assert Protocol.__init__ is protocol_impl._no_init

    def test_new_when_bases_not_protocols(self):
        with pytest.raises(TypeError, match=r"Protocols can only inherit from other protocols, got <class 'object'>"):

            class MyProtocol(object, protocol_impl.Protocol):
                ...

    def test_new_when_protocol_is_not_a_base(self):
        class MyProtocol(protocol_impl.Protocol):
            ...

        class ApiProtocol(MyProtocol):
            ...

        assert ApiProtocol._is_protocol is False
        assert hasattr(ApiProtocol, "_attributes__") is False
        assert ApiProtocol.__init__ is protocol_impl._no_init

    def test_new(self):
        class MyProtocol(protocol_impl.Protocol):
            def test1():
                ...

        class OtherProtocol(MyProtocol, protocol_impl.Protocol):
            def test2():
                ...

        assert OtherProtocol._is_protocol is True
        assert OtherProtocol.__init__ is protocol_impl._no_init
        assert sorted(OtherProtocol._attributes_) == ["test1", "test2"]

    def test_isinstance_when_not_protocol(self):
        class MyProtocol(protocol_impl.Protocol):
            ...

        class Class:
            ...

        MyProtocol._is_protocol = False
        class_instance = Class()

        with mock.patch.object(abc.ABCMeta, "__instancecheck__", return_value=True) as instance_check:
            assert isinstance(class_instance, MyProtocol) is True

            instance_check.assert_called_once_with(class_instance)

    def test_isinstance_fastfail(self):
        class MyProtocol(protocol_impl.Protocol):
            def test():
                ...

        class Class:
            ...

        assert isinstance(Class(), MyProtocol) is False

    def test_isinstance(self):
        class MyProtocol(protocol_impl.Protocol):
            def test():
                ...

        class Class:
            def test():
                ...

        assert isinstance(Class(), MyProtocol) is True

    def test_issubclass_when_not_protocol(self):
        class MyProtocol(protocol_impl.Protocol):
            ...

        class Class:
            ...

        with mock.patch.object(abc.ABCMeta, "__subclasscheck__", return_value=True) as instance_check:
            assert issubclass(Class, MyProtocol) is True

            instance_check.assert_called_once_with(Class)

    def test_issubclass_fastfail(self):
        class MyProtocol(protocol_impl.Protocol):
            def test():
                ...

        class Class:
            ...

        assert issubclass(Class, MyProtocol) is False

    def test_issubclass(self):
        class MyProtocol(protocol_impl.Protocol):
            def test():
                ...

        class Class:
            def test():
                ...

        assert issubclass(Class, MyProtocol) is True

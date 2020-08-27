# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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

from hikari.utilities import flag


class TestFlag:
    def test_flag_is_IntFlag(self):
        import enum

        TestFlagType = flag.Flag("TestFlagType", "a b c")
        assert isinstance(TestFlagType, enum.EnumMeta)
        assert issubclass(TestFlagType, enum.IntFlag)

    def test_split(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK

        # Baz is a combined field technically, so we don't expect it to be output here
        assert val.split() == [TestFlagType.BAR, TestFlagType.BORK, TestFlagType.FOO]

    def test_has_any_positive_case(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert val.has_any(TestFlagType.FOO)
        assert val.has_any(TestFlagType.BAR)
        assert val.has_any(TestFlagType.BAZ)
        assert val.has_any(TestFlagType.BORK)
        # All present
        assert val.has_any(TestFlagType.FOO, TestFlagType.BAR, TestFlagType.BAZ, TestFlagType.BORK)
        # One present, one not
        assert val.has_any(
            TestFlagType.FOO,
            TestFlagType.QUX,
        )

    def test_has_any_negative_case(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = 0x10

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert not val.has_any(TestFlagType.QUX)

    def test_has_all_positive_case(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert val.has_all(TestFlagType.FOO)

        assert val.has_all(TestFlagType.FOO, TestFlagType.BAR, TestFlagType.BAZ, TestFlagType.BORK)

    def test_has_all_negative_case(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = 0x10

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert not val.has_all(TestFlagType.QUX)
        assert not val.has_all(TestFlagType.BAZ, TestFlagType.QUX, TestFlagType.QUXX)

    def test_has_none_positive_case(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = 0x10

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert val.has_none(TestFlagType.QUX)

    def test_has_none_negative_case(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert not val.has_none(TestFlagType.FOO)
        assert not val.has_none(TestFlagType.BAR)
        assert not val.has_none(TestFlagType.BAZ)
        assert not val.has_none(TestFlagType.BORK)
        # All present
        assert not val.has_none(TestFlagType.FOO, TestFlagType.BAR, TestFlagType.BAZ, TestFlagType.BORK)
        # One present, one not
        assert not val.has_none(
            TestFlagType.FOO,
            TestFlagType.QUX,
        )

    def test_add_operator(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        assert TestFlagType.BAZ + TestFlagType.BORK == TestFlagType.BAZ | TestFlagType.BORK
        assert TestFlagType.BORK + TestFlagType.BAZ == TestFlagType.BAZ | TestFlagType.BORK
        assert TestFlagType.BAZ + 4 == TestFlagType.BAZ | TestFlagType.BORK
        assert 4 + TestFlagType.BAZ == TestFlagType.BAZ | TestFlagType.BORK

    def test_sub_operator(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK
        assert val - TestFlagType.BAZ == TestFlagType.BORK
        assert val - TestFlagType.QUX == val
        assert (TestFlagType.BAZ | TestFlagType.QUX) - val == TestFlagType.QUX

    def test_str_operator(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK

        assert str(val) == "BAR | BORK | FOO"

    def test_iter(self):
        class TestFlagType(flag.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlagType.BAZ | TestFlagType.BORK
        val_iter = iter(val)
        assert next(val_iter) == TestFlagType.BAR
        assert next(val_iter) == TestFlagType.BORK
        assert next(val_iter) == TestFlagType.FOO
        with pytest.raises(StopIteration):
            next(val_iter)

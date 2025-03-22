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
from __future__ import annotations

import enum as py_enum
import os
import sys
import timeit

from hikari.internal import enums as hikari_enum

PyIntFlag = None
HikariIntFlag = None


def build_enums() -> None:
    global PyIntFlag  # noqa: PLW0603
    global HikariIntFlag  # noqa: PLW0603

    class PyIntFlag(py_enum.IntFlag):
        a = 1
        b = 2
        c = 4
        d = 8
        e = 16
        f = 32
        g = 64
        ab = 3
        cde = 28

    class HikariIntFlag(hikari_enum.Flag):
        a = 1
        b = 2
        c = 4
        d = 8
        e = 16
        f = 32
        g = 64
        ab = 3
        cde = 28


if os.name != "nt":
    print("Making highest priority, os.SCHED_RR")
    try:
        pid = os.getpid()
        nice_value = os.nice(-20)
        sys.setswitchinterval(0.5)
        print("sys.getswitchinterval", sys.getswitchinterval())
        os.sched_setaffinity(pid, [(os.cpu_count() or 1) - 1])
        os.sched_setscheduler(pid, os.SCHED_RR, os.sched_param(1))
        print("sched_getscheduler", os.sched_getscheduler(pid))
        print("sched_getparam", os.sched_getparam(pid))
        print("sched_getaffinity", os.sched_getaffinity(pid))
        print("sched_getprioritymax", os.sched_get_priority_max(0))
        print("sched_getprioritymin", os.sched_get_priority_min(0))
        print("sched_rr_getinterval", os.sched_rr_get_interval(pid))
        print("nice", os.nice(0))
    except PermissionError:
        print("run as root to make top OS priority for more accurate results.")
else:
    print("lol windows good luck")

for i in range(5):
    print("pass", i + 1)

    for j in range(1_000_000):
        if sum(j for j in range(10)) < 0:
            raise RuntimeError

    py_intflag_call_time_member = timeit.timeit(
        setup="build_enums()", stmt="PyIntFlag(4)", number=10_000_000, globals=globals()
    )
    hikari_intflag_call_time_member = timeit.timeit(
        setup="build_enums()", stmt="HikariIntFlag(4)", number=10_000_000, globals=globals()
    )

    for j in range(1_000_000):
        if sum(j for j in range(10)) < 0:
            raise RuntimeError

    py_intflag_call_time_existing_composite = (
        timeit.timeit(stmt="PyIntFlag(71)", number=10_000_000, globals=globals()) / 10
    )
    hikari_intflag_call_time_existing_composite = (
        timeit.timeit(stmt="HikariIntFlag(71)", number=10_000_000, globals=globals()) / 10
    )

    for j in range(1_000_000):
        if sum(j for j in range(10)) < 0:
            raise RuntimeError

    build_enums_time = timeit.timeit(stmt="build_enums()", number=10_000, globals=globals())
    py_intflag_call_time_new_composite = timeit.timeit(
        stmt="build_enums(); PyIntFlag(71)", number=10_000, globals=globals()
    )
    build_enums_time = min(timeit.timeit(stmt="build_enums()", number=10_000, globals=globals()), build_enums_time)
    py_intflag_call_time_new_composite -= build_enums_time
    py_intflag_call_time_new_composite *= 100

    for j in range(1_000_000):
        if sum(j for j in range(10)) < 0:
            raise RuntimeError

    build_enums_time = timeit.timeit(stmt="build_enums()", number=10_000, globals=globals())
    hikari_intflag_call_time_new_composite = timeit.timeit(
        stmt="build_enums(); HikariIntFlag(71)", number=10_000, globals=globals()
    )
    build_enums_time = min(timeit.timeit(stmt="build_enums()", number=10_000, globals=globals()), build_enums_time)
    hikari_intflag_call_time_new_composite -= build_enums_time
    hikari_intflag_call_time_new_composite *= 100

    print("PyIntFlag.__call__(4) (existing member)", py_intflag_call_time_member, "µs")
    print("HikariIntFlag.__call__(4) (existing member)", hikari_intflag_call_time_member, "µs")

    print("PyIntFlag.__call__(71) (new composite member)", py_intflag_call_time_new_composite, "µs")
    print("HikariIntFlag.__call__(71) (new composite member)", hikari_intflag_call_time_new_composite, "µs")

    print("PyIntFlag.__call__(71) (existing composite member)", py_intflag_call_time_existing_composite, "µs")
    print("HikariIntFlag.__call__(71) (existing composite member)", hikari_intflag_call_time_existing_composite, "µs")

    print()

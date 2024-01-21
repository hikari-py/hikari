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
import signal

import mock
import pytest

from hikari import errors
from hikari.internal import signals


def test__raise_interrupt():
    with mock.patch.object(signal, "strsignal"):  # signals are not always implemented
        with pytest.raises(errors.HikariInterrupt):
            signals._raise_interrupt(1)


@pytest.mark.parametrize("trace", [True, False])
def test__interrupt_handler(trace):
    loop = mock.Mock()

    with mock.patch.object(signals, "_LOGGER", new=mock.Mock(isEnabledFor=mock.Mock(return_value=trace))):
        handler = signals._interrupt_handler(loop)

        handler(1, None)

    loop.call_soon_threadsafe.assert_called_once_with(signals._raise_interrupt, 1)


class TestHandleInterrupt:
    def test_behaviour(self):
        loop = object()

        stack = contextlib.ExitStack()
        register_signal_handler = stack.enter_context(mock.patch.object(signal, "signal"))
        interrupt_handler = stack.enter_context(mock.patch.object(signals, "_interrupt_handler"))
        stack.enter_context(mock.patch.object(signal, "SIGINT", new=2, create=True))
        stack.enter_context(mock.patch.object(signal, "SIGTERM", new=15, create=True))
        stack.enter_context(mock.patch.object(signals, "_INTERRUPT_SIGNALS", ("SIGINT", "SIGTERM", "UNIMPLEMENTED")))

        with stack:
            with signals.handle_interrupts(True, loop, True):
                interrupt_handler.assert_called_once_with(loop)

                assert register_signal_handler.call_count == 2
                register_signal_handler.assert_has_calls(
                    [mock.call(2, interrupt_handler.return_value), mock.call(15, interrupt_handler.return_value)]
                )

                register_signal_handler.reset_mock()

        assert register_signal_handler.call_count == 2
        register_signal_handler.assert_has_calls(
            [mock.call(2, signal.default_int_handler), mock.call(15, signal.SIG_DFL)]
        )

    def test_when_disabled(self):
        with mock.patch.object(signal, "signal") as register_signal_handler:
            with signals.handle_interrupts(False, object(), True):
                register_signal_handler.assert_not_called()

        register_signal_handler.assert_not_called()

    def test_when_propagate_interrupt(self):
        with mock.patch.object(signal, "signal"):
            with pytest.raises(errors.HikariInterrupt):  # noqa: PT012 - raises block should contain a single statement
                with signals.handle_interrupts(True, object(), True):
                    raise errors.HikariInterrupt(1, "t")

    def test_when_not_propagate_interrupt(self):
        with mock.patch.object(signal, "signal"):
            with signals.handle_interrupts(True, object(), False):
                raise errors.HikariInterrupt(1, "t")

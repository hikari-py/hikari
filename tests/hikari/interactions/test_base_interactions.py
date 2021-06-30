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

import mock
import pytest

from hikari import traits
from hikari.interactions import base_interactions


@pytest.fixture()
def mock_app():
    return mock.Mock(traits.CacheAware, rest=mock.AsyncMock())


class TestPartialInteraction:
    @pytest.fixture()
    def mock_partial_interaction(self, mock_app):
        return base_interactions.PartialInteraction(
            app=mock_app,
            id=34123,
            application_id=651231,
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
        )

    def test_webhook_id_property(self, mock_partial_interaction):
        assert mock_partial_interaction.webhook_id is mock_partial_interaction.application_id

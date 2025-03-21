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

import mock
import pytest

from hikari import applications
from hikari import monetization
from hikari import snowflakes
from hikari.interactions import base_interactions
from hikari.interactions import component_interactions


@pytest.fixture
def mock_app():
    return mock.Mock(rest=mock.AsyncMock())


class TestComponentInteraction:
    @pytest.fixture
    def mock_component_interaction(self, mock_app):
        return component_interactions.ComponentInteraction(
            app=mock_app,
            id=snowflakes.Snowflake(2312312),
            type=base_interactions.InteractionType.MESSAGE_COMPONENT,
            guild_id=snowflakes.Snowflake(5412231),
            channel=object(),
            member=object(),
            user=object(),
            token="httptptptptptptptp",
            version=1,
            application_id=snowflakes.Snowflake(43123),
            component_type=2,
            values=(),
            custom_id="OKOKOK",
            message=object(),
            locale="es-ES",
            guild_locale="en-US",
            app_permissions=123321,
            resolved=None,
            entitlements=[
                monetization.Entitlement(
                    id=snowflakes.Snowflake(123123),
                    sku_id=snowflakes.Snowflake(123123),
                    application_id=snowflakes.Snowflake(123123),
                    guild_id=snowflakes.Snowflake(123123),
                    user_id=snowflakes.Snowflake(123123),
                    type=monetization.EntitlementType.APPLICATION_SUBSCRIPTION,
                    starts_at=None,
                    ends_at=None,
                    is_deleted=False,
                    subscription_id=None,
                )
            ],
            authorizing_integration_owners={
                applications.ApplicationIntegrationType.GUILD_INSTALL: snowflakes.Snowflake(123)
            },
            context=applications.ApplicationContextType.PRIVATE_CHANNEL,
        )

    def test_build_response(self, mock_component_interaction, mock_app):
        mock_app.rest.interaction_message_builder = mock.Mock()
        response = mock_component_interaction.build_response(4)

        assert response is mock_app.rest.interaction_message_builder.return_value
        mock_app.rest.interaction_message_builder.assert_called_once_with(4)

    def test_build_response_with_invalid_type(self, mock_component_interaction):
        with pytest.raises(ValueError, match="Invalid type passed for an immediate response"):
            mock_component_interaction.build_response(999)

    def test_build_deferred_response(self, mock_component_interaction, mock_app):
        mock_app.rest.interaction_deferred_builder = mock.Mock()
        response = mock_component_interaction.build_deferred_response(5)

        assert response is mock_app.rest.interaction_deferred_builder.return_value
        mock_app.rest.interaction_deferred_builder.assert_called_once_with(5)

    def test_build_deferred_response_with_invalid_type(self, mock_component_interaction):
        with pytest.raises(ValueError, match="Invalid type passed for a deferred response"):
            mock_component_interaction.build_deferred_response(33333)

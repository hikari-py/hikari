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

import typing

import mock
import pytest

from hikari import applications
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.interactions import base_interactions


class TestPartialInteraction:
    @pytest.fixture
    def mock_partial_interaction(self, hikari_app: traits.RESTAware) -> base_interactions.PartialInteraction:
        return base_interactions.PartialInteraction(
            app=hikari_app,
            id=snowflakes.Snowflake(34123),
            application_id=snowflakes.Snowflake(651231),
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
            authorizing_integration_owners={
                applications.ApplicationIntegrationType.GUILD_INSTALL: snowflakes.Snowflake(123)
            },
            context=applications.ApplicationContextType.PRIVATE_CHANNEL,
        )

    def test_webhook_id_property(self, mock_partial_interaction: base_interactions.PartialInteraction):
        assert mock_partial_interaction.webhook_id is mock_partial_interaction.application_id


class TestMessageResponseMixin:
    @pytest.fixture
    def mock_message_response_mixin(
        self, hikari_app: traits.RESTAware
    ) -> base_interactions.MessageResponseMixin[typing.Any]:
        return base_interactions.MessageResponseMixin(
            app=hikari_app,
            id=snowflakes.Snowflake(34123),
            application_id=snowflakes.Snowflake(651231),
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
            authorizing_integration_owners={
                applications.ApplicationIntegrationType.GUILD_INSTALL: snowflakes.Snowflake(123)
            },
            context=applications.ApplicationContextType.PRIVATE_CHANNEL,
        )

    @pytest.mark.asyncio
    async def test_fetch_initial_response(
        self, mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any]
    ):
        with mock.patch.object(
            mock_message_response_mixin.app.rest, "fetch_interaction_response", mock.AsyncMock()
        ) as patched_fetch_interaction_response:
            result = await mock_message_response_mixin.fetch_initial_response()

            assert result is patched_fetch_interaction_response.return_value
            patched_fetch_interaction_response.assert_awaited_once_with(651231, "399393939doodsodso")

    @pytest.mark.asyncio
    async def test_create_initial_response_with_optional_args(
        self, mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any]
    ):
        mock_embed_1 = mock.Mock()
        mock_embed_2 = mock.Mock()
        mock_component = mock.Mock()
        mock_components = mock.Mock(), mock.Mock()
        mock_attachment = mock.Mock()
        mock_attachments = mock.Mock(), mock.Mock()

        with mock.patch.object(
            mock_message_response_mixin.app.rest, "create_interaction_response", mock.AsyncMock()
        ) as patched_create_interaction_response:
            await mock_message_response_mixin.create_initial_response(
                base_interactions.ResponseType.MESSAGE_CREATE,
                "content",
                tts=True,
                embed=mock_embed_1,
                flags=64,
                embeds=[mock_embed_2],
                component=mock_component,
                components=mock_components,
                attachment=mock_attachment,
                attachments=mock_attachments,
                mentions_everyone=False,
                user_mentions=[123432],
                role_mentions=[6324523],
            )

            patched_create_interaction_response.assert_awaited_once_with(
                34123,
                "399393939doodsodso",
                base_interactions.ResponseType.MESSAGE_CREATE,
                "content",
                tts=True,
                flags=64,
                embed=mock_embed_1,
                embeds=[mock_embed_2],
                component=mock_component,
                components=mock_components,
                attachment=mock_attachment,
                attachments=mock_attachments,
                mentions_everyone=False,
                user_mentions=[123432],
                role_mentions=[6324523],
            )

    @pytest.mark.asyncio
    async def test_create_initial_response_without_optional_args(
        self, mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any]
    ):
        with mock.patch.object(
            mock_message_response_mixin.app.rest, "create_interaction_response", mock.AsyncMock()
        ) as patched_create_interaction_response:
            await mock_message_response_mixin.create_initial_response(
                base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE
            )

            patched_create_interaction_response.assert_awaited_once_with(
                34123,
                "399393939doodsodso",
                base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE,
                undefined.UNDEFINED,
                flags=undefined.UNDEFINED,
                tts=undefined.UNDEFINED,
                embed=undefined.UNDEFINED,
                embeds=undefined.UNDEFINED,
                component=undefined.UNDEFINED,
                components=undefined.UNDEFINED,
                attachment=undefined.UNDEFINED,
                attachments=undefined.UNDEFINED,
                mentions_everyone=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
            )

    @pytest.mark.asyncio
    async def test_edit_initial_response_with_optional_args(
        self, mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any]
    ):
        mock_embed_1 = mock.Mock()
        mock_embed_2 = mock.Mock()
        mock_attachment_1 = mock.Mock()
        mock_attachment_2 = mock.Mock()
        mock_component = mock.Mock()
        mock_components = mock.Mock(), mock.Mock()

        with mock.patch.object(
            mock_message_response_mixin.app.rest, "edit_interaction_response", mock.AsyncMock()
        ) as patched_edit_interaction_response:
            result = await mock_message_response_mixin.edit_initial_response(
                "new content",
                embed=mock_embed_1,
                embeds=[mock_embed_2],
                attachment=mock_attachment_1,
                attachments=[mock_attachment_2],
                component=mock_component,
                components=mock_components,
                mentions_everyone=False,
                user_mentions=[123123],
                role_mentions=[562134],
            )

            assert result is patched_edit_interaction_response.return_value
            patched_edit_interaction_response.assert_awaited_once_with(
                651231,
                "399393939doodsodso",
                "new content",
                embed=mock_embed_1,
                embeds=[mock_embed_2],
                attachment=mock_attachment_1,
                attachments=[mock_attachment_2],
                component=mock_component,
                components=mock_components,
                mentions_everyone=False,
                user_mentions=[123123],
                role_mentions=[562134],
            )

    @pytest.mark.asyncio
    async def test_edit_initial_response_without_optional_args(
        self, mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any]
    ):
        with mock.patch.object(
            mock_message_response_mixin.app.rest, "edit_interaction_response", mock.AsyncMock()
        ) as patched_edit_interaction_response:
            result = await mock_message_response_mixin.edit_initial_response()

            assert result is patched_edit_interaction_response.return_value
            patched_edit_interaction_response.assert_awaited_once_with(
                651231,
                "399393939doodsodso",
                undefined.UNDEFINED,
                embed=undefined.UNDEFINED,
                embeds=undefined.UNDEFINED,
                attachment=undefined.UNDEFINED,
                attachments=undefined.UNDEFINED,
                component=undefined.UNDEFINED,
                components=undefined.UNDEFINED,
                mentions_everyone=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
            )

    @pytest.mark.asyncio
    async def test_delete_initial_response(
        self, mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any]
    ):
        with mock.patch.object(
            mock_message_response_mixin.app.rest, "delete_interaction_response", mock.AsyncMock()
        ) as patched_delete_interaction_response:
            await mock_message_response_mixin.delete_initial_response()
            patched_delete_interaction_response.assert_awaited_once_with(651231, "399393939doodsodso")


class TestModalResponseMixin:
    @pytest.fixture
    def mock_modal_response_mixin(self, hikari_app: traits.RESTAware) -> base_interactions.ModalResponseMixin:
        return base_interactions.ModalResponseMixin(
            app=hikari_app,
            id=snowflakes.Snowflake(34123),
            application_id=snowflakes.Snowflake(651231),
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
            authorizing_integration_owners={
                applications.ApplicationIntegrationType.GUILD_INSTALL: snowflakes.Snowflake(123)
            },
            context=applications.ApplicationContextType.PRIVATE_CHANNEL,
        )

    @pytest.mark.asyncio
    async def test_create_modal_response(self, mock_modal_response_mixin: base_interactions.ModalResponseMixin):
        with mock.patch.object(
            mock_modal_response_mixin.app.rest, "create_modal_response", mock.AsyncMock()
        ) as patched_create_modal_response:
            await mock_modal_response_mixin.create_modal_response("title", "custom_id", undefined.UNDEFINED, [])

            patched_create_modal_response.assert_awaited_once_with(
                34123,
                "399393939doodsodso",
                title="title",
                custom_id="custom_id",
                component=undefined.UNDEFINED,
                components=[],
            )

    def test_build_response(
        self, mock_modal_response_mixin: base_interactions.ModalResponseMixin, hikari_app: traits.RESTAware
    ):
        hikari_app.rest.interaction_modal_builder = mock.Mock()
        builder = mock_modal_response_mixin.build_modal_response("title", "custom_id")

        assert builder is hikari_app.rest.interaction_modal_builder.return_value
        hikari_app.rest.interaction_modal_builder.assert_called_once_with(title="title", custom_id="custom_id")

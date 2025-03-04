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

from hikari import traits
from hikari import undefined
from hikari.interactions import base_interactions


@pytest.fixture
def mock_app() -> traits.RESTAware:
    return mock.Mock(traits.CacheAware, rest=mock.AsyncMock())


class TestPartialInteraction:
    @pytest.fixture
    def mock_partial_interaction(self, mock_app: traits.RESTAware) -> base_interactions.PartialInteraction:
        return base_interactions.PartialInteraction(
            app=mock_app,
            id=34123,
            application_id=651231,
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
        )

    def test_webhook_id_property(self, mock_partial_interaction: base_interactions.PartialInteraction):
        assert mock_partial_interaction.webhook_id is mock_partial_interaction.application_id


class TestMessageResponseMixin:
    @pytest.fixture
    def mock_message_response_mixin(
        self, mock_app: traits.RESTAware
    ) -> base_interactions.MessageResponseMixin[typing.Any]:
        return base_interactions.MessageResponseMixin(
            app=mock_app,
            id=34123,
            application_id=651231,
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
        )

    @pytest.mark.asyncio
    async def test_fetch_initial_response(
        self,
        mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any],
        mock_app: traits.RESTAware,
    ):
        result = await mock_message_response_mixin.fetch_initial_response()

        assert result is mock_app.rest.fetch_interaction_response.return_value
        mock_app.rest.fetch_interaction_response.assert_awaited_once_with(651231, "399393939doodsodso")

    @pytest.mark.asyncio
    async def test_create_initial_response_with_optional_args(
        self,
        mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any],
        mock_app: traits.RESTAware,
    ):
        mock_embed_1 = mock.Mock()
        mock_embed_2 = mock.Mock()
        mock_component = mock.Mock()
        mock_components = mock.Mock(), mock.Mock()
        mock_attachment = mock.Mock()
        mock_attachments = mock.Mock(), mock.Mock()
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

        mock_app.rest.create_interaction_response.assert_awaited_once_with(
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
        self,
        mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any],
        mock_app: traits.RESTAware,
    ):
        await mock_message_response_mixin.create_initial_response(
            base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE
        )

        mock_app.rest.create_interaction_response.assert_awaited_once_with(
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
        self,
        mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any],
        mock_app: traits.RESTAware,
    ):
        mock_embed_1 = mock.Mock()
        mock_embed_2 = mock.Mock()
        mock_attachment_1 = mock.Mock()
        mock_attachment_2 = mock.Mock()
        mock_component = mock.Mock()
        mock_components = mock.Mock(), mock.Mock()
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

        assert result is mock_app.rest.edit_interaction_response.return_value
        mock_app.rest.edit_interaction_response.assert_awaited_once_with(
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
        self,
        mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any],
        mock_app: traits.RESTAware,
    ):
        result = await mock_message_response_mixin.edit_initial_response()

        assert result is mock_app.rest.edit_interaction_response.return_value
        mock_app.rest.edit_interaction_response.assert_awaited_once_with(
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
        self,
        mock_message_response_mixin: base_interactions.MessageResponseMixin[typing.Any],
        mock_app: traits.RESTAware,
    ):
        await mock_message_response_mixin.delete_initial_response()

        mock_app.rest.delete_interaction_response.assert_awaited_once_with(651231, "399393939doodsodso")


class TestModalResponseMixin:
    @pytest.fixture
    def mock_modal_response_mixin(self, mock_app: traits.RESTAware) -> base_interactions.ModalResponseMixin:
        return base_interactions.ModalResponseMixin(
            app=mock_app,
            id=34123,
            application_id=651231,
            type=base_interactions.InteractionType.APPLICATION_COMMAND,
            token="399393939doodsodso",
            version=3122312,
        )

    @pytest.mark.asyncio
    async def test_create_modal_response(
        self, mock_modal_response_mixin: base_interactions.ModalResponseMixin, mock_app: traits.RESTAware
    ):
        await mock_modal_response_mixin.create_modal_response("title", "custom_id", None, [])

        mock_app.rest.create_modal_response.assert_awaited_once_with(
            34123, "399393939doodsodso", title="title", custom_id="custom_id", component=None, components=[]
        )

    def test_build_response(
        self, mock_modal_response_mixin: base_interactions.ModalResponseMixin, mock_app: traits.RESTAware
    ):
        mock_app.rest.interaction_modal_builder = mock.Mock()
        builder = mock_modal_response_mixin.build_modal_response("title", "custom_id")

        assert builder is mock_app.rest.interaction_modal_builder.return_value
        mock_app.rest.interaction_modal_builder.assert_called_once_with(title="title", custom_id="custom_id")

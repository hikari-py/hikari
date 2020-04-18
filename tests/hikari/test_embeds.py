#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime

import mock
import pytest

from hikari import colors
from hikari import embeds
from hikari.internal import conversions
from tests.hikari import _helpers


@pytest.fixture
def test_footer_payload():
    return {
        "text": "footer text",
        "icon_url": "https://somewhere.com/footer.png",
        "proxy_icon_url": "https://media.somewhere.com/footer.png",
    }


@pytest.fixture
def test_image_payload():
    return {
        "url": "https://somewhere.com/image.png",
        "proxy_url": "https://media.somewhere.com/image.png",
        "height": 122,
        "width": 133,
    }


@pytest.fixture
def test_thumbnail_payload():
    return {
        "url": "https://somewhere.com/thumbnail.png",
        "proxy_url": "https://media.somewhere.com/thumbnail.png",
        "height": 123,
        "width": 456,
    }


@pytest.fixture
def test_video_payload():
    return {
        "url": "https://somewhere.com/video.mp4",
        "height": 1234,
        "width": 4567,
    }


@pytest.fixture
def test_provider_payload():
    return {"name": "some name", "url": "https://somewhere.com/provider"}


@pytest.fixture
def test_author_payload():
    return {
        "name": "some name",
        "url": "https://somewhere.com/author",
        "icon_url": "https://somewhere.com/author.png",
        "proxy_icon_url": "https://media.somewhere.com/author.png",
    }


@pytest.fixture
def test_field_payload():
    return {"name": "title", "value": "some value", "inline": True}


@pytest.fixture
def test_embed_payload(
    test_footer_payload,
    test_image_payload,
    test_thumbnail_payload,
    test_video_payload,
    test_provider_payload,
    test_author_payload,
    test_field_payload,
):
    return {
        "title": "embed title",
        "description": "embed description",
        "url": "https://somewhere.com",
        "timestamp": "2020-03-22T16:40:39.218000+00:00",
        "color": 14014915,
        "footer": test_footer_payload,
        "image": test_image_payload,
        "thumbnail": test_thumbnail_payload,
        "video": test_video_payload,
        "provider": test_provider_payload,
        "image": test_image_payload,
        "author": test_author_payload,
        "fields": [test_field_payload],
    }


class TestEmbedFooter:
    def test_deserialize(self, test_footer_payload):
        footer_obj = embeds.EmbedFooter.deserialize(test_footer_payload)

        assert footer_obj.text == "footer text"
        assert footer_obj.icon_url == "https://somewhere.com/footer.png"
        assert footer_obj.proxy_icon_url == "https://media.somewhere.com/footer.png"

    def test_serialize_full_footer(self):
        footer_obj = embeds.EmbedFooter(text="OK", icon_url="https:////////////",)

        assert footer_obj.serialize() == {"text": "OK", "icon_url": "https:////////////"}

    def test_serialize_partial_footer(self):
        footer_obj = embeds.EmbedFooter(text="OK",)

        assert footer_obj.serialize() == {"text": "OK"}


class TestEmbedImage:
    def test_deserialize(self, test_image_payload):
        image_obj = embeds.EmbedImage.deserialize(test_image_payload)

        assert image_obj.url == "https://somewhere.com/image.png"
        assert image_obj.proxy_url == "https://media.somewhere.com/image.png"
        assert image_obj.height == 122
        assert image_obj.width == 133

    def test_serialize_full_image(self):
        image_obj = embeds.EmbedImage(url="https://///////",)

        assert image_obj.serialize() == {"url": "https://///////"}

    def test_serialize_empty_image(self):
        assert embeds.EmbedImage().serialize() == {}


class TestEmbedThumbnail:
    def test_deserialize(self, test_thumbnail_payload):
        thumbnail_obj = embeds.EmbedThumbnail.deserialize(test_thumbnail_payload)

        assert thumbnail_obj.url == "https://somewhere.com/thumbnail.png"
        assert thumbnail_obj.proxy_url == "https://media.somewhere.com/thumbnail.png"
        assert thumbnail_obj.height == 123
        assert thumbnail_obj.width == 456

    def test_serialize_full_thumbnail(self):
        thumbnail_obj = embeds.EmbedThumbnail(url="https://somewhere.com/thumbnail.png")

        assert thumbnail_obj.serialize() == {"url": "https://somewhere.com/thumbnail.png"}

    def test_serialize_empty_thumbnail(self):
        assert embeds.EmbedThumbnail().serialize() == {}


class TestEmbedVideo:
    def test_deserialize(self, test_video_payload):
        video_obj = embeds.EmbedVideo.deserialize(test_video_payload)

        assert video_obj.url == "https://somewhere.com/video.mp4"
        assert video_obj.height == 1234
        assert video_obj.width == 4567


class TestEmbedProvider:
    def test_deserialize(self, test_provider_payload):
        provider_obj = embeds.EmbedProvider.deserialize(test_provider_payload)

        assert provider_obj.name == "some name"
        assert provider_obj.url == "https://somewhere.com/provider"


class TestEmbedAuthor:
    def test_deserialize(self, test_author_payload):
        author_obj = embeds.EmbedAuthor.deserialize(test_author_payload)

        assert author_obj.name == "some name"
        assert author_obj.url == "https://somewhere.com/author"
        assert author_obj.icon_url == "https://somewhere.com/author.png"
        assert author_obj.proxy_icon_url == "https://media.somewhere.com/author.png"

    def test_serialize_full_author(self):
        author_obj = embeds.EmbedAuthor(
            name="Author 187", url="https://nyaanyaanyaa", icon_url="https://a-proper-domain"
        )

        assert author_obj.serialize() == {
            "name": "Author 187",
            "url": "https://nyaanyaanyaa",
            "icon_url": "https://a-proper-domain",
        }

    def test_serialize_empty_author(self):
        assert embeds.EmbedAuthor().serialize() == {}


class TestEmbedField:
    def test_deserialize(self):
        field_obj = embeds.EmbedField.deserialize({"name": "title", "value": "some value"})

        assert field_obj.name == "title"
        assert field_obj.value == "some value"
        assert field_obj.is_inline is False

    def test_serialize(self, test_field_payload):
        field_obj = embeds.EmbedField(name="NAME", value="nyaa nyaa nyaa", is_inline=True)

        assert field_obj.serialize() == {"name": "NAME", "value": "nyaa nyaa nyaa", "inline": True}


class TestEmbed:
    def test_deserialize(
        self,
        test_embed_payload,
        test_footer_payload,
        test_image_payload,
        test_thumbnail_payload,
        test_video_payload,
        test_provider_payload,
        test_author_payload,
        test_field_payload,
    ):
        mock_datetime = mock.MagicMock(datetime.datetime)

        with _helpers.patch_marshal_attr(
            embeds.Embed, "timestamp", deserializer=conversions.parse_iso_8601_ts, return_value=mock_datetime,
        ) as patched_timestamp_deserializer:
            embed_obj = embeds.Embed.deserialize(test_embed_payload)
            patched_timestamp_deserializer.assert_called_once_with("2020-03-22T16:40:39.218000+00:00")

        assert embed_obj.title == "embed title"
        assert embed_obj.description == "embed description"
        assert embed_obj.url == "https://somewhere.com"
        assert embed_obj.timestamp == mock_datetime
        assert embed_obj.color == colors.Color(14014915)
        assert embed_obj.footer == embeds.EmbedFooter.deserialize(test_footer_payload)
        assert embed_obj.image == embeds.EmbedImage.deserialize(test_image_payload)
        assert embed_obj.thumbnail == embeds.EmbedThumbnail.deserialize(test_thumbnail_payload)
        assert embed_obj.video == embeds.EmbedVideo.deserialize(test_video_payload)
        assert embed_obj.provider == embeds.EmbedProvider.deserialize(test_provider_payload)
        assert embed_obj.author == embeds.EmbedAuthor.deserialize(test_author_payload)
        assert embed_obj.fields == [embeds.EmbedField.deserialize(test_field_payload)]

    def test_serialize_full_embed(self):
        embed_obj = embeds.Embed(
            title="Nyaa me pls >////<",
            description="Nyan >////<",
            url="https://a-url-now",
            timestamp=datetime.datetime.fromisoformat("2020-03-22T16:40:39.218000+00:00"),
            color=colors.Color(123123),
            footer=embeds.EmbedFooter(text="HI"),
            image=embeds.EmbedImage(url="https://not-a-url"),
            thumbnail=embeds.EmbedThumbnail(url="https://url-a-not"),
            author=embeds.EmbedAuthor(name="a name", url="https://a-man"),
            fields=[embeds.EmbedField(name="aField", value="agent69", is_inline=True)],
        )

        assert embed_obj.serialize() == {
            "title": "Nyaa me pls >////<",
            "description": "Nyan >////<",
            "url": "https://a-url-now",
            "timestamp": "2020-03-22T16:40:39.218000+00:00",
            "color": 123123,
            "footer": {"text": "HI"},
            "image": {"url": "https://not-a-url"},
            "thumbnail": {"url": "https://url-a-not"},
            "author": {"name": "a name", "url": "https://a-man"},
            "fields": [{"name": "aField", "value": "agent69", "inline": True}],
        }

    def test_serialize_empty_embed(self):
        assert embeds.Embed().serialize() == {"fields": []}

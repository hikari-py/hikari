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
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime

import mock
import pytest

from hikari import application
from hikari.internal import conversions
from hikari.models import colors
from hikari.models import embeds
from hikari.models import files
from tests.hikari import _helpers


@pytest.fixture()
def mock_app():
    return mock.MagicMock(application.Application)


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
    def test_deserialize(self, test_footer_payload, mock_app):
        footer_obj = embeds.EmbedFooter.deserialize(test_footer_payload, app=mock_app)

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
    def test_deserialize(self, test_image_payload, mock_app):
        image_obj = embeds.EmbedImage.deserialize(test_image_payload, app=mock_app)

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
    def test_deserialize(self, test_thumbnail_payload, mock_app):
        thumbnail_obj = embeds.EmbedThumbnail.deserialize(test_thumbnail_payload, app=mock_app)

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
    def test_deserialize(self, test_video_payload, mock_app):
        video_obj = embeds.EmbedVideo.deserialize(test_video_payload, app=mock_app)

        assert video_obj.url == "https://somewhere.com/video.mp4"
        assert video_obj.height == 1234
        assert video_obj.width == 4567


class TestEmbedProvider:
    def test_deserialize(self, test_provider_payload, mock_app):
        provider_obj = embeds.EmbedProvider.deserialize(test_provider_payload, app=mock_app)

        assert provider_obj.name == "some name"
        assert provider_obj.url == "https://somewhere.com/provider"


class TestEmbedAuthor:
    def test_deserialize(self, test_author_payload, mock_app):
        author_obj = embeds.EmbedAuthor.deserialize(test_author_payload, app=mock_app)

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
    def test_deserialize(self, mock_app):
        field_obj = embeds.EmbedField.deserialize({"name": "title", "value": "some value"}, app=mock_app)

        assert field_obj.name == "title"
        assert field_obj.value == "some value"
        assert field_obj.is_inline is False

    def test_serialize(self, test_field_payload):
        field_obj = embeds.EmbedField(name="NAME", value="nyaa nyaa nyaa", is_inline=True)

        assert field_obj.serialize() == {"name": "NAME", "value": "nyaa nyaa nyaa", "inline": True}


class TestEmbed:
    @_helpers.assert_raises(type_=ValueError)
    def test_embed___init___raises_value_error_on_invalid_title(self):
        embeds.Embed(title="x" * 257)

    @_helpers.assert_raises(type_=ValueError)
    def test_embed___init___raises_value_error_on_invalid_description(self):
        embeds.Embed(description="x" * 2049)

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
        mock_app,
    ):
        mock_datetime = mock.MagicMock(datetime.datetime)

        with _helpers.patch_marshal_attr(
            embeds.Embed, "timestamp", deserializer=conversions.parse_iso_8601_ts, return_value=mock_datetime,
        ) as patched_timestamp_deserializer:
            embed_obj = embeds.Embed.deserialize(test_embed_payload, app=mock_app)
            patched_timestamp_deserializer.assert_called_once_with("2020-03-22T16:40:39.218000+00:00")

        assert embed_obj.title == "embed title"
        assert embed_obj.description == "embed description"
        assert embed_obj.url == "https://somewhere.com"
        assert embed_obj.timestamp == mock_datetime
        assert embed_obj.color == colors.Color(14014915)
        assert embed_obj.footer == embeds.EmbedFooter.deserialize(test_footer_payload)
        assert embed_obj.footer._app is mock_app
        assert embed_obj.image == embeds.EmbedImage.deserialize(test_image_payload)
        assert embed_obj.image._app is mock_app
        assert embed_obj.thumbnail == embeds.EmbedThumbnail.deserialize(test_thumbnail_payload)
        assert embed_obj.thumbnail._app is mock_app
        assert embed_obj.video == embeds.EmbedVideo.deserialize(test_video_payload)
        assert embed_obj.video._app is mock_app
        assert embed_obj.provider == embeds.EmbedProvider.deserialize(test_provider_payload)
        assert embed_obj.provider._app is mock_app
        assert embed_obj.author == embeds.EmbedAuthor.deserialize(test_author_payload)
        assert embed_obj.author._app is mock_app
        assert embed_obj.fields == [embeds.EmbedField.deserialize(test_field_payload)]
        assert embed_obj.fields[0]._app is mock_app

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

        with mock.patch.object(embeds.Embed, "_check_total_length") as mock_check:
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
            mock_check.assert_called_once()

    def test_serialize_empty_embed(self):
        assert embeds.Embed().serialize() == {"fields": []}

    def test_assets_to_upload(self):
        em = embeds.Embed()
        em._assets_to_upload = ["asset_1", "asset_2"]
        assert em.assets_to_upload == ["asset_1", "asset_2"]

    @pytest.mark.parametrize(
        ["input", "expected_output"],
        [
            ("https://some.url/to/somewhere.png", ("https://some.url/to/somewhere.png", None)),
            (files.FileStream("test.png"), ["attachment://test.png", "the inputed file"]),
            (None, (None, None)),
        ],
    )
    def test__extract_url(self, input, expected_output):
        if isinstance(input, files.BaseStream):
            expected_output[1] = input
            expected_output = tuple(expected_output)
        em = embeds.Embed()
        assert em._extract_url(input) == expected_output

    def test__maybe_ref_file_obj(self):
        mock_file_obj = mock.MagicMock(files.BaseStream)
        em = embeds.Embed()
        em._maybe_ref_file_obj(mock_file_obj)
        assert em.assets_to_upload == [mock_file_obj]

    def test__maybe_ref_file_obj_when_None(self):
        em = embeds.Embed()
        em._maybe_ref_file_obj(None)
        assert em.assets_to_upload == []

    def test_set_footer_without_optionals(self):
        em = embeds.Embed()
        assert em.set_footer(text="test") == em
        assert em.footer.text == "test"
        assert em.footer.icon_url is None
        assert em._assets_to_upload == []

    def test_set_footer_with_optionals_with_image_as_file(self):
        mock_file_obj = mock.MagicMock(files.BaseStream)
        mock_file_obj.filename = "test.png"
        em = embeds.Embed()
        assert em.set_footer(text="test", icon=mock_file_obj) == em
        assert em.footer.text == "test"
        assert em.footer.icon_url == "attachment://test.png"
        assert em._assets_to_upload == [mock_file_obj]

    def test_set_image_with_optionals_with_image_as_string(self):
        em = embeds.Embed()
        assert em.set_footer(text="test", icon="https://somewhere.url/image.png") == em
        assert em.footer.text == "test"
        assert em.footer.icon_url == "https://somewhere.url/image.png"
        assert em._assets_to_upload == []

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.parametrize("text", ["   ", "", "x" * 2100])
    def test_set_footer_raises_value_error_on_invalid_text(self, text):
        embeds.Embed().set_footer(text=text)

    def test_set_image_without_optionals(self):
        em = embeds.Embed()
        assert em.set_image() == em
        assert em.image.url is None
        assert em._assets_to_upload == []

    def test_set_image_with_optionals_with_image_as_file(self):
        mock_file_obj = mock.MagicMock(files.BaseStream)
        mock_file_obj.filename = "test.png"
        em = embeds.Embed()
        assert em.set_image(mock_file_obj) == em
        assert em.image.url == "attachment://test.png"
        assert em._assets_to_upload == [mock_file_obj]

    def test_set_image_with_optionals_with_image_as_string(self):
        em = embeds.Embed()
        assert em.set_image("https://somewhere.url/image.png") == em
        assert em.image.url == "https://somewhere.url/image.png"
        assert em._assets_to_upload == []

    def test_set_thumbnail_without_optionals(self):
        em = embeds.Embed()
        assert em.set_thumbnail() == em
        assert em.thumbnail.url is None
        assert em._assets_to_upload == []

    def test_set_thumbnail_with_optionals_with_image_as_file(self):
        mock_file_obj = mock.MagicMock(files.BaseStream)
        mock_file_obj.filename = "test.png"
        em = embeds.Embed()
        assert em.set_thumbnail(mock_file_obj) == em
        assert em.thumbnail.url == "attachment://test.png"
        assert em._assets_to_upload == [mock_file_obj]

    def test_set_thumbnail_with_optionals_with_image_as_string(self):
        em = embeds.Embed()
        assert em.set_thumbnail("https://somewhere.url/image.png") == em
        assert em.thumbnail.url == "https://somewhere.url/image.png"
        assert em._assets_to_upload == []

    def test_set_author_without_optionals(self):
        em = embeds.Embed()
        assert em.set_author() == em
        assert em.author.name is None
        assert em.author.url is None
        assert em.author.icon_url is None
        assert em._assets_to_upload == []

    def test_set_author_with_optionals_with_icon_as_file(self):
        mock_file_obj = mock.MagicMock(files.BaseStream)
        mock_file_obj.filename = "test.png"
        em = embeds.Embed()
        assert em.set_author(name="hikari", url="nekokatt.gitlab.io/hikari", icon=mock_file_obj) == em
        assert em.author.name == "hikari"
        assert em.author.url == "nekokatt.gitlab.io/hikari"
        assert em.author.icon_url == "attachment://test.png"
        assert em._assets_to_upload == [mock_file_obj]

    def test_set_author_with_optionals_with_icon_as_string(self):
        em = embeds.Embed()
        assert (
            em.set_author(name="hikari", url="nekokatt.gitlab.io/hikari", icon="https://somewhere.url/image.png") == em
        )
        assert em.author.name == "hikari"
        assert em.author.url == "nekokatt.gitlab.io/hikari"
        assert em.author.icon_url == "https://somewhere.url/image.png"
        assert em._assets_to_upload == []

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.parametrize("name", ["", " ", "x" * 257])
    def test_set_author_raises_value_error_on_invalid_name(self, name):
        embeds.Embed().set_author(name=name)

    def test_add_field_without_optionals(self):
        em = embeds.Embed()
        assert em.add_field(name="test_name", value="test_value") == em
        assert len(em.fields) == 1
        assert em.fields[0].name == "test_name"
        assert em.fields[0].value == "test_value"
        assert em.fields[0].is_inline is False

    def test_add_field_with_optionals(self):
        field_obj1 = embeds.EmbedField(name="nothing to see here", value="still nothing")
        field_obj2 = embeds.EmbedField(name="test_name", value="test_value", is_inline=True)
        em = embeds.Embed()
        em.fields = [field_obj1]
        with mock.patch.object(embeds, "EmbedField", return_value=field_obj2) as mock_embed_field:
            assert em.add_field(name="test_name", value="test_value", inline=True, index=0) == em
            mock_embed_field.assert_called_once_with(name="test_name", value="test_value", is_inline=True)
            assert em.fields == [field_obj2, field_obj1]
            assert em.fields[0].name == "test_name"
            assert em.fields[0].value == "test_value"
            assert em.fields[0].is_inline is True

    @_helpers.assert_raises(type_=ValueError)
    def test_add_field_raises_value_error_on_too_many_fields(self):
        fields = [mock.MagicMock(embeds.EmbedField) for _ in range(25)]
        embeds.Embed(fields=fields).add_field(name="test", value="blam")

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.parametrize("name", ["", " ", "x" * 257])
    def test_add_field_raises_value_error_on_invalid_name(self, name):
        fields = [mock.MagicMock(embeds.EmbedField)]
        embeds.Embed(fields=fields).add_field(name=name, value="blam")

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.parametrize("value", ["", " ", "x" * 2049])
    def test_add_field_raises_value_error_on_invalid_value(self, value):
        fields = [mock.MagicMock(embeds.EmbedField)]
        embeds.Embed(fields=fields).add_field(name="test", value=value)

    def test_edit_field_without_optionals(self):
        field_obj = embeds.EmbedField(name="nothing to see here", value="still nothing")
        em = embeds.Embed()
        em.fields = [field_obj]
        assert em.edit_field(0) == em
        assert em.fields == [field_obj]
        assert em.fields[0].name == "nothing to see here"
        assert em.fields[0].value == "still nothing"
        assert em.fields[0].is_inline is False

    def test_edit_field_with_optionals(self):
        field_obj = embeds.EmbedField(name="nothing to see here", value="still nothing")
        em = embeds.Embed()
        em.fields = [field_obj]
        assert em.edit_field(0, name="test_name", value="test_value", inline=True) == em
        assert em.fields == [field_obj]
        assert em.fields[0].name == "test_name"
        assert em.fields[0].value == "test_value"
        assert em.fields[0].is_inline is True

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.parametrize("name", ["", " ", "x" * 257])
    def test_edit_field_raises_value_error_on_invalid_name(self, name):
        fields = [mock.MagicMock(embeds.EmbedField)]
        embeds.Embed(fields=fields).edit_field(0, name=name, value="blam")

    @_helpers.assert_raises(type_=ValueError)
    @pytest.mark.parametrize("value", ["", " ", "x" * 2049])
    def test_edit_field_raises_value_error_on_invalid_value(self, value):
        fields = [mock.MagicMock(embeds.EmbedField)]
        embeds.Embed(fields=fields).edit_field(0, name="test", value=value)

    def test_remove_field(self):
        mock_field1 = mock.MagicMock(embeds.EmbedField)
        mock_field2 = mock.MagicMock(embeds.EmbedField)
        em = embeds.Embed()
        em.fields = [mock_field1, mock_field2]

        assert em.remove_field(0) == em
        assert em.fields == [mock_field2]

    @pytest.mark.parametrize(["input", "expected_output"], [(None, 0), ("this is 21 characters", 21)])
    def test__safe_len(self, input, expected_output):
        em = embeds.Embed()
        assert em._safe_len(input) == expected_output

    @_helpers.assert_raises(type_=ValueError)
    def test__check_total(self):
        em = embeds.Embed()
        em.title = "a" * 1000
        em.description = "b" * 1000
        em.author = embeds.EmbedAuthor(name="c" * 1000)
        em.footer = embeds.EmbedFooter(text="d" * 1000)
        em.fields.append(embeds.EmbedField(name="e" * 1000, value="f" * 1001))

        em._check_total_length()

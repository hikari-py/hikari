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
import mock
import pytest

from hikari import embeds


class TestEmbedResource:
    @pytest.fixture
    def resource(self):
        return embeds.EmbedResource(resource=mock.Mock())

    def test_url(self, resource):
        assert resource.url is resource.resource.url

    def test_filename(self, resource):
        assert resource.filename is resource.resource.filename

    def test_stream(self, resource):
        mock_executor = object()

        assert resource.stream(executor=mock_executor, head_only=True) is resource.resource.stream.return_value

        resource.resource.stream.assert_called_once_with(executor=mock_executor, head_only=True)


class TestEmbedResourceWithProxy:
    @pytest.fixture
    def resource_with_proxy(self):
        return embeds.EmbedResourceWithProxy(resource=mock.Mock(), proxy_resource=mock.Mock())

    def test_proxy_url(self, resource_with_proxy):
        assert resource_with_proxy.proxy_url is resource_with_proxy.proxy_resource.url

    def test_proxy_url_when_resource_is_none(self, resource_with_proxy):
        resource_with_proxy.proxy_resource = None
        assert resource_with_proxy.proxy_url is None

    def test_proxy_filename(self, resource_with_proxy):
        assert resource_with_proxy.proxy_filename is resource_with_proxy.proxy_resource.filename

    def test_proxy_filename_when_resource_is_none(self, resource_with_proxy):
        resource_with_proxy.proxy_resource = None
        assert resource_with_proxy.proxy_filename is None


class TestEmbed:
    def test_total_length_when_embed_is_empty(self):
        embed = embeds.Embed()
        assert embed.total_length() == 0

    def test_total_length_when_title_is_none(self):
        embed = embeds.Embed(title=None)
        assert embed.total_length() == 0

    def test_total_length_title(self):
        embed = embeds.Embed(title="title")
        assert embed.total_length() == 5

    def test_total_length_when_description_is_none(self):
        embed = embeds.Embed(description=None)
        assert embed.total_length() == 0

    def test_total_length_description(self):
        embed = embeds.Embed(description="description")
        assert embed.total_length() == 11

    def test_total_length_author_name(self):
        embed = embeds.Embed().set_author(name="author name")
        assert embed.total_length() == 11

    def test_total_length_footer_text(self):
        embed = embeds.Embed().set_footer(text="footer text")
        assert embed.total_length() == 11

    def test_total_length_field_name(self):
        embed = embeds.Embed().add_field(name="field name", value="")
        assert embed.total_length() == 10

    def test_total_length_field_value(self):
        embed = embeds.Embed().add_field(name="", value="field value")
        assert embed.total_length() == 11

    def test_total_length_all(self):
        embed = embeds.Embed(title="title", description="description")
        embed.set_author(name="author name")
        embed.set_footer(text="footer text")
        embed.add_field(name="field name 1", value="field value 2")
        embed.add_field(name="field name 3", value="field value 4")
        assert embed.total_length() == 88

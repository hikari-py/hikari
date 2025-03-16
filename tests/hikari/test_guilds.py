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

import datetime

import mock
import pytest

from hikari import channels as channels_
from hikari import colors
from hikari import guilds
from hikari import permissions
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.impl import gateway_bot
from hikari.internal import routes
from hikari.internal import time
from tests.hikari import hikari_test_helpers


@pytest.fixture
def mock_app() -> traits.RESTAware:
    return mock.Mock(spec_set=gateway_bot.GatewayBot)


class TestPartialRole:
    @pytest.fixture
    def model(self, mock_app: traits.RESTAware) -> guilds.PartialRole:
        return guilds.PartialRole(app=mock_app, id=snowflakes.Snowflake(1106913972), name="The Big Cool")

    def test_str_operator(self, model: guilds.PartialRole):
        assert str(model) == "The Big Cool"

    def test_mention_property(self, model: guilds.PartialRole):
        assert model.mention == "<@&1106913972>"


def test_PartialApplication_str_operator():
    mock_application = mock.Mock(guilds.PartialApplication)
    mock_application.name = "beans"
    assert guilds.PartialApplication.__str__(mock_application) == "beans"


class TestPartialApplication:
    @pytest.fixture
    def partial_application(self) -> guilds.PartialApplication:
        return guilds.PartialApplication(
            id=snowflakes.Snowflake(123),
            name="partial_application",
            description="partial_application_description",
            icon_hash="icon_hash",
        )

    def test_icon_url_property(self, partial_application: guilds.PartialApplication):
        with mock.patch.object(
            guilds.PartialApplication, "make_icon_url", mock.Mock(return_value="url")
        ) as patched_make_icon_url:
            assert partial_application.icon_url == "url"

            patched_make_icon_url.assert_called_once_with()

    def test_make_icon_url_when_hash_is_None(self, partial_application: guilds.PartialApplication):
        partial_application.icon_hash = None

        with (
            mock.patch.object(routes, "CDN_APPLICATION_ICON") as patched_route,
            mock.patch.object(
                patched_route, "compile_to_file", mock.Mock(return_value="file")
            ) as patched_compile_to_file,
        ):
            assert partial_application.make_icon_url(ext="jpeg", size=1) is None

        patched_compile_to_file.assert_not_called()

    def test_make_icon_url_when_hash_is_not_None(self, partial_application: guilds.PartialApplication):
        with (
            mock.patch.object(routes, "CDN_APPLICATION_ICON") as patched_route,
            mock.patch.object(
                patched_route, "compile_to_file", mock.Mock(return_value="file")
            ) as patched_compile_to_file,
        ):
            assert partial_application.make_icon_url(ext="jpeg", size=1) == "file"

        patched_compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="icon_hash", size=1, file_format="jpeg"
        )


class TestIntegrationAccount:
    @pytest.fixture
    def integration_account(self) -> guilds.IntegrationAccount:
        return guilds.IntegrationAccount(id="foo", name="bar")

    def test_str_operator(self, integration_account: guilds.IntegrationAccount):
        assert str(integration_account) == "bar"


class TestPartialIntegration:
    @pytest.fixture
    def model(self) -> guilds.PartialIntegration:
        return guilds.PartialIntegration(
            account=mock.Mock(return_value=guilds.IntegrationAccount),
            id=snowflakes.Snowflake(69420),
            name="nice",
            type="illegal",
        )

    def test_str_operator(self, model: guilds.PartialIntegration):
        assert str(model) == "nice"


class TestRole:
    @pytest.fixture
    def model(self, mock_app: traits.RESTAware) -> guilds.Role:
        return guilds.Role(
            app=mock_app,
            id=snowflakes.Snowflake(979899100),
            name="@everyone",
            color=colors.Color(0x1A2B3C),
            guild_id=snowflakes.Snowflake(112233),
            is_hoisted=False,
            icon_hash="icon_hash",
            unicode_emoji=None,
            is_managed=False,
            is_mentionable=True,
            permissions=permissions.Permissions.CONNECT,
            position=12,
            bot_id=None,
            integration_id=None,
            is_premium_subscriber_role=False,
            is_guild_linked_role=True,
            subscription_listing_id=snowflakes.Snowflake(10),
            is_available_for_purchase=True,
        )

    def test_colour_property(self, model: guilds.Role):
        assert model.colour == colors.Color(0x1A2B3C)

    def test_icon_url_property(self, model: guilds.Role):
        with mock.patch.object(guilds.Role, "make_icon_url") as patched_make_icon_url:
            assert model.icon_url == patched_make_icon_url.return_value

            patched_make_icon_url.assert_called_once_with()

    def test_mention_property(self, model: guilds.Role):
        assert model.mention == "<@&979899100>"

    def test_mention_property_when_is_everyone_role(self, model: guilds.Role):
        model.id = model.guild_id
        assert model.mention == "@everyone"

    def test_make_icon_url_when_hash_is_None(self, model: guilds.Role):
        model.icon_hash = None

        with mock.patch.object(
            routes, "CDN_ROLE_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_make_icon_url_when_hash_is_not_None(self, model: guilds.Role):
        with mock.patch.object(
            routes, "CDN_ROLE_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, role_id=979899100, hash="icon_hash", size=1, file_format="jpeg"
        )


class TestGuildWidget:
    @pytest.fixture
    def guild_widget(self, mock_app: traits.RESTAware) -> guilds.GuildWidget:
        return guilds.GuildWidget(app=mock_app, channel_id=snowflakes.Snowflake(420), is_enabled=True)

    def test_app_property(self, guild_widget: guilds.GuildWidget, mock_app: traits.RESTAware):
        assert guild_widget.app is mock_app

    def test_channel_property(self, guild_widget: guilds.GuildWidget):
        assert guild_widget.channel_id == snowflakes.Snowflake(420)

    def test_is_enabled_property(self, guild_widget: guilds.GuildWidget):
        assert guild_widget.is_enabled is True

    @pytest.mark.asyncio
    async def test_fetch_channel(self, guild_widget: guilds.GuildWidget):
        mock_channel = mock.Mock(channels_.GuildChannel)
        guild_widget.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)

        assert await guild_widget.fetch_channel() is guild_widget.app.rest.fetch_channel.return_value
        guild_widget.app.rest.fetch_channel.assert_awaited_once_with(420)

    @pytest.mark.asyncio
    async def test_fetch_channel_when_None(self, guild_widget: guilds.GuildWidget):
        guild_widget.app.rest.fetch_channel = mock.AsyncMock()
        guild_widget.channel_id = None

        assert await guild_widget.fetch_channel() is None


class TestMember:
    @pytest.fixture
    def mock_user(self) -> users.User:
        return mock.Mock(id=snowflakes.Snowflake(123))

    @pytest.fixture
    def member(self, mock_user: users.User) -> guilds.Member:
        return guilds.Member(
            guild_id=snowflakes.Snowflake(456),
            is_deaf=True,
            is_mute=True,
            is_pending=False,
            joined_at=datetime.datetime.now().astimezone(),
            nickname="davb",
            guild_avatar_hash="dab",
            premium_since=None,
            role_ids=[snowflakes.Snowflake(456), snowflakes.Snowflake(1234)],
            user=mock_user,
            raw_communication_disabled_until=None,
        )

    def test_str_operator(self, member: guilds.Member, mock_user: users.User):
        assert str(member) == str(mock_user)

    def test_app_property(self, member: guilds.Member, mock_user: users.User):
        assert member.app is mock_user.app

    def test_id_property(self, member: guilds.Member, mock_user: users.User):
        assert member.id is mock_user.id

    def test_username_property(self, member: guilds.Member, mock_user: users.User):
        assert member.username is mock_user.username

    def test_discriminator_property(self, member: guilds.Member, mock_user: users.User):
        assert member.discriminator is mock_user.discriminator

    def test_avatar_hash_property(self, member: guilds.Member, mock_user: users.User):
        assert member.avatar_hash is mock_user.avatar_hash

    def test_is_bot_property(self, member: guilds.Member, mock_user: users.User):
        assert member.is_bot is mock_user.is_bot

    def test_is_system_property(self, member: guilds.Member, mock_user: users.User):
        assert member.is_system is mock_user.is_system

    def test_flags_property(self, member: guilds.Member, mock_user: users.User):
        assert member.flags is mock_user.flags

    def test_avatar_url_property(self, member: guilds.Member, mock_user: users.User):
        assert member.avatar_url is mock_user.avatar_url

    def test_display_avatar_url_when_guild_hash_is_None(self, member: guilds.Member, mock_user: users.User):
        with mock.patch.object(guilds.Member, "make_guild_avatar_url") as mock_make_guild_avatar_url:
            assert member.display_avatar_url is mock_make_guild_avatar_url.return_value

    def test_display_guild_avatar_url_when_guild_hash_is_not_None(self, member: guilds.Member, mock_user: users.User):
        with mock.patch.object(guilds.Member, "make_guild_avatar_url", return_value=None):
            with mock.patch.object(users.User, "display_avatar_url") as mock_display_avatar_url:
                assert member.display_avatar_url is mock_display_avatar_url

    def test_banner_hash_property(self, member: guilds.Member, mock_user: users.User):
        assert member.banner_hash is mock_user.banner_hash

    def test_banner_url_property(self, member: guilds.Member, mock_user: users.User):
        assert member.banner_url is mock_user.banner_url

    def test_accent_color_property(self, member: guilds.Member, mock_user: users.User):
        assert member.accent_color is mock_user.accent_color

    def test_guild_avatar_url_property(self, member: guilds.Member):
        with mock.patch.object(guilds.Member, "make_guild_avatar_url") as make_guild_avatar_url:
            assert member.guild_avatar_url is make_guild_avatar_url.return_value

    def test_communication_disabled_until(self, member: guilds.Member):
        member.raw_communication_disabled_until = datetime.datetime(2021, 11, 22)

        with mock.patch.object(time, "utc_datetime", return_value=datetime.datetime(2021, 10, 18)):
            assert member.communication_disabled_until() == datetime.datetime(2021, 11, 22)

    def test_communication_disabled_until_when_raw_communication_disabled_until_is_None(self, member: guilds.Member):
        member.raw_communication_disabled_until = None

        with mock.patch.object(time, "utc_datetime", return_value=datetime.datetime(2021, 10, 18)):
            assert member.communication_disabled_until() is None

    def test_communication_disabled_until_when_raw_communication_disabled_until_is_in_the_past(
        self, member: guilds.Member
    ):
        member.raw_communication_disabled_until = datetime.datetime(2021, 10, 18)

        with mock.patch.object(time, "utc_datetime", return_value=datetime.datetime(2021, 11, 22)):
            assert member.communication_disabled_until() is None

    def test_make_avatar_url(self, member: guilds.Member, mock_user: users.User):
        with mock.patch.object(mock_user, "make_avatar_url") as patched_make_avatar_url:
            result = member.make_avatar_url(ext="png", size=4096)
            patched_make_avatar_url.assert_called_once_with(ext="png", size=4096)
            assert result is patched_make_avatar_url.return_value

    def test_make_guild_avatar_url_when_no_hash(self, member: guilds.Member):
        member.guild_avatar_hash = None
        assert member.make_guild_avatar_url(ext="png", size=1024) is None

    def test_make_guild_avatar_url_when_format_is_None_and_avatar_hash_is_for_gif(self, member: guilds.Member):
        member.guild_avatar_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_MEMBER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert member.make_guild_avatar_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            user_id=member.id,
            guild_id=member.guild_id,
            hash=member.guild_avatar_hash,
            size=4096,
            file_format="gif",
        )

    def test_make_guild_avatar_url_when_format_is_None_and_avatar_hash_is_not_for_gif(self, member: guilds.Member):
        member.guild_avatar_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_MEMBER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert member.make_guild_avatar_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            user_id=member.id,
            guild_id=member.guild_id,
            hash=member.guild_avatar_hash,
            size=4096,
            file_format="png",
        )

    def test_make_guild_avatar_url_with_all_args(self, member: guilds.Member):
        member.guild_avatar_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_MEMBER_AVATAR", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert member.make_guild_avatar_url(ext="url", size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL,
            guild_id=member.guild_id,
            user_id=member.id,
            hash=member.guild_avatar_hash,
            size=4096,
            file_format="url",
        )

    @pytest.mark.asyncio
    async def test_fetch_dm_channel(self, member: guilds.Member):
        member.user.fetch_dm_channel = mock.AsyncMock()

        assert await member.fetch_dm_channel() is member.user.fetch_dm_channel.return_value

        member.user.fetch_dm_channel.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_fetch_self(self, member: guilds.Member):
        member.user.app.rest.fetch_member = mock.AsyncMock()

        assert await member.fetch_self() is member.user.app.rest.fetch_member.return_value

        member.user.app.rest.fetch_member.assert_awaited_once_with(456, 123)

    @pytest.mark.asyncio
    async def test_fetch_roles(self, member: guilds.Member):
        member.user.app.rest.fetch_roles = mock.AsyncMock()
        await member.fetch_roles()
        member.user.app.rest.fetch_roles.assert_awaited_once_with(456)

    @pytest.mark.asyncio
    async def test_ban(self, member: guilds.Member):
        member.app.rest.ban_user = mock.AsyncMock()

        await member.ban(delete_message_seconds=600, reason="bored")

        member.app.rest.ban_user.assert_awaited_once_with(456, 123, delete_message_seconds=600, reason="bored")

    @pytest.mark.asyncio
    async def test_unban(self, member: guilds.Member):
        member.app.rest.unban_user = mock.AsyncMock()

        await member.unban(reason="Unbored")

        member.app.rest.unban_user.assert_awaited_once_with(456, 123, reason="Unbored")

    @pytest.mark.asyncio
    async def test_kick(self, member: guilds.Member):
        member.app.rest.kick_user = mock.AsyncMock()

        await member.kick(reason="bored")

        member.app.rest.kick_user.assert_awaited_once_with(456, 123, reason="bored")

    @pytest.mark.asyncio
    async def test_add_role(self, member: guilds.Member):
        member.app.rest.add_role_to_member = mock.AsyncMock()

        await member.add_role(563412, reason="Promoted")

        member.app.rest.add_role_to_member.assert_awaited_once_with(456, 123, 563412, reason="Promoted")

    @pytest.mark.asyncio
    async def test_remove_role(self, member: guilds.Member):
        member.app.rest.remove_role_from_member = mock.AsyncMock()

        await member.remove_role(563412, reason="Demoted")

        member.app.rest.remove_role_from_member.assert_awaited_once_with(456, 123, 563412, reason="Demoted")

    @pytest.mark.asyncio
    async def test_edit(self, member: guilds.Member):
        member.app.rest.edit_member = mock.AsyncMock()
        disabled_until = datetime.datetime(2021, 11, 17)
        edit = await member.edit(
            nickname="Imposter",
            roles=[123, 432, 345],
            mute=False,
            deaf=True,
            voice_channel=4321245,
            communication_disabled_until=disabled_until,
            reason="I'm God",
        )

        member.app.rest.edit_member.assert_awaited_once_with(
            456,
            123,
            nickname="Imposter",
            roles=[123, 432, 345],
            mute=False,
            deaf=True,
            voice_channel=4321245,
            communication_disabled_until=disabled_until,
            reason="I'm God",
        )

        assert edit == member.app.rest.edit_member.return_value

    def test_default_avatar_url_property(self, member: guilds.Member, mock_user: users.User):
        assert member.default_avatar_url is mock_user.default_avatar_url

    def test_display_name_property_when_nickname(self, member: guilds.Member):
        assert member.display_name == "davb"

    def test_display_name_property_when_no_nickname(self, member: guilds.Member, mock_user: users.User):
        member.nickname = None
        assert member.display_name is mock_user.global_name

    def test_mention_property(self, member: guilds.Member, mock_user: users.User):
        assert member.mention == mock_user.mention

    def test_get_guild(self, member: guilds.Member):
        guild = mock.Mock(id=456)

        with (
            mock.patch.object(member.user.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild", side_effect=[guild]) as patched_get_guild,
        ):
            assert member.get_guild() == guild

            patched_get_guild.assert_has_calls([mock.call(456)])

    def test_get_guild_when_guild_not_in_cache(self, member: guilds.Member):
        with (
            mock.patch.object(member.user.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_guild", side_effect=[None]) as patched_get_guild,
        ):
            assert member.get_guild() is None

            patched_get_guild.assert_has_calls([mock.call(456)])

    def test_get_guild_when_no_cache_trait(self, member: guilds.Member):
        with (
            mock.patch.object(member.user.app, "cache", mock.Mock()) as mocked_cache,
            mock.patch.object(mocked_cache, "get_guild", mock.Mock(return_value=None)),
        ):
            assert member.get_guild() is None

    def test_get_roles(self, member: guilds.Member):
        role1 = mock.Mock(id=321, position=2)
        role2 = mock.Mock(id=654, position=1)
        with (
            mock.patch.object(member.user.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_role", side_effect=[role1, role2]) as patched_get_role,
        ):
            member.role_ids = [snowflakes.Snowflake(321), snowflakes.Snowflake(654)]

            assert member.get_roles() == [role1, role2]

            patched_get_role.assert_has_calls([mock.call(321), mock.call(654)])

    def test_get_roles_when_role_ids_not_in_cache(self, member: guilds.Member):
        role = mock.Mock(id=456, position=1)
        with (
            mock.patch.object(member.user.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_role", side_effect=[None, role]) as patched_get_role,
        ):
            member.role_ids = [snowflakes.Snowflake(321), snowflakes.Snowflake(456)]

            assert member.get_roles() == [role]

            patched_get_role.assert_has_calls([mock.call(321), mock.call(456)])

    def test_get_roles_when_empty_cache(self, member: guilds.Member):
        member.role_ids = [snowflakes.Snowflake(132), snowflakes.Snowflake(432)]
        with (
            mock.patch.object(member.user.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_role", side_effect=[None, None]) as patched_get_role,
        ):
            assert member.get_roles() == []

            patched_get_role.assert_has_calls([mock.call(132), mock.call(432)])

    def test_get_roles_when_no_cache_trait(self, member: guilds.Member):
        with mock.patch.object(member.user, "app", mock.Mock(traits.RESTAware)):
            assert member.get_roles() == []

    def test_get_top_role(self, member: guilds.Member):
        role1 = mock.Mock(id=321, position=2)
        role2 = mock.Mock(id=654, position=1)

        with mock.patch.object(guilds.Member, "get_roles", return_value=[role1, role2]):
            assert member.get_top_role() is role1

    def test_get_top_role_when_roles_is_empty(self, member: guilds.Member):
        with mock.patch.object(guilds.Member, "get_roles", return_value=[]):
            assert member.get_top_role() is None

    def test_get_presence(self, member: guilds.Member):
        with (
            mock.patch.object(member.user.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_presence") as patched_get_presence,
        ):
            assert member.get_presence() is patched_get_presence.return_value
            patched_get_presence.assert_called_once_with(456, 123)

    def test_get_presence_when_no_cache_trait(self, member: guilds.Member):
        with mock.patch.object(member.user, "app", mock.Mock(traits.RESTAware)):
            assert member.get_presence() is None


class TestPartialGuild:
    @pytest.fixture
    def partial_guild(self, mock_app: traits.RESTAware) -> guilds.PartialGuild:
        return guilds.PartialGuild(app=mock_app, id=snowflakes.Snowflake(90210), icon_hash="yeet", name="hikari")

    def test_str_operator(self, partial_guild: guilds.PartialGuild):
        assert str(partial_guild) == "hikari"

    def test_shard_id_property(self, partial_guild: guilds.PartialGuild):
        with mock.patch.object(partial_guild.app, "shard_count", 4):
            assert partial_guild.shard_id == 0

    def test_shard_id_when_not_shard_aware(self, partial_guild: guilds.PartialGuild):
        partial_guild.app = mock.Mock(traits.RESTAware)

        assert partial_guild.shard_id is None

    def test_icon_url(self, partial_guild: guilds.PartialGuild):
        icon = mock.Mock()

        with mock.patch.object(guilds.PartialGuild, "make_icon_url", return_value=icon):
            assert partial_guild.icon_url is icon

    def test_make_icon_url_when_no_hash(self, partial_guild: guilds.PartialGuild):
        partial_guild.icon_hash = None

        assert partial_guild.make_icon_url(ext="png", size=2048) is None

    def test_make_icon_url_when_format_is_None_and_avatar_hash_is_for_gif(self, partial_guild: guilds.PartialGuild):
        partial_guild.icon_hash = "a_yeet"

        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert partial_guild.make_icon_url(ext=None, size=1024) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=90210, hash="a_yeet", size=1024, file_format="gif"
        )

    def test_make_icon_url_when_format_is_None_and_avatar_hash_is_not_for_gif(self, partial_guild: guilds.PartialGuild):
        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert partial_guild.make_icon_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=90210, hash="yeet", size=4096, file_format="png"
        )

    def test_make_icon_url_with_all_args(self, partial_guild: guilds.PartialGuild):
        with mock.patch.object(
            routes, "CDN_GUILD_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert partial_guild.make_icon_url(ext="url", size=2048) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=90210, hash="yeet", size=2048, file_format="url"
        )

    @pytest.mark.asyncio
    async def test_kick(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.kick_user = mock.AsyncMock()
        await partial_guild.kick(4321, reason="Go away!")

        partial_guild.app.rest.kick_user.assert_awaited_once_with(90210, 4321, reason="Go away!")

    @pytest.mark.asyncio
    async def test_ban(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.ban_user = mock.AsyncMock()

        await partial_guild.ban(4321, delete_message_seconds=864000, reason="Go away!")

        partial_guild.app.rest.ban_user.assert_awaited_once_with(
            90210, 4321, delete_message_seconds=864000, reason="Go away!"
        )

    @pytest.mark.asyncio
    async def test_unban(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.unban_user = mock.AsyncMock()
        await partial_guild.unban(4321, reason="Comeback!!")

        partial_guild.app.rest.unban_user.assert_awaited_once_with(90210, 4321, reason="Comeback!!")

    @pytest.mark.asyncio
    async def test_edit(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.edit_guild = mock.AsyncMock()
        edited_guild = await partial_guild.edit(
            name="chad server",
            verification_level=guilds.GuildVerificationLevel.LOW,
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ALL_MESSAGES,
            explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.DISABLED,
            owner=6996,
            afk_timeout=400,
            preferred_locale="us-en",
            features=[guilds.GuildFeature.COMMUNITY, guilds.GuildFeature.RAID_ALERTS_DISABLED],
            reason="beep boop",
        )

        partial_guild.app.rest.edit_guild.assert_awaited_once_with(
            90210,
            name="chad server",
            verification_level=guilds.GuildVerificationLevel.LOW,
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ALL_MESSAGES,
            explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.DISABLED,
            afk_channel=undefined.UNDEFINED,
            afk_timeout=400,
            icon=undefined.UNDEFINED,
            owner=6996,
            splash=undefined.UNDEFINED,
            banner=undefined.UNDEFINED,
            system_channel=undefined.UNDEFINED,
            rules_channel=undefined.UNDEFINED,
            public_updates_channel=undefined.UNDEFINED,
            preferred_locale="us-en",
            features=[guilds.GuildFeature.COMMUNITY, guilds.GuildFeature.RAID_ALERTS_DISABLED],
            reason="beep boop",
        )

        assert edited_guild is partial_guild.app.rest.edit_guild.return_value

    @pytest.mark.asyncio
    async def test_fetch_emojis(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.fetch_guild_emojis = mock.AsyncMock()

        emojis = await partial_guild.fetch_emojis()

        partial_guild.app.rest.fetch_guild_emojis.assert_awaited_once_with(partial_guild.id)
        assert emojis is partial_guild.app.rest.fetch_guild_emojis.return_value

    @pytest.mark.asyncio
    async def test_fetch_emoji(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.fetch_emoji = mock.AsyncMock()

        emoji = await partial_guild.fetch_emoji(349)

        partial_guild.app.rest.fetch_emoji.assert_awaited_once_with(partial_guild.id, 349)
        assert emoji is partial_guild.app.rest.fetch_emoji.return_value

    @pytest.mark.asyncio
    async def test_fetch_stickers(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.fetch_guild_stickers = mock.AsyncMock()

        stickers = await partial_guild.fetch_stickers()

        partial_guild.app.rest.fetch_guild_stickers.assert_awaited_once_with(partial_guild.id)
        assert stickers is partial_guild.app.rest.fetch_guild_stickers.return_value

    @pytest.mark.asyncio
    async def test_fetch_sticker(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.fetch_guild_sticker = mock.AsyncMock()

        sticker = await partial_guild.fetch_sticker(6969)

        partial_guild.app.rest.fetch_guild_sticker.assert_awaited_once_with(partial_guild.id, 6969)
        assert sticker is partial_guild.app.rest.fetch_guild_sticker.return_value

    @pytest.mark.asyncio
    async def test_create_sticker(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_sticker = mock.AsyncMock()
        file = mock.Mock()

        sticker = await partial_guild.create_sticker(
            "NewSticker", "funny", file, description="A sticker", reason="blah blah blah"
        )
        assert sticker is partial_guild.app.rest.create_sticker.return_value

        partial_guild.app.rest.create_sticker.assert_awaited_once_with(
            90210, "NewSticker", "funny", file, description="A sticker", reason="blah blah blah"
        )

    @pytest.mark.asyncio
    async def test_edit_sticker(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.edit_sticker = mock.AsyncMock()

        sticker = await partial_guild.edit_sticker(4567, name="Brilliant", tag="parmesan", description="amazing")

        partial_guild.app.rest.edit_sticker.assert_awaited_once_with(
            90210, 4567, name="Brilliant", tag="parmesan", description="amazing", reason=undefined.UNDEFINED
        )

        assert sticker is partial_guild.app.rest.edit_sticker.return_value

    @pytest.mark.asyncio
    async def test_delete_sticker(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.delete_sticker = mock.AsyncMock()

        sticker = await partial_guild.delete_sticker(951)

        partial_guild.app.rest.delete_sticker.assert_awaited_once_with(90210, 951, reason=undefined.UNDEFINED)

        assert sticker is partial_guild.app.rest.delete_sticker.return_value

    @pytest.mark.asyncio
    async def test_create_category(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_guild_category = mock.AsyncMock()

        category = await partial_guild.create_category("very cool category", position=2)

        partial_guild.app.rest.create_guild_category.assert_awaited_once_with(
            90210,
            "very cool category",
            position=2,
            permission_overwrites=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert category is partial_guild.app.rest.create_guild_category.return_value

    @pytest.mark.asyncio
    async def test_create_text_channel(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_guild_text_channel = mock.AsyncMock()

        text_channel = await partial_guild.create_text_channel(
            "cool text channel", position=3, nsfw=False, rate_limit_per_user=30
        )

        partial_guild.app.rest.create_guild_text_channel.assert_awaited_once_with(
            90210,
            "cool text channel",
            position=3,
            topic=undefined.UNDEFINED,
            nsfw=False,
            rate_limit_per_user=30,
            permission_overwrites=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert text_channel is partial_guild.app.rest.create_guild_text_channel.return_value

    @pytest.mark.asyncio
    async def test_create_news_channel(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_guild_news_channel = mock.AsyncMock()

        news_channel = await partial_guild.create_news_channel(
            "cool news channel", position=1, nsfw=False, rate_limit_per_user=420
        )

        partial_guild.app.rest.create_guild_news_channel.assert_awaited_once_with(
            90210,
            "cool news channel",
            position=1,
            topic=undefined.UNDEFINED,
            nsfw=False,
            rate_limit_per_user=420,
            permission_overwrites=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert news_channel is partial_guild.app.rest.create_guild_news_channel.return_value

    @pytest.mark.asyncio
    async def test_create_forum_channel(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_guild_forum_channel = mock.AsyncMock()

        forum_channel = await partial_guild.create_forum_channel(
            "cool forum channel", position=1, nsfw=False, rate_limit_per_user=420
        )

        partial_guild.app.rest.create_guild_forum_channel.assert_awaited_once_with(
            90210,
            "cool forum channel",
            position=1,
            topic=undefined.UNDEFINED,
            nsfw=False,
            rate_limit_per_user=420,
            permission_overwrites=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
            default_auto_archive_duration=undefined.UNDEFINED,
            default_thread_rate_limit_per_user=undefined.UNDEFINED,
            default_forum_layout=undefined.UNDEFINED,
            default_sort_order=undefined.UNDEFINED,
            available_tags=undefined.UNDEFINED,
            default_reaction_emoji=undefined.UNDEFINED,
        )

        assert forum_channel is partial_guild.app.rest.create_guild_forum_channel.return_value

    @pytest.mark.asyncio
    async def test_create_voice_channel(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_guild_voice_channel = mock.AsyncMock()

        voice_channel = await partial_guild.create_voice_channel(
            "cool voice channel", position=1, bitrate=3200, video_quality_mode=2
        )

        partial_guild.app.rest.create_guild_voice_channel.assert_awaited_once_with(
            90210,
            "cool voice channel",
            position=1,
            user_limit=undefined.UNDEFINED,
            bitrate=3200,
            video_quality_mode=2,
            permission_overwrites=undefined.UNDEFINED,
            region=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert voice_channel is partial_guild.app.rest.create_guild_voice_channel.return_value

    @pytest.mark.asyncio
    async def test_create_stage_channel(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.create_guild_stage_channel = mock.AsyncMock()

        stage_channel = await partial_guild.create_stage_channel(
            "cool stage channel", position=1, bitrate=3200, user_limit=100
        )

        partial_guild.app.rest.create_guild_stage_channel.assert_awaited_once_with(
            90210,
            "cool stage channel",
            position=1,
            user_limit=100,
            bitrate=3200,
            permission_overwrites=undefined.UNDEFINED,
            region=undefined.UNDEFINED,
            category=undefined.UNDEFINED,
            reason=undefined.UNDEFINED,
        )

        assert stage_channel is partial_guild.app.rest.create_guild_stage_channel.return_value

    @pytest.mark.asyncio
    async def test_delete_channel(self, partial_guild: guilds.PartialGuild):
        mock_channel = mock.Mock(channels_.GuildChannel)
        partial_guild.app.rest.delete_channel = mock.AsyncMock(return_value=mock_channel)

        deleted_channel = await partial_guild.delete_channel(1288820)

        partial_guild.app.rest.delete_channel.assert_awaited_once_with(1288820)
        assert deleted_channel is partial_guild.app.rest.delete_channel.return_value

    @pytest.mark.asyncio
    async def test_fetch_guild(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.fetch_guild = mock.AsyncMock(return_value=partial_guild)

        assert await partial_guild.fetch_self() is partial_guild.app.rest.fetch_guild.return_value
        partial_guild.app.rest.fetch_guild.assert_awaited_once_with(partial_guild.id)

    @pytest.mark.asyncio
    async def test_fetch_roles(self, partial_guild: guilds.PartialGuild):
        partial_guild.app.rest.fetch_roles = mock.AsyncMock()

        roles = await partial_guild.fetch_roles()

        partial_guild.app.rest.fetch_roles.assert_awaited_once_with(90210)
        assert roles is partial_guild.app.rest.fetch_roles.return_value


class TestGuildPreview:
    @pytest.fixture
    def model(self, mock_app: traits.RESTAware) -> guilds.GuildPreview:
        return guilds.GuildPreview(
            app=mock_app,
            features=["huge super secret nsfw channel"],
            id=snowflakes.Snowflake(123),
            icon_hash="dis is mah icon hash",
            name="DAPI",
            splash_hash="dis is also mah splash hash",
            discovery_splash_hash=None,
            emojis={},
            approximate_active_member_count=12,
            approximate_member_count=999_283_252_124_633,
            description="the place for quality shitposting!",
        )

    def test_splash_url(self, model: guilds.GuildPreview):
        splash = mock.Mock()

        with mock.patch.object(guilds.GuildPreview, "make_splash_url", return_value=splash):
            assert model.splash_url is splash

    def test_make_splash_url_when_hash(self, model: guilds.GuildPreview):
        model.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_splash_url(ext="url", size=1024) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123, hash="18dnf8dfbakfdh", size=1024, file_format="url"
        )

    def test_make_splash_url_when_no_hash(self, model: guilds.GuildPreview):
        model.splash_hash = None
        assert model.make_splash_url(ext="png", size=512) is None

    def test_discovery_splash_url(self, model: guilds.GuildPreview):
        discovery_splash = mock.Mock()

        with mock.patch.object(guilds.GuildPreview, "make_discovery_splash_url", return_value=discovery_splash):
            assert model.discovery_splash_url is discovery_splash

    def test_make_discovery_splash_url_when_hash(self, model: guilds.GuildPreview):
        model.discovery_splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_DISCOVERY_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_discovery_splash_url(ext="url", size=2048) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123, hash="18dnf8dfbakfdh", size=2048, file_format="url"
        )

    def test_make_discovery_splash_url_when_no_hash(self, model: guilds.GuildPreview):
        model.discovery_splash_hash = None
        assert model.make_discovery_splash_url(ext="png", size=4096) is None


class TestGuild:
    @pytest.fixture
    def guild(self, mock_app: traits.RESTAware) -> guilds.Guild:
        return hikari_test_helpers.mock_class_namespace(guilds.Guild)(
            app=mock_app,
            id=snowflakes.Snowflake(123),
            splash_hash="splash_hash",
            discovery_splash_hash="discovery_splash_hash",
            banner_hash="banner_hash",
            icon_hash="icon_hash",
            features=[guilds.GuildFeature.ANIMATED_ICON],
            name="some guild",
            application_id=snowflakes.Snowflake(9876),
            afk_channel_id=snowflakes.Snowflake(1234),
            afk_timeout=datetime.timedelta(seconds=60),
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
            description=None,
            explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
            is_widget_enabled=False,
            max_video_channel_users=10,
            mfa_level=guilds.GuildMFALevel.NONE,
            nsfw_level=guilds.GuildNSFWLevel.AGE_RESTRICTED,
            owner_id=snowflakes.Snowflake(1111),
            preferred_locale="en-GB",
            premium_subscription_count=12,
            premium_tier=guilds.GuildPremiumTier.TIER_3,
            public_updates_channel_id=snowflakes.Snowflake(99699),
            rules_channel_id=snowflakes.Snowflake(123445),
            system_channel_id=snowflakes.Snowflake(123888),
            vanity_url_code="yeet",
            verification_level=guilds.GuildVerificationLevel.VERY_HIGH,
            widget_channel_id=snowflakes.Snowflake(192729),
            system_channel_flags=guilds.GuildSystemChannelFlag.SUPPRESS_PREMIUM_SUBSCRIPTION,
        )

    def test_get_channels(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channels_view_for_guild"
            ) as patched_get_guild_channels_view_for_guild,
        ):
            assert guild.get_channels() is patched_get_guild_channels_view_for_guild.return_value
            patched_get_guild_channels_view_for_guild.assert_called_once_with(123)

    def test_get_channels_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_channels() == {}

    def test_get_members(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_members_view_for_guild") as patched_get_members_view_for_guild,
        ):
            assert guild.get_members() is patched_get_members_view_for_guild.return_value
            patched_get_members_view_for_guild.assert_called_once_with(123)

    def test_get_members_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_members() == {}

    def test_get_presences(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_presences_view_for_guild") as patched_get_presences_view_for_guild,
        ):
            assert guild.get_presences() is patched_get_presences_view_for_guild.return_value
            patched_get_presences_view_for_guild.assert_called_once_with(123)

    def test_get_presences_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_presences() == {}

    def test_get_voice_states(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_voice_states_view_for_guild"
            ) as patched_get_voice_states_view_for_guild,
        ):
            assert guild.get_voice_states() is patched_get_voice_states_view_for_guild.return_value
            patched_get_voice_states_view_for_guild.assert_called_once_with(123)

    def test_get_voice_states_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_voice_states() == {}

    def test_get_emojis(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_emojis_view_for_guild") as patched_get_emojis_view_for_guild,
        ):
            assert guild.get_emojis() is patched_get_emojis_view_for_guild.return_value
            patched_get_emojis_view_for_guild.assert_called_once_with(123)

    def test_emojis_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_emojis() == {}

    def test_get_sticker(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_sticker", mock.Mock(return_value=mock.Mock(guild_id=guild.id))
            ) as patched_get_sticker,
        ):
            assert guild.get_sticker(456) is patched_get_sticker.return_value
            patched_get_sticker.assert_called_once_with(456)

    def test_get_sticker_when_not_from_guild(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_sticker", mock.Mock(return_value=mock.Mock(guild_id=546123123433))
            ) as patched_get_sticker,
        ):
            assert guild.get_sticker(456) is None

            patched_get_sticker.assert_called_once_with(456)

    def test_get_sticker_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock()
        assert guild.get_sticker(1234) is None

    def test_get_stickers(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_stickers_view_for_guild") as patched_get_stickers_view_for_guild,
        ):
            assert guild.get_stickers() is patched_get_stickers_view_for_guild.return_value
            patched_get_stickers_view_for_guild.assert_called_once_with(123)

    def test_get_stickers_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_stickers() == {}

    def test_roles(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_roles_view_for_guild") as patched_get_roles_view_for_guild,
        ):
            assert guild.get_roles() is patched_get_roles_view_for_guild.return_value
            patched_get_roles_view_for_guild.assert_called_once_with(123)

    def test_get_roles_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_roles() == {}

    def test_get_emoji(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_emoji", mock.Mock(return_value=mock.Mock(guild_id=guild.id))
            ) as patched_get_emoji,
        ):
            assert guild.get_emoji(456) is patched_get_emoji.return_value
            patched_get_emoji.assert_called_once_with(456)

    def test_get_emoji_when_not_from_guild(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_emoji", mock.Mock(return_value=mock.Mock(guild_id=1233212))
            ) as patched_get_emoji,
        ):
            assert guild.get_emoji(456) is None

            patched_get_emoji.assert_called_once_with(456)

    def test_get_emoji_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock()
        assert guild.get_emoji(456) is None

    def test_get_role(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_role", mock.Mock(return_value=mock.Mock(guild_id=guild.id))
            ) as patched_get_role,
        ):
            assert guild.get_role(456) is patched_get_role.return_value
            patched_get_role.assert_called_once_with(456)

    def test_get_role_when_not_from_guild(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_role", mock.Mock(return_value=mock.Mock(guild_id=7623123321123))
            ) as patched_get_role,
        ):
            assert guild.get_role(456) is None
            patched_get_role.assert_called_once_with(456)

    def test_get_role_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock()
        assert guild.get_role(456) is None

    def test_splash_url(self, guild: guilds.Guild):
        splash = mock.Mock()

        with mock.patch.object(guilds.Guild, "make_splash_url", return_value=splash):
            assert guild.splash_url is splash

    def test_make_splash_url_when_hash(self, guild: guilds.Guild):
        guild.splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert guild.make_splash_url(ext="url", size=2) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123, hash="18dnf8dfbakfdh", size=2, file_format="url"
        )

    def test_make_splash_url_when_no_hash(self, guild: guilds.Guild):
        guild.splash_hash = None
        assert guild.make_splash_url(ext="png", size=1024) is None

    def test_discovery_splash_url(self, guild: guilds.Guild):
        discovery_splash = mock.Mock()

        with mock.patch.object(guilds.Guild, "make_discovery_splash_url", return_value=discovery_splash):
            assert guild.discovery_splash_url is discovery_splash

    def test_make_discovery_splash_url_when_hash(self, guild: guilds.Guild):
        guild.discovery_splash_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_DISCOVERY_SPLASH", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert guild.make_discovery_splash_url(ext="url", size=1024) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123, hash="18dnf8dfbakfdh", size=1024, file_format="url"
        )

    def test_make_discovery_splash_url_when_no_hash(self, guild: guilds.Guild):
        guild.discovery_splash_hash = None
        assert guild.make_discovery_splash_url(ext="png", size=2048) is None

    def test_banner_url(self, guild: guilds.Guild):
        banner = mock.Mock()

        with mock.patch.object(guilds.Guild, "make_banner_url", return_value=banner):
            assert guild.banner_url is banner

    def test_make_banner_url_when_hash(self, guild: guilds.Guild):
        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert guild.make_banner_url(ext="url", size=512) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=123, hash="banner_hash", size=512, file_format="url"
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_for_gif(self, guild: guilds.Guild):
        guild.banner_hash = "a_18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert guild.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=guild.id, hash="a_18dnf8dfbakfdh", size=4096, file_format="gif"
        )

    def test_make_banner_url_when_format_is_None_and_banner_hash_is_not_for_gif(self, guild: guilds.Guild):
        guild.banner_hash = "18dnf8dfbakfdh"

        with mock.patch.object(
            routes, "CDN_GUILD_BANNER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert guild.make_banner_url(ext=None, size=4096) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, guild_id=guild.id, hash=guild.banner_hash, size=4096, file_format="png"
        )

    def test_make_banner_url_when_no_hash(self, guild: guilds.Guild):
        guild.banner_hash = None
        assert guild.make_banner_url(ext="png", size=2048) is None

    @pytest.mark.asyncio
    async def test_fetch_owner(self, guild: guilds.Guild):
        guild.app.rest.fetch_member = mock.AsyncMock()

        assert await guild.fetch_owner() is guild.app.rest.fetch_member.return_value
        guild.app.rest.fetch_member.assert_awaited_once_with(123, 1111)

    @pytest.mark.asyncio
    async def test_fetch_widget_channel(self, guild: guilds.Guild):
        mock_channel = mock.Mock(channels_.GuildChannel)
        guild.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)

        assert await guild.fetch_widget_channel() is guild.app.rest.fetch_channel.return_value
        guild.app.rest.fetch_channel.assert_awaited_once_with(192729)

    @pytest.mark.asyncio
    async def test_fetch_widget_channel_when_None(self, guild: guilds.Guild):
        guild.widget_channel_id = None

        assert await guild.fetch_widget_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_rules_channel(self, guild: guilds.Guild):
        mock_channel = mock.Mock(channels_.GuildTextChannel)
        guild.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)

        assert await guild.fetch_rules_channel() is guild.app.rest.fetch_channel.return_value
        guild.app.rest.fetch_channel.assert_awaited_once_with(123445)

    @pytest.mark.asyncio
    async def test_fetch_rules_channel_when_None(self, guild: guilds.Guild):
        guild.rules_channel_id = None

        assert await guild.fetch_rules_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_system_channel(self, guild: guilds.Guild):
        mock_channel = mock.Mock(channels_.GuildTextChannel)
        guild.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)

        assert await guild.fetch_system_channel() is guild.app.rest.fetch_channel.return_value
        guild.app.rest.fetch_channel.assert_awaited_once_with(123888)

    @pytest.mark.asyncio
    async def test_fetch_system_channel_when_None(self, guild: guilds.Guild):
        guild.system_channel_id = None

        assert await guild.fetch_system_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_public_updates_channel(self, guild: guilds.Guild):
        mock_channel = mock.Mock(channels_.GuildTextChannel)
        guild.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)

        assert await guild.fetch_public_updates_channel() is guild.app.rest.fetch_channel.return_value
        guild.app.rest.fetch_channel.assert_awaited_once_with(99699)

    @pytest.mark.asyncio
    async def test_fetch_public_updates_channel_when_None(self, guild: guilds.Guild):
        guild.public_updates_channel_id = None

        assert await guild.fetch_public_updates_channel() is None

    @pytest.mark.asyncio
    async def test_fetch_afk_channel(self, guild: guilds.Guild):
        mock_channel = mock.Mock(channels_.GuildVoiceChannel)
        guild.app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)

        assert await guild.fetch_afk_channel() is guild.app.rest.fetch_channel.return_value
        guild.app.rest.fetch_channel.assert_awaited_once_with(1234)

    @pytest.mark.asyncio
    async def test_fetch_afk_channel_when_None(self, guild: guilds.Guild):
        guild.afk_channel_id = None

        assert await guild.fetch_afk_channel() is None

    def test_get_channel(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", mock.Mock(return_value=mock.Mock(guild_id=guild.id))
            ) as patched_get_guild_channel,
        ):
            assert guild.get_channel(456) is patched_get_guild_channel.return_value
            patched_get_guild_channel.assert_called_once_with(456)

    def test_get_channel_when_not_from_guild(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(
                patched_cache, "get_guild_channel", mock.Mock(return_value=mock.Mock(guild_id=654523123))
            ) as patched_get_guild_channel,
        ):
            assert guild.get_channel(456) is None
            patched_get_guild_channel.assert_called_once_with(456)

    def test_get_channel_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock()
        assert guild.get_channel(456) is None

    def test_get_member(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_member") as patched_get_member,
        ):
            assert guild.get_member(456) is patched_get_member.return_value
            patched_get_member.assert_called_once_with(123, 456)

    def test_get_member_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_member(456) is None

    def test_get_presence(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_presence") as patched_get_presence,
        ):
            assert guild.get_presence(456) is patched_get_presence.return_value
            patched_get_presence.assert_called_once_with(123, 456)

    def test_get_presence_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_presence(456) is None

    def test_get_voice_state(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_voice_state") as patched_get_voice_state,
        ):
            assert guild.get_voice_state(456) is patched_get_voice_state.return_value
            patched_get_voice_state.assert_called_once_with(123, 456)

    def test_get_voice_state_when_no_cache_trait(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_voice_state(456) is None

    def test_get_my_member_when_not_shardaware(self, guild: guilds.Guild):
        guild.app = mock.Mock(traits.RESTAware)
        assert guild.get_my_member() is None

    def test_get_my_member_when_no_me(self, guild: guilds.Guild):
        with mock.patch.object(guild.app, "get_me", mock.Mock(return_value=None)) as patched_get_me:
            assert guild.get_my_member() is None
            patched_get_me.assert_called_once_with()

    def test_get_my_member(self, guild: guilds.Guild):
        with (
            mock.patch.object(guild.app, "get_me", mock.Mock(return_value=mock.Mock(id=123))) as patched_get_me,
            mock.patch.object(guilds.Guild, "get_member") as patched_get_member,
        ):
            assert guild.get_my_member() is patched_get_member.return_value

        patched_get_member.assert_called_once_with(123)
        patched_get_me.assert_called_once_with()


class TestRestGuild:
    @pytest.fixture
    def rest_guild(self, mock_app: traits.RESTAware) -> guilds.RESTGuild:
        return guilds.RESTGuild(
            app=mock_app,
            id=snowflakes.Snowflake(123),
            splash_hash="splash_hash",
            discovery_splash_hash="discovery_splash_hash",
            banner_hash="banner_hash",
            icon_hash="icon_hash",
            features=[guilds.GuildFeature.ANIMATED_ICON],
            name="some guild",
            application_id=snowflakes.Snowflake(9876),
            afk_channel_id=snowflakes.Snowflake(1234),
            afk_timeout=datetime.timedelta(seconds=60),
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
            description=None,
            explicit_content_filter=guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS,
            is_widget_enabled=False,
            max_video_channel_users=10,
            mfa_level=guilds.GuildMFALevel.NONE,
            owner_id=snowflakes.Snowflake(1111),
            preferred_locale="en-GB",
            premium_subscription_count=12,
            premium_tier=guilds.GuildPremiumTier.TIER_3,
            public_updates_channel_id=None,
            rules_channel_id=None,
            system_channel_id=None,
            vanity_url_code="yeet",
            verification_level=guilds.GuildVerificationLevel.VERY_HIGH,
            widget_channel_id=None,
            system_channel_flags=guilds.GuildSystemChannelFlag.SUPPRESS_PREMIUM_SUBSCRIPTION,
            emojis={},
            stickers={},
            roles={},
            approximate_active_member_count=1000,
            approximate_member_count=100,
            max_presences=100,
            max_members=100,
            nsfw_level=guilds.GuildNSFWLevel.AGE_RESTRICTED,
        )

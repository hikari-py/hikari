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
import datetime

import mock
import pytest

from hikari import applications as application_models
from hikari import audit_logs as audit_log_models
from hikari import channels as channel_models
from hikari import colors as color_models
from hikari import commands
from hikari import embeds as embed_models
from hikari import emojis as emoji_models
from hikari import errors
from hikari import files
from hikari import guilds as guild_models
from hikari import invites as invite_models
from hikari import messages as message_models
from hikari import permissions as permission_models
from hikari import presences as presence_models
from hikari import sessions as gateway_models
from hikari import snowflakes
from hikari import stickers as sticker_models
from hikari import traits
from hikari import undefined
from hikari import users as user_models
from hikari import voices as voice_models
from hikari import webhooks as webhook_models
from hikari.impl import entity_factory
from hikari.interactions import base_interactions
from hikari.interactions import command_interactions


def test__with_int_cast():
    cast = mock.Mock()

    assert entity_factory._with_int_cast(cast)("42") is cast.return_value
    cast.assert_called_once_with(42)


def test__deserialize_seconds_timedelta():
    assert entity_factory._deserialize_seconds_timedelta(30) == datetime.timedelta(seconds=30)


def test__deserialize_day_timedelta():
    assert entity_factory._deserialize_day_timedelta("4") == datetime.timedelta(days=4)


def test__deserialize_max_uses_returns_int():
    assert entity_factory._deserialize_max_uses(120) == 120


def test__deserialize_max_uses_returns_none_when_zero():
    # Yes, I changed this from float("inf") so that it returns None. I did this
    # to provide some level of consistency with `max_age`. We need to revisit
    # this if possible.
    assert entity_factory._deserialize_max_uses(0) is None


def test__deserialize_max_age_returns_timedelta():
    assert entity_factory._deserialize_max_age(120) == datetime.timedelta(seconds=120)


def test__deserialize_max_age_returns_null():
    assert entity_factory._deserialize_max_age(0) is None


class TestEntityFactoryImpl:
    @pytest.fixture()
    def mock_app(self) -> traits.RESTAware:
        return mock.MagicMock(traits.RESTAware)

    @pytest.fixture()
    def entity_factory_impl(self, mock_app) -> entity_factory.EntityFactoryImpl:
        return entity_factory.EntityFactoryImpl(app=mock_app)

    def test_app(self, entity_factory_impl, mock_app):
        assert entity_factory_impl._app is mock_app

    ######################
    # APPLICATION MODELS #
    ######################

    @pytest.fixture()
    def partial_integration(self):
        return {
            "id": "123123123123123",
            "name": "A Name",
            "type": "twitch",
            "account": {"name": "twitchUsername", "id": "123123"},
        }

    @pytest.fixture()
    def own_connection_payload(self, partial_integration):
        return {
            "friend_sync": False,
            "id": "2513849648abc",
            "integrations": [partial_integration],
            "name": "FS",
            "revoked": False,
            "show_activity": True,
            "type": "twitter",
            "verified": True,
            "visibility": 0,
        }

    def test_deserialize_own_connection(self, entity_factory_impl, own_connection_payload, partial_integration):
        own_connection = entity_factory_impl.deserialize_own_connection(own_connection_payload)
        assert own_connection.id == "2513849648abc"
        assert own_connection.name == "FS"
        assert own_connection.type == "twitter"
        assert own_connection.is_revoked is False
        assert own_connection.integrations == [entity_factory_impl.deserialize_partial_integration(partial_integration)]
        assert own_connection.is_verified is True
        assert own_connection.is_friend_sync_enabled is False
        assert own_connection.is_activity_visible is True
        assert own_connection.visibility == application_models.ConnectionVisibility.NONE
        assert isinstance(own_connection, application_models.OwnConnection)

    def test_deserialize_own_connection_when_integrations_is_None(self, entity_factory_impl, own_connection_payload):
        del own_connection_payload["integrations"]
        own_connection = entity_factory_impl.deserialize_own_connection(own_connection_payload)
        assert own_connection.id == "2513849648abc"
        assert own_connection.name == "FS"
        assert own_connection.type == "twitter"
        assert own_connection.is_revoked is False
        assert own_connection.integrations == []
        assert own_connection.is_verified is True
        assert own_connection.is_friend_sync_enabled is False
        assert own_connection.is_activity_visible is True
        assert own_connection.visibility == application_models.ConnectionVisibility.NONE
        assert isinstance(own_connection, application_models.OwnConnection)

    @pytest.fixture()
    def own_guild_payload(self):
        return {
            "id": "152559372126519269",
            "name": "Isopropyl",
            "icon": "d4a983885dsaa7691ce8bcaaf945a",
            "owner": False,
            "permissions": "2147483647",
            "features": ["DISCOVERABLE", "FORCE_RELAY"],
        }

    def test_deserialize_own_guild(self, entity_factory_impl, mock_app, own_guild_payload):
        own_guild = entity_factory_impl.deserialize_own_guild(own_guild_payload)
        assert own_guild.id == 152559372126519269
        assert own_guild.name == "Isopropyl"
        assert own_guild.icon_hash == "d4a983885dsaa7691ce8bcaaf945a"
        assert own_guild.features == [guild_models.GuildFeature.DISCOVERABLE, "FORCE_RELAY"]
        assert own_guild.is_owner is False
        assert own_guild.my_permissions == permission_models.Permissions(2147483647)

    def test_deserialize_own_guild_with_null_and_unset_fields(self, entity_factory_impl):
        own_guild = entity_factory_impl.deserialize_own_guild(
            {
                "id": "152559372126519269",
                "name": "Isopropyl",
                "icon": None,
                "owner": False,
                "permissions": "2147483647",
                "features": ["DISCOVERABLE", "FORCE_RELAY"],
            }
        )
        assert own_guild.icon_hash is None

    @pytest.fixture()
    def owner_payload(self, user_payload):
        return {**user_payload, "flags": 1 << 10}

    @pytest.fixture()
    def application_payload(self, owner_payload, user_payload):
        return {
            "id": "209333111222",
            "name": "Dream Sweet in Sea Major",
            "icon": "iwiwiwiwiw",
            "description": "I am an application",
            "rpc_origins": ["127.0.0.0"],
            "bot_public": True,
            "bot_require_code_grant": False,
            "owner": owner_payload,
            "summary": "not a blank string",
            "verify_key": "698c5d0859abb686be1f8a19e0e7634d8471e33817650f9fb29076de227bca90",
            "team": {
                "icon": "hashtag",
                "id": "202020202",
                "name": "Hikari Development",
                "members": [
                    {"membership_state": 1, "permissions": ["*"], "team_id": "209333111222", "user": user_payload}
                ],
                "owner_user_id": "393030292",
            },
            "guild_id": "2020293939",
            "primary_sku_id": "2020202002",
            "slug": "192.168.1.254",
            "cover_image": "hashmebaby",
            "privacy_policy_url": "hahaha://hahaha",
            "terms_of_service_url": "haha2:2h2h2h2",
        }

    def test_deserialize_application(
        self, entity_factory_impl, mock_app, application_payload, owner_payload, user_payload
    ):
        application = entity_factory_impl.deserialize_application(application_payload)

        assert application.app is mock_app
        assert application.id == 209333111222
        assert application.name == "Dream Sweet in Sea Major"
        assert application.description == "I am an application"
        assert application.is_bot_public is True
        assert application.is_bot_code_grant_required is False
        assert application.owner == entity_factory_impl.deserialize_user(owner_payload)
        assert application.rpc_origins == ["127.0.0.0"]
        assert application.summary == "not a blank string"
        assert (
            application.public_key
            == b'i\x8c]\x08Y\xab\xb6\x86\xbe\x1f\x8a\x19\xe0\xe7cM\x84q\xe38\x17e\x0f\x9f\xb2\x90v\xde"{\xca\x90'
        )
        assert application.privacy_policy_url == "hahaha://hahaha"
        assert application.terms_of_service_url == "haha2:2h2h2h2"
        assert application.icon_hash == "iwiwiwiwiw"
        # Team
        assert application.team.id == 202020202
        assert application.team.name == "Hikari Development"
        assert application.team.icon_hash == "hashtag"
        assert application.team.owner_id == 393030292
        assert isinstance(application.team, application_models.Team)
        # TeamMember
        assert len(application.team.members) == 1
        member = application.team.members[115590097100865541]
        assert member.membership_state == application_models.TeamMembershipState.INVITED
        assert member.permissions == ["*"]
        assert member.team_id == 209333111222
        assert member.user == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(member, application_models.TeamMember)

        assert application.guild_id == 2020293939
        assert application.primary_sku_id == 2020202002
        assert application.slug == "192.168.1.254"
        assert application.cover_image_hash == "hashmebaby"
        assert isinstance(application, application_models.Application)

    def test_deserialize_application_with_unset_fields(self, entity_factory_impl, mock_app, owner_payload):
        application = entity_factory_impl.deserialize_application(
            {
                "id": "209333111222",
                "name": "Dream Sweet in Sea Major",
                "description": "I am an application",
                "summary": "not a blank string",
                "bot_public": True,
                "bot_require_code_grant": False,
                "verify_key": "1232313223",
                "owner": owner_payload,
            }
        )

        assert application.rpc_origins is None
        assert application.team is None
        assert application.guild_id is None
        assert application.primary_sku_id is None
        assert application.slug is None
        assert application.icon_hash is None
        assert application.cover_image_hash is None
        assert application.privacy_policy_url is None
        assert application.terms_of_service_url is None

    def test_deserialize_application_with_null_fields(self, entity_factory_impl, mock_app, owner_payload):
        application = entity_factory_impl.deserialize_application(
            {
                "id": "209333111222",
                "name": "Dream Sweet in Sea Major",
                "icon": None,
                "description": "",
                "summary": "",
                "team": None,
                "owner": owner_payload,
                "bot_public": True,
                "bot_require_code_grant": False,
                "verify_key": "1232313223",
            }
        )

        assert application.description is None
        assert application.summary is None
        assert application.icon_hash is None
        assert application.cover_image_hash is None
        assert application.team is None

    @pytest.fixture()
    def invite_application_payload(self):
        return {
            "id": "773336526917861400",
            "name": "Betrayal.io",
            "icon": "0227b2e89ea08d666c43003fbadbc72a",
            "description": "Play inside Discord with your friends!",
            "summary": "Play inside Discord with your friends! (but as a summary)",
            "cover_image": "0227b2e89ea08d666c43003fbadbc72a (but as cover)",
            "verify_key": "1bf78fdbfcbabe2e1256f9b133818976591203a22febabba5ff89f86f24760ff",
        }

    @pytest.fixture()
    def authorization_information_payload(self, user_payload):
        return {
            "application": {
                "id": "4123123123123",
                "name": "abotnotabot",
                "icon": "7c635c3cc8c7b109d254d8fcc1be85e6",
                "description": "2123",
                "summary": "dsasd",
                "hook": True,
                "bot_public": True,
                "bot_require_code_grant": False,
                "verify_key": "6f6b6f6b6f646f646f646f",
                "terms_of_service_url": "htttpyptptp",
                "privacy_policy_url": "hphphphphph",
            },
            "scopes": ["identify", "guilds", "applications.commands.update"],
            "expires": "2021-02-01T18:03:20.888000+00:00",
            "user": user_payload,
        }

    def test_deserialize_authorization_information(
        self, entity_factory_impl, authorization_information_payload, user_payload
    ):
        authorization_information = entity_factory_impl.deserialize_authorization_information(
            authorization_information_payload
        )
        # AuthorizationApplication
        application = authorization_information.application
        assert application.id == 4123123123123
        assert application.name == "abotnotabot"
        assert application.description == "2123"
        assert application.icon_hash == "7c635c3cc8c7b109d254d8fcc1be85e6"
        assert application.summary == "dsasd"
        assert application.public_key == b"okokodododo"
        assert application.is_bot_public is True
        assert application.is_bot_code_grant_required is False
        assert application.terms_of_service_url == "htttpyptptp"
        assert application.privacy_policy_url == "hphphphphph"
        assert isinstance(application, application_models.AuthorizationApplication)

        assert authorization_information.expires_at == datetime.datetime(
            2021, 2, 1, 18, 3, 20, 888000, tzinfo=datetime.timezone.utc
        )
        assert authorization_information.scopes == ["identify", "guilds", "applications.commands.update"]
        assert authorization_information.user == entity_factory_impl.deserialize_user(user_payload)

    def test_deserialize_authorization_information_with_unset_fields(
        self, entity_factory_impl, authorization_information_payload
    ):
        del authorization_information_payload["application"]["icon"]
        del authorization_information_payload["application"]["bot_public"]
        del authorization_information_payload["application"]["bot_require_code_grant"]
        del authorization_information_payload["application"]["terms_of_service_url"]
        del authorization_information_payload["application"]["privacy_policy_url"]
        del authorization_information_payload["user"]
        authorization_information = entity_factory_impl.deserialize_authorization_information(
            authorization_information_payload
        )

        assert authorization_information.user is None
        assert authorization_information.application.icon_hash is None
        assert authorization_information.application.is_bot_public is None
        assert authorization_information.application.is_bot_code_grant_required is None
        assert authorization_information.application.terms_of_service_url is None
        assert authorization_information.application.privacy_policy_url is None

    @pytest.fixture()
    def client_credentials_payload(self):
        return {
            "access_token": "6qrZcUqja7812RVdnEKjpzOL4CvHBFG",
            "token_type": "Bearer",
            "expires_in": 604800,
            "scope": "identify connections",
        }

    def test_deserialize_partial_token(self, entity_factory_impl, client_credentials_payload):
        partial_token = entity_factory_impl.deserialize_partial_token(client_credentials_payload)

        assert partial_token.access_token == "6qrZcUqja7812RVdnEKjpzOL4CvHBFG"
        assert partial_token.token_type is application_models.TokenType.BEARER
        assert partial_token.expires_in == datetime.timedelta(weeks=1)
        assert partial_token.scopes == [
            application_models.OAuth2Scope.IDENTIFY,
            application_models.OAuth2Scope.CONNECTIONS,
        ]
        assert isinstance(partial_token, application_models.PartialOAuth2Token)

    @pytest.fixture()
    def access_token_payload(self, deserialize_rest_guild_payload, incoming_webhook_payload):
        return {
            "token_type": "Bearer",
            "guild": deserialize_rest_guild_payload,
            "access_token": "zMndOe7jFLXGawdlxMOdNvXjjOce5X",
            "scope": "bot webhook.incoming",
            "expires_in": 2419200,
            "refresh_token": "mgp8qnvBwJcmadwgCYKyYD5CAzGAX4",
            "webhook": incoming_webhook_payload,
        }

    def test_deserialize_authorization_token(
        self, entity_factory_impl, access_token_payload, deserialize_rest_guild_payload, incoming_webhook_payload
    ):
        access_token = entity_factory_impl.deserialize_authorization_token(access_token_payload)

        assert access_token.token_type is application_models.TokenType.BEARER
        assert access_token.guild == entity_factory_impl.deserialize_rest_guild(deserialize_rest_guild_payload)
        assert access_token.access_token == "zMndOe7jFLXGawdlxMOdNvXjjOce5X"
        assert access_token.scopes == [
            application_models.OAuth2Scope.BOT,
            application_models.OAuth2Scope.WEBHOOK_INCOMING,
        ]
        assert access_token.expires_in == datetime.timedelta(weeks=4)
        assert access_token.refresh_token == "mgp8qnvBwJcmadwgCYKyYD5CAzGAX4"
        assert access_token.webhook == entity_factory_impl.deserialize_incoming_webhook(incoming_webhook_payload)

    def test_deserialize_authorization_token_without_optional_fields(self, entity_factory_impl, access_token_payload):
        del access_token_payload["guild"]
        del access_token_payload["webhook"]

        access_token = entity_factory_impl.deserialize_authorization_token(access_token_payload)

        assert access_token.guild is None
        assert access_token.webhook is None

    @pytest.fixture()
    def implicit_token_payload(self):
        return {
            "access_token": "RTfP0OK99U3kbRtHOoKLmJbOn45PjL",
            "token_type": "Basic",
            "expires_in": 1209600,
            "scope": "identify",
            "state": "15773059ghq9183habn",
        }

    def test_deserialize_implicit_token(self, entity_factory_impl, implicit_token_payload):
        implicit_token = entity_factory_impl.deserialize_implicit_token(implicit_token_payload)

        assert implicit_token.access_token == "RTfP0OK99U3kbRtHOoKLmJbOn45PjL"
        assert implicit_token.token_type is application_models.TokenType.BASIC
        assert implicit_token.expires_in == datetime.timedelta(weeks=2)
        assert implicit_token.scopes == [application_models.OAuth2Scope.IDENTIFY]
        assert implicit_token.state == "15773059ghq9183habn"
        assert isinstance(implicit_token, application_models.OAuth2ImplicitToken)

    def test_deserialize_implicit_token_without_state(self, entity_factory_impl, implicit_token_payload):
        del implicit_token_payload["state"]

        implicit_token = entity_factory_impl.deserialize_implicit_token(implicit_token_payload)

        assert implicit_token.state is None

    #####################
    # AUDIT LOGS MODELS #
    #####################

    def test__deserialize_audit_log_change_roles(self, entity_factory_impl):
        test_role_payloads = [
            {"id": "24", "name": "roleA"},
        ]
        roles = entity_factory_impl._deserialize_audit_log_change_roles(test_role_payloads)
        assert len(roles) == 1
        role = roles[24]
        assert role.id == 24
        assert role.name == "roleA"
        assert isinstance(role, guild_models.PartialRole)

    def test__deserialize_audit_log_overwrites(self, entity_factory_impl):
        test_overwrite_payloads = [
            {"id": "24", "type": 0, "allow": "21", "deny": "0"},
            {"id": "48", "type": 1, "deny": "42", "allow": "0"},
        ]
        overwrites = entity_factory_impl._deserialize_audit_log_overwrites(test_overwrite_payloads)
        assert overwrites == {
            24: entity_factory_impl.deserialize_permission_overwrite(
                {"id": "24", "type": 0, "allow": "21", "deny": "0"}
            ),
            48: entity_factory_impl.deserialize_permission_overwrite(
                {"id": "48", "type": 1, "deny": "42", "allow": "0"}
            ),
        }

    @pytest.fixture()
    def overwrite_info_payload(self):
        return {"id": "123123123", "type": 0, "role_name": "aRole"}

    def test__deserialize_channel_overwrite_entry_info(self, entity_factory_impl, overwrite_info_payload):
        overwrite_entry_info = entity_factory_impl._deserialize_channel_overwrite_entry_info(overwrite_info_payload)
        assert overwrite_entry_info.id == 123123123
        assert overwrite_entry_info.type is channel_models.PermissionOverwriteType.ROLE
        assert overwrite_entry_info.role_name == "aRole"
        assert isinstance(overwrite_entry_info, audit_log_models.ChannelOverwriteEntryInfo)

    @pytest.fixture()
    def message_pin_info_payload(self):
        return {
            "channel_id": "123123123",
            "message_id": "69696969",
        }

    def test__deserialize_message_pin_entry_info(self, entity_factory_impl, message_pin_info_payload):
        message_pin_info = entity_factory_impl._deserialize_message_pin_entry_info(message_pin_info_payload)
        assert message_pin_info.channel_id == 123123123
        assert message_pin_info.message_id == 69696969
        assert isinstance(message_pin_info, audit_log_models.MessagePinEntryInfo)

    @pytest.fixture()
    def member_prune_info_payload(self):
        return {
            "delete_member_days": "7",
            "members_removed": "1",
        }

    def test__deserialize_member_prune_entry_info(self, entity_factory_impl, member_prune_info_payload):
        member_prune_info = entity_factory_impl._deserialize_member_prune_entry_info(member_prune_info_payload)
        assert member_prune_info.delete_member_days == datetime.timedelta(days=7)
        assert member_prune_info.members_removed == 1
        assert isinstance(member_prune_info, audit_log_models.MemberPruneEntryInfo)

    @pytest.fixture()
    def message_bulk_delete_info_payload(self):
        return {"count": "42"}

    def test__deserialize_message_bulk_delete_entry_info(self, entity_factory_impl, message_bulk_delete_info_payload):
        message_bulk_delete_entry_info = entity_factory_impl._deserialize_message_bulk_delete_entry_info(
            message_bulk_delete_info_payload
        )
        assert message_bulk_delete_entry_info.count == 42
        assert isinstance(message_bulk_delete_entry_info, audit_log_models.MessageBulkDeleteEntryInfo)

    @pytest.fixture()
    def message_delete_info_payload(self):
        return {"count": "42", "channel_id": "4206942069"}

    def test__deserialize_message_delete_entry_info(self, entity_factory_impl, message_delete_info_payload):
        message_delete_entry_info = entity_factory_impl._deserialize_message_delete_entry_info(
            message_delete_info_payload
        )
        assert message_delete_entry_info.count == 42
        assert message_delete_entry_info.channel_id == 4206942069
        assert isinstance(message_delete_entry_info, audit_log_models.MessageDeleteEntryInfo)

    @pytest.fixture()
    def member_disconnect_info_payload(self):
        return {"count": "42"}

    def test__deserialize_member_disconnect_entry_info(self, entity_factory_impl, member_disconnect_info_payload):
        member_disconnect_entry_info = entity_factory_impl._deserialize_member_disconnect_entry_info(
            member_disconnect_info_payload
        )
        assert member_disconnect_entry_info.count == 42
        assert isinstance(member_disconnect_entry_info, audit_log_models.MemberDisconnectEntryInfo)

    @pytest.fixture()
    def member_move_info_payload(self):
        return {"count": "42", "channel_id": "22222222"}

    def test__deserialize_member_move_entry_info(self, entity_factory_impl, member_move_info_payload):
        member_move_entry_info = entity_factory_impl._deserialize_member_move_entry_info(member_move_info_payload)
        assert member_move_entry_info.channel_id == 22222222
        assert isinstance(member_move_entry_info, audit_log_models.MemberMoveEntryInfo)

    @pytest.fixture()
    def audit_log_entry_payload(self):
        return {
            "action_type": 14,
            "changes": [
                {
                    "key": "$add",
                    "new_value": [{"id": "568651298858074123", "name": "Casual"}],
                    "old_value": [{"id": "123123123312312", "name": "aRole"}],
                }
            ],
            "id": "694026906592477214",
            "options": {"id": "115590097100865541", "type": 1},
            "target_id": "115590097100865541",
            "user_id": "560984860634644482",
            "reason": "An artificial insanity.",
        }

    @pytest.fixture()
    def partial_integration_payload(self):
        return {
            "id": "4949494949",
            "name": "Blah blah",
            "type": "twitch",
            "account": {"id": "543453", "name": "Blam"},
        }

    @pytest.fixture()
    def audit_log_payload(
        self,
        audit_log_entry_payload,
        user_payload,
        incoming_webhook_payload,
        application_webhook_payload,
        follower_webhook_payload,
        partial_integration_payload,
    ):
        return {
            "audit_log_entries": [audit_log_entry_payload],
            "integrations": [partial_integration_payload],
            "users": [user_payload],
            "webhooks": [incoming_webhook_payload, application_webhook_payload, follower_webhook_payload],
        }

    def test_deserialize_audit_log(
        self,
        entity_factory_impl,
        mock_app,
        audit_log_payload,
        user_payload,
        incoming_webhook_payload,
        application_webhook_payload,
        follower_webhook_payload,
        partial_integration_payload,
    ):
        audit_log = entity_factory_impl.deserialize_audit_log(audit_log_payload)

        assert len(audit_log.entries) == 1
        entry = audit_log.entries[694026906592477214]
        assert entry.app is mock_app
        assert entry.id == 694026906592477214
        assert entry.target_id == 115590097100865541
        assert entry.user_id == 560984860634644482
        assert entry.action_type == audit_log_models.AuditLogEventType.CHANNEL_OVERWRITE_UPDATE
        assert entry.options.id == 115590097100865541
        assert entry.options.type == channel_models.PermissionOverwriteType.MEMBER
        assert entry.options.role_name is None
        assert entry.reason == "An artificial insanity."

        assert len(entry.changes) == 1
        change = entry.changes[0]
        assert change.key == audit_log_models.AuditLogChangeKey.ADD_ROLE_TO_MEMBER

        assert len(change.new_value) == 1
        role = change.new_value[568651298858074123]
        role.app is mock_app
        role.id == 568651298858074123
        role.name == "Casual"

        assert len(change.old_value) == 1
        role = change.old_value[123123123312312]
        role.app is mock_app
        role.id == 123123123312312
        role.name == "aRole"

        assert audit_log.integrations == {
            4949494949: entity_factory_impl.deserialize_partial_integration(partial_integration_payload)
        }
        assert audit_log.users == {115590097100865541: entity_factory_impl.deserialize_user(user_payload)}
        assert audit_log.webhooks == {
            223704706495545344: entity_factory_impl.deserialize_incoming_webhook(incoming_webhook_payload),
            658822586720976555: entity_factory_impl.deserialize_application_webhook(application_webhook_payload),
            752831914402115456: entity_factory_impl.deserialize_channel_follower_webhook(follower_webhook_payload),
        }

    def test_deserialize_audit_log_with_unset_or_unknown_fields(self, entity_factory_impl, audit_log_payload):
        # Unset fields
        audit_log_payload["audit_log_entries"][0]["changes"] = None
        audit_log_payload["audit_log_entries"][0]["target_id"] = None
        audit_log_payload["audit_log_entries"][0]["user_id"] = None
        audit_log_payload["audit_log_entries"][0]["options"] = None
        audit_log_payload["audit_log_entries"][0]["action_type"] = 69
        del audit_log_payload["audit_log_entries"][0]["reason"]

        audit_log = entity_factory_impl.deserialize_audit_log(audit_log_payload)

        assert len(audit_log.entries) == 1
        entry = audit_log.entries[694026906592477214]
        assert entry.changes == []
        assert entry.target_id is None
        assert entry.user_id is None
        assert entry.action_type == 69
        assert entry.options is None
        assert entry.reason is None

    def test_deserialize_audit_log_with_unhandled_change_key(self, entity_factory_impl, audit_log_payload):
        # Unset fields
        audit_log_payload["audit_log_entries"][0]["changes"][0]["key"] = "name"

        audit_log = entity_factory_impl.deserialize_audit_log(audit_log_payload)

        assert len(audit_log.entries) == 1
        entry = audit_log.entries[694026906592477214]
        assert len(entry.changes) == 1
        change = entry.changes[0]
        assert change.key == audit_log_models.AuditLogChangeKey.NAME
        assert change.new_value == [{"id": "568651298858074123", "name": "Casual"}]
        assert change.old_value == [{"id": "123123123312312", "name": "aRole"}]

    def test_deserialize_audit_log_with_change_key_unknown(self, entity_factory_impl, audit_log_payload):
        # Unset fields
        audit_log_payload["audit_log_entries"][0]["changes"][0]["key"] = "unknown"

        audit_log = entity_factory_impl.deserialize_audit_log(audit_log_payload)

        assert len(audit_log.entries) == 1
        entry = audit_log.entries[694026906592477214]
        assert len(entry.changes) == 1
        change = entry.changes[0]
        assert change.key == "unknown"
        assert change.new_value == [{"id": "568651298858074123", "name": "Casual"}]
        assert change.old_value == [{"id": "123123123312312", "name": "aRole"}]

    def test_deserialize_audit_log_with_action_type_unknown_gets_ignored(self, entity_factory_impl, audit_log_payload):
        # Unset fields
        audit_log_payload["audit_log_entries"][0]["action_type"] = 1000
        audit_log_payload["audit_log_entries"][0]["options"] = {"field1": "value1", "field2": 96}

        audit_log = entity_factory_impl.deserialize_audit_log(audit_log_payload)

        assert len(audit_log.entries) == 0

    def test_deserialize_audit_log_skips_unknown_webhook_type(
        self,
        entity_factory_impl,
        incoming_webhook_payload,
        application_webhook_payload,
    ):
        audit_log = entity_factory_impl.deserialize_audit_log(
            {
                "webhooks": [incoming_webhook_payload, {"type": -99999}, application_webhook_payload],
                "users": [],
                "audit_log_entries": [],
                "integrations": [],
            }
        )

        assert audit_log.webhooks == {
            223704706495545344: entity_factory_impl.deserialize_incoming_webhook(incoming_webhook_payload),
            658822586720976555: entity_factory_impl.deserialize_application_webhook(application_webhook_payload),
        }

    ##################
    # CHANNEL MODELS #
    ##################

    def test_deserialize_channel_follow(self, entity_factory_impl, mock_app):
        follow = entity_factory_impl.deserialize_channel_follow({"channel_id": "41231", "webhook_id": "939393"})
        assert follow.app is mock_app
        assert follow.channel_id == 41231
        assert follow.webhook_id == 939393

    @pytest.fixture()
    def permission_overwrite_payload(self):
        return {"id": "4242", "type": 1, "allow": 65, "deny": 49152, "allow_new": "65", "deny_new": "49152"}

    @pytest.mark.parametrize("type", [0, 1])
    def test_deserialize_permission_overwrite(self, entity_factory_impl, type):
        permission_overwrite_payload = {
            "id": "4242",
            "type": type,
            "allow": 65,
            "deny": 49152,
            "allow_new": "65",
            "deny_new": "49152",
        }
        overwrite = entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        assert overwrite.type == channel_models.PermissionOverwriteType(type)
        assert overwrite.allow == permission_models.Permissions(65)
        assert overwrite.deny == permission_models.Permissions(49152)
        assert isinstance(overwrite, channel_models.PermissionOverwrite)

    @pytest.mark.parametrize(
        "type",
        [channel_models.PermissionOverwriteType.MEMBER, channel_models.PermissionOverwriteType.ROLE],
    )
    def test_serialize_permission_overwrite(self, entity_factory_impl, type):
        overwrite = channel_models.PermissionOverwrite(id=123123, type=type, allow=42, deny=62)
        payload = entity_factory_impl.serialize_permission_overwrite(overwrite)
        assert payload == {"id": "123123", "type": int(type), "allow": "42", "deny": "62"}

    @pytest.fixture()
    def partial_channel_payload(self):
        return {"id": "561884984214814750", "name": "general", "type": 0}

    def test_deserialize_partial_channel(self, entity_factory_impl, mock_app, partial_channel_payload):
        partial_channel = entity_factory_impl.deserialize_partial_channel(partial_channel_payload)
        assert partial_channel.app is mock_app
        assert partial_channel.id == 561884984214814750
        assert partial_channel.name == "general"
        assert partial_channel.type == channel_models.ChannelType.GUILD_TEXT
        assert isinstance(partial_channel, channel_models.PartialChannel)

    def test_deserialize_partial_channel_with_unset_fields(self, entity_factory_impl):
        assert entity_factory_impl.deserialize_partial_channel({"id": "22", "type": 0}).name is None

    @pytest.fixture()
    def dm_channel_payload(self, user_payload):
        return {
            "id": "123",
            "last_message_id": "456",
            "type": 1,
            "recipients": [user_payload],
        }

    def test_deserialize_dm_channel(self, entity_factory_impl, mock_app, dm_channel_payload, user_payload):
        dm_channel = entity_factory_impl.deserialize_dm(dm_channel_payload)
        assert dm_channel.app is mock_app
        assert dm_channel.id == 123
        assert dm_channel.name is None
        assert dm_channel.last_message_id == 456
        assert dm_channel.type is channel_models.ChannelType.DM
        assert dm_channel.recipient == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(dm_channel, channel_models.DMChannel)

    def test_deserialize_dm_channel_with_null_fields(self, entity_factory_impl, user_payload):
        dm_channel = entity_factory_impl.deserialize_dm(
            {"id": "123", "last_message_id": None, "type": 1, "recipients": [user_payload]}
        )
        assert dm_channel.last_message_id is None

    def test_deserialize_dm_channel_with_unsetfields(self, entity_factory_impl, user_payload):
        dm_channel = entity_factory_impl.deserialize_dm({"id": "123", "type": 1, "recipients": [user_payload]})
        assert dm_channel.last_message_id is None

    @pytest.fixture()
    def group_dm_channel_payload(self, user_payload):
        return {
            "id": "123",
            "name": "Secret Developer Group",
            "icon": "123asdf123adsf",
            "owner_id": "456",
            "application_id": "123789",
            "last_message_id": "456",
            "nicks": [{"id": "115590097100865541", "nick": "nyaa"}],
            "type": 3,
            "recipients": [user_payload],
        }

    def test_deserialize_group_dm_channel(self, entity_factory_impl, mock_app, group_dm_channel_payload, user_payload):
        group_dm = entity_factory_impl.deserialize_group_dm(group_dm_channel_payload)
        assert group_dm.app is mock_app
        assert group_dm.id == 123
        assert group_dm.name == "Secret Developer Group"
        assert group_dm.icon_hash == "123asdf123adsf"
        assert group_dm.application_id == 123789
        assert group_dm.nicknames == {115590097100865541: "nyaa"}
        assert group_dm.last_message_id == 456
        assert group_dm.type == channel_models.ChannelType.GROUP_DM
        assert group_dm.recipients == {115590097100865541: entity_factory_impl.deserialize_user(user_payload)}
        assert isinstance(group_dm, channel_models.GroupDMChannel)

    def test_test_deserialize_group_dm_channel_with_unset_fields(self, entity_factory_impl, user_payload):
        group_dm = entity_factory_impl.deserialize_group_dm(
            {
                "id": "123",
                "name": "Secret Developer Group",
                "icon": "123asdf123adsf",
                "owner_id": "456",
                "type": 3,
                "recipients": [user_payload],
            }
        )
        assert group_dm.nicknames == {}
        assert group_dm.application_id is None
        assert group_dm.last_message_id is None

    @pytest.fixture()
    def guild_category_payload(self, permission_overwrite_payload):
        return {
            "id": "123",
            "permission_overwrites": [permission_overwrite_payload],
            "name": "Test",
            "parent_id": "664565",
            "nsfw": True,
            "position": 3,
            "guild_id": "9876",
            "type": 4,
        }

    def test_deserialize_guild_category(
        self, entity_factory_impl, mock_app, guild_category_payload, permission_overwrite_payload
    ):
        guild_category = entity_factory_impl.deserialize_guild_category(guild_category_payload)
        assert guild_category.app is mock_app
        assert guild_category.id == 123
        assert guild_category.name == "Test"
        assert guild_category.type == channel_models.ChannelType.GUILD_CATEGORY
        assert guild_category.guild_id == 9876
        assert guild_category.position == 3
        assert guild_category.permission_overwrites == {
            4242: entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        }
        assert guild_category.is_nsfw is True
        assert guild_category.parent_id == 664565
        assert isinstance(guild_category, channel_models.GuildCategory)

    def test_deserialize_guild_category_with_unset_fields(self, entity_factory_impl, permission_overwrite_payload):
        guild_category = entity_factory_impl.deserialize_guild_category(
            {
                "id": "123",
                "permission_overwrites": [permission_overwrite_payload],
                "name": "Test",
                "position": 3,
                "type": 4,
                "guild_id": "123123",
            }
        )
        assert guild_category.parent_id is None
        assert guild_category.is_nsfw is None

    def test_deserialize_guild_category_with_null_fields(self, entity_factory_impl, permission_overwrite_payload):
        guild_category = entity_factory_impl.deserialize_guild_category(
            {
                "id": "123",
                "permission_overwrites": [permission_overwrite_payload],
                "name": "Test",
                "parent_id": None,
                "nsfw": True,
                "position": 3,
                "guild_id": "9876",
                "type": 4,
            }
        )
        assert guild_category.parent_id is None

    @pytest.fixture()
    def guild_text_channel_payload(self, permission_overwrite_payload):
        return {
            "id": "123",
            "guild_id": "567",
            "name": "general",
            "type": 0,
            "position": 6,
            "permission_overwrites": [permission_overwrite_payload],
            "rate_limit_per_user": 2,
            "nsfw": True,
            "topic": "¯\\_(ツ)_/¯",
            "last_message_id": "123456",
            "last_pin_timestamp": "2020-05-27T15:58:51.545252+00:00",
            "parent_id": "987",
        }

    def test_deserialize_guild_text_channel(
        self, entity_factory_impl, mock_app, guild_text_channel_payload, permission_overwrite_payload
    ):
        guild_text_channel = entity_factory_impl.deserialize_guild_text_channel(guild_text_channel_payload)
        assert guild_text_channel.app is mock_app
        assert guild_text_channel.id == 123
        assert guild_text_channel.name == "general"
        assert guild_text_channel.type == channel_models.ChannelType.GUILD_TEXT
        assert guild_text_channel.guild_id == 567
        assert guild_text_channel.position == 6
        assert guild_text_channel.permission_overwrites == {
            4242: entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        }
        assert guild_text_channel.is_nsfw is True
        assert guild_text_channel.parent_id == 987
        assert guild_text_channel.topic == "¯\\_(ツ)_/¯"
        assert guild_text_channel.last_message_id == 123456
        assert guild_text_channel.rate_limit_per_user == datetime.timedelta(seconds=2)
        assert guild_text_channel.last_pin_timestamp == datetime.datetime(
            2020, 5, 27, 15, 58, 51, 545252, tzinfo=datetime.timezone.utc
        )
        assert isinstance(guild_text_channel, channel_models.GuildTextChannel)

    def test_deserialize_guild_text_channel_with_unset_fields(self, entity_factory_impl):
        guild_text_channel = entity_factory_impl.deserialize_guild_text_channel(
            {
                "id": "123",
                "name": "general",
                "type": 0,
                "position": 6,
                "permission_overwrites": [],
                "topic": "¯\\_(ツ)_/¯",
                "guild_id": "123123123",
            }
        )
        assert guild_text_channel.is_nsfw is None
        assert guild_text_channel.rate_limit_per_user.total_seconds() == 0
        assert guild_text_channel.last_pin_timestamp is None
        assert guild_text_channel.parent_id is None
        assert guild_text_channel.last_message_id is None

    def test_deserialize_guild_text_channel_with_null_fields(self, entity_factory_impl):
        guild_text_channel = entity_factory_impl.deserialize_guild_text_channel(
            {
                "id": "123",
                "guild_id": "567",
                "name": "general",
                "type": 0,
                "position": 6,
                "permission_overwrites": [],
                "rate_limit_per_user": 2,
                "nsfw": True,
                "topic": None,
                "last_message_id": None,
                "last_pin_timestamp": None,
                "parent_id": None,
            }
        )
        assert guild_text_channel.topic is None
        assert guild_text_channel.last_message_id is None
        assert guild_text_channel.last_pin_timestamp is None
        assert guild_text_channel.parent_id is None

    @pytest.fixture()
    def guild_news_channel_payload(self, permission_overwrite_payload):
        return {
            "id": "7777",
            "guild_id": "123",
            "name": "Important Announcements",
            "type": 5,
            "position": 0,
            "permission_overwrites": [permission_overwrite_payload],
            "nsfw": True,
            "topic": "Super Important Announcements",
            "last_message_id": "456",
            "parent_id": "654",
            "last_pin_timestamp": "2020-05-27T15:58:51.545252+00:00",
        }

    def test_deserialize_guild_news_channel(
        self, entity_factory_impl, mock_app, guild_news_channel_payload, permission_overwrite_payload
    ):
        news_channel = entity_factory_impl.deserialize_guild_news_channel(guild_news_channel_payload)
        assert news_channel.app is mock_app
        assert news_channel.id == 7777
        assert news_channel.name == "Important Announcements"
        assert news_channel.type == channel_models.ChannelType.GUILD_NEWS
        assert news_channel.guild_id == 123
        assert news_channel.position == 0
        assert news_channel.permission_overwrites == {
            4242: entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        }
        assert news_channel.is_nsfw is True
        assert news_channel.parent_id == 654
        assert news_channel.topic == "Super Important Announcements"
        assert news_channel.last_message_id == 456
        assert news_channel.last_pin_timestamp == datetime.datetime(
            2020, 5, 27, 15, 58, 51, 545252, tzinfo=datetime.timezone.utc
        )
        assert isinstance(news_channel, channel_models.GuildNewsChannel)

    def test_deserialize_guild_news_channel_with_unset_fields(self, entity_factory_impl):
        news_channel = entity_factory_impl.deserialize_guild_news_channel(
            {
                "id": "567",
                "name": "Important Announcements",
                "type": 5,
                "position": 0,
                "permission_overwrites": [],
                "topic": "Super Important Announcements",
                "guild_id": "4123",
            }
        )
        assert news_channel.is_nsfw is None
        assert news_channel.parent_id is None
        assert news_channel.last_pin_timestamp is None
        assert news_channel.last_message_id is None

    def test_deserialize_guild_news_channel_with_null_fields(self, entity_factory_impl):
        news_channel = entity_factory_impl.deserialize_guild_news_channel(
            {
                "id": "567",
                "guild_id": "123",
                "name": "Important Announcements",
                "type": 5,
                "position": 0,
                "permission_overwrites": [],
                "nsfw": True,
                "topic": None,
                "last_message_id": None,
                "parent_id": None,
                "last_pin_timestamp": None,
            }
        )
        assert news_channel.topic is None
        assert news_channel.last_message_id is None
        assert news_channel.parent_id is None
        assert news_channel.last_pin_timestamp is None

    @pytest.fixture()
    def guild_store_channel_payload(self, permission_overwrite_payload):
        return {
            "id": "123",
            "permission_overwrites": [permission_overwrite_payload],
            "name": "Half Life 3",
            "parent_id": "9876",
            "nsfw": True,
            "position": 2,
            "guild_id": "1234",
            "type": 6,
        }

    def test_deserialize_guild_store_channel(
        self, entity_factory_impl, mock_app, guild_store_channel_payload, permission_overwrite_payload
    ):
        store_chanel = entity_factory_impl.deserialize_guild_store_channel(guild_store_channel_payload)
        assert store_chanel.id == 123
        assert store_chanel.name == "Half Life 3"
        assert store_chanel.type == channel_models.ChannelType.GUILD_STORE
        assert store_chanel.guild_id == 1234
        assert store_chanel.position == 2
        assert store_chanel.permission_overwrites == {
            4242: entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        }
        assert store_chanel.is_nsfw is True
        assert store_chanel.parent_id == 9876
        assert isinstance(store_chanel, channel_models.GuildStoreChannel)

    def test_deserialize_guild_store_channel_with_unset_fields(self, entity_factory_impl):
        store_chanel = entity_factory_impl.deserialize_guild_store_channel(
            {
                "id": "123",
                "permission_overwrites": [],
                "name": "Half Life 3",
                "position": 2,
                "type": 6,
                "guild_id": 123123,
            }
        )
        assert store_chanel.parent_id is None
        assert store_chanel.is_nsfw is None

    def test_deserialize_guild_store_channel_with_null_fields(self, entity_factory_impl):
        store_chanel = entity_factory_impl.deserialize_guild_store_channel(
            {
                "id": "123",
                "permission_overwrites": [],
                "name": "Half Life 3",
                "parent_id": None,
                "nsfw": True,
                "position": 2,
                "guild_id": "1234",
                "type": 6,
            }
        )
        assert store_chanel.parent_id is None

    @pytest.fixture()
    def guild_voice_channel_payload(self, permission_overwrite_payload):
        return {
            "id": "555",
            "guild_id": "789",
            "name": "Secret Developer Discussions",
            "type": 2,
            "nsfw": True,
            "position": 4,
            "permission_overwrites": [permission_overwrite_payload],
            "bitrate": 64000,
            "user_limit": 3,
            "rtc_region": "europe",
            "parent_id": "456",
            "video_quality_mode": 1,
        }

    def test_deserialize_guild_voice_channel(
        self, entity_factory_impl, mock_app, guild_voice_channel_payload, permission_overwrite_payload
    ):
        voice_channel = entity_factory_impl.deserialize_guild_voice_channel(guild_voice_channel_payload)
        assert voice_channel.id == 555
        assert voice_channel.name == "Secret Developer Discussions"
        assert voice_channel.type == channel_models.ChannelType.GUILD_VOICE
        assert voice_channel.guild_id == 789
        assert voice_channel.position == 4
        assert voice_channel.permission_overwrites == {
            4242: entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        }
        assert voice_channel.is_nsfw is True
        assert voice_channel.parent_id == 456
        assert voice_channel.region == "europe"
        assert voice_channel.bitrate == 64000
        assert voice_channel.video_quality_mode is channel_models.VideoQualityMode.AUTO
        assert voice_channel.user_limit == 3
        assert isinstance(voice_channel, channel_models.GuildVoiceChannel)

    def test_deserialize_guild_voice_channel_with_null_fields(self, entity_factory_impl):
        voice_channel = entity_factory_impl.deserialize_guild_voice_channel(
            {
                "id": "123",
                "permission_overwrites": [],
                "name": "Half Life 3",
                "parent_id": None,
                "nsfw": True,
                "position": 2,
                "guild_id": "1234",
                "bitrate": 64000,
                "user_limit": 3,
                "rtc_region": None,
                "type": 6,
                "video_quality_mode": 1,
            }
        )
        assert voice_channel.parent_id is None
        assert voice_channel.region is None

    def test_deserialize_guild_voice_channel_with_unset_fields(self, entity_factory_impl):
        voice_channel = entity_factory_impl.deserialize_guild_voice_channel(
            {
                "id": "123",
                "permission_overwrites": [],
                "name": "Half Life 3",
                "position": 2,
                "bitrate": 64000,
                "user_limit": 3,
                "type": 6,
                "guild_id": "123123",
            }
        )
        assert voice_channel.video_quality_mode is channel_models.VideoQualityMode.AUTO
        assert voice_channel.parent_id is None
        assert voice_channel.is_nsfw is None
        assert voice_channel.region is None

    @pytest.fixture()
    def guild_stage_channel_payload(self, permission_overwrite_payload):
        return {
            "id": "555",
            "guild_id": "666",
            "name": "Secret Developer Discussions",
            "type": 13,
            "nsfw": False,
            "position": 6,
            "permission_overwrites": [permission_overwrite_payload],
            "bitrate": 64000,
            "user_limit": 3,
            "rtc_region": "euoo",
            "parent_id": "543",
        }

    def test_deserialize_guild_stage_channel(
        self, entity_factory_impl, mock_app, guild_stage_channel_payload, permission_overwrite_payload
    ):
        voice_channel = entity_factory_impl.deserialize_guild_stage_channel(guild_stage_channel_payload)
        assert voice_channel.id == 555
        assert voice_channel.name == "Secret Developer Discussions"
        assert voice_channel.type == channel_models.ChannelType.GUILD_STAGE
        assert voice_channel.guild_id == 666
        assert voice_channel.position == 6
        assert voice_channel.permission_overwrites == {
            4242: entity_factory_impl.deserialize_permission_overwrite(permission_overwrite_payload)
        }
        assert voice_channel.is_nsfw is False
        assert voice_channel.parent_id == 543
        assert voice_channel.region == "euoo"
        assert voice_channel.bitrate == 64000
        assert voice_channel.user_limit == 3
        assert isinstance(voice_channel, channel_models.GuildStageChannel)

    def test_deserialize_guild_stage_channel_with_null_fields(self, entity_factory_impl):
        voice_channel = entity_factory_impl.deserialize_guild_voice_channel(
            {
                "id": "123",
                "permission_overwrites": [],
                "name": "Half Life 3",
                "parent_id": None,
                "nsfw": True,
                "position": 2,
                "guild_id": "1234",
                "bitrate": 64000,
                "user_limit": 3,
                "rtc_region": None,
                "type": 6,
            }
        )
        assert voice_channel.parent_id is None
        assert voice_channel.region is None

    def test_deserialize_guild_stage_channel_with_unset_fields(self, entity_factory_impl):
        voice_channel = entity_factory_impl.deserialize_guild_stage_channel(
            {
                "id": "123",
                "permission_overwrites": [],
                "name": "Half Life 3",
                "position": 2,
                "bitrate": 64000,
                "user_limit": 3,
                "rtc_region": "europe",
                "type": 6,
                "guild_id": "123123",
            }
        )
        assert voice_channel.parent_id is None
        assert voice_channel.is_nsfw is None

    def test_deserialize_channel_returns_right_type(
        self,
        entity_factory_impl,
        dm_channel_payload,
        group_dm_channel_payload,
        guild_category_payload,
        guild_text_channel_payload,
        guild_news_channel_payload,
        guild_store_channel_payload,
        guild_voice_channel_payload,
        guild_stage_channel_payload,
    ):
        for payload, expected_type in [
            (dm_channel_payload, channel_models.DMChannel),
            (group_dm_channel_payload, channel_models.GroupDMChannel),
            (guild_category_payload, channel_models.GuildCategory),
            (guild_text_channel_payload, channel_models.GuildTextChannel),
            (guild_news_channel_payload, channel_models.GuildNewsChannel),
            (guild_store_channel_payload, channel_models.GuildStoreChannel),
            (guild_voice_channel_payload, channel_models.GuildVoiceChannel),
            (guild_stage_channel_payload, channel_models.GuildStageChannel),
        ]:
            assert isinstance(entity_factory_impl.deserialize_channel(payload), expected_type)

    def test_deserialize_channel_handles_unknown_channel_type(self, entity_factory_impl):
        with pytest.raises(errors.UnrecognisedEntityError):
            entity_factory_impl.deserialize_channel({"type": -9999999999})

    ################
    # EMBED MODELS #
    ################

    @pytest.fixture()
    def embed_payload(self):
        return {
            "title": "embed title",
            "description": "embed description",
            "url": "https://somewhere.com",
            "timestamp": "2020-03-22T16:40:39.218000+00:00",
            "color": 14014915,
            "footer": {
                "text": "footer text",
                "icon_url": "https://somewhere.com/footer.png",
                "proxy_icon_url": "https://media.somewhere.com/footer.png",
            },
            "image": {
                "url": "https://somewhere.com/image.png",
                "proxy_url": "https://media.somewhere.com/image.png",
                "height": 122,
                "width": 133,
            },
            "thumbnail": {
                "url": "https://somewhere.com/thumbnail.png",
                "proxy_url": "https://media.somewhere.com/thumbnail.png",
                "height": 123,
                "width": 456,
            },
            "video": {
                "url": "https://somewhere.com/video.mp4",
                "height": 1234,
                "width": 4567,
                "proxy_url": "https://somewhere.com/proxy/video.mp4",
            },
            "provider": {"name": "some name", "url": "https://somewhere.com/provider"},
            "author": {
                "name": "some name",
                "url": "https://somewhere.com/author-url",
                "icon_url": "https://somewhere.com/author.png",
                "proxy_icon_url": "https://media.somewhere.com/author.png",
            },
            "fields": [{"name": "title", "value": "some value", "inline": True}],
        }

    def test_deserialize_embed_with_full_embed(self, entity_factory_impl, embed_payload):
        embed = entity_factory_impl.deserialize_embed(embed_payload)
        assert embed.title == "embed title"
        assert embed.description == "embed description"
        assert embed.url == "https://somewhere.com"
        assert embed.timestamp == datetime.datetime(2020, 3, 22, 16, 40, 39, 218000, tzinfo=datetime.timezone.utc)
        assert embed.color == color_models.Color(14014915)
        assert isinstance(embed.color, color_models.Color)
        # EmbedFooter
        assert embed.footer.text == "footer text"
        assert embed.footer.icon.resource.url == "https://somewhere.com/footer.png"
        assert embed.footer.icon.proxy_resource.url == "https://media.somewhere.com/footer.png"
        assert isinstance(embed.footer, embed_models.EmbedFooter)
        # EmbedImage
        assert embed.image.resource.url == "https://somewhere.com/image.png"
        assert embed.image.proxy_resource.url == "https://media.somewhere.com/image.png"
        assert embed.image.height == 122
        assert embed.image.width == 133
        assert isinstance(embed.image, embed_models.EmbedImage)
        # EmbedThumbnail
        assert embed.thumbnail.resource.url == "https://somewhere.com/thumbnail.png"
        assert embed.thumbnail.proxy_resource.url == "https://media.somewhere.com/thumbnail.png"
        assert embed.thumbnail.height == 123
        assert embed.thumbnail.width == 456
        assert isinstance(embed.thumbnail, embed_models.EmbedImage)
        # EmbedVideo
        assert embed.video.resource.url == "https://somewhere.com/video.mp4"
        assert embed.video.proxy_resource.url == "https://somewhere.com/proxy/video.mp4"
        assert embed.video.height == 1234
        assert embed.video.width == 4567
        assert isinstance(embed.video, embed_models.EmbedVideo)
        # EmbedProvider
        assert embed.provider.name == "some name"
        assert embed.provider.url == "https://somewhere.com/provider"
        assert isinstance(embed.provider, embed_models.EmbedProvider)
        # EmbedAuthor
        assert embed.author.name == "some name"
        assert embed.author.url == "https://somewhere.com/author-url"
        assert embed.author.icon.resource.url == "https://somewhere.com/author.png"
        assert embed.author.icon.proxy_resource.url == "https://media.somewhere.com/author.png"
        assert isinstance(embed.author, embed_models.EmbedAuthor)
        # EmbedField
        assert len(embed.fields) == 1
        field = embed.fields[0]
        assert field.name == "title"
        assert field.value == "some value"
        assert field.is_inline is True
        assert isinstance(field, embed_models.EmbedField)

    def test_deserialize_embed_with_partial_sub_fields(self, entity_factory_impl, embed_payload):
        embed = entity_factory_impl.deserialize_embed(
            {
                "footer": {"text": "footer text"},
                "image": {"url": "https://blahblah.blahblahblah"},
                "thumbnail": {"url": "https://blahblah2.blahblahblah"},
                "video": {"url": "https://blahblah3.blahblahblah"},
                "provider": {"url": "https://blahbla5h.blahblahblah"},
                "author": {"name": "author name"},
            }
        )
        # EmbedFooter
        assert embed.footer.text == "footer text"
        assert embed.footer.icon is None
        # EmbedImage
        assert embed.image.resource.url == "https://blahblah.blahblahblah"
        assert embed.image.proxy_resource is None
        assert embed.image.width is None
        assert embed.image.height is None
        # EmbedThumbnail
        assert embed.thumbnail.resource.url == "https://blahblah2.blahblahblah"
        assert embed.thumbnail.proxy_resource is None
        assert embed.thumbnail.height is None
        assert embed.thumbnail.width is None
        # EmbedVideo
        assert embed.video.resource.url == "https://blahblah3.blahblahblah"
        assert embed.video.proxy_resource is None
        assert embed.video.height is None
        assert embed.video.width is None
        # EmbedProvider
        assert embed.provider.name is None
        assert embed.provider.url == "https://blahbla5h.blahblahblah"
        # EmbedAuthor
        assert embed.author.name == "author name"
        assert embed.author.url is None
        assert embed.author.icon is None

    def test_deserialize_embed_with_other_null_sub_fields(self, entity_factory_impl, embed_payload):
        embed = entity_factory_impl.deserialize_embed(
            {
                "footer": {"text": "footer text"},
                "provider": {"name": "name name"},
                "author": {"url": "urlurlurl"},
                "fields": [{"name": "title", "value": "some value"}],
            }
        )
        # EmbedProvider
        assert embed.provider.name == "name name"
        assert embed.provider.url is None
        # EmbedAuthor
        assert embed.author.name is None
        assert embed.author.url == "urlurlurl"
        assert embed.author.icon is None

    def test_deserialize_embed_with_partial_fields(self, entity_factory_impl, embed_payload):
        embed = entity_factory_impl.deserialize_embed(
            {
                "footer": {"text": "footer text"},
                "image": {},
                "thumbnail": {},
                "video": {},
                "provider": {},
                "author": {"name": "author name"},
                "fields": [{"name": "title", "value": "some value"}],
            }
        )
        # EmbedFooter
        assert embed.footer.text == "footer text"
        assert embed.footer.icon is None
        # EmbedImage
        assert embed.image is None
        # EmbedThumbnail
        assert embed.thumbnail is None
        # EmbedVideo
        assert embed.video is None
        # EmbedProvider
        assert embed.provider is None
        # EmbedAuthor
        assert embed.author.name == "author name"
        assert embed.author.url is None
        assert embed.author.icon is None
        # EmbedField
        assert len(embed.fields) == 1
        field = embed.fields[0]
        assert field.name == "title"
        assert field.value == "some value"
        assert field.is_inline is False
        assert isinstance(field, embed_models.EmbedField)

    def test_deserialize_embed_with_empty_embed(self, entity_factory_impl):
        embed = entity_factory_impl.deserialize_embed({})
        assert embed.title is None
        assert embed.description is None
        assert embed.url is None
        assert embed.timestamp is None
        assert embed.color is None
        assert embed.footer is None
        assert embed.image is None
        assert embed.thumbnail is None
        assert embed.video is None
        assert embed.provider is None
        assert embed.author is None
        assert embed.fields == []

    def test_serialize_embed_with_non_url_resources_provides_attachments(self, entity_factory_impl):
        footer_icon = embed_models.EmbedResource(resource=files.File("cat.png"))
        thumbnail = embed_models.EmbedImage(resource=files.File("dog.png"))
        image = embed_models.EmbedImage(resource=files.Bytes(b"potato kung fu", "sushi.pdf"))
        author_icon = embed_models.EmbedResource(resource=files.Bytes(b"potato kung fu^2", "sushi².jpg"))
        video_icon = embed_models.EmbedResource(resource=files.Bytes(b"whatevr", "sushi².mp4"))

        payload, resources = entity_factory_impl.serialize_embed(
            embed_models.Embed.from_received_embed(
                title="Title",
                description="Nyaa",
                url="https://some-url",
                timestamp=datetime.datetime(2020, 5, 29, 20, 37, 22, 865139),
                color=color_models.Color(321321),
                footer=embed_models.EmbedFooter(text="TEXT", icon=footer_icon),
                image=image,
                thumbnail=thumbnail,
                author=embed_models.EmbedAuthor(name="AUTH ME", url="wss://\\_/-_-\\_/", icon=author_icon),
                fields=[embed_models.EmbedField(value="VALUE", name="NAME", inline=True)],
                provider=None,
                video=embed_models.EmbedVideo(resource=video_icon),
            )
        )

        # Non URL bois should be returned in the resources container.
        assert len(resources) == 4
        assert footer_icon.resource in resources
        assert thumbnail.resource in resources
        assert image.resource in resources
        assert author_icon.resource in resources

        assert payload == {
            "title": "Title",
            "description": "Nyaa",
            "url": "https://some-url",
            "timestamp": "2020-05-29T20:37:22.865139",
            "color": 321321,
            "footer": {"text": "TEXT", "icon_url": footer_icon.url},
            "image": {"url": image.url},
            "thumbnail": {"url": thumbnail.url},
            "author": {"name": "AUTH ME", "url": "wss://\\_/-_-\\_/", "icon_url": author_icon.url},
            "fields": [{"value": "VALUE", "name": "NAME", "inline": True}],
        }

    def test_serialize_embed_with_url_resources_does_not_provide_attachments(self, entity_factory_impl):
        class DummyWebResource(files.WebResource):
            @property
            def url(self) -> str:
                return "http://lolbook.com"

            @property
            def filename(self) -> str:
                return "lolbook.png"

        footer_icon = embed_models.EmbedResource(resource=files.URL("http://http.cat"))
        thumbnail = embed_models.EmbedImage(resource=DummyWebResource())
        image = embed_models.EmbedImage(resource=files.URL("http://bazbork.com"))
        author_icon = embed_models.EmbedResource(resource=files.URL("http://foobar.com"))

        payload, resources = entity_factory_impl.serialize_embed(
            embed_models.Embed.from_received_embed(
                title="Title",
                description="Nyaa",
                url="https://some-url",
                timestamp=datetime.datetime(2020, 5, 29, 20, 37, 22, 865139),
                color=color_models.Color(321321),
                footer=embed_models.EmbedFooter(text="TEXT", icon=footer_icon),
                image=image,
                thumbnail=thumbnail,
                author=embed_models.EmbedAuthor(name="AUTH ME", url="wss://\\_/-_-\\_/", icon=author_icon),
                fields=[embed_models.EmbedField(value="VALUE", name="NAME", inline=True)],
                video=embed_models.EmbedVideo(
                    resource=embed_models.EmbedResource(resource=files.URL("http://foobar.com"))
                ),
                provider=embed_models.EmbedProvider(name="I said nya"),
            )
        )

        # Non URL bois should be returned in the resources container.
        assert footer_icon.resource not in resources
        assert thumbnail.resource not in resources
        assert image.resource not in resources
        assert author_icon.resource not in resources
        assert not resources

        assert payload == {
            "title": "Title",
            "description": "Nyaa",
            "url": "https://some-url",
            "timestamp": "2020-05-29T20:37:22.865139",
            "color": 321321,
            "footer": {"text": "TEXT", "icon_url": footer_icon.url},
            "image": {"url": image.url},
            "thumbnail": {"url": thumbnail.url},
            "author": {"name": "AUTH ME", "url": "wss://\\_/-_-\\_/", "icon_url": author_icon.url},
            "fields": [{"value": "VALUE", "name": "NAME", "inline": True}],
        }

    def test_serialize_embed_with_null_sub_fields(self, entity_factory_impl):
        payload, resources = entity_factory_impl.serialize_embed(
            embed_models.Embed.from_received_embed(
                title="Title",
                description="Nyaa",
                url="https://some-url",
                timestamp=datetime.datetime(2020, 5, 29, 20, 37, 22, 865139),
                color=color_models.Color(321321),
                footer=embed_models.EmbedFooter(),
                author=embed_models.EmbedAuthor(),
                video=None,
                provider=None,
                fields=None,
                image=None,
                thumbnail=None,
            )
        )
        assert payload == {
            "title": "Title",
            "description": "Nyaa",
            "url": "https://some-url",
            "timestamp": "2020-05-29T20:37:22.865139",
            "color": 321321,
            "author": {},
            "footer": {},
        }
        assert resources == []

    def test_serialize_embed_with_null_attributes(self, entity_factory_impl):
        assert entity_factory_impl.serialize_embed(embed_models.Embed()) == ({}, [])

    @pytest.mark.parametrize(
        "field_kwargs",
        [
            {"name": None, "value": "correct value"},
            {"name": "", "value": "correct value"},
            {"name": "    ", "value": "correct value"},
            {"name": "correct value", "value": None},
            {"name": "correct value", "value": ""},
            {"name": "correct value", "value": "    "},
        ],
    )
    def test_serialize_embed_validators(self, entity_factory_impl, field_kwargs):
        embed_obj = embed_models.Embed()
        embed_obj.add_field(**field_kwargs)
        with pytest.raises(TypeError):
            entity_factory_impl.serialize_embed(embed_obj)

    ################
    # EMOJI MODELS #
    ################

    def test_deserialize_unicode_emoji(self, entity_factory_impl):
        emoji = entity_factory_impl.deserialize_unicode_emoji({"name": "🤷"})
        assert emoji.name == "🤷"
        assert isinstance(emoji, emoji_models.UnicodeEmoji)

    @pytest.fixture()
    def custom_emoji_payload(self):
        return {"id": "691225175349395456", "name": "test", "animated": True}

    def test_deserialize_custom_emoji(self, entity_factory_impl, mock_app, custom_emoji_payload):
        emoji = entity_factory_impl.deserialize_custom_emoji(custom_emoji_payload)
        assert emoji.id == snowflakes.Snowflake(691225175349395456)
        assert emoji.name == "test"
        assert emoji.is_animated is True
        assert isinstance(emoji, emoji_models.CustomEmoji)

    def test_deserialize_custom_emoji_with_unset_and_null_fields(
        self, entity_factory_impl, mock_app, custom_emoji_payload
    ):
        emoji = entity_factory_impl.deserialize_custom_emoji({"id": "691225175349395456", "name": None})
        assert emoji.is_animated is False
        assert emoji.name is None

    @pytest.fixture()
    def known_custom_emoji_payload(self, user_payload):
        return {
            "id": "12345",
            "name": "testing",
            "animated": False,
            "available": True,
            "roles": ["123", "456"],
            "user": user_payload,
            "require_colons": True,
            "managed": False,
        }

    def test_deserialize_known_custom_emoji(
        self, entity_factory_impl, mock_app, user_payload, known_custom_emoji_payload
    ):
        emoji = entity_factory_impl.deserialize_known_custom_emoji(
            known_custom_emoji_payload, guild_id=snowflakes.Snowflake(1235123)
        )
        assert emoji.app is mock_app
        assert emoji.id == 12345
        assert emoji.guild_id == 1235123
        assert emoji.name == "testing"
        assert emoji.is_animated is False
        assert emoji.role_ids == [123, 456]
        assert emoji.user == entity_factory_impl.deserialize_user(user_payload)
        assert emoji.is_colons_required is True
        assert emoji.is_managed is False
        assert emoji.is_available is True
        assert isinstance(emoji, emoji_models.KnownCustomEmoji)

    def test_deserialize_known_custom_emoji_with_unset_fields(self, entity_factory_impl):
        emoji = entity_factory_impl.deserialize_known_custom_emoji(
            {
                "id": "12345",
                "name": "testing",
                "available": True,
                "roles": ["123", "456"],
                "require_colons": True,
                "managed": False,
            },
            guild_id=snowflakes.Snowflake(642334234),
        )
        assert emoji.user is None
        assert emoji.is_animated is False

    @pytest.mark.parametrize(
        ("payload", "expected_type"),
        [({"name": "🤷"}, emoji_models.UnicodeEmoji), ({"id": "1234", "name": "test"}, emoji_models.CustomEmoji)],
    )
    def test_deserialize_emoji_returns_expected_type(self, entity_factory_impl, payload, expected_type):
        isinstance(entity_factory_impl.deserialize_emoji(payload), expected_type)

    ##################
    # GATEWAY MODELS #
    ##################

    @pytest.fixture()
    def gateway_bot_payload(self):
        return {
            "url": "wss://gateway.discord.gg",
            "shards": 1,
            "session_start_limit": {"total": 1000, "remaining": 991, "reset_after": 14170186, "max_concurrency": 5},
        }

    def test_deserialize_gateway_bot(self, entity_factory_impl, gateway_bot_payload):
        gateway_bot = entity_factory_impl.deserialize_gateway_bot_info(gateway_bot_payload)
        assert isinstance(gateway_bot, gateway_models.GatewayBotInfo)
        assert gateway_bot.url == "wss://gateway.discord.gg"
        assert gateway_bot.shard_count == 1
        # SessionStartLimit
        assert isinstance(gateway_bot.session_start_limit, gateway_models.SessionStartLimit)
        assert gateway_bot.session_start_limit.max_concurrency == 5
        assert gateway_bot.session_start_limit.total == 1000
        assert gateway_bot.session_start_limit.remaining == 991
        assert gateway_bot.session_start_limit.reset_after == datetime.timedelta(milliseconds=14170186)

    ################
    # GUILD MODELS #
    ################

    @pytest.fixture()
    def guild_embed_payload(self):
        return {"channel_id": "123123123", "enabled": True}

    def test_deserialize_widget_embed(self, entity_factory_impl, mock_app, guild_embed_payload):
        guild_embed = entity_factory_impl.deserialize_guild_widget(guild_embed_payload)
        assert guild_embed.app is mock_app
        assert guild_embed.channel_id == 123123123
        assert guild_embed.is_enabled is True
        assert isinstance(guild_embed, guild_models.GuildWidget)

    def test_deserialize_guild_embed_with_null_fields(self, entity_factory_impl, mock_app):
        assert entity_factory_impl.deserialize_guild_widget({"channel_id": None, "enabled": True}).channel_id is None

    @pytest.fixture()
    def guild_welcome_screen_payload(self):
        return {
            "description": "What does the fox say? Nico Nico Nico NIIIIIIIIIIIIIIIIIIIIIII!!!!",
            "welcome_channels": [
                {
                    "channel_id": "87656344532234",
                    "description": "Follow for nothing",
                    "emoji_id": None,
                    "emoji_name": "📡",
                },
                {
                    "channel_id": "89563452341234",
                    "description": "Get help with cats",
                    "emoji_id": 31231351234,
                    "emoji_name": "dogGoesMeow",
                },
                {
                    "channel_id": "89563452341234",
                    "description": "Get help with cats",
                    "emoji_id": None,
                    "emoji_name": None,
                },
                {"channel_id": "92929292929", "description": "hi there", "emoji_id": "49494949", "emoji_name": None},
            ],
        }

    def test_deserialize_welcome_screen(self, entity_factory_impl, mock_app, guild_welcome_screen_payload):
        welcome_screen = entity_factory_impl.deserialize_welcome_screen(guild_welcome_screen_payload)

        assert welcome_screen.description == "What does the fox say? Nico Nico Nico NIIIIIIIIIIIIIIIIIIIIIII!!!!"

        assert welcome_screen.channels[0].channel_id == 87656344532234
        assert welcome_screen.channels[0].description == "Follow for nothing"

        assert isinstance(welcome_screen.channels[0].emoji_name, emoji_models.UnicodeEmoji)
        assert welcome_screen.channels[0].emoji_name == "📡"
        assert welcome_screen.channels[0].emoji_id is None

        assert not isinstance(welcome_screen.channels[1].emoji_name, emoji_models.UnicodeEmoji)
        assert welcome_screen.channels[1].emoji_name == "dogGoesMeow"
        assert welcome_screen.channels[1].emoji_id == 31231351234

        assert welcome_screen.channels[2].emoji_name is None
        assert welcome_screen.channels[2].emoji_id is None

        assert welcome_screen.channels[3].emoji_name is None
        assert welcome_screen.channels[3].emoji_id == 49494949

    def test_serialize_welcome_channel_with_custom_emoji(self, entity_factory_impl, mock_app):
        channel = guild_models.WelcomeChannel(
            channel_id=snowflakes.Snowflake(431231),
            description="meow",
            emoji_id=snowflakes.Snowflake(564123),
            emoji_name="boom",
        )
        result = entity_factory_impl.serialize_welcome_channel(channel)

        assert result == {"channel_id": "431231", "description": "meow", "emoji_id": "564123"}

    def test_serialize_welcome_channel_with_unicode_emoji(self, entity_factory_impl, mock_app):
        channel = guild_models.WelcomeChannel(
            channel_id=snowflakes.Snowflake(4312311),
            description="meow1",
            emoji_name=emoji_models.UnicodeEmoji("a"),
            emoji_id=None,
        )
        result = entity_factory_impl.serialize_welcome_channel(channel)

        assert result == {"channel_id": "4312311", "description": "meow1", "emoji_name": "a"}

    def test_serialize_welcome_channel_with_no_emoji(self, entity_factory_impl, mock_app):
        channel = guild_models.WelcomeChannel(
            channel_id=snowflakes.Snowflake(4312312), description="meow2", emoji_id=None, emoji_name=None
        )
        result = entity_factory_impl.serialize_welcome_channel(channel)

        assert result == {"channel_id": "4312312", "description": "meow2"}

    @pytest.fixture()
    def member_payload(self, user_payload):
        return {
            "nick": "foobarbaz",
            "roles": ["11111", "22222", "33333", "44444"],
            "joined_at": "2015-04-26T06:26:56.936000+00:00",
            "premium_since": "2019-05-17T06:26:56.936000+00:00",
            "deaf": False,
            "mute": True,
            "pending": False,
            "user": user_payload,
        }

    def test_deserialize_member(self, entity_factory_impl, mock_app, member_payload, user_payload):
        member_payload = {**member_payload, "guild_id": "76543325"}
        member = entity_factory_impl.deserialize_member(member_payload)
        assert member.app is mock_app
        assert member.guild_id == 76543325
        assert member.user == entity_factory_impl.deserialize_user(user_payload)
        assert member.nickname == "foobarbaz"
        assert member.role_ids == [11111, 22222, 33333, 44444, 76543325]
        assert member.joined_at == datetime.datetime(2015, 4, 26, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc)
        assert member.premium_since == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc)
        assert member.is_deaf is False
        assert member.is_mute is True
        assert member.is_pending is False
        assert isinstance(member, guild_models.Member)

    def test_deserialize_member_when_guild_id_already_in_role_array(
        self, entity_factory_impl, mock_app, member_payload, user_payload
    ):
        # While this isn't a legitimate case based on the current behaviour of the API, we still want to cover this
        # to ensure no duplication occurs.
        member_payload = {**member_payload, "guild_id": "76543325"}
        member_payload["roles"] = [11111, 22222, 76543325, 33333, 44444]
        member = entity_factory_impl.deserialize_member(member_payload)
        assert member.app is mock_app
        assert member.guild_id == 76543325
        assert member.user == entity_factory_impl.deserialize_user(user_payload)
        assert member.nickname == "foobarbaz"
        assert member.role_ids == [11111, 22222, 76543325, 33333, 44444]
        assert member.joined_at == datetime.datetime(2015, 4, 26, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc)
        assert member.premium_since == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc)
        assert member.is_deaf is False
        assert member.is_mute is True
        assert isinstance(member, guild_models.Member)

    def test_deserialize_member_with_null_fields(self, entity_factory_impl, user_payload):
        member = entity_factory_impl.deserialize_member(
            {
                "nick": None,
                "roles": ["11111", "22222", "33333", "44444"],
                "joined_at": "2015-04-26T06:26:56.936000+00:00",
                "premium_since": None,
                "deaf": False,
                "mute": True,
                "pending": False,
                "user": user_payload,
                "guild_id": "123123453234",
            }
        )
        assert member.nickname is None
        assert member.premium_since is None
        assert isinstance(member, guild_models.Member)

    def test_deserialize_member_with_undefined_fields(self, entity_factory_impl, user_payload):
        member = entity_factory_impl.deserialize_member(
            {
                "roles": ["11111", "22222", "33333", "44444"],
                "joined_at": "2015-04-26T06:26:56.936000+00:00",
                "user": user_payload,
                "guild_id": "123123123",
                "premium_since": "2019-05-17T06:26:56.936000+00:00",
            }
        )
        assert member.nickname is None
        assert member.is_deaf is undefined.UNDEFINED
        assert member.is_mute is undefined.UNDEFINED
        assert member.is_pending is undefined.UNDEFINED
        assert member.premium_since == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc)

    def test_deserialize_member_with_passed_through_user_object_and_guild_id(self, entity_factory_impl):
        mock_user = mock.Mock(user_models.UserImpl)
        member = entity_factory_impl.deserialize_member(
            {
                "nick": "foobarbaz",
                "roles": ["11111", "22222", "33333", "44444"],
                "joined_at": "2015-04-26T06:26:56.936000+00:00",
                "premium_since": "2019-05-17T06:26:56.936000+00:00",
                "deaf": False,
                "mute": True,
            },
            user=mock_user,
            guild_id=snowflakes.Snowflake(64234),
        )
        assert member.user is mock_user
        assert member.guild_id == 64234

    @pytest.fixture()
    def guild_role_payload(self):
        return {
            "id": "41771983423143936",
            "name": "WE DEM BOYZZ!!!!!!",
            "color": 3_447_003,
            "hoist": True,
            "position": 0,
            "permissions": "66321471",
            "managed": False,
            "mentionable": False,
            "tags": {
                "bot_id": "123",
                "integration_id": "456",
                "premium_subscriber": None,
            },
        }

    def test_deserialize_role(self, entity_factory_impl, mock_app, guild_role_payload):
        guild_role = entity_factory_impl.deserialize_role(guild_role_payload, guild_id=snowflakes.Snowflake(76534453))
        assert guild_role.app is mock_app
        assert guild_role.id == 41771983423143936
        assert guild_role.guild_id == 76534453
        assert guild_role.name == "WE DEM BOYZZ!!!!!!"
        assert guild_role.color == color_models.Color(3_447_003)
        assert guild_role.is_hoisted is True
        assert guild_role.position == 0
        assert guild_role.permissions == permission_models.Permissions(66_321_471)
        assert guild_role.is_managed is False
        assert guild_role.is_mentionable is False
        assert guild_role.bot_id == 123
        assert guild_role.integration_id == 456
        assert guild_role.is_premium_subscriber_role is True
        assert isinstance(guild_role, guild_models.Role)

    def test_deserialize_role_with_missing_or_unset_fields(self, entity_factory_impl, guild_role_payload):
        guild_role_payload["tags"] = {}
        guild_role = entity_factory_impl.deserialize_role(guild_role_payload, guild_id=snowflakes.Snowflake(76534453))
        assert guild_role.bot_id is None
        assert guild_role.integration_id is None
        assert guild_role.is_premium_subscriber_role is False

    def test_deserialize_role_with_no_tags(self, entity_factory_impl, guild_role_payload):
        del guild_role_payload["tags"]
        guild_role = entity_factory_impl.deserialize_role(guild_role_payload, guild_id=snowflakes.Snowflake(76534453))
        assert guild_role.bot_id is None
        assert guild_role.integration_id is None
        assert guild_role.is_premium_subscriber_role is False

    def test_deserialize_partial_integration(self, entity_factory_impl, partial_integration_payload):
        partial_integration = entity_factory_impl.deserialize_partial_integration(partial_integration_payload)
        assert partial_integration.id == 4949494949
        assert partial_integration.name == "Blah blah"
        assert partial_integration.type == "twitch"
        assert isinstance(partial_integration, guild_models.PartialIntegration)
        # IntegrationAccount
        assert partial_integration.account.id == "543453"
        assert partial_integration.account.name == "Blam"
        assert isinstance(partial_integration.account, guild_models.IntegrationAccount)

    @pytest.fixture()
    def integration_payload(self, user_payload):
        return {
            "id": "420",
            "name": "blaze it",
            "type": "youtube",
            "account": {"id": "6969", "name": "Blaze it"},
            "guild_id": "9292929292",
            "enabled": True,
            "syncing": False,
            "revoked": True,
            "role_id": "98494949",
            "enable_emoticons": False,
            "expire_behavior": 1,
            "expire_grace_period": 7,
            "user": user_payload,
            "synced_at": "2015-04-26T06:26:56.936000+00:00",
            "subscriber_count": 69,
            "application": {
                "id": "123",
                "name": "some bot",
                "icon": "123abc",
                "summary": "same as desc",
                "description": "same as desc2",
                "bot": {
                    "id": "456",
                    "username": "some rando bot",
                    "avatar": "123456avc",
                    "discriminator": "6127",
                    "bot": True,
                },
            },
        }

    def test_deserialize_integration(self, entity_factory_impl, integration_payload, user_payload):
        integration = entity_factory_impl.deserialize_integration(integration_payload)
        assert integration.id == 420
        assert integration.guild_id == 9292929292
        assert integration.name == "blaze it"
        assert integration.type == guild_models.IntegrationType.YOUTUBE
        # IntegrationAccount
        assert integration.account.id == "6969"
        assert integration.account.name == "Blaze it"
        assert isinstance(integration.account, guild_models.IntegrationAccount)

        assert integration.is_enabled is True
        assert integration.is_syncing is False
        assert integration.is_revoked is True
        assert integration.role_id == 98494949
        assert integration.is_emojis_enabled is False
        assert integration.expire_behavior == guild_models.IntegrationExpireBehaviour.KICK
        assert integration.expire_grace_period == datetime.timedelta(days=7)
        assert integration.user == entity_factory_impl.deserialize_user(user_payload)
        assert integration.last_synced_at == datetime.datetime(
            2015, 4, 26, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc
        )
        assert integration.subscriber_count == 69
        # IntegrationApplication
        assert integration.application.id == 123
        assert integration.application.name == "some bot"
        assert integration.application.icon_hash == "123abc"
        assert integration.application.summary == "same as desc"
        assert integration.application.description == "same as desc2"
        assert integration.application.bot == entity_factory_impl.deserialize_user(
            {
                "id": "456",
                "username": "some rando bot",
                "avatar": "123456avc",
                "discriminator": "6127",
                "bot": True,
            }
        )
        assert isinstance(integration, guild_models.Integration)

    def test_deserialize_guild_integration_with_null_and_unset_fields(self, entity_factory_impl):
        integration = entity_factory_impl.deserialize_integration(
            {
                "id": "420",
                "name": "blaze it",
                "type": "youtube",
                "account": {"id": "6969", "name": "Blaze it"},
                "enabled": True,
                "role_id": None,
                "synced_at": None,
            },
            guild_id=snowflakes.Snowflake(383838383883),
        )
        assert integration.guild_id == 383838383883
        assert integration.is_emojis_enabled is None
        assert integration.role_id is None
        assert integration.last_synced_at is None
        assert integration.expire_grace_period is None
        assert integration.expire_behavior is None
        assert integration.user is None
        assert integration.application is None
        assert integration.is_revoked is None
        assert integration.is_syncing is None
        assert integration.subscriber_count is None

    def test_deserialize_guild_integration_with_unset_bot(self, entity_factory_impl):
        integration = entity_factory_impl.deserialize_integration(
            {
                "id": "420",
                "guild_id": "929292929",
                "name": "blaze it",
                "type": "youtube",
                "account": {"id": "6969", "name": "Blaze it"},
                "enabled": True,
                "role_id": None,
                "synced_at": None,
                "application": {
                    "id": 123,
                    "name": "some bot",
                    "icon": "123abc",
                    "summary": "same as desc",
                    "description": "same as desc2",
                    "cover_image": "SMKLdiosa89123u",
                    "primary_sku_id": "499494949494994",
                },
            }
        )
        assert integration.application.bot is None

    @pytest.fixture()
    def guild_member_ban_payload(self, user_payload):
        return {"reason": "Get nyaa'ed", "user": user_payload}

    def test_deserialize_guild_member_ban(self, entity_factory_impl, guild_member_ban_payload, user_payload):
        member_ban = entity_factory_impl.deserialize_guild_member_ban(guild_member_ban_payload)
        assert member_ban.reason == "Get nyaa'ed"
        assert member_ban.user == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(member_ban, guild_models.GuildBan)

    def test_deserialize_guild_member_ban_with_null_fields(self, entity_factory_impl, user_payload):
        assert entity_factory_impl.deserialize_guild_member_ban({"reason": None, "user": user_payload}).reason is None

    @pytest.fixture()
    def guild_preview_payload(self, known_custom_emoji_payload):
        return {
            "id": "152559372126519269",
            "name": "Isopropyl",
            "icon": "d4a983885dsaa7691ce8bcaaf945a",
            "splash": "dsa345tfcdg54b",
            "discovery_splash": "lkodwaidi09239uid",
            "emojis": [known_custom_emoji_payload],
            "features": ["DISCOVERABLE", "FORCE_RELAY"],
            "approximate_member_count": 69,
            "approximate_presence_count": 42,
            "description": "A DESCRIPTION.",
        }

    def test_deserialize_guild_preview(
        self, entity_factory_impl, mock_app, guild_preview_payload, known_custom_emoji_payload
    ):
        guild_preview = entity_factory_impl.deserialize_guild_preview(guild_preview_payload)
        assert guild_preview.app is mock_app
        assert guild_preview.id == 152559372126519269
        assert guild_preview.name == "Isopropyl"
        assert guild_preview.icon_hash == "d4a983885dsaa7691ce8bcaaf945a"
        assert guild_preview.features == [guild_models.GuildFeature.DISCOVERABLE, "FORCE_RELAY"]
        assert guild_preview.splash_hash == "dsa345tfcdg54b"
        assert guild_preview.discovery_splash_hash == "lkodwaidi09239uid"
        assert guild_preview.emojis == {
            12345: entity_factory_impl.deserialize_known_custom_emoji(
                known_custom_emoji_payload, guild_id=snowflakes.Snowflake(152559372126519269)
            )
        }
        assert guild_preview.approximate_member_count == 69
        assert guild_preview.approximate_active_member_count == 42
        assert guild_preview.description == "A DESCRIPTION."
        assert isinstance(guild_preview, guild_models.GuildPreview)

    def test_deserialize_guild_preview_with_null_fields(self, entity_factory_impl, mock_app, guild_preview_payload):
        guild_preview = entity_factory_impl.deserialize_guild_preview(
            {
                "id": "152559372126519269",
                "name": "Isopropyl",
                "icon": None,
                "splash": None,
                "discovery_splash": None,
                "emojis": [],
                "features": ["DISCOVERABLE", "FORCE_RELAY"],
                "approximate_member_count": 69,
                "approximate_presence_count": 42,
                "description": None,
            }
        )
        assert guild_preview.icon_hash is None
        assert guild_preview.splash_hash is None
        assert guild_preview.discovery_splash_hash is None
        assert guild_preview.description is None

    @pytest.fixture()
    def deserialize_rest_guild_payload(
        self,
        known_custom_emoji_payload,
        guild_role_payload,
    ):
        return {
            "afk_channel_id": "99998888777766",
            "afk_timeout": 1200,
            "application_id": "39494949",
            "approximate_member_count": 15,
            "approximate_presence_count": 7,
            "banner": "1a2b3c",
            "default_message_notifications": 1,
            "description": "This is a server I guess, its a bit crap though",
            "discovery_splash": "famfamFAMFAMfam",
            "embed_channel_id": "9439394949",
            "embed_enabled": True,
            "emojis": [known_custom_emoji_payload],
            "explicit_content_filter": 2,
            "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
            "icon": "1a2b3c4d",
            "id": "265828729970753537",
            "max_members": 25000,
            "max_presences": 250,
            "max_video_channel_users": 25,
            "mfa_level": 1,
            "name": "L33t guild",
            "owner_id": "6969696",
            "preferred_locale": "en-GB",
            "premium_subscription_count": 1,
            "premium_tier": 2,
            "public_updates_channel_id": "33333333",
            "roles": [guild_role_payload],
            "rules_channel_id": "42042069",
            "splash": "0ff0ff0ff",
            "system_channel_flags": 3,
            "system_channel_id": "19216801",
            "vanity_url_code": "loool",
            "verification_level": 4,
            "widget_channel_id": "9439394949",
            "widget_enabled": True,
            "nsfw_level": 0,
        }

    def test_deserialize_rest_guild(
        self,
        entity_factory_impl,
        mock_app,
        deserialize_rest_guild_payload,
        known_custom_emoji_payload,
        guild_role_payload,
    ):
        guild = entity_factory_impl.deserialize_rest_guild(deserialize_rest_guild_payload)
        assert guild.app is mock_app
        assert guild.id == 265828729970753537
        assert guild.name == "L33t guild"
        assert guild.icon_hash == "1a2b3c4d"
        assert guild.features == [
            guild_models.GuildFeature.ANIMATED_ICON,
            guild_models.GuildFeature.MORE_EMOJI,
            guild_models.GuildFeature.NEWS,
            "SOME_UNDOCUMENTED_FEATURE",
        ]
        assert guild.splash_hash == "0ff0ff0ff"
        assert guild.discovery_splash_hash == "famfamFAMFAMfam"
        assert guild.owner_id == 6969696
        assert guild.afk_channel_id == 99998888777766
        assert guild.afk_timeout == datetime.timedelta(seconds=1200)
        assert guild.verification_level == guild_models.GuildVerificationLevel.VERY_HIGH
        assert guild.default_message_notifications == guild_models.GuildMessageNotificationsLevel.ONLY_MENTIONS
        assert guild.explicit_content_filter == guild_models.GuildExplicitContentFilterLevel.ALL_MEMBERS
        assert guild.roles == {
            41771983423143936: entity_factory_impl.deserialize_role(
                guild_role_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            )
        }
        assert guild.emojis == {
            12345: entity_factory_impl.deserialize_known_custom_emoji(
                known_custom_emoji_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            )
        }
        assert guild.mfa_level == guild_models.GuildMFALevel.ELEVATED
        assert guild.application_id == 39494949
        assert guild.widget_channel_id == 9439394949
        assert guild.is_widget_enabled is True
        assert guild.system_channel_id == 19216801
        assert guild.system_channel_flags == guild_models.GuildSystemChannelFlag(3)
        assert guild.rules_channel_id == 42042069
        assert guild.max_presences == 250
        assert guild.max_members == 25000
        assert guild.max_video_channel_users == 25
        assert guild.vanity_url_code == "loool"
        assert guild.description == "This is a server I guess, its a bit crap though"
        assert guild.banner_hash == "1a2b3c"
        assert guild.premium_tier == guild_models.GuildPremiumTier.TIER_2
        assert guild.premium_subscription_count == 1
        assert guild.preferred_locale == "en-GB"
        assert guild.public_updates_channel_id == 33333333
        assert guild.approximate_member_count == 15
        assert guild.approximate_active_member_count == 7
        assert guild.nsfw_level == guild_models.GuildNSFWLevel.DEFAULT

    def test_deserialize_rest_guild_with_unset_fields(self, entity_factory_impl):
        guild = entity_factory_impl.deserialize_rest_guild(
            {
                "afk_channel_id": "99998888777766",
                "afk_timeout": 1200,
                "application_id": "39494949",
                "banner": "1a2b3c",
                "default_message_notifications": 1,
                "description": "This is a server I guess, its a bit crap though",
                "discovery_splash": "famfamFAMFAMfam",
                "emojis": [],
                "explicit_content_filter": 2,
                "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
                "icon": "1a2b3c4d",
                "id": "265828729970753537",
                "mfa_level": 1,
                "nsfw_level": 0,
                "name": "L33t guild",
                "owner_id": "6969696",
                "preferred_locale": "en-GB",
                "premium_tier": 2,
                "public_updates_channel_id": "33333333",
                "roles": [],
                "rules_channel_id": "42042069",
                "splash": "0ff0ff0ff",
                "system_channel_flags": 3,
                "system_channel_id": "19216801",
                "vanity_url_code": "loool",
                "verification_level": 4,
                "max_presences": 8,
                "max_members": 9,
            }
        )
        assert guild.max_video_channel_users is None
        assert guild.premium_subscription_count is None
        assert guild.widget_channel_id is None
        assert guild.is_widget_enabled is None
        assert guild.approximate_active_member_count is None
        assert guild.approximate_member_count is None

    def test_deserialize_rest_guild_with_null_fields(self, entity_factory_impl):
        guild = entity_factory_impl.deserialize_rest_guild(
            {
                "afk_channel_id": None,
                "afk_timeout": 1200,
                "application_id": None,
                "approximate_member_count": 15,
                "approximate_presence_count": 7,
                "banner": None,
                "default_message_notifications": 1,
                "description": None,
                "discovery_splash": None,
                "embed_channel_id": None,
                "embed_enabled": True,
                "emojis": [],
                "explicit_content_filter": 2,
                "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
                "icon": None,
                "id": "265828729970753537",
                "max_members": 25000,
                "max_presences": None,
                "max_video_channel_users": 25,
                "mfa_level": 1,
                "nsfw_level": 0,
                "name": "L33t guild",
                "owner_id": "6969696",
                "preferred_locale": "en-GB",
                "premium_subscription_count": None,
                "premium_tier": 2,
                "public_updates_channel_id": None,
                "roles": [],
                "rules_channel_id": None,
                "splash": None,
                "system_channel_flags": 3,
                "system_channel_id": None,
                "vanity_url_code": None,
                "verification_level": 4,
                "voice_states": [],
                "widget_channel_id": None,
                "widget_enabled": True,
            }
        )
        assert guild.icon_hash is None
        assert guild.splash_hash is None
        assert guild.discovery_splash_hash is None
        assert guild.afk_channel_id is None
        assert guild.application_id is None
        assert guild.widget_channel_id is None
        assert guild.system_channel_id is None
        assert guild.rules_channel_id is None
        assert guild.max_presences is None
        assert guild.vanity_url_code is None
        assert guild.description is None
        assert guild.banner_hash is None
        assert guild.premium_subscription_count is None
        assert guild.public_updates_channel_id is None

    @pytest.fixture()
    def deserialize_gateway_guild_payload(
        self,
        guild_text_channel_payload,
        guild_voice_channel_payload,
        guild_news_channel_payload,
        known_custom_emoji_payload,
        member_payload,
        member_presence_payload,
        guild_role_payload,
        voice_state_payload,
    ):
        return {
            "afk_channel_id": "99998888777766",
            "afk_timeout": 1200,
            "application_id": "39494949",
            "banner": "1a2b3c",
            "channels": [guild_text_channel_payload, guild_voice_channel_payload, guild_news_channel_payload],
            "default_message_notifications": 1,
            "description": "This is a server I guess, its a bit crap though",
            "discovery_splash": "famfamFAMFAMfam",
            "embed_channel_id": "9439394949",
            "embed_enabled": True,
            "emojis": [known_custom_emoji_payload],
            "explicit_content_filter": 2,
            "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
            "icon": "1a2b3c4d",
            "id": "265828729970753537",
            "joined_at": "2019-05-17T06:26:56.936000+00:00",
            "large": False,
            "max_members": 25000,
            "max_presences": 250,
            "max_video_channel_users": 25,
            "member_count": 14,
            "members": [member_payload],
            "mfa_level": 1,
            "name": "L33t guild",
            "owner_id": "6969696",
            "preferred_locale": "en-GB",
            "premium_subscription_count": 1,
            "premium_tier": 2,
            "presences": [member_presence_payload],
            "public_updates_channel_id": "33333333",
            "roles": [guild_role_payload],
            "rules_channel_id": "42042069",
            "splash": "0ff0ff0ff",
            "system_channel_flags": 3,
            "system_channel_id": "19216801",
            "unavailable": False,
            "vanity_url_code": "loool",
            "verification_level": 4,
            "voice_states": [voice_state_payload],
            "widget_channel_id": "9439394949",
            "widget_enabled": True,
            "nsfw_level": 0,
        }

    def test_deserialize_gateway_guild(
        self,
        entity_factory_impl,
        mock_app,
        deserialize_gateway_guild_payload,
        guild_text_channel_payload,
        guild_voice_channel_payload,
        guild_news_channel_payload,
        known_custom_emoji_payload,
        member_payload,
        member_presence_payload,
        guild_role_payload,
        voice_state_payload,
    ):
        guild_definition = entity_factory_impl.deserialize_gateway_guild(deserialize_gateway_guild_payload)
        guild = guild_definition.guild
        assert guild.app is mock_app
        assert guild.id == 265828729970753537
        assert guild.name == "L33t guild"
        assert guild.icon_hash == "1a2b3c4d"
        assert guild.features == [
            guild_models.GuildFeature.ANIMATED_ICON,
            guild_models.GuildFeature.MORE_EMOJI,
            guild_models.GuildFeature.NEWS,
            "SOME_UNDOCUMENTED_FEATURE",
        ]
        assert guild.splash_hash == "0ff0ff0ff"
        assert guild.discovery_splash_hash == "famfamFAMFAMfam"
        assert guild.owner_id == 6969696
        assert guild.afk_channel_id == 99998888777766
        assert guild.afk_timeout == datetime.timedelta(seconds=1200)
        assert guild.verification_level == guild_models.GuildVerificationLevel.VERY_HIGH
        assert guild.default_message_notifications == guild_models.GuildMessageNotificationsLevel.ONLY_MENTIONS
        assert guild.explicit_content_filter == guild_models.GuildExplicitContentFilterLevel.ALL_MEMBERS
        assert guild.mfa_level == guild_models.GuildMFALevel.ELEVATED
        assert guild.application_id == 39494949
        assert guild.widget_channel_id == 9439394949
        assert guild.is_widget_enabled is True
        assert guild.system_channel_id == 19216801
        assert guild.system_channel_flags == guild_models.GuildSystemChannelFlag(3)
        assert guild.rules_channel_id == 42042069
        assert guild.joined_at == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc)
        assert guild.is_large is False
        assert guild.member_count == 14
        assert guild.max_video_channel_users == 25
        assert guild.vanity_url_code == "loool"
        assert guild.description == "This is a server I guess, its a bit crap though"
        assert guild.banner_hash == "1a2b3c"
        assert guild.premium_tier == guild_models.GuildPremiumTier.TIER_2
        assert guild.premium_subscription_count == 1
        assert guild.preferred_locale == "en-GB"
        assert guild.public_updates_channel_id == 33333333
        assert guild.nsfw_level == guild_models.GuildNSFWLevel.DEFAULT

        assert guild_definition.roles == {
            41771983423143936: entity_factory_impl.deserialize_role(
                guild_role_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            )
        }
        assert guild_definition.emojis == {
            12345: entity_factory_impl.deserialize_known_custom_emoji(
                known_custom_emoji_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            )
        }
        assert guild_definition.members == {
            115590097100865541: entity_factory_impl.deserialize_member(
                member_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            )
        }
        assert guild_definition.channels == {
            123: entity_factory_impl.deserialize_guild_text_channel(
                guild_text_channel_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            ),
            555: entity_factory_impl.deserialize_guild_voice_channel(
                guild_voice_channel_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            ),
            7777: entity_factory_impl.deserialize_guild_news_channel(
                guild_news_channel_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            ),
        }
        assert guild_definition.presences == {
            115590097100865541: entity_factory_impl.deserialize_member_presence(
                member_presence_payload, guild_id=snowflakes.Snowflake(265828729970753537)
            )
        }
        assert guild_definition.voice_states == {
            115590097100865541: entity_factory_impl.deserialize_voice_state(
                voice_state_payload,
                guild_id=snowflakes.Snowflake(265828729970753537),
                member=entity_factory_impl.deserialize_member(
                    member_payload,
                    guild_id=snowflakes.Snowflake(265828729970753537),
                ),
            )
        }

    def test_deserialize_gateway_guild_with_unset_fields(self, entity_factory_impl):
        guild_definition = entity_factory_impl.deserialize_gateway_guild(
            {
                "afk_channel_id": "99998888777766",
                "afk_timeout": 1200,
                "application_id": "39494949",
                "banner": "1a2b3c",
                "default_message_notifications": 1,
                "description": "This is a server I guess, its a bit crap though",
                "discovery_splash": "famfamFAMFAMfam",
                "emojis": [],
                "explicit_content_filter": 2,
                "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
                "icon": "1a2b3c4d",
                "id": "265828729970753537",
                "mfa_level": 1,
                "name": "L33t guild",
                "owner_id": "6969696",
                "preferred_locale": "en-GB",
                "premium_tier": 2,
                "public_updates_channel_id": "33333333",
                "roles": [],
                "rules_channel_id": "42042069",
                "splash": "0ff0ff0ff",
                "system_channel_flags": 3,
                "system_channel_id": "19216801",
                "vanity_url_code": "loool",
                "verification_level": 4,
                "nsfw_level": 0,
            }
        )
        guild = guild_definition.guild
        assert guild.joined_at is None
        assert guild.is_large is None
        assert guild.max_video_channel_users is None
        assert guild.member_count is None
        assert guild.premium_subscription_count is None
        assert guild.widget_channel_id is None
        assert guild.is_widget_enabled is None
        assert guild_definition.channels is None
        assert guild_definition.members is None
        assert guild_definition.presences is None
        assert guild_definition.voice_states is None

    def test_deserialize_gateway_guild_with_null_fields(self, entity_factory_impl):
        guild_definition = entity_factory_impl.deserialize_gateway_guild(
            {
                "afk_channel_id": None,
                "afk_timeout": 1200,
                "application_id": None,
                "banner": None,
                "channels": [],
                "default_message_notifications": 1,
                "description": None,
                "discovery_splash": None,
                "embed_channel_id": None,
                "embed_enabled": True,
                "emojis": [],
                "explicit_content_filter": 2,
                "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
                "icon": None,
                "id": "265828729970753537",
                "joined_at": "2019-05-17T06:26:56.936000+00:00",
                "large": False,
                "max_members": 25000,
                "max_presences": None,
                "max_video_channel_users": 25,
                "member_count": 14,
                "members": [],
                "mfa_level": 1,
                "name": "L33t guild",
                "owner_id": "6969696",
                "permissions": 66_321_471,
                "preferred_locale": "en-GB",
                "premium_subscription_count": None,
                "premium_tier": 2,
                "presences": [],
                "public_updates_channel_id": None,
                "roles": [],
                "rules_channel_id": None,
                "splash": None,
                "system_channel_flags": 3,
                "system_channel_id": None,
                "unavailable": False,
                "vanity_url_code": None,
                "verification_level": 4,
                "voice_states": [],
                "widget_channel_id": None,
                "widget_enabled": True,
                "nsfw_level": 0,
            }
        )
        guild = guild_definition.guild
        assert guild.icon_hash is None
        assert guild.splash_hash is None
        assert guild.discovery_splash_hash is None
        assert guild.afk_channel_id is None
        assert guild.application_id is None
        assert guild.widget_channel_id is None
        assert guild.system_channel_id is None
        assert guild.rules_channel_id is None
        assert guild.vanity_url_code is None
        assert guild.description is None
        assert guild.banner_hash is None
        assert guild.premium_subscription_count is None
        assert guild.public_updates_channel_id is None

    def test_deserialize_gateway_guild_ignores_unrecognised_channels(
        self, entity_factory_impl, deserialize_gateway_guild_payload
    ):
        deserialize_gateway_guild_payload["channels"] = [{"id": 123, "type": 1000}]
        guild_definition = entity_factory_impl.deserialize_gateway_guild(deserialize_gateway_guild_payload)

        assert guild_definition.channels == {}

    ######################
    # INTERACTION MODELS #
    ######################

    @pytest.fixture()
    def command_payload(self):
        return {
            "id": "1231231231",
            "application_id": "12354123",
            "guild_id": "49949494",
            "name": "good name",
            "description": "very good description",
            "default_permission": False,
            "options": [
                {
                    "type": 1,
                    "name": "a dumb name",
                    "description": "42",
                    "required": True,
                    "options": [
                        {
                            "type": 6,
                            "name": "a name",
                            "description": "84",
                            "choices": [{"name": "a choice", "value": "4 u"}],
                        }
                    ],
                }
            ],
        }

    def test_deserialize_command(self, entity_factory_impl, mock_app, command_payload):
        command = entity_factory_impl.deserialize_command(payload=command_payload)

        assert command.app is mock_app
        assert command.id == 1231231231
        assert command.application_id == 12354123
        assert command.guild_id == 49949494
        assert command.name == "good name"
        assert command.description == "very good description"
        assert command.default_permission is False

        # CommandOption
        assert len(command.options) == 1
        option = command.options[0]
        assert option.type is commands.OptionType.SUB_COMMAND
        assert option.name == "a dumb name"
        assert option.description == "42"
        assert option.is_required is True
        assert option.description == "42"
        assert option.choices is None
        assert len(option.options) == 1

        suboption = option.options[0]
        assert suboption.type is commands.OptionType.USER
        assert suboption.name == "a name"
        assert suboption.description == "84"
        assert suboption.is_required is False
        assert suboption.options is None

        # CommandChoice
        assert len(suboption.choices) == 1
        choice = suboption.choices[0]
        assert choice.name == "a choice"
        assert choice.value == "4 u"
        assert isinstance(choice, commands.CommandChoice)

        assert isinstance(suboption, commands.CommandOption)
        assert isinstance(option, commands.CommandOption)
        assert isinstance(command, commands.Command)

    def test_deserialize_command_with_passed_through_guild_id(self, entity_factory_impl):
        payload = {
            "id": "1231231231",
            "application_id": "12354123",
            "name": "good name",
            "description": "very good description",
            "options": [],
        }

        command = entity_factory_impl.deserialize_command(payload, guild_id=123123)

        assert command.guild_id == 123123

    def test_deserialize_command_with_null_and_unset_values(self, entity_factory_impl):
        payload = {
            "id": "1231231231",
            "application_id": "12354123",
            "guild_id": "49949494",
            "name": "good name",
            "description": "very good description",
            "options": [],
        }

        command = entity_factory_impl.deserialize_command(payload)

        assert command.options is None
        assert command.default_permission is True
        assert isinstance(command, commands.Command)

    @pytest.fixture()
    def guild_command_permissions_payload(self):
        return {
            "id": "123321",
            "application_id": "431321123",
            "guild_id": "323223322332",
            "permissions": [{"id": "22222", "type": 1, "permission": True}],
        }

    def test_deserialize_guild_command_permissions(self, entity_factory_impl, guild_command_permissions_payload):
        command = entity_factory_impl.deserialize_guild_command_permissions(guild_command_permissions_payload)

        assert command.command_id == 123321
        assert command.application_id == 431321123
        assert command.guild_id == 323223322332

        # CommandPermission
        assert len(command.permissions) == 1
        permission = command.permissions[0]
        assert permission.id == 22222
        assert permission.type is commands.CommandPermissionType.ROLE
        assert permission.has_access is True
        assert isinstance(permission, commands.CommandPermission)

    def test_serialize_command_permission(self, entity_factory_impl):
        command = commands.CommandPermission(type=commands.CommandPermissionType.ROLE, has_access=True, id=123321)

        assert entity_factory_impl.serialize_command_permission(command) == {
            "type": 1,
            "id": "123321",
            "permission": True,
        }

    @pytest.fixture()
    def partial_interaction_payload(self):
        return {
            "id": "795459528803745843",
            "token": "-- token redacted --",
            "type": 1,
            "version": 1,
            "application_id": "1",
        }

    def test_deserialize_partial_interaction(self, mock_app, entity_factory_impl, partial_interaction_payload):
        interaction = entity_factory_impl.deserialize_partial_interaction(partial_interaction_payload)

        assert interaction.app is mock_app
        assert interaction.id == 795459528803745843
        assert interaction.token == "-- token redacted --"
        assert interaction.type == 1
        assert interaction.version == 1
        assert interaction.application_id == 1
        assert type(interaction) is base_interactions.PartialInteraction

    @pytest.fixture()
    def command_interaction_payload(self, member_payload, user_payload, guild_role_payload):
        member_payload["permissions"] = "47"
        return {
            "id": "3490190239012093",
            "type": 2,
            "guild_id": "43123123",
            "data": {
                "id": "43123123",
                "name": "okokokok",
                "options": [
                    {"name": "an option", "type": 1, "options": [{"name": "go ice", "type": 4, "value": "42"}]},
                ],
                "resolved": {
                    "channels": {
                        "695382395666300958": {
                            "id": "695382395666300958",
                            "name": "discord-announcements",
                            "permissions": "17179869183",
                            "type": 0,
                        }
                    },
                    "members": {
                        "115590097100865541": {
                            "is_pending": False,
                            "joined_at": "2020-09-27T22:58:10.282000+00:00",
                            "nick": "Snab",
                            "pending": False,
                            "permissions": "17179869183",
                            "premium_since": "2020-10-01T23:06:10.431000+00:00",
                            "roles": [
                                "582345963851743243",
                                "582689893965365248",
                                "734164204679856290",
                                "757331666388910181",
                            ],
                        }
                    },
                    "roles": {"41771983423143936": guild_role_payload},
                    "users": {"115590097100865541": user_payload},
                },
            },
            "channel_id": "49949494",
            "member": member_payload,
            "token": "moe cat girls",
            "version": 69420,
            "application_id": "76234234",
        }

    def test_deserialize_command_interaction(
        self, entity_factory_impl, mock_app, command_interaction_payload, user_payload, guild_role_payload
    ):
        interaction = entity_factory_impl.deserialize_command_interaction(command_interaction_payload)

        assert interaction.app is mock_app
        assert interaction.application_id == 76234234
        assert interaction.id == 3490190239012093
        assert interaction.type is base_interactions.InteractionType.APPLICATION_COMMAND
        assert interaction.token == "moe cat girls"
        assert interaction.version == 69420
        assert interaction.channel_id == 49949494
        assert interaction.guild_id == 43123123

        # InteractionMember
        assert interaction.member.app is mock_app
        assert interaction.member.guild_id == 43123123
        assert interaction.member.user == entity_factory_impl.deserialize_user(user_payload)
        assert interaction.member.nickname == "foobarbaz"
        assert interaction.member.role_ids == [11111, 22222, 33333, 44444, 43123123]
        assert interaction.member.joined_at == datetime.datetime(
            2015, 4, 26, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc
        )
        assert interaction.member.premium_since == datetime.datetime(
            2019, 5, 17, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc
        )
        assert interaction.member.is_deaf is False
        assert interaction.member.is_mute is True
        assert interaction.member.is_pending is False
        assert interaction.member.permissions == 47
        assert isinstance(interaction.member, base_interactions.InteractionMember)

        assert interaction.user is interaction.member.user
        assert interaction.command_id == 43123123
        assert interaction.command_name == "okokokok"

        # CommandInteractionOption
        assert len(interaction.options) == 1
        option = interaction.options[0]
        assert option.name == "an option"
        assert option.value is None
        assert option.type is commands.OptionType.SUB_COMMAND
        assert len(option.options) == 1
        sub_option = option.options[0]
        assert sub_option.name == "go ice"
        assert sub_option.value == "42"
        assert sub_option.type is commands.OptionType.INTEGER
        assert sub_option.options is None
        assert isinstance(sub_option, command_interactions.CommandInteractionOption)
        assert isinstance(option, command_interactions.CommandInteractionOption)

        # ResolvedOptionData
        assert len(interaction.resolved.channels) == 1
        channel = interaction.resolved.channels[695382395666300958]
        assert channel.type is channel_models.ChannelType.GUILD_TEXT
        assert channel.id == 695382395666300958
        assert channel.name == "discord-announcements"
        assert channel.permissions == permission_models.Permissions(17179869183)
        assert isinstance(channel, command_interactions.InteractionChannel)
        # InteractionMember
        assert len(interaction.resolved.members) == 1
        member = interaction.resolved.members[115590097100865541]
        assert member.id == 115590097100865541
        assert member.joined_at == datetime.datetime(2020, 9, 27, 22, 58, 10, 282000, tzinfo=datetime.timezone.utc)
        assert member.nickname == "Snab"
        assert member.guild_id == 43123123
        assert member.is_deaf is undefined.UNDEFINED
        assert member.is_mute is undefined.UNDEFINED
        assert member.is_pending is False
        assert member.premium_since == datetime.datetime(2020, 10, 1, 23, 6, 10, 431000, tzinfo=datetime.timezone.utc)
        assert member.role_ids == [
            582345963851743243,
            582689893965365248,
            734164204679856290,
            757331666388910181,
            43123123,
        ]
        assert member.user == entity_factory_impl.deserialize_user(user_payload)
        assert member.permissions == permission_models.Permissions(17179869183)
        assert isinstance(member, base_interactions.InteractionMember)

        assert interaction.resolved.roles == {
            41771983423143936: entity_factory_impl.deserialize_role(guild_role_payload, guild_id=43123123)
        }
        assert interaction.resolved.users == {115590097100865541: entity_factory_impl.deserialize_user(user_payload)}
        assert isinstance(interaction.resolved, command_interactions.ResolvedOptionData)

        assert isinstance(interaction, command_interactions.CommandInteraction)

    def test_deserialize_command_interaction_with_null_attributes(
        self, entity_factory_impl, mock_app, command_interaction_payload, user_payload
    ):
        del command_interaction_payload["guild_id"]
        del command_interaction_payload["member"]
        command_interaction_payload["user"] = user_payload
        del command_interaction_payload["data"]["options"]
        del command_interaction_payload["data"]["resolved"]

        interaction = entity_factory_impl.deserialize_command_interaction(command_interaction_payload)

        assert interaction.guild_id is None
        assert interaction.member is None
        assert interaction.user == entity_factory_impl.deserialize_user(user_payload)
        assert interaction.options is None
        assert interaction.resolved is None

    def test_deserialize_command_interaction_with_empty_resolved_resources(
        self, entity_factory_impl, mock_app, command_interaction_payload, user_payload
    ):
        del command_interaction_payload["data"]["resolved"]["channels"]
        del command_interaction_payload["data"]["resolved"]["members"]
        del command_interaction_payload["data"]["resolved"]["roles"]
        del command_interaction_payload["data"]["resolved"]["users"]
        # This makes sure the bool check to see if there's anything in resolve will still pass
        # to separate this case from it just not being provided
        command_interaction_payload["data"]["resolved"]["not a real field"] = 42

        interaction = entity_factory_impl.deserialize_command_interaction(command_interaction_payload)

        assert interaction.resolved.channels == {}
        assert interaction.resolved.members == {}
        assert interaction.resolved.roles == {}
        assert interaction.resolved.users == {}

    def test_deserialize_interaction_returns_expected_type(self, entity_factory_impl, command_interaction_payload):
        for payload, expected_type in [(command_interaction_payload, command_interactions.CommandInteraction)]:
            assert type(entity_factory_impl.deserialize_interaction(payload)) is expected_type

    def test_deserialize_interaction_handles_unknown_type(self, entity_factory_impl):
        with pytest.raises(errors.UnrecognisedEntityError):
            entity_factory_impl.deserialize_interaction({"type": -999})

    def test_serialize_command_option_with_choices(self, entity_factory_impl):
        option = commands.CommandOption(
            type=commands.OptionType.INTEGER,
            name="a name",
            description="go away",
            is_required=True,
            choices=[commands.CommandChoice(name="a", value="choice")],
            options=None,
        )

        result = entity_factory_impl.serialize_command_option(option)

        assert result == {
            "type": 4,
            "name": "a name",
            "description": "go away",
            "required": True,
            "choices": [{"name": "a", "value": "choice"}],
        }

    def test_serialize_command_option_with_options(self, entity_factory_impl):
        option = commands.CommandOption(
            type=commands.OptionType.SUB_COMMAND,
            name="a name",
            description="go away",
            is_required=True,
            choices=None,
            options=[
                commands.CommandOption(
                    type=commands.OptionType.STRING,
                    name="go home",
                    description="you're drunk",
                    is_required=False,
                    choices=[commands.CommandChoice(name="boo", value="hoo")],
                    options=None,
                )
            ],
        )

        result = entity_factory_impl.serialize_command_option(option)

        assert result == {
            "type": 1,
            "name": "a name",
            "description": "go away",
            "required": True,
            "options": [
                {
                    "type": 3,
                    "description": "you're drunk",
                    "name": "go home",
                    "required": False,
                    "choices": [{"name": "boo", "value": "hoo"}],
                }
            ],
        }

    #################
    # INVITE MODELS #
    #################

    @pytest.fixture()
    def vanity_url_payload(self):
        return {"code": "iamacode", "uses": 42}

    def test_deserialize_vanity_url(self, entity_factory_impl, mock_app, vanity_url_payload):
        vanity_url = entity_factory_impl.deserialize_vanity_url(vanity_url_payload)
        assert vanity_url.app is mock_app
        assert vanity_url.code == "iamacode"
        assert vanity_url.uses == 42
        assert isinstance(vanity_url, invite_models.VanityURL)

    @pytest.fixture()
    def alternative_user_payload(self):
        return {"id": "1231231", "username": "soad", "discriminator": "3333", "avatar": None}

    @pytest.fixture()
    def invite_payload(
        self,
        partial_channel_payload,
        user_payload,
        alternative_user_payload,
        guild_welcome_screen_payload,
        invite_application_payload,
    ):
        return {
            "code": "aCode",
            "guild": {
                "id": "56188492224814744",
                "name": "Testin' Your Scene",
                "splash": "aSplashForSure",
                "banner": "aBannerForSure",
                "description": "Describe me cute kitty.",
                "icon": "bb71f469c158984e265093a81b3397fb",
                "features": ["FORCE_RELAY"],
                "verification_level": 2,
                "vanity_url_code": "I-am-very-vain",
                "welcome_screen": guild_welcome_screen_payload,
                "nsfw_level": 1,
            },
            "channel": partial_channel_payload,
            "inviter": user_payload,
            "target_type": 1,
            "target_user": alternative_user_payload,
            "target_application": invite_application_payload,
            "approximate_presence_count": 42,
            "approximate_member_count": 84,
            "expires_at": "2021-05-08T00:15:24.534000+00:00",
        }

    def test_deserialize_invite(
        self,
        entity_factory_impl,
        mock_app,
        invite_payload,
        partial_channel_payload,
        user_payload,
        guild_welcome_screen_payload,
        alternative_user_payload,
        application_payload,
    ):
        invite = entity_factory_impl.deserialize_invite(invite_payload)
        assert invite.app is mock_app
        assert invite.code == "aCode"
        # InviteGuild
        assert invite.guild.id == 56188492224814744
        assert invite.guild.name == "Testin' Your Scene"
        assert invite.guild.icon_hash == "bb71f469c158984e265093a81b3397fb"
        assert invite.guild.features == ["FORCE_RELAY"]
        assert invite.guild.splash_hash == "aSplashForSure"
        assert invite.guild.banner_hash == "aBannerForSure"
        assert invite.guild.description == "Describe me cute kitty."
        assert invite.guild.verification_level == guild_models.GuildVerificationLevel.MEDIUM
        assert invite.guild.vanity_url_code == "I-am-very-vain"
        assert invite.guild.welcome_screen == entity_factory_impl.deserialize_welcome_screen(
            guild_welcome_screen_payload
        )
        assert invite.guild.nsfw_level == guild_models.GuildNSFWLevel.EXPLICIT

        assert invite.guild_id == 56188492224814744
        assert invite.channel == entity_factory_impl.deserialize_partial_channel(partial_channel_payload)
        assert invite.channel_id == 561884984214814750
        assert invite.inviter == entity_factory_impl.deserialize_user(user_payload)
        assert invite.target_type == invite_models.TargetType.STREAM
        assert invite.target_user == entity_factory_impl.deserialize_user(alternative_user_payload)
        assert invite.approximate_member_count == 84
        assert invite.approximate_active_member_count == 42
        assert invite.expires_at == datetime.datetime(2021, 5, 8, 0, 15, 24, 534000, tzinfo=datetime.timezone.utc)
        assert isinstance(invite, invite_models.Invite)

        # InviteApplication
        application = invite.target_application
        assert application.app is mock_app
        assert application.id == 773336526917861400
        assert application.name == "Betrayal.io"
        assert application.description == "Play inside Discord with your friends!"
        assert application.summary == "Play inside Discord with your friends! (but as a summary)"
        assert (
            application.public_key
            == b"\x1b\xf7\x8f\xdb\xfc\xba\xbe.\x12V\xf9\xb13\x81\x89vY\x12\x03\xa2/\xeb\xab\xba_\xf8\x9f\x86\xf2G`\xff"
        )
        assert application.icon_hash == "0227b2e89ea08d666c43003fbadbc72a"
        assert application.cover_image_hash == "0227b2e89ea08d666c43003fbadbc72a (but as cover)"
        assert isinstance(application, application_models.InviteApplication)

    def test_deserialize_invite_with_null_fields(
        self, entity_factory_impl, partial_channel_payload, invite_application_payload
    ):
        invite = entity_factory_impl.deserialize_invite(
            {
                "code": "aCode",
                "channel_id": "43123123",
                "approximate_member_count": 231,
                "approximate_presence_count": 9,
                "expires_at": None,
                "target_application": {
                    "id": "773336526917861400",
                    "name": "Betrayal.io",
                    "description": "",
                    "summary": "",
                    "verify_key": "1bf78fdbfcbabe2e1256f9b133818976591203a22febabba5ff89f86f24760ff",
                },
            }
        )
        assert invite.expires_at is None
        assert invite.target_application.description is None
        assert invite.target_application.summary is None

    def test_deserialize_invite_with_unset_fields(self, entity_factory_impl, partial_channel_payload):
        invite = entity_factory_impl.deserialize_invite(
            {
                "code": "aCode",
                "channel_id": "43123123",
                "approximate_member_count": 231,
                "approximate_presence_count": 9,
            }
        )
        assert invite.channel is None
        assert invite.channel_id == 43123123
        assert invite.guild is None
        assert invite.inviter is None
        assert invite.target_type is None
        assert invite.target_user is None
        assert invite.target_application is None
        assert invite.expires_at is None

    def test_deserialize_invite_with_unset_sub_fields(self, entity_factory_impl, invite_payload):
        del invite_payload["guild"]["welcome_screen"]
        invite_payload["target_application"] = {
            "id": "773336526917861400",
            "name": "Betrayal.io",
            "description": "Play inside Discord with your friends!",
            "summary": "Play inside Discord with your friends! (but as a summary)",
            "verify_key": "1bf78fdbfcbabe2e1256f9b133818976591203a22febabba5ff89f86f24760ff",
        }

        invite = entity_factory_impl.deserialize_invite(invite_payload)

        assert invite.guild.welcome_screen is None
        assert invite.target_application.icon_hash is None
        assert invite.target_application.cover_image_hash is None

    def test_deserialize_invite_with_guild_and_channel_ids_without_objects(self, entity_factory_impl):
        invite = entity_factory_impl.deserialize_invite({"code": "aCode", "guild_id": "42", "channel_id": "202020"})
        assert invite.channel is None
        assert invite.channel_id == 202020
        assert invite.guild is None
        assert invite.guild_id == 42

    @pytest.fixture()
    def invite_with_metadata_payload(
        self,
        partial_channel_payload,
        user_payload,
        alternative_user_payload,
        guild_welcome_screen_payload,
        invite_application_payload,
    ):
        return {
            "code": "aCode",
            "guild": {
                "id": "56188492224814744",
                "name": "Testin' Your Scene",
                "splash": "aSplashForSure",
                "banner": "aBannerForSure",
                "description": "Describe me cute kitty.",
                "icon": "bb71f469c158984e265093a81b3397fb",
                "features": ["FORCE_RELAY"],
                "verification_level": 2,
                "vanity_url_code": "I-am-very-vain",
                "welcome_screen": guild_welcome_screen_payload,
                "nsfw_level": 0,
            },
            "channel": partial_channel_payload,
            "inviter": user_payload,
            "target_type": 1,
            "target_user": alternative_user_payload,
            "target_application": invite_application_payload,
            "approximate_presence_count": 42,
            "approximate_member_count": 84,
            "uses": 3,
            "max_uses": 8,
            "max_age": 239349393,
            "temporary": True,
            "created_at": "2015-04-26T06:26:56.936000+00:00",
        }

    def test_deserialize_invite_with_metadata(
        self,
        entity_factory_impl,
        mock_app,
        invite_with_metadata_payload,
        partial_channel_payload,
        user_payload,
        alternative_user_payload,
        guild_welcome_screen_payload,
        invite_application_payload,
    ):
        invite_with_metadata = entity_factory_impl.deserialize_invite_with_metadata(invite_with_metadata_payload)
        assert invite_with_metadata.app is mock_app
        assert invite_with_metadata.code == "aCode"
        # InviteGuild
        assert invite_with_metadata.guild.id == 56188492224814744
        assert invite_with_metadata.guild.name == "Testin' Your Scene"
        assert invite_with_metadata.guild.icon_hash == "bb71f469c158984e265093a81b3397fb"
        assert invite_with_metadata.guild.features == ["FORCE_RELAY"]
        assert invite_with_metadata.guild.splash_hash == "aSplashForSure"
        assert invite_with_metadata.guild.banner_hash == "aBannerForSure"
        assert invite_with_metadata.guild.description == "Describe me cute kitty."
        assert invite_with_metadata.guild.verification_level == guild_models.GuildVerificationLevel.MEDIUM
        assert invite_with_metadata.guild.vanity_url_code == "I-am-very-vain"
        assert invite_with_metadata.guild.welcome_screen == entity_factory_impl.deserialize_welcome_screen(
            guild_welcome_screen_payload
        )
        assert invite_with_metadata.guild.nsfw_level == guild_models.GuildNSFWLevel.DEFAULT

        assert invite_with_metadata.channel == entity_factory_impl.deserialize_partial_channel(partial_channel_payload)
        assert invite_with_metadata.inviter == entity_factory_impl.deserialize_user(user_payload)
        assert invite_with_metadata.target_type == invite_models.TargetType.STREAM
        assert invite_with_metadata.target_user == entity_factory_impl.deserialize_user(alternative_user_payload)
        assert invite_with_metadata.approximate_member_count == 84
        assert invite_with_metadata.approximate_active_member_count == 42
        assert invite_with_metadata.uses == 3
        assert invite_with_metadata.max_uses == 8
        assert invite_with_metadata.max_age == datetime.timedelta(seconds=239349393)
        assert invite_with_metadata.is_temporary is True
        assert invite_with_metadata.created_at == datetime.datetime(
            2015, 4, 26, 6, 26, 56, 936000, tzinfo=datetime.timezone.utc
        )
        assert invite_with_metadata.expires_at == datetime.datetime(
            2022, 11, 25, 12, 23, 29, 936000, tzinfo=datetime.timezone.utc
        )
        assert isinstance(invite_with_metadata, invite_models.InviteWithMetadata)

        # InviteApplication
        application = invite_with_metadata.target_application
        assert application.app is mock_app
        assert application.id == 773336526917861400
        assert application.name == "Betrayal.io"
        assert application.description == "Play inside Discord with your friends!"
        assert application.summary == "Play inside Discord with your friends! (but as a summary)"
        assert (
            application.public_key
            == b"\x1b\xf7\x8f\xdb\xfc\xba\xbe.\x12V\xf9\xb13\x81\x89vY\x12\x03\xa2/\xeb\xab\xba_\xf8\x9f\x86\xf2G`\xff"
        )
        assert application.icon_hash == "0227b2e89ea08d666c43003fbadbc72a"
        assert application.cover_image_hash == "0227b2e89ea08d666c43003fbadbc72a (but as cover)"
        assert isinstance(application, application_models.InviteApplication)

    def test_deserialize_invite_with_metadata_with_unset_and_0_fields(
        self, entity_factory_impl, partial_channel_payload
    ):
        invite_with_metadata = entity_factory_impl.deserialize_invite_with_metadata(
            {
                "code": "aCode",
                "channel": partial_channel_payload,
                "uses": 42,
                "max_uses": 0,
                "max_age": 0,
                "temporary": True,
                "created_at": "2015-04-26T06:26:56.936000+00:00",
                "approximate_presence_count": 4,
                "approximate_member_count": 9,
            }
        )
        assert invite_with_metadata.guild is None
        assert invite_with_metadata.inviter is None
        assert invite_with_metadata.target_type is None
        assert invite_with_metadata.target_user is None
        assert invite_with_metadata.target_application is None
        assert invite_with_metadata.max_age is None
        assert invite_with_metadata.max_uses is None
        assert invite_with_metadata.expires_at is None

    def test_deserialize_invite_with_metadata_with_null_guild_fields(
        self, entity_factory_impl, invite_with_metadata_payload
    ):
        del invite_with_metadata_payload["guild"]["welcome_screen"]

        invite = entity_factory_impl.deserialize_invite_with_metadata(invite_with_metadata_payload)
        assert invite.guild.welcome_screen is None

    def test_max_age_when_zero(self, entity_factory_impl, invite_with_metadata_payload):
        invite_with_metadata_payload["max_age"] = 0
        assert entity_factory_impl.deserialize_invite_with_metadata(invite_with_metadata_payload).max_age is None

    ##################
    # MESSAGE MODELS #
    ##################

    @pytest.fixture()
    def partial_application_payload(self):
        return {
            "id": "456",
            "name": "hikari",
            "description": "The best application",
            "icon": "2658b3029e775a931ffb49380073fa63",
            "cover_image": "58982a23790c4f22787b05d3be38a026",
            "summary": "asas",
            "primary_sku_id": "499494949494994",
        }

    @pytest.fixture()
    def message_payload(
        self, user_payload, member_payload, custom_emoji_payload, partial_application_payload, embed_payload
    ):
        del member_payload["user"]
        return {
            "id": "123",
            "channel_id": "456",
            "guild_id": "678",
            "author": user_payload,
            "member": member_payload,
            "content": "some info",
            "timestamp": "2020-03-21T21:20:16.510000+00:00",
            "edited_timestamp": "2020-04-21T21:20:16.510000+00:00",
            "tts": True,
            "mention_everyone": True,
            "mentions": [
                {"id": "5678", "username": "uncool username", "avatar": "129387dskjafhasf", "discriminator": "4532"}
            ],
            "mention_roles": ["987"],
            "mention_channels": [{"id": "456", "guild_id": "678", "type": 1, "name": "hikari-testing"}],
            "attachments": [
                {
                    "id": "690922406474154014",
                    "filename": "IMG.jpg",
                    "content_type": "image/png",
                    "size": 660521,
                    "url": "https://somewhere.com/attachments/123/456/IMG.jpg",
                    "proxy_url": "https://media.somewhere.com/attachments/123/456/IMG.jpg",
                    "width": 1844,
                    "height": 2638,
                }
            ],
            "embeds": [embed_payload],
            "reactions": [{"emoji": custom_emoji_payload, "count": 100, "me": True}],
            "pinned": True,
            "webhook_id": "1234",
            "type": 0,
            "activity": {"type": 5, "party_id": "ae488379-351d-4a4f-ad32-2b9b01c91657"},
            "application": partial_application_payload,
            "message_reference": {
                "channel_id": "278325129692446722",
                "guild_id": "278325129692446720",
                "message_id": "306588351130107906",
            },
            "referenced_message": {"message_reference_payload": "testing"},
            "flags": 2,
            "sticker_items": [
                {
                    "id": "749046696482439188",
                    "name": "Thinking",
                    "format_type": 3,
                }
            ],
            "nonce": "171000788183678976",
            "application_id": "123123123123",
            "interaction": {"id": "123123123", "type": 2, "name": "OKOKOK", "user": user_payload},
        }

    def test_deserialize_partial_message(
        self,
        entity_factory_impl,
        mock_app,
        message_payload,
        user_payload,
        member_payload,
        partial_application_payload,
        custom_emoji_payload,
        embed_payload,
    ):
        with mock.patch.object(entity_factory.EntityFactoryImpl, "deserialize_message") as deserialize_message:
            partial_message = entity_factory_impl.deserialize_partial_message(message_payload)

        assert partial_message.app is mock_app
        assert partial_message.id == 123
        assert partial_message.channel_id == 456
        assert partial_message.guild_id == 678
        assert partial_message.author == entity_factory_impl.deserialize_user(user_payload)
        assert partial_message.member == entity_factory_impl.deserialize_member(
            member_payload, user=partial_message.author, guild_id=snowflakes.Snowflake(678)
        )
        assert partial_message.content == "some info"
        assert partial_message.timestamp == datetime.datetime(
            2020, 3, 21, 21, 20, 16, 510000, tzinfo=datetime.timezone.utc
        )
        assert partial_message.edited_timestamp == datetime.datetime(
            2020, 4, 21, 21, 20, 16, 510000, tzinfo=datetime.timezone.utc
        )
        assert partial_message.is_tts is True
        assert partial_message.mentions.everyone is True
        assert partial_message.mentions.user_ids == [5678]
        assert partial_message.mentions.role_ids == [987]
        assert partial_message.mentions.channels_ids == [456]
        # Attachment
        assert len(partial_message.attachments) == 1
        attachment = partial_message.attachments[0]
        assert attachment.id == 690922406474154014
        assert attachment.filename == "IMG.jpg"
        assert attachment.size == 660521
        assert attachment.media_type == "image/png"
        assert attachment.url == "https://somewhere.com/attachments/123/456/IMG.jpg"
        assert attachment.proxy_url == "https://media.somewhere.com/attachments/123/456/IMG.jpg"
        assert attachment.width == 1844
        assert attachment.height == 2638
        assert isinstance(attachment, message_models.Attachment)

        expected_embed = entity_factory_impl.deserialize_embed(embed_payload)
        assert partial_message.embeds == [expected_embed]
        # Reaction
        reaction = partial_message.reactions[0]
        assert reaction.count == 100
        assert reaction.is_me is True
        expected_emoji = entity_factory_impl.deserialize_emoji(custom_emoji_payload)
        assert reaction.emoji == expected_emoji
        assert isinstance(reaction, message_models.Reaction)

        assert partial_message.is_pinned is True
        assert partial_message.webhook_id == 1234
        assert partial_message.type == message_models.MessageType.DEFAULT

        # Activity
        assert partial_message.activity.type == message_models.MessageActivityType.JOIN_REQUEST
        assert partial_message.activity.party_id == "ae488379-351d-4a4f-ad32-2b9b01c91657"
        assert isinstance(partial_message.activity, message_models.MessageActivity)

        # Message Activity
        assert partial_message.application.id == 456
        assert partial_message.application.name == "hikari"
        assert partial_message.application.description == "The best application"
        assert partial_message.application.icon_hash == "2658b3029e775a931ffb49380073fa63"
        assert partial_message.application.summary == "asas"
        assert partial_message.application.cover_image_hash == "58982a23790c4f22787b05d3be38a026"
        assert partial_message.application.primary_sku_id == 499494949494994
        assert isinstance(partial_message.application, message_models.MessageApplication)
        # MessageReference
        assert partial_message.message_reference.app is mock_app
        assert partial_message.message_reference.id == 306588351130107906
        assert partial_message.message_reference.channel_id == 278325129692446722
        assert partial_message.message_reference.guild_id == 278325129692446720
        assert isinstance(partial_message.message_reference, message_models.MessageReference)

        assert partial_message.referenced_message is deserialize_message.return_value
        deserialize_message.assert_called_once_with({"message_reference_payload": "testing"})
        assert partial_message.flags == message_models.MessageFlag.IS_CROSSPOST

        # Sticker
        assert len(partial_message.stickers) == 1
        sticker = partial_message.stickers[0]
        assert sticker.id == 749046696482439188
        assert sticker.name == "Thinking"
        assert sticker.format_type is sticker_models.StickerFormatType.LOTTIE
        assert isinstance(sticker, sticker_models.PartialSticker)

        assert partial_message.nonce == "171000788183678976"
        assert partial_message.application_id == 123123123123

        # MessageInteraction
        assert partial_message.interaction.id == 123123123
        assert partial_message.interaction.name == "OKOKOK"
        assert partial_message.interaction.type is base_interactions.InteractionType.APPLICATION_COMMAND
        assert partial_message.interaction.user == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(partial_message.interaction, message_models.MessageInteraction)

    def test_deserialize_partial_message_with_partial_fields(self, entity_factory_impl, message_payload):
        message_payload["content"] = ""
        message_payload["edited_timestamp"] = None
        message_payload["member"] = None
        message_payload["application"]["primary_sku_id"] = None
        message_payload["application"]["icon"] = None
        message_payload["referenced_message"] = None
        del message_payload["message_reference"]["message_id"]
        del message_payload["message_reference"]["guild_id"]
        del message_payload["application"]["cover_image"]

        partial_message = entity_factory_impl.deserialize_partial_message(message_payload)

        assert partial_message.content is None
        assert partial_message.edited_timestamp is None
        assert partial_message.guild_id is not None
        assert partial_message.member is None
        assert partial_message.application.primary_sku_id is None
        assert partial_message.application.icon_hash is None
        assert partial_message.application.cover_image_hash is None
        assert partial_message.message_reference.id is None
        assert partial_message.message_reference.guild_id is None
        assert partial_message.referenced_message is None

    def test_deserialize_partial_message_with_unset_fields(self, entity_factory_impl, mock_app):
        partial_message = entity_factory_impl.deserialize_partial_message({"id": 123, "channel_id": 456})

        assert partial_message.app is mock_app
        assert partial_message.id == 123
        assert partial_message.channel_id == 456
        assert partial_message.guild_id is None
        assert partial_message.author is None
        assert partial_message.member is None
        assert partial_message.content is undefined.UNDEFINED
        assert partial_message.timestamp is undefined.UNDEFINED
        assert partial_message.edited_timestamp is undefined.UNDEFINED
        assert partial_message.is_tts is undefined.UNDEFINED
        assert partial_message.mentions.everyone is undefined.UNDEFINED
        assert partial_message.mentions.user_ids is undefined.UNDEFINED
        assert partial_message.mentions.role_ids is undefined.UNDEFINED
        assert partial_message.mentions.channels_ids is undefined.UNDEFINED
        assert partial_message.attachments is undefined.UNDEFINED
        assert partial_message.embeds is undefined.UNDEFINED
        assert partial_message.reactions is undefined.UNDEFINED
        assert partial_message.is_pinned is undefined.UNDEFINED
        assert partial_message.webhook_id is undefined.UNDEFINED
        assert partial_message.type is undefined.UNDEFINED
        assert partial_message.activity is undefined.UNDEFINED
        assert partial_message.application is undefined.UNDEFINED
        assert partial_message.message_reference is undefined.UNDEFINED
        assert partial_message.referenced_message is undefined.UNDEFINED
        assert partial_message.flags is undefined.UNDEFINED
        assert partial_message.stickers is undefined.UNDEFINED
        assert partial_message.nonce is undefined.UNDEFINED
        assert partial_message.application_id is undefined.UNDEFINED
        assert partial_message.interaction is undefined.UNDEFINED

    def test_deserialize_full_message(
        self,
        entity_factory_impl,
        mock_app,
        message_payload,
        user_payload,
        member_payload,
        partial_application_payload,
        custom_emoji_payload,
        embed_payload,
    ):
        referenced_message = object()
        original = entity_factory_impl.deserialize_message

        def side_effect(call_args):
            if call_args == {"message_reference_payload": "testing"}:
                return referenced_message

            return original(call_args)

        with mock.patch.object(entity_factory.EntityFactoryImpl, "deserialize_message", side_effect=side_effect):
            message = entity_factory_impl.deserialize_message(message_payload)

        assert message.app is mock_app
        assert message.id == 123
        assert message.channel_id == 456
        assert message.guild_id == 678
        assert message.author == entity_factory_impl.deserialize_user(user_payload)
        assert message.member == entity_factory_impl.deserialize_member(
            member_payload, user=message.author, guild_id=snowflakes.Snowflake(678)
        )
        assert message.content == "some info"
        assert message.timestamp == datetime.datetime(2020, 3, 21, 21, 20, 16, 510000, tzinfo=datetime.timezone.utc)
        assert message.edited_timestamp == datetime.datetime(
            2020, 4, 21, 21, 20, 16, 510000, tzinfo=datetime.timezone.utc
        )
        assert message.is_tts is True
        assert message.mentions.everyone is True
        assert message.mentions.user_ids == [5678]
        assert message.mentions.role_ids == [987]
        assert message.mentions.channels_ids == [456]
        # Attachment
        assert len(message.attachments) == 1
        attachment = message.attachments[0]
        assert attachment.id == 690922406474154014
        assert attachment.filename == "IMG.jpg"
        assert attachment.size == 660521
        assert attachment.url == "https://somewhere.com/attachments/123/456/IMG.jpg"
        assert attachment.proxy_url == "https://media.somewhere.com/attachments/123/456/IMG.jpg"
        assert attachment.width == 1844
        assert attachment.height == 2638
        assert isinstance(attachment, message_models.Attachment)

        expected_embed = entity_factory_impl.deserialize_embed(embed_payload)
        assert message.embeds == [expected_embed]
        # Reaction
        reaction = message.reactions[0]
        assert reaction.count == 100
        assert reaction.is_me is True
        expected_emoji = entity_factory_impl.deserialize_emoji(custom_emoji_payload)
        assert reaction.emoji == expected_emoji
        assert isinstance(reaction, message_models.Reaction)

        assert message.is_pinned is True
        assert message.webhook_id == 1234
        assert message.type == message_models.MessageType.DEFAULT

        # Activity
        assert message.activity.type == message_models.MessageActivityType.JOIN_REQUEST
        assert message.activity.party_id == "ae488379-351d-4a4f-ad32-2b9b01c91657"
        assert isinstance(message.activity, message_models.MessageActivity)

        # MessageApplication
        assert message.application.id == 456
        assert message.application.name == "hikari"
        assert message.application.description == "The best application"
        assert message.application.icon_hash == "2658b3029e775a931ffb49380073fa63"
        assert message.application.summary == "asas"
        assert message.application.cover_image_hash == "58982a23790c4f22787b05d3be38a026"
        assert message.application.primary_sku_id == 499494949494994
        assert isinstance(message.application, message_models.MessageApplication)

        # MessageReference
        assert message.message_reference.app is mock_app
        assert message.message_reference.id == 306588351130107906
        assert message.message_reference.channel_id == 278325129692446722
        assert message.message_reference.guild_id == 278325129692446720
        assert isinstance(message.message_reference, message_models.MessageReference)

        assert message.referenced_message is referenced_message
        assert message.flags == message_models.MessageFlag.IS_CROSSPOST

        # Sticker
        assert len(message.stickers) == 1
        sticker = message.stickers[0]
        assert sticker.id == 749046696482439188
        assert sticker.name == "Thinking"
        assert sticker.format_type is sticker_models.StickerFormatType.LOTTIE
        assert isinstance(sticker, sticker_models.PartialSticker)

        assert message.nonce == "171000788183678976"
        assert message.application_id == 123123123123

        # MessageInteraction
        assert message.interaction.id == 123123123
        assert message.interaction.name == "OKOKOK"
        assert message.interaction.type is base_interactions.InteractionType.APPLICATION_COMMAND
        assert message.interaction.user == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(message.interaction, message_models.MessageInteraction)

    def test_deserialize_message_with_null_and_unset_fields(
        self,
        entity_factory_impl,
        mock_app,
        user_payload,
    ):
        message_payload = {
            "id": "123",
            "channel_id": "456",
            "author": user_payload,
            "content": "",
            "timestamp": "2020-03-21T21:20:16.510000+00:00",
            "edited_timestamp": None,
            "tts": True,
            "mention_everyone": True,
            "mentions": [],
            "mention_roles": [],
            "attachments": [],
            "embeds": [],
            "pinned": True,
            "type": 0,
        }

        message = entity_factory_impl.deserialize_message(message_payload)
        assert message.app is mock_app
        assert message.content is None
        assert message.guild_id is None
        assert message.member is None
        assert message.edited_timestamp is None
        assert message.mentions.everyone is True
        assert message.mentions.user_ids == []
        assert message.mentions.role_ids == []
        assert message.mentions.channels_ids == []
        assert message.attachments == []
        assert message.embeds == []
        assert message.reactions == []
        assert message.webhook_id is None
        assert message.activity is None
        assert message.application is None
        assert message.message_reference is None
        assert message.referenced_message is undefined.UNDEFINED
        assert message.stickers == []
        assert message.nonce is None
        assert message.application_id is None
        assert message.interaction is None

    def test_deserialize_message_with_other_unset_fields(self, entity_factory_impl, message_payload):
        message_payload["application"]["primary_sku_id"] = None
        message_payload["application"]["icon"] = None
        message_payload["referenced_message"] = None
        del message_payload["application"]["cover_image"]

        message = entity_factory_impl.deserialize_message(message_payload)
        assert message.application.primary_sku_id is None
        assert message.application.cover_image_hash is None
        assert message.application.icon_hash is None
        assert message.referenced_message is None

    ###################
    # PRESENCE MODELS #
    ###################

    @pytest.fixture()
    def presence_activity_payload(self, custom_emoji_payload):
        return {
            "name": "an activity",
            "type": 1,
            "url": "https://69.420.owouwunyaa",
            "created_at": 1584996792798,
            "timestamps": {"start": 1584996792798, "end": 1999999792798},
            "application_id": "40404040404040",
            "details": "They are doing stuff",
            "state": "STATED",
            "emoji": custom_emoji_payload,
            "party": {"id": "spotify:3234234234", "size": [2, 5]},
            "assets": {
                "large_image": "34234234234243",
                "large_text": "LARGE TEXT",
                "small_image": "3939393",
                "small_text": "small text",
            },
            "secrets": {"join": "who's a good secret?", "spectate": "I'm a good secret", "match": "No."},
            "instance": True,
            "flags": 3,
            "buttons": ["owo", "no"],
        }

    @pytest.fixture()
    def member_presence_payload(self, user_payload, presence_activity_payload):
        return {
            "user": user_payload,
            "activity": presence_activity_payload,
            "guild_id": "44004040",
            "status": "dnd",
            "activities": [presence_activity_payload],
            "client_status": {"desktop": "online", "mobile": "idle", "web": "dnd"},
        }

    def test_deserialize_member_presence(
        self, entity_factory_impl, mock_app, member_presence_payload, custom_emoji_payload, user_payload
    ):
        presence = entity_factory_impl.deserialize_member_presence(member_presence_payload)
        assert presence.app is mock_app
        assert presence.user_id == 115590097100865541
        assert presence.guild_id == 44004040
        assert presence.visible_status == presence_models.Status.DO_NOT_DISTURB
        # PresenceActivity
        assert len(presence.activities) == 1
        activity = presence.activities[0]
        assert activity.name == "an activity"
        assert activity.type == presence_models.ActivityType.STREAMING
        assert activity.url == "https://69.420.owouwunyaa"
        assert activity.created_at == datetime.datetime(2020, 3, 23, 20, 53, 12, 798000, tzinfo=datetime.timezone.utc)
        # ActivityTimestamps
        assert activity.timestamps.start == datetime.datetime(
            2020, 3, 23, 20, 53, 12, 798000, tzinfo=datetime.timezone.utc
        )
        assert activity.timestamps.end == datetime.datetime(
            2033, 5, 18, 3, 29, 52, 798000, tzinfo=datetime.timezone.utc
        )

        assert activity.application_id == 40404040404040
        assert activity.details == "They are doing stuff"
        assert activity.state == "STATED"
        assert activity.emoji == entity_factory_impl.deserialize_emoji(custom_emoji_payload)
        # ActivityParty
        assert activity.party is not None
        assert activity.party.id == "spotify:3234234234"
        assert activity.party.current_size == 2
        assert activity.party.max_size == 5
        assert isinstance(activity.party, presence_models.ActivityParty)
        # ActivityAssets
        assert activity.assets is not None
        assert activity.assets.large_image == "34234234234243"
        assert activity.assets.large_text == "LARGE TEXT"
        assert activity.assets.small_image == "3939393"
        assert activity.assets.small_text == "small text"
        assert isinstance(activity.assets, presence_models.ActivityAssets)
        # ActivitySecrets
        assert activity.secrets is not None
        assert activity.secrets.join == "who's a good secret?"
        assert activity.secrets.spectate == "I'm a good secret"
        assert activity.secrets.match == "No."
        assert isinstance(activity.secrets, presence_models.ActivitySecret)
        assert activity.is_instance is True
        assert activity.flags == presence_models.ActivityFlag(3)
        assert isinstance(activity, presence_models.RichActivity)

        # ClientStatus
        assert presence.client_status.desktop == presence_models.Status.ONLINE
        assert presence.client_status.mobile == presence_models.Status.IDLE
        assert presence.client_status.web == presence_models.Status.DO_NOT_DISTURB
        assert isinstance(presence.client_status, presence_models.ClientStatus)

        assert activity.buttons == ["owo", "no"]
        assert isinstance(presence, presence_models.MemberPresence)

    def test_deserialize_member_presence_with_unset_fields(
        self, entity_factory_impl, user_payload, presence_activity_payload
    ):
        presence = entity_factory_impl.deserialize_member_presence(
            {
                "user": {"id": "42"},
                "game": presence_activity_payload,
                "status": "dnd",
                "activities": [],
                "client_status": {},
            },
            guild_id=snowflakes.Snowflake(9654234123),
        )
        assert presence.guild_id == snowflakes.Snowflake(9654234123)
        # ClientStatus
        assert presence.client_status.desktop is presence_models.Status.OFFLINE
        assert presence.client_status.mobile is presence_models.Status.OFFLINE
        assert presence.client_status.web is presence_models.Status.OFFLINE

    def test_deserialize_member_presence_with_unset_activity_fields(self, entity_factory_impl, user_payload):
        presence = entity_factory_impl.deserialize_member_presence(
            {
                "user": user_payload,
                "game": None,
                "guild_id": "44004040",
                "status": "dnd",
                "activities": [
                    {
                        "name": "an activity",
                        "type": 1,
                        "created_at": 1584996792798,
                    }
                ],
                "client_status": {},
            }
        )
        assert len(presence.activities) == 1
        activity = presence.activities[0]
        assert activity.url is None
        assert activity.timestamps is None
        assert activity.application_id is None
        assert activity.details is None
        assert activity.state is None
        assert activity.emoji is None
        assert activity.party is None
        assert activity.assets is None
        assert activity.secrets is None
        assert activity.is_instance is None
        assert activity.flags is None
        assert activity.buttons == []

    def test_deserialize_member_presence_with_null_activity_fields(self, entity_factory_impl, user_payload):
        presence = entity_factory_impl.deserialize_member_presence(
            {
                "user": user_payload,
                "game": None,
                "guild_id": "44004040",
                "status": "dnd",
                "activities": [
                    {
                        "name": "an activity",
                        "type": 1,
                        "url": None,
                        "created_at": 1584996792798,
                        "timestamps": {
                            "start": 1584996792798,
                            "end": 1999999792798,
                        },
                        "application_id": "40404040404040",
                        "details": None,
                        "state": None,
                        "emoji": None,
                        "party": {"id": "spotify:3234234234", "size": [2, 5]},
                        "assets": {
                            "large_image": "34234234234243",
                            "large_text": "LARGE TEXT",
                            "small_image": "3939393",
                            "small_text": "small text",
                        },
                        "secrets": {"join": "who's a good secret?", "spectate": "I'm a good secret", "match": "No."},
                        "instance": True,
                        "flags": 3,
                    }
                ],
                "client_status": {},
            }
        )
        assert len(presence.activities) == 1
        activity = presence.activities[0]
        assert activity.url is None
        assert activity.details is None
        assert activity.state is None
        assert activity.emoji is None

    def test_deserialize_member_presence_with_unset_activity_sub_fields(self, entity_factory_impl, user_payload):
        presence = entity_factory_impl.deserialize_member_presence(
            {
                "user": user_payload,
                "game": None,
                "guild_id": "44004040",
                "status": "dnd",
                "activities": [
                    {
                        "name": "an activity",
                        "type": 1,
                        "url": "https://69.420.owouwunyaa",
                        "created_at": 1584996792798,
                        "timestamps": {},
                        "application_id": "40404040404040",
                        "details": "They are doing stuff",
                        "state": "STATED",
                        "emoji": None,
                        "party": {},
                        "assets": {},
                        "secrets": {},
                        "instance": True,
                        "flags": 3,
                    }
                ],
                "client_status": {},
            }
        )
        activity = presence.activities[0]
        # ActivityTimestamps
        assert activity.timestamps is not None
        assert activity.timestamps.start is None
        assert activity.timestamps.end is None
        # ActivityParty
        assert activity.party is not None
        assert activity.party.id is None
        assert activity.party.max_size is None
        assert activity.party.current_size is None
        # ActivityAssets
        assert activity.assets is not None
        assert activity.assets.small_text is None
        assert activity.assets.small_image is None
        assert activity.assets.large_text is None
        assert activity.assets.large_image is None
        # ActivitySecrets
        assert activity.secrets is not None
        assert activity.secrets.join is None
        assert activity.secrets.spectate is None
        assert activity.secrets.match is None

    ###################
    # TEMPLATE MODELS #
    ###################

    @pytest.fixture()
    def template_payload(self, guild_text_channel_payload, user_payload):
        return {
            "code": "4rDaewUKeYVj",
            "name": "ttt",
            "description": "eee",
            "usage_count": 42,
            "creator_id": "115590097100865541",
            "creator": user_payload,
            "created_at": "2020-12-15T01:54:35+00:00",
            "updated_at": "2020-12-15T01:57:35+00:00",
            "source_guild_id": "574921006817476608",
            "serialized_source_guild": {
                "name": "hikari",
                "description": "a descript description",
                "icon_hash": "27b75989b5b42aba51346a6b69d8fcfe",
                "verification_level": 2,
                "default_message_notifications": 1,
                "explicit_content_filter": 2,
                "preferred_locale": "en-GB",
                "afk_timeout": 3600,
                "roles": [
                    {
                        "id": "33",
                        "name": "@everyone",
                        "color": 0,
                        "hoist": True,
                        "mentionable": False,
                        "permissions": "104189505",
                    }
                ],
                "channels": [guild_text_channel_payload],
                "afk_channel_id": "321123",
                "system_channel_id": "8",
                "system_channel_flags": 0,
            },
            "is_dirty": True,
        }

    def test_deserialize_template(
        self, entity_factory_impl, mock_app, template_payload, user_payload, guild_text_channel_payload
    ):
        template = entity_factory_impl.deserialize_template(template_payload)
        assert template.code == "4rDaewUKeYVj"
        assert template.name == "ttt"
        assert template.description == "eee"
        assert template.usage_count == 42
        assert template.creator == entity_factory_impl.deserialize_user(user_payload)
        assert template.created_at == datetime.datetime(2020, 12, 15, 1, 54, 35, tzinfo=datetime.timezone.utc)
        assert template.updated_at == datetime.datetime(2020, 12, 15, 1, 57, 35, tzinfo=datetime.timezone.utc)

        # TemplateGuild
        assert template.source_guild.app is mock_app
        assert template.source_guild.id == 574921006817476608
        assert template.source_guild.icon_hash == "27b75989b5b42aba51346a6b69d8fcfe"
        assert template.source_guild.name == "hikari"
        assert template.source_guild.description == "a descript description"
        assert template.source_guild.verification_level is guild_models.GuildVerificationLevel.MEDIUM
        assert (
            template.source_guild.default_message_notifications
            is guild_models.GuildMessageNotificationsLevel.ONLY_MENTIONS
        )
        assert template.source_guild.explicit_content_filter is guild_models.GuildExplicitContentFilterLevel.ALL_MEMBERS
        assert template.source_guild.preferred_locale == "en-GB"
        assert template.source_guild.afk_timeout == datetime.timedelta(seconds=3600)

        # TemplateRole
        assert len(template.source_guild.roles) == 1
        role = template.source_guild.roles[33]
        assert role.app is mock_app
        assert role.id == 33
        assert role.name == "@everyone"
        assert role.permissions == permission_models.Permissions(104189505)
        assert role.color == color_models.Color(0)
        assert role.is_hoisted is True
        assert role.is_mentionable is False

        assert template.source_guild.channels == {
            123: entity_factory_impl.deserialize_channel(guild_text_channel_payload)
        }
        assert template.source_guild.afk_channel_id == 321123
        assert template.source_guild.system_channel_id == 8
        assert template.source_guild.system_channel_flags == guild_models.GuildSystemChannelFlag.NONE

        assert template.is_unsynced is True

    def test_deserialize_template_with_null_fields(self, entity_factory_impl, template_payload, user_payload):
        template = entity_factory_impl.deserialize_template(
            {
                "code": "4rDaewUKeYVj",
                "name": "ttt",
                "description": None,
                "usage_count": 42,
                "creator_id": "115590097100865541",
                "creator": user_payload,
                "created_at": "2020-12-15T01:54:35+00:00",
                "updated_at": "2020-12-15T01:57:35+00:00",
                "source_guild_id": "574921006817476608",
                "serialized_source_guild": {
                    "name": "hikari",
                    "description": "a descript description",
                    "icon_hash": "27b75989b5b42aba51346a6b69d8fcfe",
                    "verification_level": 2,
                    "default_message_notifications": 1,
                    "explicit_content_filter": 2,
                    "preferred_locale": "en-GB",
                    "afk_timeout": 3600,
                    "roles": [
                        {
                            "id": "33",
                            "name": "@everyone",
                            "color": 0,
                            "hoist": True,
                            "mentionable": False,
                            "permissions": "104189505",
                        }
                    ],
                    "channels": [],
                    "afk_channel_id": None,
                    "system_channel_id": None,
                    "system_channel_flags": 0,
                },
                "is_dirty": None,
            }
        )
        assert template.description is None
        assert template.source_guild.afk_channel_id is None
        assert template.source_guild.system_channel_id is None
        assert template.is_unsynced is False

    ###############
    # USER MODELS #
    ###############

    @pytest.fixture()
    def user_payload(self):
        return {
            "id": "115590097100865541",
            "username": "nyaa",
            "avatar": "b3b24c6d7cbcdec129d5d537067061a8",
            "discriminator": "6127",
            "bot": True,
            "system": True,
            "public_flags": int(user_models.UserFlag.EARLY_VERIFIED_DEVELOPER),
        }

    def test_deserialize_user(self, entity_factory_impl, mock_app, user_payload):
        user = entity_factory_impl.deserialize_user(user_payload)
        assert user.app is mock_app
        assert user.id == 115590097100865541
        assert user.username == "nyaa"
        assert user.avatar_hash == "b3b24c6d7cbcdec129d5d537067061a8"
        assert user.discriminator == "6127"
        assert user.is_bot is True
        assert user.is_system is True
        assert user.flags == user_models.UserFlag.EARLY_VERIFIED_DEVELOPER
        assert isinstance(user, user_models.UserImpl)

    def test_deserialize_user_with_unset_fields(self, entity_factory_impl, mock_app, user_payload):
        user = entity_factory_impl.deserialize_user(
            {
                "id": "115590097100865541",
                "username": "nyaa",
                "avatar": "b3b24c6d7cbcdec129d5d537067061a8",
                "discriminator": "6127",
            }
        )
        assert user.is_bot is False
        assert user.is_system is False
        assert user.flags == user_models.UserFlag.NONE

    @pytest.fixture()
    def my_user_payload(self):
        return {
            "id": "379953393319542784",
            "username": "qt pi",
            "avatar": "820d0e50543216e812ad94e6ab7",
            "discriminator": "2880",
            "bot": True,
            "system": True,
            "email": "blahblah@blah.blah",
            "verified": True,
            "locale": "en-US",
            "mfa_enabled": True,
            "public_flags": int(user_models.UserFlag.EARLY_VERIFIED_DEVELOPER),
            "flags": int(user_models.UserFlag.PARTNERED_SERVER_OWNER | user_models.UserFlag.DISCORD_EMPLOYEE),
            "premium_type": 1,
        }

    def test_deserialize_my_user(self, entity_factory_impl, mock_app, my_user_payload):
        my_user = entity_factory_impl.deserialize_my_user(my_user_payload)
        assert my_user.app is mock_app
        assert my_user.id == 379953393319542784
        assert my_user.username == "qt pi"
        assert my_user.avatar_hash == "820d0e50543216e812ad94e6ab7"
        assert my_user.discriminator == "2880"
        assert my_user.is_bot is True
        assert my_user.is_system is True
        assert my_user.is_mfa_enabled is True
        assert my_user.locale == "en-US"
        assert my_user.is_verified is True
        assert my_user.email == "blahblah@blah.blah"
        assert my_user.flags == user_models.UserFlag.PARTNERED_SERVER_OWNER | user_models.UserFlag.DISCORD_EMPLOYEE
        assert my_user.premium_type is user_models.PremiumType.NITRO_CLASSIC
        assert isinstance(my_user, user_models.OwnUser)

    def test_deserialize_my_user_with_unset_fields(self, entity_factory_impl, mock_app, my_user_payload):
        my_user = entity_factory_impl.deserialize_my_user(
            {
                "id": "379953393319542784",
                "username": "qt pi",
                "avatar": "820d0e50543216e812ad94e6ab7",
                "discriminator": "2880",
                "locale": "en-US",
                "mfa_enabled": True,
                "public_flags": int(user_models.UserFlag.EARLY_VERIFIED_DEVELOPER),
                "flags": int(user_models.UserFlag.PARTNERED_SERVER_OWNER | user_models.UserFlag.DISCORD_EMPLOYEE),
                "premium_type": 1,
            }
        )
        assert my_user.app is mock_app
        assert my_user.is_bot is False
        assert my_user.is_system is False
        assert my_user.is_verified is None
        assert my_user.email is None
        assert isinstance(my_user, user_models.OwnUser)

    ################
    # VOICE MODELS #
    ################

    @pytest.fixture()
    def voice_state_payload(self, member_payload):
        return {
            "guild_id": "929292929292992",
            "channel_id": "157733188964188161",
            "user_id": "115590097100865541",
            "member": member_payload,
            "session_id": "90326bd25d71d39b9ef95b299e3872ff",
            "deaf": True,
            "mute": True,
            "self_deaf": False,
            "self_mute": True,
            "self_stream": True,
            "self_video": True,
            "suppress": False,
            "request_to_speak_timestamp": "2021-04-17T10:11:19.970105+00:00",
        }

    def test_deserialize_voice_state_with_guild_id_in_payload(
        self, entity_factory_impl, mock_app, voice_state_payload, member_payload
    ):
        voice_state = entity_factory_impl.deserialize_voice_state(voice_state_payload)
        assert voice_state.app is mock_app
        assert voice_state.guild_id == 929292929292992
        assert voice_state.channel_id == 157733188964188161
        assert voice_state.user_id == 115590097100865541
        assert voice_state.member == entity_factory_impl.deserialize_member(
            member_payload, guild_id=snowflakes.Snowflake(929292929292992)
        )
        assert voice_state.session_id == "90326bd25d71d39b9ef95b299e3872ff"
        assert voice_state.is_guild_deafened is True
        assert voice_state.is_guild_muted is True
        assert voice_state.is_self_deafened is False
        assert voice_state.is_self_muted is True
        assert voice_state.is_streaming is True
        assert voice_state.is_video_enabled is True
        assert voice_state.is_suppressed is False
        assert voice_state.requested_to_speak_at == datetime.datetime(
            2021, 4, 17, 10, 11, 19, 970105, tzinfo=datetime.timezone.utc
        )
        assert isinstance(voice_state, voice_models.VoiceState)

    def test_deserialize_voice_state_with_injected_guild_id(
        self, entity_factory_impl, voice_state_payload, member_payload
    ):
        voice_state = entity_factory_impl.deserialize_voice_state(
            {
                "guild_id": "929292929292992",
                "channel_id": "157733188964188161",
                "user_id": "80351110224678912",
                "member": member_payload,
                "session_id": "90326bd25d71d39b9ef95b299e3872ff",
                "deaf": True,
                "mute": True,
                "self_deaf": False,
                "self_mute": True,
                "self_stream": True,
                "self_video": True,
                "suppress": False,
                "request_to_speak_timestamp": None,
            },
            guild_id=snowflakes.Snowflake(43123),
        )
        assert voice_state.guild_id == 43123
        assert voice_state.member == entity_factory_impl.deserialize_member(
            member_payload, guild_id=snowflakes.Snowflake(43123)
        )

    def test_deserialize_voice_state_with_null_and_unset_fields(self, entity_factory_impl, member_payload):
        voice_state = entity_factory_impl.deserialize_voice_state(
            {
                "channel_id": None,
                "user_id": "80351110224678912",
                "session_id": "90326bd25d71d39b9ef95b299e3872ff",
                "deaf": True,
                "mute": True,
                "self_deaf": False,
                "self_mute": True,
                "self_video": False,
                "suppress": False,
                "guild_id": "123123123",
                "member": member_payload,
                "request_to_speak_timestamp": None,
            }
        )
        assert voice_state.channel_id is None
        assert voice_state.is_streaming is False
        assert voice_state.requested_to_speak_at is None

    @pytest.fixture()
    def voice_region_payload(self):
        return {"id": "london", "name": "LONDON", "vip": True, "optimal": False, "deprecated": True, "custom": False}

    def test_deserialize_voice_region(self, entity_factory_impl, voice_region_payload):
        voice_region = entity_factory_impl.deserialize_voice_region(voice_region_payload)
        assert voice_region.id == "london"
        assert voice_region.name == "LONDON"
        assert voice_region.is_vip is True
        assert voice_region.is_optimal_location is False
        assert voice_region.is_deprecated is True
        assert voice_region.is_custom is False
        assert isinstance(voice_region, voice_models.VoiceRegion)

    ##################
    # WEBHOOK MODELS #
    ##################

    @pytest.fixture()
    def incoming_webhook_payload(self, user_payload):
        return {
            "name": "test webhook",
            "type": 1,
            "channel_id": "199737254929760256",
            "token": "3d89bb7572e0fb30d8128367b3b1b44fecd1726de135cbe28a41f8b2f777c372ba2939e72279b94526ff5d1bd4358d65cf11",
            "avatar": "dppdpdpdpdpd",
            "guild_id": "199737254929760256",
            "id": "223704706495545344",
            "application_id": "32123123123",
            "user": user_payload,
        }

    @pytest.fixture()
    def follower_webhook_payload(self, user_payload, partial_channel_payload):
        return {
            "type": 2,
            "id": "752831914402115456",
            "name": "Guildy name",
            "avatar": "bb71f469c158984e265093a81b3397fb",
            "channel_id": "561885260615255432",
            "guild_id": "56188498421443265",
            "application_id": "312123123",
            "source_guild": {
                "id": "56188498421476534",
                "name": "Guildy name",
                "icon": "bb71f469c158984e265093a81b3397fb",
            },
            "source_channel": {"id": "5618852344134324", "name": "announcements"},
            "user": user_payload,
        }

    @pytest.fixture()
    def application_webhook_payload(self):
        return {
            "type": 3,
            "id": "658822586720976555",
            "name": "Clyde",
            "avatar": "689161dc90ac261d00f1608694ac6bfd",
            "channel_id": None,  # This field is always null
            "guild_id": None,  # This field is always null
            "application_id": "658822586720976555",
        }

    def test_deserialize_incoming_webhook(self, entity_factory_impl, mock_app, incoming_webhook_payload, user_payload):
        webhook = entity_factory_impl.deserialize_incoming_webhook(incoming_webhook_payload)

        assert webhook.app is mock_app
        assert webhook.name == "test webhook"
        assert webhook.type is webhook_models.WebhookType.INCOMING
        assert webhook.channel_id == 199737254929760256
        assert (
            webhook.token
            == "3d89bb7572e0fb30d8128367b3b1b44fecd1726de135cbe28a41f8b2f777c372ba2939e72279b94526ff5d1bd4358d65cf11"
        )
        assert webhook.avatar_hash == "dppdpdpdpdpd"
        assert webhook.guild_id == 199737254929760256
        assert webhook.id == 223704706495545344
        assert webhook.application_id == 32123123123
        assert webhook.author == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(webhook, webhook_models.IncomingWebhook)

    def test_deserialize_incoming_webhook_with_null_fields(
        self, entity_factory_impl, incoming_webhook_payload, user_payload
    ):
        del incoming_webhook_payload["user"]
        del incoming_webhook_payload["token"]
        del incoming_webhook_payload["application_id"]
        incoming_webhook_payload["avatar"] = None

        webhook = entity_factory_impl.deserialize_incoming_webhook(incoming_webhook_payload)

        assert webhook.name == "test webhook"
        assert webhook.type is webhook_models.WebhookType.INCOMING
        assert webhook.channel_id == 199737254929760256
        assert webhook.token is None
        assert webhook.avatar_hash is None
        assert webhook.application_id is None
        assert webhook.author is None
        assert isinstance(webhook, webhook_models.IncomingWebhook)

    def test_deserialize_channel_follower_webhook(
        self, entity_factory_impl, mock_app, follower_webhook_payload, user_payload
    ):
        webhook = entity_factory_impl.deserialize_channel_follower_webhook(follower_webhook_payload)

        assert webhook.app is mock_app
        assert webhook.type is webhook_models.WebhookType.CHANNEL_FOLLOWER
        assert webhook.id == 752831914402115456
        assert webhook.name == "Guildy name"
        assert webhook.avatar_hash == "bb71f469c158984e265093a81b3397fb"
        assert webhook.channel_id == 561885260615255432
        assert webhook.guild_id == 56188498421443265
        assert webhook.application_id == 312123123

        assert webhook.source_guild.app is mock_app
        assert webhook.source_guild.id == 56188498421476534
        assert webhook.source_guild.name == "Guildy name"
        assert webhook.source_guild.icon_hash == "bb71f469c158984e265093a81b3397fb"
        assert isinstance(webhook.source_guild, guild_models.PartialGuild)

        assert webhook.source_channel == entity_factory_impl.deserialize_partial_channel(
            {"id": "5618852344134324", "name": "announcements", "type": channel_models.ChannelType.GUILD_NEWS}
        )
        assert webhook.author == entity_factory_impl.deserialize_user(user_payload)
        assert isinstance(webhook, webhook_models.ChannelFollowerWebhook)

    def test_deserialize_channel_follower_webhook_without_optional_fields(
        self, entity_factory_impl, mock_app, follower_webhook_payload, user_payload
    ):
        follower_webhook_payload["avatar"] = None
        del follower_webhook_payload["user"]
        del follower_webhook_payload["application_id"]

        webhook = entity_factory_impl.deserialize_channel_follower_webhook(follower_webhook_payload)

        assert webhook.avatar_hash is None
        assert webhook.application_id is None
        assert webhook.author is None

    def test_deserialize_application_webhook(self, entity_factory_impl, mock_app, application_webhook_payload):
        webhook = entity_factory_impl.deserialize_application_webhook(application_webhook_payload)

        assert webhook.app is mock_app
        assert webhook.type is webhook_models.WebhookType.APPLICATION
        assert webhook.id == 658822586720976555
        assert webhook.name == "Clyde"
        assert webhook.avatar_hash == "689161dc90ac261d00f1608694ac6bfd"
        assert webhook.application_id == 658822586720976555
        assert isinstance(webhook, webhook_models.ApplicationWebhook)

    def test_deserialize_application_webhook_without_optional_fields(
        self, entity_factory_impl, mock_app, application_webhook_payload
    ):
        application_webhook_payload["avatar"] = None

        webhook = entity_factory_impl.deserialize_application_webhook(application_webhook_payload)

        assert webhook.avatar_hash is None

    def test_deserialize_webhook(
        self, entity_factory_impl, incoming_webhook_payload, follower_webhook_payload, application_webhook_payload
    ):
        for expected_type, payload in [
            (webhook_models.IncomingWebhook, incoming_webhook_payload),
            (webhook_models.ChannelFollowerWebhook, follower_webhook_payload),
            (webhook_models.ApplicationWebhook, application_webhook_payload),
        ]:
            result = entity_factory_impl.deserialize_webhook(payload)
            assert isinstance(result, expected_type)

    def test_deserialize_webhook_for_unexpected_webhook_type(self, entity_factory_impl):
        with pytest.raises(errors.UnrecognisedEntityError):
            entity_factory_impl.deserialize_webhook({"type": -7999})

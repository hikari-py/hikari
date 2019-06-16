#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Client mix of all mixin components.
"""
import enum
import inspect

from hikari.models.audit import action_type
from hikari.net import utils

from . import base


class _Scope(enum.Enum):
    AUDIT_LOG = "/resources/audit-log"
    CHANNEL = "/resources/channel"
    EMOJI = "/resources/emoji"
    GUILD = "/resources/guild"
    INVITE = "/resources/invite"
    OAUTH2 = "/topics/oauth2"
    USER = "/resources/user"
    VOICE = "/resources/voice"
    WEBHOOK = "/resources/webhook"


def _rtfm(scope: _Scope, *see):
    """Injects some common documentation into the given member's docstring."""

    def decorator(obj):
        BASE_URL = "https://discordapp.com/developers/docs"
        doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        name, url = scope.name.replace("_", " ").title(), BASE_URL + scope.value
        doc = f"This is part of the `{name} <{url}>`_ API.\n\n{doc}"

        doc += "\nSee:\n"
        for url in see:
            doc += f"\t* {BASE_URL}{url}"

        setattr(obj, "__doc__", doc)
        return obj

    return decorator


class HTTPClient(base.BaseHTTPClient):
    """
    Combination of all components for API handling logic for the V7 Discord HTTP API.
    """

    __slots__ = []

    ##############
    # AUDIT LOGS #
    ##############

    @_rtfm(
        _Scope.AUDIT_LOG,
        "/resources/audit-log#get-guild-audit-log",
        "/resources/audit-log#audit-log-entry-object-audit-log-events",
        "/resources/audit-log#audit-log-object",
    )
    async def get_guild_audit_log(
        self,
        guild_id: utils.RawSnowflakeish,
        user_id: utils.RawSnowflakeish = None,
        action: action_type.ActionType = None,
        limit: int = None,
    ) -> utils.ResponseBody:
        """
        Get an audit log object for the given guild.

        Args:
            guild_id:
                The guild ID to look up.
            user_id:
                Optional user ID to filter by.
            action:
                Optional action type to look up.
            limit:
                Optional limit to apply to the number of records. Defaults to 50. Must be between 1 and 100 inclusive.

        Returns:
            An audit log object.

        Raises:
            :class:`hikari.errors.Forbidden` if you lack the given permissions to view an audit log.
            :class:`hikari.errors.NotFound` if the guild does not exist.
            :class:`ValueError` if the limit is not within an acceptable range.
        """
        query = {}

        if limit is not None:
            if 1 <= limit <= 100:
                query["limit"] = limit
            else:
                raise ValueError("limit should either be None or in the range [1, 100]")

        if user_id is not None:
            query["user_id"] = user_id

        if action is not None:
            query["action_type"] = action.value

        params = {"guild_id": guild_id}

        _, _, body = await self.request("get", "/guilds/{guild_id}/audit-logs", params=params, query=query)

        return body

    ############
    # CHANNELS #
    ############

    ##########
    # EMOJIS #
    ##########

    ##########
    # GUILDS #
    ##########

    ###############
    # INVITATIONS #
    ###############

    ##########
    # OAUTH2 #
    ##########

    @_rtfm(_Scope.OAUTH2, "/topics/oauth2#get-current-application-information")
    async def application_info(self) -> utils.ResponseBody:
        """
        Get the current application information.

        Returns:
             An application info object.

        Example Response:

            .. code-block:: python

                {
                    "description": "Test",
                    "icon": null,
                    "id": "172150183260323840",
                    "name": "Baba O-Riley",
                    "bot_public": true,
                    "bot_require_code_grant": false,
                    "owner": {
                        "username": "i own a bot",
                        "discriminator": "1738",
                        "id": "172150183260323840",
                        "avatar": null
                    }
                }
        """
        _, _, body = await self.request("get", "/oauth2/applications/@me")
        return body

    #########
    # USERS #
    #########

    ############
    # WEBHOOKS #
    ############


del _Scope, _rtfm

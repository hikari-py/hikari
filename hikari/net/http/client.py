#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Client mix of all mixin components.
"""
import enum
import inspect

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


def _rtfm(scope: _Scope, see):
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

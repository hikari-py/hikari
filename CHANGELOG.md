# Changelog

All notable changes to this project will be documented in this file.

This file is updated every release with the use of `towncrier` from the fragments found under `changes/`.

.. towncrier release notes start

Hikari 2.0.0.dev104 (2021-10-09)
================================

Features
--------

- User banners and accent colors to user models. ([#811](https://github.com/hikari-py/hikari/issues/811))
- Add attachment "is_ephemeral" field ([#824](https://github.com/hikari-py/hikari/issues/824))
- Guild member avatars ([#825](https://github.com/hikari-py/hikari/issues/825))
- Add role icons ([#838](https://github.com/hikari-py/hikari/issues/838))


Bugfixes
--------

- Don't raise in bulk delete when message not found by delete single message endpoint ([#828](https://github.com/hikari-py/hikari/issues/828))
- Setup basic handler if no handlers are defined in favour passed to `logging.config.dictConfig` ([#832](https://github.com/hikari-py/hikari/issues/832))
- InteractionMessageBuilder and RESTClientImpl.create_interaction_response now cast content to str to be consistent with the other message create methods. ([#834](https://github.com/hikari-py/hikari/issues/834))


Hikari 2.0.0.dev103 (2021-10-06)
================================

Breaking Changes
----------------

- `USE_PUBLIC_THREADS` and `USE_PRIVATE_THREADS` permissions have been removed in favour of new threads permission
  - New permissions are split into `CREATE_PUBLIC_THREADS`, `CREATE_PRIVATE_THREADS` and `SEND_MESSAGES_IN_THREADS` ([#799](https://github.com/hikari-py/hikari/issues/799))
- `GuildAvailableEvent` will no longer fire when the bot joins new guilds
  - Some `guild_create`-ish methods were renamed to `guild_available` ([#809](https://github.com/hikari-py/hikari/issues/809))
- Remove `hikari.errors.RESTErrorCode` enum
  - The message that is sent with the error code is the info that the enum contained ([#816](https://github.com/hikari-py/hikari/issues/816))
- PermissionOverwrite doesn't inherit from Unique anymore and isn't hashable. Equality checks now consider all its fields. ([#820](https://github.com/hikari-py/hikari/issues/820))


Features
--------

- Add new `START_EMBEDDED_ACTIVITIES` permission ([#798](https://github.com/hikari-py/hikari/issues/798))
- Support new `channel_types` field in `CommandOption` ([#800](https://github.com/hikari-py/hikari/issues/800))
- Add the `add_component` method to `hikari.api.special_endpoints.ActionRowBuilder` ([#804](https://github.com/hikari-py/hikari/issues/804))
- Add `old_guild` attribute to `GuildLeaveEvent`. ([#806](https://github.com/hikari-py/hikari/issues/806))
- Add `GuildJoinEvent` that will fire when the bot joins new guilds ([#809](https://github.com/hikari-py/hikari/issues/809))


Bugfixes
--------

- Fix re-uploading forms with resources ([#787](https://github.com/hikari-py/hikari/issues/787))
- Prevent double linking embed resources, which causes them to upload twice
  - This was caused by attempting to move the resource from one embed to another ([#788](https://github.com/hikari-py/hikari/issues/788))
- Fix `BulkDeleteError` returning incorrect values for `messages_skipped`
  - This affected the `__str__` and `percentage_completion`, which also returned incorrect values ([#817](https://github.com/hikari-py/hikari/issues/817))


Documentation Improvements
--------------------------

- Add docstrings to the remaining undocumented `GatewayBot` methods ([#804](https://github.com/hikari-py/hikari/issues/804))


Hikari 2.0.0.dev102 (2021-09-19)
================================

Deprecations and Removals
-------------------------

- `MessageType.APPLICATION_COMMAND` renamed to `MessageType.CHAT_INPUT` ([#775](https://github.com/hikari-py/hikari/issues/775))
- Removal of deprecated `hikari.impl.bot.BotApp` and `hikari.traits.BotAware`
  - Use `hikari.impl.bot.GatewayBot` and `hikari.traits.GatewayBotAware` respectively instead ([#778](https://github.com/hikari-py/hikari/issues/778))


Features
--------

- Message components support ([#684](https://github.com/hikari-py/hikari/issues/684))
- Web dashboard example with `rillrate` ([#752](https://github.com/hikari-py/hikari/issues/752))
- Sticker methods to PartialGuild ([#754](https://github.com/hikari-py/hikari/issues/754))
- Sticker audit log event types ([#756](https://github.com/hikari-py/hikari/issues/756))
- Helpful Application object methods ([#757](https://github.com/hikari-py/hikari/issues/757))
- Missing audit log change keys ([#759](https://github.com/hikari-py/hikari/issues/759))
- Retry request on 500, 502, 503 and 504 errors
  - Default retry count is 3, with a hard top of 5. This can be changed with the `max_retries` argument ([#763](https://github.com/hikari-py/hikari/issues/763))
- New `is_for_emoji` methods to relevant reaction events ([#770](https://github.com/hikari-py/hikari/issues/770))
- Add `USE_EXTERNAL_STICKERS` permission ([#774](https://github.com/hikari-py/hikari/issues/774))
- Add `MessageType.CONTEXT_MENU_COMMAND` message type ([#775](https://github.com/hikari-py/hikari/issues/775))
- Add `ApplicationCommand.version` ([#776](https://github.com/hikari-py/hikari/issues/776))


Bugfixes
--------

- Handling of interaction models passed to the webhook message endpoints as the "webhook" field ([#759](https://github.com/hikari-py/hikari/issues/759))
- Fix passing `embeds` arguments in `create_interaction_response` and `edit_initial_response` endpoints
  - Fix deserialization of embeds in `create_interaction_response`
  - Fix `TypeErrors` raised in `edit_initial_response` when passing a list of embeds ([#779](https://github.com/hikari-py/hikari/issues/779))
- Improve typing for message objects and message update methods
  - Fix the use of `typing.Optional` where `undefined.UndefinedOr` should have been used
  - Remove trying to acquire guild_id from the cached channel on PartialMessage
    - Instead, clearly document the issue Discord imposes by not sending the guild_id
  - `is_webhook` will now return `undefined.UNDEFINED` if the information is not available
  - Fix logic in `is_human` to account for the changes in the typing
  - Set `PartialMessage.member` to `undefined.UNDEFINED` when Discord edit the message to display an embed/attachment ([#783](https://github.com/hikari-py/hikari/issues/783))
- `CommandInteractionOption.value` will now be cast to a `Snowflake` for types 6-9 ([#785](https://github.com/hikari-py/hikari/issues/785))


Improved Documentation
----------------------

- Fix typo in Colorish docstring ([#755](https://github.com/hikari-py/hikari/issues/755))
- Remove duplicate raise type in REST and guilds docstrings ([#768](https://github.com/hikari-py/hikari/issues/768))
- Fix various spelling mistakes ([#773](https://github.com/hikari-py/hikari/issues/773))


*This file was added during the development of version 2.0.0.dev102, so nothing before that is documented.*

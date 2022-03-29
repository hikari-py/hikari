# Changelog

All notable changes to this project will be documented in this file.

This file is updated every release with the use of `towncrier` from the fragments found under `changes/`.

.. towncrier release notes start

Hikari 2.0.0.dev108 (2022-03-27)
================================

Breaking Changes
----------------

- `hikari.config` has now been split up to `hikari.api.config` and `hikari.impl.config` to avoid leaking impl detail.
  This also means that config types are no-longer accessible at the top level (directly on `hikari`). ([#1067](https://github.com/hikari-py/hikari/issues/1067))
- Hide the entity factory's component deserialize methods. ([#1074](https://github.com/hikari-py/hikari/issues/1074))
- Remove nonce parameter from create message.
  This was purposely removed from the bot api documentation inferring that its no-longer officially supported. ([#1075](https://github.com/hikari-py/hikari/issues/1075))
- Remove `VoiceRegion.is_vip` due to Discord no longer sending it. ([#1086](https://github.com/hikari-py/hikari/issues/1086))
- Remove store sku related application fields and store channels. ([#1092](https://github.com/hikari-py/hikari/issues/1092))


Deprecation
-----------

- Renamed `nick` argument to `nickname` for edit member and add user to guild REST methods. ([#1095](https://github.com/hikari-py/hikari/issues/1095))


Features
--------

- Scheduled event support. ([#1056](https://github.com/hikari-py/hikari/issues/1056))
- `get_guild()` is now available on `hikari.GuildChannel`. ([#1057](https://github.com/hikari-py/hikari/issues/1057))
- Optimize receiving websocket JSON for the happy path. ([#1058](https://github.com/hikari-py/hikari/issues/1058))
- The threaded file reader now persists the open file pointer while the context manager is active. ([#1073](https://github.com/hikari-py/hikari/issues/1073))
- Optimize event dispatching by only deserializing events when they are needed. ([#1094](https://github.com/hikari-py/hikari/issues/1094))
- Add `hikari.locales.Locale` to help with Discord locale strings. ([#1090](https://github.com/hikari-py/hikari/issues/1090))


Bugfixes
--------

- `fetch_my_guilds` no-longer returns duplicate guilds nor makes unnecessary (duplicated) requests when `newest_first` is set to `True`. ([#1059](https://github.com/hikari-py/hikari/issues/1059))
- Add `InviteEvent` to `hikari.events.channel_events.__all__`, `hikari.events.__all__` and `hikari.__all__`. ([#1065](https://github.com/hikari-py/hikari/issues/1065))
- Fix incorrect type for ATTACHMENT option values. ([#1066](https://github.com/hikari-py/hikari/issues/1066))
- `EventManager.get_listeners` now correctly defines polymorphic and returns accordingly. ([#1094](https://github.com/hikari-py/hikari/issues/1094))
- Take the major param for webhook without token endpoints when handling bucket ratelimits. ([#1102](https://github.com/hikari-py/hikari/issues/1102))
- Fix incorrect value for `GuildFeature.MORE_STICKERS`. ([#1989](https://github.com/hikari-py/hikari/issues/1989))


Hikari 2.0.0.dev107 (2022-03-04)
================================

Features
--------

- Added a `total_length` function to `hikari.embeds.Embed`
  - Takes into account the character length of the embed's title, description, fields (all field names and values), footer, and author combined.
  - Useful for determining if the embed exceeds Discord's 6000 character limit. ([#796](https://github.com/hikari-py/hikari/issues/796))
- Added attachment command option type support. ([#1015](https://github.com/hikari-py/hikari/issues/1015))
- Add MESSAGE_CONTENT intent. ([#1021](https://github.com/hikari-py/hikari/issues/1021))
- Custom substitutions can now be used in `hikari.internal.ux.print_banner`. ([#1022](https://github.com/hikari-py/hikari/issues/1022))
- `get_guild()` is now available on `hikari.Member`. ([#1025](https://github.com/hikari-py/hikari/issues/1025))
- The notorious "failed to communicate with server" log message is now a warning rather than an error. ([#1041](https://github.com/hikari-py/hikari/issues/1041))
- `hikari.applications`, `hikari.files`, `hikari.snowflakes` and `hikari.undefined` are now all explicitly exported by `hikari.__init__`, allowing pyright to see them without a direct import. ([#1042](https://github.com/hikari-py/hikari/issues/1042))


Bugfixes
--------

- Fix bucket lock not being released on errors while being acquired, which locked the bucket infinitely ([#841](https://github.com/hikari-py/hikari/issues/841))
- `enable_signal_handlers` now only defaults to `True` when the run/start method is called in the main thread.
  This avoids these functions from always raising when being run in a threaded environment as only the main thread can register signal handlers. ([#998](https://github.com/hikari-py/hikari/issues/998))
- Sub-command options are now properly deserialized in the autocomplete flow to `AutocompleteInteractionOption` instead of `CommandInteractionOption`. ([#1012](https://github.com/hikari-py/hikari/issues/1012))
- Attempt to reconnect on a gateway `TimeoutError`. ([#1014](https://github.com/hikari-py/hikari/issues/1014))
- Properly close `GatewayBot` when not fully started. ([#1023](https://github.com/hikari-py/hikari/issues/1023))
- The async context manager returned by `File.stream` now errors on enter if the target file doesn't exist to improve error handling when a file that doesn't exist is sent as an attachment.

  The multiprocessing file reader strategy now expands user relative (`~`) links (like the threaded strategy). ([#1046](https://github.com/hikari-py/hikari/issues/1046))


Hikari 2.0.0.dev106 (2022-02-03)
================================

Breaking Changes
----------------

- Running the standard interaction server implementation now requires a `hikari[server]` install.

  This matches a switch over to PyNacl for the cryptographic payload validation. ([#986](https://github.com/hikari-py/hikari/issues/986))


Deprecation
-----------

- Deprecated `RESTClient.command_builder` and `RESTClient.create_application_command`.

  You should switch to `RESTClient.slash_command_builder`and `RESTClient.create_slash_command` respectively. ([#924](https://github.com/hikari-py/hikari/issues/924))


Features
--------

- Add context menu commands and command autocomplete. ([#924](https://github.com/hikari-py/hikari/issues/924))
- Added support for GET /users/@me/guilds/{guild}/member. ([#955](https://github.com/hikari-py/hikari/issues/955))
- Add the `SUPPRESS_USER_JOIN_REPLIES` system channel flag. ([#957](https://github.com/hikari-py/hikari/issues/957))
- Add new message content intent related application flags. ([#958](https://github.com/hikari-py/hikari/issues/958))
- Add the `BOT_HTTP_INTERACTIONS` user flag. ([#959](https://github.com/hikari-py/hikari/issues/959))
- Add new presence activity flags. ([#960](https://github.com/hikari-py/hikari/issues/960))
- Add URL methods and properties for rich presence assets. ([#961](https://github.com/hikari-py/hikari/issues/961))
- Add `locale` and `guild_locale` properties to interactions. ([#962](https://github.com/hikari-py/hikari/issues/962))
- Add ability to send attachments in an interaction initial response. ([#971](https://github.com/hikari-py/hikari/issues/971))
- Add `display_avatar_url` property to `hikari.Member` and `hikari.User`. ([#975](https://github.com/hikari-py/hikari/issues/975))
- old_x keyword arguments in the event factory now default to `None`. ([#984](https://github.com/hikari-py/hikari/issues/984))
- Strip tokens in the standard bot impls and RESTApp.

  This helps avoids a common mistake with trailing new-lines which leads to confusing errors on request. ([#989](https://github.com/hikari-py/hikari/issues/989))


Bugfixes
--------

- Relaxed typing of methods with union entry specific specialisations through overloads. ([#876](https://github.com/hikari-py/hikari/issues/876))
- Fix deprecation warnings raised by usage of `asyncio.gather` outside of an active event loop in `GatewayBot.run`. ([#954](https://github.com/hikari-py/hikari/issues/954))
- UTF-8 characters are now properly handled for audit-log reasons in REST requests. ([#963](https://github.com/hikari-py/hikari/issues/963))
- Fix magic methods for `UserImpl` and its subclasses. ([#982](https://github.com/hikari-py/hikari/issues/982))


Hikari 2.0.0.dev105 (2022-01-01)
================================

Features
--------

- Add min_value and max_value to `CommandOption` ([#920](https://github.com/hikari-py/hikari/issues/920))
- Add `flags` attribute to Application ([#939](https://github.com/hikari-py/hikari/issues/939))
- Implement member timeouts
   - Add `raw_communication_disabled_until` and `communication_disabled_until` to `Member`
   - Add `MODERATE_MEMBERS` to `Permission`
   - Add `communication_disabled_until` attribute to `edit_member` ([#940](https://github.com/hikari-py/hikari/issues/940))


Bugfixes
--------

- Improved pyright compatibility and introduced pyright "type-completeness" checking. ([#916](https://github.com/hikari-py/hikari/issues/916))
- Add EventStream.filter specialisation to the abc. ([#917](https://github.com/hikari-py/hikari/issues/917))
- Update the app command name regex to account for more recently documented support for non-english characters on Discord's end. ([#918](https://github.com/hikari-py/hikari/issues/918))
- Fix reposition_roles using the wrong route. ([#928](https://github.com/hikari-py/hikari/issues/928))
- Fix `PartialSticker.image_url` not passing the hash as a string ([#930](https://github.com/hikari-py/hikari/issues/930))
- Fixed the url being generated for role icons to not erroneously insert ".png" before the file extension ([#931](https://github.com/hikari-py/hikari/issues/931))
- Fix some bugs in message deserialization
    - Remove case for setting `member` and `reference_message` to `undefined.Undefined` in full message deserialization
    - Don't set `message.member` to `undefined.UNDEFINED` on partial message deserialization if message was sent by a webhook ([#933](https://github.com/hikari-py/hikari/issues/933))


Hikari 2.0.0.dev104 (2021-11-22)
================================

Breaking Changes
----------------

- Remove the redundant `ChannelCreateEvent`, `ChannelUpdateEvent` and `ChannelDeleteEvent` base classes.
  `GuildChannelCreateEvent`, `GuildChannelUpdateEvent` and `GuildChannelDeleteEvent` should now be used. ([#862](https://github.com/hikari-py/hikari/issues/862))
- Split bulk message delete from normal delete
    - The new event is now `hikari.events.message_events.GuildBulkMessageDeleteEvent` ([#897](https://github.com/hikari-py/hikari/issues/897))


Deprecation
-----------

- `edit_my_nick` rest method. ([#827](https://github.com/hikari-py/hikari/issues/827))
- EventStream is now a sync context manager, not async. ([#864](https://github.com/hikari-py/hikari/issues/864))


Features
--------

- User banners and accent colors to user models. ([#811](https://github.com/hikari-py/hikari/issues/811))
- Add attachment "is_ephemeral" field ([#824](https://github.com/hikari-py/hikari/issues/824))
- Guild member avatars ([#825](https://github.com/hikari-py/hikari/issues/825))
- RESTClient `edit_my_member` method which currently only takes "nick". ([#827](https://github.com/hikari-py/hikari/issues/827))
- Add role icons ([#838](https://github.com/hikari-py/hikari/issues/838))
- RESTClient.entity_factory property ([#848](https://github.com/hikari-py/hikari/issues/848))
- Added component support to InteractionMessageBuilder. ([#851](https://github.com/hikari-py/hikari/issues/851))
- `EventStream.filter` now always returns `EventStream`. ([#864](https://github.com/hikari-py/hikari/issues/864))
- Allow for passing a URL for avatar_url on execute_webhook. ([#889](https://github.com/hikari-py/hikari/issues/889))
- Add `old_message` attribute to `hikari.events.message_events.MessageDelete` ([#897](https://github.com/hikari-py/hikari/issues/897))
- Switch to more relaxed requirements. ([#906](https://github.com/hikari-py/hikari/issues/906))


Bugfixes
--------

- Don't raise in bulk delete when message not found by delete single message endpoint ([#828](https://github.com/hikari-py/hikari/issues/828))
- Setup basic handler if no handlers are defined in favour passed to `logging.config.dictConfig` ([#832](https://github.com/hikari-py/hikari/issues/832))
- InteractionMessageBuilder and RESTClientImpl.create_interaction_response now cast content to str to be consistent with the other message create methods. ([#834](https://github.com/hikari-py/hikari/issues/834))
- create_sticker method failing due to using an incorrect body. ([#858](https://github.com/hikari-py/hikari/issues/858))
- Fix logic for asserting listeners to not error when using defaults for other arguments ([#911](https://github.com/hikari-py/hikari/issues/911))
- Fix error message given by action row when a conflicted type is added. ([#912](https://github.com/hikari-py/hikari/issues/912))


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

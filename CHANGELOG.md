## 2.0.0.dev125 (2024-04-28)

### Features

- Add monetization support. ([#1803](https://github.com/hikari-py/hikari/issues/1803))
- - Add `message_link` property to `MessageReference`
  - Add `channel_link` property to `MessageReference` ([#1877](https://github.com/hikari-py/hikari/issues/1877))
- Add missing `video_quality_mode` field to `GuildStageChannel` ([#1891](https://github.com/hikari-py/hikari/issues/1891))
- Optimize gateway transport
  - Merge cold path for zlib compression into main path to avoid additional call
  - Handle data in `bytes`, rather than in `str` to make good use of speedups (similar to `RESTClient`) ([#1898](https://github.com/hikari-py/hikari/issues/1898))

### Bugfixes

- Fix warning raised in aiohttp 3.9.4 when using `FormData` (most commonly, when uploading attachments) ([#1881](https://github.com/hikari-py/hikari/issues/1881))
- Properly handle websocket transport errors and recover
  - Additionally, errors will now include additional information ([#1897](https://github.com/hikari-py/hikari/issues/1897))

---
## 2.0.0.dev124 (2024-04-07)

### Features

- Improve `Emoji.parse` typing to make it more explicit ([#1870](https://github.com/hikari-py/hikari/issues/1870))
- Add ability to edit own user banner ([#1871](https://github.com/hikari-py/hikari/issues/1871))

### Bugfixes

- Fix incorrectly formatted error strings ([#1866](https://github.com/hikari-py/hikari/issues/1866))
- Properly handle initial opcode as being RECONNECT (7) ([#1867](https://github.com/hikari-py/hikari/issues/1867))

### Documentation Improvements

- Replace mentions of `PRIVATE_MESSAGES` with `DM_MESSAGES` ([#1874](https://github.com/hikari-py/hikari/issues/1874))

---
## 2.0.0.dev123 (2024-03-31)

### Breaking Changes

- Remove previously deprecated `Permissions.MANAGE_EMOJIS_AND_STICKERS` ([#1762](https://github.com/hikari-py/hikari/issues/1762))

### Features

- Allow subscribing to generic events ([#1814](https://github.com/hikari-py/hikari/issues/1814))
- Allow changing guild features (community, etc.) ([#1828](https://github.com/hikari-py/hikari/issues/1828))
- Improve embed parameters typing ([#1841](https://github.com/hikari-py/hikari/issues/1841))

### Bugfixes

- Fix `CommandInteractionOption.value` typehint not including `float` ([#1805](https://github.com/hikari-py/hikari/issues/1805))
- `Member.joined_at` is now nullable due to breaking API change
   - This will be received on guest members with temporary membership ([#1812](https://github.com/hikari-py/hikari/issues/1812))
- Shard rate-limiters are now reset per websocket connection, avoiding a rare issue where a persistent network issue could allow the shard to be rate-limited ([#1813](https://github.com/hikari-py/hikari/issues/1813))

### Documentation Improvements

- Switch documentation to mkdocs ([#1810](https://github.com/hikari-py/hikari/issues/1810))

---
## 2.0.0.dev122 (2023-11-18)

### Deprecation

- Deprecate `Permissions.MANAGE_EMOJIS_AND_STICKERS` in favour of `Permissions.MANAGE_GUILD_EXPREASSIONS` ([#1758](https://github.com/hikari-py/hikari/issues/1758))

### Features

- Add Python 3.12 support. ([#1357](https://github.com/hikari-py/hikari/issues/1357))
- Allow class listeners ([#1661](https://github.com/hikari-py/hikari/issues/1661))
- Add missing `clear_x` methods to `InteractionMessageBuilder`
  - This brings the functionality more in-line with other message edit APIs ([#1740](https://github.com/hikari-py/hikari/issues/1740))
- Add missing permissions ([#1758](https://github.com/hikari-py/hikari/issues/1758))

### Bugfixes

- Fix optional connection "revoked" field KeyError when fetching connections. ([#1720](https://github.com/hikari-py/hikari/issues/1720))
- Ensure shard connect and disconnect always get sent in pairs and properly waited for ([#1744](https://github.com/hikari-py/hikari/issues/1744))
- Improve handing of force exiting a bot (double interrupt)
  - Improve exception message
  - Reset signal handlers to original ones after no longer capturing signals ([#1745](https://github.com/hikari-py/hikari/issues/1745))

---
## 2.0.0.dev121 (2023-09-10)

### Features

- Add `approximate_member_count` and `approximate_presence_count` to `OwnGuild`. ([#1659](https://github.com/hikari-py/hikari/issues/1659))
- Add `CacheSettings.only_my_member` to only cache the bot member. ([#1679](https://github.com/hikari-py/hikari/issues/1679))
- Bots can now utilize `Activity.state`
  - When used with `type` set to `ActivityType.CUSTOM`, it will show as the text for the custom status.
    Syntactic sugar also exists to support simply using `name` instead of `state`.
  - Can be used with other activity types to provide additional information on the activity. ([#1683](https://github.com/hikari-py/hikari/issues/1683))
- Add missing Audit Log event types to `AuditLogEventType` ([#1705](https://github.com/hikari-py/hikari/issues/1705))
- Add `approximate_guild_count` field to own `Application` ([#1712](https://github.com/hikari-py/hikari/issues/1712))

### Bugfixes

- Handle connection reset error on shards. ([#1645](https://github.com/hikari-py/hikari/issues/1645))
- Retry REST requests on connection errors ([#1648](https://github.com/hikari-py/hikari/issues/1648))
- Add support for text in stage channels ([#1653](https://github.com/hikari-py/hikari/issues/1653))
- Fix incorrect calculation for the default avatar of migrated users ([#1673](https://github.com/hikari-py/hikari/issues/1673))
- Fix attachments not being removed in message edits when `attachment` or `attachments` is `None` ([#1702](https://github.com/hikari-py/hikari/issues/1702))

---


## 2.0.0.dev120 (2023-06-08)

### Breaking Changes

- Remove previously deprecated `hikari.impl.bot` module ([#1612](https://github.com/hikari-py/hikari/issues/1612))

### Deprecation

- Deprecate `User.discriminator` ([#1631](https://github.com/hikari-py/hikari/issues/1631))

### Features

- Implement voice messages ([#1609](https://github.com/hikari-py/hikari/issues/1609))
- Implement username changes:
  - Add `global_name`
  - `User.__str__()` respects `global_name` now
  - `User.default_avatar_url` returns correct URL for migrated accounts ([#1631](https://github.com/hikari-py/hikari/issues/1631))

### Bugfixes

- Fix a bug in `RESTClient.edit_guild` which load to closed stream errors ([#1627](https://github.com/hikari-py/hikari/issues/1627))
- Properly handle DM channels in resolved interaction channels. ([#1628](https://github.com/hikari-py/hikari/issues/1628))

---


## 2.0.0.dev119 (2023-05-08)

### Breaking Changes

- Remove deprecated functionality for 2.0.0.dev119
  - Removed `TextInputBuilder.required` in favour of `TextInputBuilder.is_required`.
  - Removed the ability to pass `CommandChoices` instead of `AutocompleteChoiceBuilders` when making autocomplete responses. ([#1580](https://github.com/hikari-py/hikari/issues/1580))

### Bugfixes

- Fix `messages` argument typing for `RESTClient.delete_messages`. ([#1581](https://github.com/hikari-py/hikari/issues/1581))
- Default `HTTPSettings.enable_cleanup_closed` to `False`.
  - CPython3.11 changes around SSLProto have made this quite unstable and prone to errors when dealing with unclosed TLS transports, which ends up in aiohttp calling close and abort twice. ([#1585](https://github.com/hikari-py/hikari/issues/1585))
- `Guild.get_channel`, `Guild.get_emoji`, `Guild.get_sticker` and `Guild.get_role` now only return entries from the relevant guild. ([#1608](https://github.com/hikari-py/hikari/issues/1608))

---


## 2.0.0.dev118 (2023-04-02)

### Breaking Changes

- Refactors to the component builder interfaces which make them flatter:

  * Removed `add_to_container` from `ButtonBuilder`, `LinkButtonBuilder`, `InteractiveButtonBuilder`, `SelectMenuBuilder`, `ChannelSelectMenuBuilder`, and `TextInputBuilder`; these classes are no-longer generic and no-longer take `container` in their inits.
  * Replaced `TextSelectMenuBuilder.add_to_container` with the `TextSelectMenuBuilder.parent` property.
      This new property doesn't "finalise" the addition but rather just returns the parent object, or raises if the select menu is an orphan. This change also involves replacing the `container` parameter in `TextSelectMenuBuilder.__init__` with an optional `parent` parameter.
  * Removed `SelectOptionBuilder.add_to_menu`; this class isn't generic anymore.
  * `TextSelectMenuBuilder.add_option` now takes all the option's configuration as parameters and returns `Self`.
  * Split `MessageActionRowBuilder.add_button` into `.add_interactive_button` and `.add_link_button`.
      These both now take all the button's configuration as parameters and return `Self`.
  * `MessageActionRowBuilder.add_select_menu` now takes all the menu's configuration as parameters and returns `Self`.
      The new `.add_channel_menu` and `.add_text_menu` methods should be used for adding text and channel menus. Where `.add_channel_menu` returns `Self` and `.add_text_menu` returns a text menu builder with a `parent` property for getting back to the action row builder.
  * `ModalActionRowBuilder.add_text_input` now takes all the text input's configuration as parameters and returns `Self`.
  * `min_length` and `max_length` can no-longer be `hikari.undefined.UNDEFINED` for the text input builder, and default to `0` and `4000` respectively. This change effects both the types accepted by `ModalActionRowBuilder.__init__` and the return types of the relevant properties.
  * Removed the `emoji_id` and `emoji_name` parameters from `LinkButtonBuilder.__init__`, and `InteractiveButtonBuilder.__init__`.
  * Removed the `style` and `custom_id` parameters from `LinkButtonBuilder.__init__`.
  * Removed the `url` parameter from `InteractiveButtonBuilder.__init__`. ([#1533](https://github.com/hikari-py/hikari/issues/1533))
- Remove previously deprecated functionality:
  - `Intents.GUILD_BANS` (deprecated alias for `Intents.GUILD_MODERATION`)
  - `ComponentType.SELECT_MENU` (deprecated alias for `Intents.TEXT_SELECT_MENU`)
  - Not passing type through `type` argument explicitly to `MessageActionRowBuilder.add_select_menu` ([#1535](https://github.com/hikari-py/hikari/issues/1535))
- Renamed `StickerPack.banner_hash` to `StickerPack.banner_asset_id`. ([#1572](https://github.com/hikari-py/hikari/issues/1572))

### Deprecation

- Renamed `TextInputBuilder.required` property to `TextInputBuilder.is_required`. ([#1533](https://github.com/hikari-py/hikari/issues/1533))
- Passing `CommandChoice`s instead of `AutocompleteChoiceBuilder`s when making autocomplete responses. ([#1539](https://github.com/hikari-py/hikari/issues/1539))
- `hikari.impl.bot` moved to `hikari.impl.gateway_bot`. ([#1576](https://github.com/hikari-py/hikari/issues/1576))

### Features

- `Role.mention` now returns `"@everyone"` for the `@everyone` role. ([#1528](https://github.com/hikari-py/hikari/issues/1528))
- Refactors to the component builder interfaces which make them flatter:

  * `hikari.undefined.UNDEFINED` can now be passed to `TextInputBuilder.set_placeholder` and `TextInputBuilder.set_value`.
  * The standard implementation of a select option builder is now exposed at `hikari.impl.special_endpoints.SelectOptionBuilder`. ([#1533](https://github.com/hikari-py/hikari/issues/1533))
- `CommandChoice.name_localizations` field and separate `AutocompleteChoiceBuilder` for use when making autocomplete responses. ([#1539](https://github.com/hikari-py/hikari/issues/1539))
- Implement guild role subscriptions. ([#1550](https://github.com/hikari-py/hikari/issues/1550))
- Add `Role.is_guild_linked_role`. ([#1551](https://github.com/hikari-py/hikari/issues/1551))
- `hikari.iterators.LazyIterator.flatten` method for flattening a lazy iterator of synchronous iterables. ([#1562](https://github.com/hikari-py/hikari/issues/1562))
- Support sending stickers when creating a message. ([#1571](https://github.com/hikari-py/hikari/issues/1571))
- Added several set methods for required values to the builders:

  * `CommandBuilder.set_name`
  * `SlashCommandBuilder.set_description`
  * `InteractiveButtonBuilder.set_custom_id`
  * `SelectOptionBuilder.set_label`
  * `SelectOptionBuilder.set_value`
  * `SelectMenuBuilder.set_custom_id` ([#1574](https://github.com/hikari-py/hikari/issues/1574))

### Bugfixes

- `emoji=` can now be passed to `LinkButtonBuilder.__init__` and `InteractiveButtonBuilder.__init__` alone without causing serialization issues (and Pyright will now let you pass it). ([#1533](https://github.com/hikari-py/hikari/issues/1533))
- Open `banner.txt`s with `utf-8` encoding explicitly. ([#1545](https://github.com/hikari-py/hikari/issues/1545))
- Pyright will now let you pass `role_mentions` and `user_mentions` to `InteractionMessageBuilder.__init__`. ([#1560](https://github.com/hikari-py/hikari/issues/1560))
- Fixed forum channel applied tags not being a sequence of snowflakes. ([#1564](https://github.com/hikari-py/hikari/issues/1564))
- Switch to using <https://github.com/discord/twemoji> for emoji images. ([#1568](https://github.com/hikari-py/hikari/issues/1568))
- Fixed sticker pack handling and typing:

  * Fixed deserialization raising when `"banner_asset_id"` or `"cover_sticker_id"` weren't included in the payload.
  * `StickerPack.banner_asset_id` is now correctly typed as `Optional[Snowflake]`.
  * `StickerPack.banner_url` and `StickerPack.make_banner_url` both now correctly return `None` when `StickerPack.banner_asset_id` is `None`. ([#1572](https://github.com/hikari-py/hikari/issues/1572))

---


## 2.0.0.dev117 (2023-03-06)

### Breaking Changes

- Remove previously deprecated functionality:
   - `delete_message_days` parameter for `ban` methods. ([#1496](https://github.com/hikari-py/hikari/issues/1496))
- `type` can no-longer be specified while initialise `hikari.impl.special_endpoints.TextSelectMenuBuilder` and `hikari.impl.special_endpoints.ChannelSelectMenuBuilder`.
  `hikari.api.special_endpoints.SelectOptionBuilder` no-longer inherits from `hikari.api.special_endpoints.ComponentBuilder` (but it still has a `build` method). ([#1509](https://github.com/hikari-py/hikari/issues/1509))

### Features

- Pre-maturely fetch the public key if not present when starting an interaction server. ([#1423](https://github.com/hikari-py/hikari/issues/1423))
- Add and document the new `SUPPRESS_NOTIFICATIONS` message flag. ([#1504](https://github.com/hikari-py/hikari/issues/1504))
- `hikari.impl.special_endpoints.ChannelSelectMenuBuilder` and `hikari.impl.special_endpoints.TextSelectMenuBuilder` are now both exported directly on `hikari.impl`. ([#1508](https://github.com/hikari-py/hikari/issues/1508))
- `type` property to the component builders. ([#1509](https://github.com/hikari-py/hikari/issues/1509))
- Traits now use `abc.abstractmethod`. This gives better type errors. ([#1516](https://github.com/hikari-py/hikari/issues/1516))
- `token_type` now defaults to `"Bot"` when initialising `RESTBot` with a string token. ([#1527](https://github.com/hikari-py/hikari/issues/1527))

### Bugfixes

- Re-export missing exports from `hikari.api.special_endpoints` and `hikari.components`. ([#1501](https://github.com/hikari-py/hikari/issues/1501))
- Fix `PartialSticker.image_url` not accounting for stickers with GIF format. ([#1506](https://github.com/hikari-py/hikari/issues/1506))
- Await bucket manager gc task to completion when closing ([#1529](https://github.com/hikari-py/hikari/issues/1529))

---


## 2.0.0.dev116 (2023-02-06)

### Breaking Changes

- Remove `RateLimitedError` in favour of always waiting on ratelimits. ([#1441](https://github.com/hikari-py/hikari/issues/1441))
-  ([#1455](https://github.com/hikari-py/hikari/issues/1455))
- Default logging to `sys.stdout` stream to bring more in-line with banner output. ([#1485](https://github.com/hikari-py/hikari/issues/1485))

### Deprecation

- Deprecate selects v1 functionality:
   - `ComponentType.SELECT_MENU` -> `ComponentType.TEXT_SELECT_MENU`
   - Not passing `MessageActionRowBuilder.add_select_menu`'s `type` argument explicitly.
   - `InteractionChannel` and `ResolvedOptionData` moved from `hikari.interactions.command_interactions` to `hikari.interactions.base_interactions`. ([#1455](https://github.com/hikari-py/hikari/issues/1455))
- Renamed `Intents.GUILD_BANS` to `Intents.GUILD_MODERATION`. ([#1471](https://github.com/hikari-py/hikari/issues/1471))

### Features

- Add linked roles support (models + endpoints). ([#1422](https://github.com/hikari-py/hikari/issues/1422))
- Add selects v2 components. ([#1455](https://github.com/hikari-py/hikari/issues/1455))
- Added `fetch_self`, `edit`, `delete`, `sync`, and `create_guild` methods to `hikari.templates.Template`. ([#1457](https://github.com/hikari-py/hikari/issues/1457))
- Add ability to suppress optimization warnings through `suppress_optimization_warning=True` to the `GatewayBot` or `RESTBot` constructors. ([#1459](https://github.com/hikari-py/hikari/issues/1459))
- Support GIF sticker image format ([#1464](https://github.com/hikari-py/hikari/issues/1464))
- Add support for guild audit log entry create events. ([#1471](https://github.com/hikari-py/hikari/issues/1471))
- Update `RESTClient.edit_channnel` to support setting `applied_tags` on forum threads. ([#1474](https://github.com/hikari-py/hikari/issues/1474))
- Implement `reply_must_exist` in create message methods ([#1475](https://github.com/hikari-py/hikari/issues/1475))
- Support loading files through `logging.config.fileConfig` in `init_logging`. ([#1485](https://github.com/hikari-py/hikari/issues/1485))
- Add `orjson` as an optional speedup and allow to pass custom `json.dumps` and `json.loads` functions to all components. ([#1486](https://github.com/hikari-py/hikari/issues/1486))

### Bugfixes

- The global ratelimit now abides by `max_rate_limit`. ([#1441](https://github.com/hikari-py/hikari/issues/1441))
- Move `description_localizations` from `PartialCommand` to `SlashCommand` (removing it from `ContextMenuCommand`). ([#1470](https://github.com/hikari-py/hikari/issues/1470))
- Add missing fields to `GuildChannel.edit`. ([#1474](https://github.com/hikari-py/hikari/issues/1474))
- Fix `hikari.webhooks.ChannelFollowWebhook` not including source in all cases.
  - `source_channel` and `source_guild` will be `None` instead. ([#1480](https://github.com/hikari-py/hikari/issues/1480))
- Fix colour logging not occurring on specific terminals (ie, Pycharm). ([#1485](https://github.com/hikari-py/hikari/issues/1485))

---


## 2.0.0.dev115 (2023-01-03)

### Breaking Changes

- Remove previously deprecated functionality.
  This includes:
  - `RESTClient.build_action_row` ([#1438](https://github.com/hikari-py/hikari/issues/1438))

### Bugfixes

- Fix deserializing old forum channels on `GUILD_CREATE` missing some fields. ([#1439](https://github.com/hikari-py/hikari/issues/1439))

---


## 2.0.0.dev114 (2023-01-01)

### Breaking Changes

- `BulkDeleteError`:
  - No longer contains a `messages_skipped` attribute.
  - `messages_deleted` renamed to `deleted_messages`. ([#1134](https://github.com/hikari-py/hikari/issues/1134))
- `RESTApp` and `RESTBucketManager` now need to be started and stopped by using `.start` and `.close`. ([#1230](https://github.com/hikari-py/hikari/issues/1230))
- Remove long deprecated `async with` support for `EventStream`. ([#1426](https://github.com/hikari-py/hikari/issues/1426))

### Deprecation

- Deprecate the `delete_message_days` parameter for PartialGuild.ban and Member.ban. ([#1378](https://github.com/hikari-py/hikari/issues/1378))

### Features

- Allow async iterators in `RESTClient.delete_messages`. ([#1134](https://github.com/hikari-py/hikari/issues/1134))
- `RESTClientImpl` improvements:
   - You can now share client sessions and bucket managers across these objects or have them created for you.
   - Speedup of request lifetime
   - No-ratelimit routes no longer attempt to acquire rate limits
     - Just for safety, a check is in place to treat the route as a rate limited route if a bucket is ever received for it and a error log is emitted. If you spot it around, please inform us! ([#1230](https://github.com/hikari-py/hikari/issues/1230))
- Add `save()` method to `Resource`. ([#1272](https://github.com/hikari-py/hikari/issues/1272))
- Allow specifying the `delete_message_seconds` parameter for PartialGuild.ban and Member.ban.
  - This parameter can be specified as either an int, a float, or a datetime.timedelta object. ([#1378](https://github.com/hikari-py/hikari/issues/1378))
- Support yielding in interaction listeners. ([#1383](https://github.com/hikari-py/hikari/issues/1383))
- Add Indonesian locale as `hikari.Locale.ID`. ([#1404](https://github.com/hikari-py/hikari/issues/1404))
- Improve pyright support ([#1412](https://github.com/hikari-py/hikari/issues/1412))
- Improve error raised when attempting to use an asynchronous iterator synchronously. ([#1419](https://github.com/hikari-py/hikari/issues/1419))
- Add missing `Application` fields:
  - `Application.custom_install_url`
  - `Application.tags`
  - `Application.install_parameters` ([#1420](https://github.com/hikari-py/hikari/issues/1420))
- Add support for guild forum channels. ([#1430](https://github.com/hikari-py/hikari/issues/1430))
- Add a warning when not running in (at least) level 1 optimization mode. ([#1431](https://github.com/hikari-py/hikari/issues/1431))

### Bugfixes

- Buckets across different authentications are not shared any more, which would lead to incorrect rate limiting. ([#1230](https://github.com/hikari-py/hikari/issues/1230))
- Suppress incorrect deprecation warning regarding event loops. ([#1425](https://github.com/hikari-py/hikari/issues/1425))
- Properly close unclosed file descriptor when reading banner.
  - This only affects versions of Python >= 3.9. ([#1434](https://github.com/hikari-py/hikari/issues/1434))
- Start GC of bucket manager when creating a rest client. ([#1435](https://github.com/hikari-py/hikari/issues/1435))
- Fix incorrect value in `CommandBuilder.is_nsfw`. ([#1436](https://github.com/hikari-py/hikari/issues/1436))

---


## 2.0.0.dev113 (2022-12-04)

### Breaking Changes

- Remove previously deprecated functionality.

  This includes:
  - `Message.mentions`
  - `nick` argument in rest methods
  - `edit_permission_overwrites`, `edit_my_nick` and `command_builder` rest methods
  - `CacheView.iterator` ([#1347](https://github.com/hikari-py/hikari/issues/1347))

### Deprecation

- Deprecate `RESTClientImpl.build_action_row` in favour of `RESTClientImpl.build_message_action_row`. ([#1002](https://github.com/hikari-py/hikari/issues/1002))

### Features

- Implement modal interactions.
  - Additionally, it is now guaranteed (typing-wise) that top level components will be an action row ([#1002](https://github.com/hikari-py/hikari/issues/1002))
- Add new `UserFlag.ACTIVE_DEVELOPER`. ([#1355](https://github.com/hikari-py/hikari/issues/1355))
- Allow specifying a filename to `hikari.files.URL`. ([#1368](https://github.com/hikari-py/hikari/issues/1368))
- Only subscribe to voice events when needed in the voice manager. ([#1369](https://github.com/hikari-py/hikari/issues/1369))
- Add functionality to create and deserialize age-restricted (NSFW) commands. ([#1382](https://github.com/hikari-py/hikari/issues/1382))
- Threads cache. ([#1384](https://github.com/hikari-py/hikari/issues/1384))

### Bugfixes

- Allow re-uploading attachments when creating messages ([#1367](https://github.com/hikari-py/hikari/issues/1367))
- Fix error caused when disconnecting the bot and having active voice connections. ([#1369](https://github.com/hikari-py/hikari/issues/1369))
- Remove incorrect `is_nsfw` field from threads.
  - The "NSFW" status is inherited from the parent object and not sent for threads.
  - This also involved moving the base attribute from `GuildChannel` to `PermissibleGuildChannel`. ([#1386](https://github.com/hikari-py/hikari/issues/1386))

### Documentation Improvements

- Documentation overhaul and move to docs.hikari-py.dev domain. ([#1118](https://github.com/hikari-py/hikari/issues/1118))

---


## 2.0.0.dev112 (2022-11-06)

### Breaking Changes

- Moved permission overwrite mapping and permission related methods from `GuildChannel` to `PermissibleGuildChannel`. ([#811](https://github.com/hikari-py/hikari/issues/811))
- Support v10 attachments edits

  This includes breaking changes, features and things to look out for when editing messages:
  - Modifying attachments in messages that contain embeds with any image attached to them now requires the images of that embed
    image to be re-passed in the edit or they will be lost.
  - `attachment` and `attachments` in message edits now support passing an `Attachment` object to keep existing attachments.
  - `replace_attachments` has been removed, as it is now the default.
    - `attachment` and `attachments` now supports `None` to replicate the behaviour of fully removing all attachments.
  - `InteractionMessageBuilder.clear_attachments` has been implemented to remove existing attachments from messages. ([#1260](https://github.com/hikari-py/hikari/issues/1260))

### Features

- Thread support for REST requests and gateway events. ([#811](https://github.com/hikari-py/hikari/issues/811))
- Startup and shutdown callbacks for the RESTBot interface/impl. ([#999](https://github.com/hikari-py/hikari/issues/999))
- Support specifying `with_counts` and `with_expiration` in `RESTClient.fetch_invite` ([#1330](https://github.com/hikari-py/hikari/issues/1330))
- Support for including the `SUPPRESS_EMBEDS` flag while creating a message. ([#1331](https://github.com/hikari-py/hikari/issues/1331))
- Add `MANAGE_EVENTS` permission to `hikari.Permissions` ([#1334](https://github.com/hikari-py/hikari/issues/1334))

### Bugfixes

- Wrong typehint for `InviteGuild.features`. ([#1307](https://github.com/hikari-py/hikari/issues/1307))
- Fix aiohttp error "charset must not be in content type" when using `InteractionServer` ([#1320](https://github.com/hikari-py/hikari/issues/1320))
- The REST list methods (e.g. `fetch_channels`) no-longer raise `hikari.errors.UnrecognisedEntityError` when they encounter an unknown type. ([#1337](https://github.com/hikari-py/hikari/issues/1337))
- Fix deprecation warnings in CPython3.11 in `hikari.internal.ux`. ([#1344](https://github.com/hikari-py/hikari/issues/1344))

---


## 2.0.0.dev111 (2022-09-26)

### Breaking Changes

- Lifetime improvements breaking changes:
  - `GatewayBot.join`'s `until_close` argument removed.
  - `GatewayShardImpl.get_user_id` is no longer async and will now always be available.
  - `GatewayBotAware` no longer defines the default parameters for `join`, `start` and `run`. It is left to implementation detail. ([#1204](https://github.com/hikari-py/hikari/issues/1204))
- Remove support for ProcessPoolExecutor executor when reading files
  - It is much more efficient to use a threadpool executor for I/O actions like this one
    - Due to the nature of process pool, we were also not able to perform proper chunking when reading off the file ([#1273](https://github.com/hikari-py/hikari/issues/1273))

### Deprecation

- Deprecate `CacheView.iterator` in favour of using the `itertools` module. ([#1289](https://github.com/hikari-py/hikari/issues/1289))

### Features

- Add python 3.11-dev support. ([#847](https://github.com/hikari-py/hikari/issues/847))
- Support for Application Command Localizations. ([#1141](https://github.com/hikari-py/hikari/issues/1141))
- Improve components lifetimes:
  - `GatewayBot`:
    - General speedups.
    - Fix a lot of edge cases of hard crashes if the application shuts unexpectedly.
    - More consistent signal handling.
    - `run`'s `shard_ids` argument can now be a `typing.Sequence`.
    - Improved logging.
  - `RESTBot`:
    - Consistent signal handling inline with `GatewayBot`.
    - Improved logging.
    - Improved loop closing.
  - `GatewayShardImpl`:
    - New `is_connected` property to determine whether the shard is connected to the gateway.
    - Faster websocket pulling and heartbeating.
    - Improved error handling.
    - Rate limiting changes:
      - Chunking no longer has its own special ratelimit. Now it is shared with the rest of
      "non-priority" packages sent, which is of 117/60s (3 less than the hard limit).
        - "priority" packages currently only include heartbeating. ([#1204](https://github.com/hikari-py/hikari/issues/1204))
- Implement slash option min/max length fields ([#1216](https://github.com/hikari-py/hikari/issues/1216))
- Add `mention` property to `PartialChannel`. ([#1221](https://github.com/hikari-py/hikari/issues/1221))
- Implement new Gateway reconnect logic enforced by Discord. ([#1245](https://github.com/hikari-py/hikari/issues/1245))

### Bugfixes

- Lifetime improvements bugfixes:
  - `GatewayShardImpl` can now be instantiated out of an async environment for consistency with other components.
  - Correct signal handling in `RESTBot`. ([#1204](https://github.com/hikari-py/hikari/issues/1204))
- Improve `BadRequestError`'s error string. ([#1213](https://github.com/hikari-py/hikari/issues/1213))
- Fix `hikari.impl.VoiceImpl.connect_to` silently failing if the guild or voice channel do not exist by providing a timeout. ([#1242](https://github.com/hikari-py/hikari/issues/1242))
- `dm_permission` now correctly defaults to `True` instead of `False` when parsing command objects from Discord. ([#1243](https://github.com/hikari-py/hikari/issues/1243))
- Fix float precision issues when creating a snowflake from a datetime object. ([#1247](https://github.com/hikari-py/hikari/issues/1247))
- Fix `reposition_channels` to use the correct route. ([#1259](https://github.com/hikari-py/hikari/issues/1259))
- Allow for `replace_attachments` kwarg to be used in `RESTClient.create_initial_response`. ([#1266](https://github.com/hikari-py/hikari/issues/1266))
- Ignore guild create events which contain unavailable guilds ([#1284](https://github.com/hikari-py/hikari/issues/1284))

---


## 2.0.0.dev110 (2022-08-08)

### Breaking Changes

- Removed case of `Member.mention` returning bang (`!`) mention, as it is deprecated by Discord. ([#1207](https://github.com/hikari-py/hikari/issues/1207))

### Deprecation

- `RESTClient.edit_permission_overwrites` renamed to `RESTClient.edit_permission_overwrite` ([#1195](https://github.com/hikari-py/hikari/issues/1195))

### Features

- Add `hikari.events.StickersUpdateEvent` and relevant cache internals.
  Add sticker related public methods onto `hikari.impl.CacheImpl` and `hikari.guilds.Guild`. ([#1126](https://github.com/hikari-py/hikari/issues/1126))
- `GuildVoiceChannel` now inherits from `TextableGuildChannel` instead of `GuildChannel`. ([#1189](https://github.com/hikari-py/hikari/issues/1189))
- Add the `app_permissions` field to command and component interactions. ([#1201](https://github.com/hikari-py/hikari/issues/1201))
- Add application command badge ([#1225](https://github.com/hikari-py/hikari/issues/1225))

### Bugfixes

- Fix how CommandBuilder handles `default_member_permissions` to match the behaviour on PartialCommand. ([#1212](https://github.com/hikari-py/hikari/issues/1212))

---


## 2.0.0.dev109 (2022-06-26)

### Breaking Changes

- Removal of all application commands v1 related fields and endpoints.
   - Discord has completely disabled some endpoints, so we unfortunately can't
     deprecate them instead of removing them ([#1148](https://github.com/hikari-py/hikari/issues/1148))
- Removed the `resolved` attribute from `AutocompleteInteraction` as autocomplete interactions never have resolved objects. ([#1152](https://github.com/hikari-py/hikari/issues/1152))
- `build` methods are now typed as returning `MutableMapping[str, typing.Any]`. ([#1164](https://github.com/hikari-py/hikari/issues/1164))

### Deprecation

- `messages.Mentions` object deprecated
   - Alternatives can be found in the base message object ([#1149](https://github.com/hikari-py/hikari/issues/1149))

### Features

- Add `create` method to `CommandBuilder`. ([#1016](https://github.com/hikari-py/hikari/issues/1016))
- Support for attachments in REST-based interaction responses. ([#1048](https://github.com/hikari-py/hikari/issues/1048))
- Add option to disable automatic member chunking.
  Added the `auto_chunk_members` kwarg to `GatewayBot` and `EventManagerImpl`, which when `False` will disable automatic member chunking. ([#1084](https://github.com/hikari-py/hikari/issues/1084))
- Allow passing multiple event types to the listen decorator.
  Parse union type hints for events if listen decorator is empty. ([#1103](https://github.com/hikari-py/hikari/issues/1103))
- Animated guild banner support. ([#1116](https://github.com/hikari-py/hikari/issues/1116))
- Implement application commands permission v2.
   - New `default_member_permissions` and `is_dm_enabled` related fields.
   - Added `hikari.events.application_events.ApplicationCommandPermissionsUpdate`.
   - Added `APPLICATION_COMMAND_PERMISSION_UPDATE` audit log entry ([#1148](https://github.com/hikari-py/hikari/issues/1148))

### Bugfixes

- Improved pyright support. ([#1108](https://github.com/hikari-py/hikari/issues/1108))
- `RESTClientImpl.fetch_bans` now return a `LazyIterator` to allow pagination of values. ([#1119](https://github.com/hikari-py/hikari/issues/1119))
- Fix unicode decode error caused by `latin-1` encoding when sending the banner. ([#1120](https://github.com/hikari-py/hikari/issues/1120))
- Don't error on an out-of-spec HTTP status code (e.g one of Cloudflare's custom status codes).
  `HTTPResponseError.status` may now be of type `http.HTTPStatus` or `int`. ([#1121](https://github.com/hikari-py/hikari/issues/1121))
- Fix name of polish locale (`hikari.Locale.OL` -> `hikari.Locale.PL`) ([#1144](https://github.com/hikari-py/hikari/issues/1144))
- Properly garbage collect message references in the cache
    - Properly deserialize `PartialMessage.referenced_message` as a partial message ([#1192](https://github.com/hikari-py/hikari/issues/1192))

---


## 2.0.0.dev108 (2022-03-27)

### Breaking Changes

- `hikari.config` has now been split up to `hikari.api.config` and `hikari.impl.config` to avoid leaking impl detail.
  This also means that config types are no-longer accessible at the top level (directly on `hikari`). ([#1067](https://github.com/hikari-py/hikari/issues/1067))
- Hide the entity factory's component deserialize methods. ([#1074](https://github.com/hikari-py/hikari/issues/1074))
- Remove nonce parameter from create message.
  This was purposely removed from the bot api documentation inferring that its no-longer officially supported. ([#1075](https://github.com/hikari-py/hikari/issues/1075))
- Remove `VoiceRegion.is_vip` due to Discord no longer sending it. ([#1086](https://github.com/hikari-py/hikari/issues/1086))
- Remove store sku related application fields and store channels. ([#1092](https://github.com/hikari-py/hikari/issues/1092))

### Deprecation

- Renamed `nick` argument to `nickname` for edit member and add user to guild REST methods. ([#1095](https://github.com/hikari-py/hikari/issues/1095))

### Features

- Scheduled event support. ([#1056](https://github.com/hikari-py/hikari/issues/1056))
- `get_guild()` is now available on `hikari.GuildChannel`. ([#1057](https://github.com/hikari-py/hikari/issues/1057))
- Optimize receiving websocket JSON for the happy path. ([#1058](https://github.com/hikari-py/hikari/issues/1058))
- The threaded file reader now persists the open file pointer while the context manager is active. ([#1073](https://github.com/hikari-py/hikari/issues/1073))
- Optimize event dispatching by only deserializing events when they are needed. ([#1094](https://github.com/hikari-py/hikari/issues/1094))
- Add `hikari.locales.Locale` to help with Discord locale strings. ([#1090](https://github.com/hikari-py/hikari/issues/1090))

### Bugfixes

- `fetch_my_guilds` no-longer returns duplicate guilds nor makes unnecessary (duplicated) requests when `newest_first` is set to `True`. ([#1059](https://github.com/hikari-py/hikari/issues/1059))
- Add `InviteEvent` to `hikari.events.channel_events.__all__`, `hikari.events.__all__` and `hikari.__all__`. ([#1065](https://github.com/hikari-py/hikari/issues/1065))
- Fix incorrect type for ATTACHMENT option values. ([#1066](https://github.com/hikari-py/hikari/issues/1066))
- `EventManager.get_listeners` now correctly defines polymorphic and returns accordingly. ([#1094](https://github.com/hikari-py/hikari/issues/1094))
- Take the major param for webhook without token endpoints when handling bucket ratelimits. ([#1102](https://github.com/hikari-py/hikari/issues/1102))
- Fix incorrect value for `GuildFeature.MORE_STICKERS`. ([#1989](https://github.com/hikari-py/hikari/issues/1989))

---


## 2.0.0.dev107 (2022-03-04)

### Features

- Added a `total_length` function to `hikari.embeds.Embed`
  - Takes into account the character length of the embed's title, description, fields (all field names and values), footer, and author combined.
  - Useful for determining if the embed exceeds Discord's 6000 character limit. ([#796](https://github.com/hikari-py/hikari/issues/796))
- Added attachment command option type support. ([#1015](https://github.com/hikari-py/hikari/issues/1015))
- Add MESSAGE_CONTENT intent. ([#1021](https://github.com/hikari-py/hikari/issues/1021))
- Custom substitutions can now be used in `hikari.internal.ux.print_banner`. ([#1022](https://github.com/hikari-py/hikari/issues/1022))
- `get_guild()` is now available on `hikari.Member`. ([#1025](https://github.com/hikari-py/hikari/issues/1025))
- The notorious "failed to communicate with server" log message is now a warning rather than an error. ([#1041](https://github.com/hikari-py/hikari/issues/1041))
- `hikari.applications`, `hikari.files`, `hikari.snowflakes` and `hikari.undefined` are now all explicitly exported by `hikari.__init__`, allowing pyright to see them without a direct import. ([#1042](https://github.com/hikari-py/hikari/issues/1042))

### Bugfixes

- Fix bucket lock not being released on errors while being acquired, which locked the bucket infinitely ([#841](https://github.com/hikari-py/hikari/issues/841))
- `enable_signal_handlers` now only defaults to `True` when the run/start method is called in the main thread.
  This avoids these functions from always raising when being run in a threaded environment as only the main thread can register signal handlers. ([#998](https://github.com/hikari-py/hikari/issues/998))
- Sub-command options are now properly deserialized in the autocomplete flow to `AutocompleteInteractionOption` instead of `CommandInteractionOption`. ([#1012](https://github.com/hikari-py/hikari/issues/1012))
- Attempt to reconnect on a gateway `TimeoutError`. ([#1014](https://github.com/hikari-py/hikari/issues/1014))
- Properly close `GatewayBot` when not fully started. ([#1023](https://github.com/hikari-py/hikari/issues/1023))
- The async context manager returned by `File.stream` now errors on enter if the target file doesn't exist to improve error handling when a file that doesn't exist is sent as an attachment.

  The multiprocessing file reader strategy now expands user relative (`~`) links (like the threaded strategy). ([#1046](https://github.com/hikari-py/hikari/issues/1046))

---


## 2.0.0.dev106 (2022-02-03)

### Breaking Changes

- Running the standard interaction server implementation now requires a `hikari[server]` install.

  This matches a switch over to PyNacl for the cryptographic payload validation. ([#986](https://github.com/hikari-py/hikari/issues/986))

### Deprecation

- Deprecated `RESTClient.command_builder` and `RESTClient.create_application_command`.

  You should switch to `RESTClient.slash_command_builder`and `RESTClient.create_slash_command` respectively. ([#924](https://github.com/hikari-py/hikari/issues/924))

### Features

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

### Bugfixes

- Relaxed typing of methods with union entry specific specialisations through overloads. ([#876](https://github.com/hikari-py/hikari/issues/876))
- Fix deprecation warnings raised by usage of `asyncio.gather` outside of an active event loop in `GatewayBot.run`. ([#954](https://github.com/hikari-py/hikari/issues/954))
- UTF-8 characters are now properly handled for audit-log reasons in REST requests. ([#963](https://github.com/hikari-py/hikari/issues/963))
- Fix magic methods for `UserImpl` and its subclasses. ([#982](https://github.com/hikari-py/hikari/issues/982))

---


## 2.0.0.dev105 (2022-01-01)

### Features

- Add min_value and max_value to `CommandOption` ([#920](https://github.com/hikari-py/hikari/issues/920))
- Add `flags` attribute to Application ([#939](https://github.com/hikari-py/hikari/issues/939))
- Implement member timeouts
   - Add `raw_communication_disabled_until` and `communication_disabled_until` to `Member`
   - Add `MODERATE_MEMBERS` to `Permission`
   - Add `communication_disabled_until` attribute to `edit_member` ([#940](https://github.com/hikari-py/hikari/issues/940))

### Bugfixes

- Improved pyright compatibility and introduced pyright "type-completeness" checking. ([#916](https://github.com/hikari-py/hikari/issues/916))
- Add EventStream.filter specialisation to the abc. ([#917](https://github.com/hikari-py/hikari/issues/917))
- Update the app command name regex to account for more recently documented support for non-english characters on Discord's end. ([#918](https://github.com/hikari-py/hikari/issues/918))
- Fix reposition_roles using the wrong route. ([#928](https://github.com/hikari-py/hikari/issues/928))
- Fix `PartialSticker.image_url` not passing the hash as a string ([#930](https://github.com/hikari-py/hikari/issues/930))
- Fixed the url being generated for role icons to not erroneously insert ".png" before the file extension ([#931](https://github.com/hikari-py/hikari/issues/931))
- Fix some bugs in message deserialization
    - Remove case for setting `member` and `reference_message` to `undefined.Undefined` in full message deserialization
    - Don't set `message.member` to `undefined.UNDEFINED` on partial message deserialization if message was sent by a webhook ([#933](https://github.com/hikari-py/hikari/issues/933))

---


## 2.0.0.dev104 (2021-11-22)

### Breaking Changes

- Remove the redundant `ChannelCreateEvent`, `ChannelUpdateEvent` and `ChannelDeleteEvent` base classes.
  `GuildChannelCreateEvent`, `GuildChannelUpdateEvent` and `GuildChannelDeleteEvent` should now be used. ([#862](https://github.com/hikari-py/hikari/issues/862))
- Split bulk message delete from normal delete
    - The new event is now `hikari.events.message_events.GuildBulkMessageDeleteEvent` ([#897](https://github.com/hikari-py/hikari/issues/897))

### Deprecation

- `edit_my_nick` rest method. ([#827](https://github.com/hikari-py/hikari/issues/827))
- EventStream is now a sync context manager, not async. ([#864](https://github.com/hikari-py/hikari/issues/864))

### Features

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

### Bugfixes

- Don't raise in bulk delete when message not found by delete single message endpoint ([#828](https://github.com/hikari-py/hikari/issues/828))
- Setup basic handler if no handlers are defined in favour passed to `logging.config.dictConfig` ([#832](https://github.com/hikari-py/hikari/issues/832))
- InteractionMessageBuilder and RESTClientImpl.create_interaction_response now cast content to str to be consistent with the other message create methods. ([#834](https://github.com/hikari-py/hikari/issues/834))
- create_sticker method failing due to using an incorrect body. ([#858](https://github.com/hikari-py/hikari/issues/858))
- Fix logic for asserting listeners to not error when using defaults for other arguments ([#911](https://github.com/hikari-py/hikari/issues/911))
- Fix error message given by action row when a conflicted type is added. ([#912](https://github.com/hikari-py/hikari/issues/912))

---


## 2.0.0.dev103 (2021-10-06)

### Breaking Changes

- `USE_PUBLIC_THREADS` and `USE_PRIVATE_THREADS` permissions have been removed in favour of new threads permission
  - New permissions are split into `CREATE_PUBLIC_THREADS`, `CREATE_PRIVATE_THREADS` and `SEND_MESSAGES_IN_THREADS` ([#799](https://github.com/hikari-py/hikari/issues/799))
- `GuildAvailableEvent` will no longer fire when the bot joins new guilds
  - Some `guild_create`-ish methods were renamed to `guild_available` ([#809](https://github.com/hikari-py/hikari/issues/809))
- Remove `hikari.errors.RESTErrorCode` enum
  - The message that is sent with the error code is the info that the enum contained ([#816](https://github.com/hikari-py/hikari/issues/816))
- PermissionOverwrite doesn't inherit from Unique anymore and isn't hashable. Equality checks now consider all its fields. ([#820](https://github.com/hikari-py/hikari/issues/820))

### Features

- Add new `START_EMBEDDED_ACTIVITIES` permission ([#798](https://github.com/hikari-py/hikari/issues/798))
- Support new `channel_types` field in `CommandOption` ([#800](https://github.com/hikari-py/hikari/issues/800))
- Add the `add_component` method to `hikari.api.special_endpoints.ActionRowBuilder` ([#804](https://github.com/hikari-py/hikari/issues/804))
- Add `old_guild` attribute to `GuildLeaveEvent`. ([#806](https://github.com/hikari-py/hikari/issues/806))
- Add `GuildJoinEvent` that will fire when the bot joins new guilds ([#809](https://github.com/hikari-py/hikari/issues/809))

### Bugfixes

- Fix re-uploading forms with resources ([#787](https://github.com/hikari-py/hikari/issues/787))
- Prevent double linking embed resources, which causes them to upload twice
  - This was caused by attempting to move the resource from one embed to another ([#788](https://github.com/hikari-py/hikari/issues/788))
- Fix `BulkDeleteError` returning incorrect values for `messages_skipped`
  - This affected the `__str__` and `percentage_completion`, which also returned incorrect values ([#817](https://github.com/hikari-py/hikari/issues/817))

### Documentation Improvements

- Add docstrings to the remaining undocumented `GatewayBot` methods ([#804](https://github.com/hikari-py/hikari/issues/804))

---


## 2.0.0.dev102 (2021-09-19)

### Deprecations and Removals

- `MessageType.APPLICATION_COMMAND` renamed to `MessageType.CHAT_INPUT` ([#775](https://github.com/hikari-py/hikari/issues/775))
- Removal of deprecated `hikari.impl.bot.BotApp` and `hikari.traits.BotAware`
  - Use `hikari.impl.bot.GatewayBot` and `hikari.traits.GatewayBotAware` respectively instead ([#778](https://github.com/hikari-py/hikari/issues/778))

### Features

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

### Bugfixes

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

### Documentation Improvements

- Fix typo in Colorish docstring ([#755](https://github.com/hikari-py/hikari/issues/755))
- Remove duplicate raise type in REST and guilds docstrings ([#768](https://github.com/hikari-py/hikari/issues/768))
- Fix various spelling mistakes ([#773](https://github.com/hikari-py/hikari/issues/773))

---


*The changelog was added during the development of version 2.0.0.dev102, so nothing prior is documented here.*

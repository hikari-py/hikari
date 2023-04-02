Fix sticker packs:

* Fixed raises of deserialization.
* `StickerPack.banner_asset_id` is now correctly typed as `Optional[Snowflake]`.
* `StickerPack.banner_url` and `StickerPack.make_banner_url` both now correctly return `None` when `StickerPack.banner_asset_id` is `None`.

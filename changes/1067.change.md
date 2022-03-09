`hikari.config` has now been split up to `hikari.api.config` and `hikari.impl.config` to avoid leaking impl detail.
This also means that config types are no-longer accessible at the top level (directly on `hikari`).

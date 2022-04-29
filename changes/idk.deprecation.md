Deprecate application commands v1 related fields and endpoints.
 - `RESTClientImpl.set_application_guild_commands_permissions` deprecated due to Discord disabling it.
   - Instead, you can use `RESTClientImpl.set_application_command_permissions` to set the permissions per command.
 - `default_permission` field in all objects with it.
   - You can instead use `default_member_permissions` related fields.

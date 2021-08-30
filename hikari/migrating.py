"""
## Migrating from discord.py to hikari, a sane beginners guide.

Hikari is built around the idea of being performant and extendable.
This means that it does not have a built in command handler, it lets
you choose whichever route you wish to take. Due to this, command handling
will be covered in the bottom part of this guide.


#### Users

`discord.User` translates over to `hikari.users.User`

The usage of which is fairly similar between packages with a notable exception
being hikari uses `username` where discord.py simply uses `hikari.users.User.name`
"""

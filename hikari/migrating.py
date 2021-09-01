"""
## Migrating from discord.py to hikari, a sane beginners guide.

Hikari is built around the idea of being performant and extendable.
This means that it does not have a built in command handler, it lets
you choose whichever route you wish to take. Due to this, command handling
will be covered in the bottom part of this guide.


The following will detail major thing's I've picked up. There are details missing but if your unsure simply check the docs.

#### Users

`discord.User` translates over to `hikari.users.User`

The usage of which is fairly similar between packages with a notable exception
being hikari uses `username` where discord.py simply uses `hikari.users.User.name`


#### Members

`discord.Member` translates over to `hikari.guilds.Member`

Usage differences include:
 - There is no .guild, you will need to fetch it using .guild_id
 - You can add a singular role with `hikari.guilds.Member.add_role`
 - There are no attached options such as `discord.Member.mentioned_in`


#### Guilds

`discord.Guild` translates over to `hikari.guilds.Guild`

Most usage differences are that there are no cached attributes, instead you will need to call methods on a guild in order to get the relevant data back. 
For this reason, I'd recomennd checking the docs for your usecase.

For example:
 - There is no members attribute, instead it is a method called get_members()
 
 
#### Embeds

`discord.Embed` translates over to `hikari.embeds.Embed`

The usage of which is basically the same, with some small changes such as icon vs icon_url. 
Something notable however, is the lack of `from_dict` and `to_dict` methods
"""

# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""An example OAuth server."""

from __future__ import annotations

import logging
import os

from aiohttp import web

import hikari

logging.basicConfig(level=logging.DEBUG)

host = "localhost"
port = 8080
CLIENT_ID = int(os.environ["CLIENT_ID"])  # ID as an int
CLIENT_SECRET = os.environ["CLIENT_SECRET"]  # Secret as a str
BOT_TOKEN = os.environ["BOT_TOKEN"]  # Token as a str
CHANNEL_ID = int(os.environ["CHANNEL_ID"])  # Channel to post in as an int
REDIRECT_URI = "http://localhost:8080"

route_table = web.RouteTableDef()


@route_table.get("/")
async def oauth(request: web.Request) -> web.Response:
    """Handle an OAuth request."""
    code = request.query.get("code")
    if not code:
        return web.json_response({"error": "'code' is not provided"}, status=400)

    discord_rest: hikari.RESTApp = request.app["discord_rest"]

    # Exchange code to acquire a Bearer one for the user
    async with discord_rest.acquire(None) as r:
        auth = await r.authorize_access_token(CLIENT_ID, CLIENT_SECRET, code, REDIRECT_URI)

    # Perform a request as the user to get their own user object
    async with discord_rest.acquire(auth.access_token, hikari.TokenType.BEARER) as client:
        user = await client.fetch_my_user()
        # user is a hikari.OwnUser object where we can access attributes on it

    # Notify the success
    async with discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as client:
        await client.create_message(CHANNEL_ID, f"{user} ({user.id}) just authorized!")

    return web.Response(text="Successfully authenticated!")


async def start_discord_rest(app: web.Application) -> None:
    """Start the RESTApp."""
    discord_rest = hikari.RESTApp()
    await discord_rest.start()

    app["discord_rest"] = discord_rest


async def stop_discord_rest(app: web.Application) -> None:
    """Stop the RESTApp."""
    discord_rest: hikari.RESTApp = app["discord_rest"]

    await discord_rest.close()


if __name__ == "__main__":
    server = web.Application()
    server.add_routes(route_table)

    server.on_startup.append(start_discord_rest)
    server.on_cleanup.append(stop_discord_rest)

    web.run_app(server, host=host, port=port)

import logging
import os
from typing import Any

import rillrate
from rillrate import prime as rr_prime

import hikari

PREFIX = ","

PACKAGE = "Package"
DASHBOARD = "Dashboard"
GROUP_CONFIG = "1 - Config"


def is_command(cmd_name: str, content: str) -> bool:
    return content.startswith(f"{PREFIX}{cmd_name}")


class Data:
    def __init__(self) -> None:
        self.value = 0


class Bot(hikari.GatewayBot):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.data = Data()


# Startup the dashboard.
# To see the dashboard, go to http://localhost:6361/ui/
rillrate.install()
bot = Bot(token=os.environ["DISCORD_TOKEN"], intents=hikari.Intents.ALL)


values = []
for i in range(0, 256 + 1):
    if i % 32 == 0:
        values.append(str(i))


selector = rr_prime.Selector(f"{PACKAGE}.{DASHBOARD}.{GROUP_CONFIG}.Selector", label="Choose!", options=values)
slider = rr_prime.Slider(
    f"{PACKAGE}.{DASHBOARD}.{GROUP_CONFIG}.Slider", label="More fine grain control", min=0, max=256, step=2
)


def selector_callback(activity: rillrate.Activity, action: rillrate.Action) -> None:
    logging.info("Selector activity: %s | action = %s", activity, action)

    if action is not None:
        logging.info("Selected: %s", action.value)

        selector.apply(action.value)
        slider.apply(float(action.value))

        bot.data.value = int(action.value)


def slider_callback(activity: rillrate.Activity, action: rillrate.Action) -> None:
    logging.info("Slider activity: %s | action = %s", activity, action)

    if action is not None:
        logging.info("Slided: %f", action.value)

        slider.apply(action.value)
        selector.apply(str(int(action.value)))

        bot.data.value = int(action.value)


selector.sync_callback(selector_callback)
slider.sync_callback(slider_callback)


@bot.listen()
async def message(event: hikari.GuildMessageCreateEvent) -> None:
    if event.is_bot or not event.content:
        return

    if event.content.startswith(PREFIX):
        if is_command("ping", event.content):
            await event.message.respond("Ping?")
        elif is_command("value", event.content):
            await event.message.respond(f"Current value: {bot.data.value}")


@bot.listen()
async def on_ready(event: hikari.ShardReadyEvent) -> None:
    logging.info("Bot is ready! %s", event)


bot.run()

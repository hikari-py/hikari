import os
import logging

import hikari
import rillrate
from rillrate import prime as rr_prime

PREFIX = ","

def is_command(cmd_name: str, content: str) -> bool:
    return content.startswith(f"{PREFIX}{cmd_name}")

class Data:
    def __init__(self):
        self.value = 0

class Bot(hikari.GatewayBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = Data()

rillrate.install()
bot = Bot(token=os.environ["DISCORD_TOKEN"], intents=hikari.Intents.ALL)

values = []
for i in range(0, 256+1):
    if i % 32 == 0:
        values.append(str(i))

selector = rr_prime.Selector("Package.Dashboard.1 - Config.Selector", label="Choose!", options=values)
slider = rr_prime.Slider("Package.Dashboard.1 - Config.Slider", label="More fine grain control", min=0, max=256, step=2)

def selector_callback(activity, action):
    logging.info("Selector activity: %s | action = %s", activity, action)

    if action is not None:
        logging.info("Selected: %s", action.value)

        selector.apply(action.value)
        slider.apply(float(action.value))

        bot.data.value = int(action.value)

selector.sync_callback(selector_callback)


def slider_callback(activity, action):
    logging.info("Slider activity: %s | action = %s", activity, action)

    if action is not None:
        logging.info("Slided: %f", action.value)

        slider.apply(action.value)
        selector.apply(str(int(action.value)))

        bot.data.value = int(action.value)

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

# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""A simple bot that can send an audio file as a voice message."""

from __future__ import annotations

import base64
import os

import numpy as np
from pydub import AudioSegment

import hikari

bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])


# This function works at time of writing this (2025.03.22) but
# Discord states that this is an implementation detail and might
# change without notice. You have been warned!
def calculate_waveform(audio_file_path: str) -> tuple[str, float]:
    """Calculate the waveform and the duration from an audio file."""
    # Author note: This function is a python port from here:
    # https://github.com/Vendicated/Vencord/blob/b3bff83dd5040950c55e09bed9e47a60490f81d8/src/plugins/voiceMessages/index.tsx#L145

    # Get an array of samples from the audio file.
    # Note:
    #   To use any other file format then .wav you need
    #   to install ffmpeg or libav
    audio = AudioSegment.from_file(audio_file_path)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

    # Normalize the Samples from -1 to 1
    samples /= np.iinfo(audio.array_type).max

    # Determine the duration of the audio file in seconds
    duration = len(audio) / 1000.0

    # Determine the number of "bins"
    num_bins = np.clip(int(duration * 10), min(32, len(samples)), 256)

    # Determine the amount of samples for each bin
    samples_per_bin = len(samples) // num_bins

    # Create an array for the bins, each bin being 0 at first
    bins = np.zeros(num_bins, dtype=np.uint8)

    for i in range(num_bins):
        start = i * samples_per_bin
        end = start + samples_per_bin
        # Compute root-mean-square for each bin to determine the
        # "volume" of each bin
        rms = np.sqrt(np.mean(np.square(samples[start:end])))
        # Multiply the rms by 255 since each bin has 8 bits
        bins[i] = int(rms * 255)

    # Normalize bins
    max_bin = np.max(bins)
    if max_bin > 0:
        ratio = 1 + (255 / max_bin - 1) * min(1, 100 * (max_bin / 255) ** 3)
        bins = np.minimum(255, (bins * ratio).astype(np.uint8))

    # encode it using base64 since discord wants that
    waveform_encoded = base64.b64encode(bins.tobytes()).decode("utf-8")

    return waveform_encoded, duration


@bot.listen()
async def register_commands(_: hikari.StartingEvent) -> None:
    """Register /audio command."""
    application = await bot.rest.fetch_application()

    commands = [bot.rest.slash_command_builder("audio", "Receive a voice message from the bot!")]

    await bot.rest.set_application_commands(application=application.id, commands=commands)


@bot.listen()
async def handle_interactions(event: hikari.CommandInteractionCreateEvent) -> None:
    """Listen for command interaction."""
    if event.interaction.command_name == "audio":
        waveform, duration = calculate_waveform("./sample.wav")
        await event.app.rest.create_interaction_voice_message_response(
            interaction=event.interaction,
            token=event.interaction.token,
            attachment=hikari.File("./sample.wav"),
            waveform=waveform,
            duration=duration,
        )


bot.run()

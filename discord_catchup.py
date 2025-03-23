import os
import asyncio
import logging
import click
import discord
from discord.ext import commands
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_token: str
    debug_logging: bool = False

    class Config:
        env_file = ".env"


# Load settings from environment variables or .env file
settings = Settings()

# Set up logging
logging_level = logging.DEBUG if settings.debug_logging else logging.WARNING
logging.basicConfig(level=logging_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("discord_catchup")

# Create Discord client with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
client = commands.Bot(command_prefix="!", intents=intents)


async def get_channels(guild_id):
    """Get all channels in a guild."""
    guild = await client.fetch_guild(guild_id)
    channels = await guild.fetch_channels()
    return channels


async def get_threads(guild_id, channel_id=None):
    """Get all threads in a guild, optionally filtered by channel."""
    guild = await client.fetch_guild(guild_id)

    if channel_id:
        channel = await client.fetch_channel(channel_id)
        threads = await channel.fetch_active_threads()
    else:
        threads = []
        channels = await guild.fetch_channels()
        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                active_threads = await channel.fetch_active_threads()
                threads.extend(active_threads)

    return threads


async def get_messages(channel_id, limit=10):
    """Get the last N messages from a channel or thread."""
    channel = await client.fetch_channel(channel_id)
    messages = []

    async for message in channel.history(limit=limit):
        messages.append(message)

    return messages


@click.group()
def cli():
    """Discord CLI tool for retrieving channel information and messages."""
    pass


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
def list_channels(guild_id):
    """List all channels in a Discord server."""

    async def run():
        channels = await get_channels(int(guild_id))

        click.echo("Channels in the server:")
        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                click.echo(f"Text Channel - {channel.name} (ID: {channel.id})")
            elif isinstance(channel, discord.VoiceChannel):
                click.echo(f"Voice Channel - {channel.name} (ID: {channel.id})")
            elif isinstance(channel, discord.CategoryChannel):
                click.echo(f"Category - {channel.name} (ID: {channel.id})")
            else:
                click.echo(f"Other Channel - {channel.name} (ID: {channel.id})")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
@click.option("--channel-id", help="Optional channel ID to filter threads")
def list_threads(guild_id, channel_id):
    """List all threads in a Discord server, optionally filtered by channel."""

    async def run():
        threads = await get_threads(int(guild_id), int(channel_id) if channel_id else None)

        click.echo("Threads in the server:")
        for thread in threads:
            click.echo(
                f"Thread - {thread.name} (ID: {thread.id}, Parent: {thread.parent.name if thread.parent else 'None'})"
            )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@cli.command()
@click.option("--channel-id", required=True, help="Channel or thread ID")
@click.option("--limit", default=10, help="Number of messages to retrieve (default: 10)")
def get_messages_cmd(channel_id, limit):
    """Retrieve the last N messages from a channel or thread."""

    async def run():
        messages = await get_messages(int(channel_id), limit)

        click.echo(f"Last {limit} messages from channel/thread {channel_id}:")
        for message in messages:
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"[{timestamp}] {message.author.name}: {message.content}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@client.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f"Logged in as {client.user.name}")


def main():
    """Start the Discord client and CLI."""

    # Use asyncio to run the bot login in the background
    async def start_client():
        logger.debug("Starting Discord client...")
        await client.login(settings.discord_token)
        logger.debug("Logged in successfully.")

    async def close_client():
        logger.debug("Closing Discord client...")
        await client.close()
        logger.debug("Discord client closed successfully.")

    logger.debug("Starting Discord Event Loop...")
    loop = asyncio.get_event_loop()
    logger.debug("Running Discord client...")
    loop.run_until_complete(start_client())

    try:
        # Run the CLI commands
        cli()
    finally:
        # Ensure we close the client session
        loop.run_until_complete(close_client())
        loop.close()


if __name__ == "__main__":
    main()

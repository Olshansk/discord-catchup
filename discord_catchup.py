import os
import asyncio
import logging
import click
import discord
from discord.ext import commands
from pydantic_settings import BaseSettings
from InquirerPy import inquirer
from InquirerPy.base.control import Choice


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
@click.option("--interactive", is_flag=True, help="Use interactive mode to navigate channels")
def list_channels(guild_id, interactive):
    """List all channels in a Discord server."""

    async def run():
        channels = await get_channels(int(guild_id))

        if not interactive:
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
            return

        # Organize channels by category for interactive mode
        categories = {}
        uncategorized = []

        for channel in channels:
            if isinstance(channel, discord.CategoryChannel):
                categories[channel.id] = {"name": channel.name, "channels": []}

        for channel in channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                if channel.category_id and channel.category_id in categories:
                    categories[channel.category_id]["channels"].append(channel)
                else:
                    uncategorized.append(channel)

        # Create choices for category selection
        category_choices = [
            Choice(value=cat_id, name=f"{cat_data['name']} ({len(cat_data['channels'])} channels)")
            for cat_id, cat_data in categories.items()
        ]

        if uncategorized:
            category_choices.append(
                Choice(value="uncategorized", name=f"Uncategorized ({len(uncategorized)} channels)")
            )

        category_choices.append(Choice(value="all", name="Show all channels"))

        # Ask user to select a category
        selected_category = inquirer.select(
            message="Select a category:",
            choices=category_choices,
        ).execute()

        # Show channels based on selection
        if selected_category == "all":
            # Show all channels
            channel_choices = []
            for channel in channels:
                if isinstance(channel, discord.TextChannel):
                    channel_choices.append(Choice(value=str(channel.id), name=f"# {channel.name}"))
                elif isinstance(channel, discord.VoiceChannel):
                    channel_choices.append(Choice(value=str(channel.id), name=f"🔊 {channel.name}"))

        elif selected_category == "uncategorized":
            # Show uncategorized channels
            channel_choices = []
            for channel in uncategorized:
                if isinstance(channel, discord.TextChannel):
                    channel_choices.append(Choice(value=str(channel.id), name=f"# {channel.name}"))
                elif isinstance(channel, discord.VoiceChannel):
                    channel_choices.append(Choice(value=str(channel.id), name=f"🔊 {channel.name}"))

        else:
            # Show channels in selected category
            channel_choices = []
            for channel in categories[selected_category]["channels"]:
                if isinstance(channel, discord.TextChannel):
                    channel_choices.append(Choice(value=str(channel.id), name=f"# {channel.name}"))
                elif isinstance(channel, discord.VoiceChannel):
                    channel_choices.append(Choice(value=str(channel.id), name=f"🔊 {channel.name}"))

        if channel_choices:
            selected_channel = inquirer.select(
                message="Select a channel:",
                choices=channel_choices,
            ).execute()

            # Ask what action to take with the selected channel
            action = inquirer.select(
                message=f"What would you like to do with channel {selected_channel}?",
                choices=[
                    Choice(value="messages", name="Get messages"),
                    Choice(value="threads", name="List threads"),
                    Choice(value="copy", name="Copy channel ID to clipboard"),
                ],
            ).execute()

            if action == "messages":
                # Ask for number of messages
                limit = inquirer.number(
                    message="How many messages do you want to retrieve?",
                    min_allowed=1,
                    max_allowed=100,
                    default=10,
                ).execute()

                # Get messages
                messages = await get_messages(int(selected_channel), limit)
                click.echo(f"\nLast {limit} messages from channel:")
                for message in messages:
                    timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    click.echo(f"[{timestamp}] {message.author.name}: {message.content}")

            elif action == "threads":
                # List threads in the channel
                threads = await get_threads(int(guild_id), int(selected_channel))
                click.echo(f"\nThreads in channel:")
                for thread in threads:
                    click.echo(f"Thread - {thread.name} (ID: {thread.id})")

            elif action == "copy":
                try:
                    import pyperclip

                    pyperclip.copy(selected_channel)
                    click.echo(f"Channel ID {selected_channel} copied to clipboard")
                except ImportError:
                    click.echo(f"Channel ID: {selected_channel} (pyperclip not installed, could not copy to clipboard)")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
@click.option("--channel-id", help="Optional channel ID to filter threads")
@click.option("--interactive", is_flag=True, help="Use interactive mode to navigate threads")
def list_threads(guild_id, channel_id, interactive):
    """List all threads in a Discord server, optionally filtered by channel."""

    async def run():
        threads = await get_threads(int(guild_id), int(channel_id) if channel_id else None)

        if not interactive:
            click.echo("Threads in the server:")
            for thread in threads:
                click.echo(
                    f"Thread - {thread.name} (ID: {thread.id}, Parent: {thread.parent.name if thread.parent else 'None'})"
                )
            return

        if not threads:
            click.echo("No threads found.")
            return

        # Create choices for thread selection
        thread_choices = [
            Choice(
                value=str(thread.id), name=f"{thread.name} (in #{thread.parent.name if thread.parent else 'unknown'})"
            )
            for thread in threads
        ]

        selected_thread = inquirer.select(
            message="Select a thread:",
            choices=thread_choices,
        ).execute()

        # Ask what action to take with the selected thread
        action = inquirer.select(
            message=f"What would you like to do with thread {selected_thread}?",
            choices=[
                Choice(value="messages", name="Get messages"),
                Choice(value="copy", name="Copy thread ID to clipboard"),
            ],
        ).execute()

        if action == "messages":
            # Ask for number of messages
            limit = inquirer.number(
                message="How many messages do you want to retrieve?",
                min_allowed=1,
                max_allowed=100,
                default=10,
            ).execute()

            # Get messages
            messages = await get_messages(int(selected_thread), limit)
            click.echo(f"\nLast {limit} messages from thread:")
            for message in messages:
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                click.echo(f"[{timestamp}] {message.author.name}: {message.content}")

        elif action == "copy":
            try:
                import pyperclip

                pyperclip.copy(selected_thread)
                click.echo(f"Thread ID {selected_thread} copied to clipboard")
            except ImportError:
                click.echo(f"Thread ID: {selected_thread} (pyperclip not installed, could not copy to clipboard)")

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


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
def interactive(guild_id):
    """Interactive navigation of Discord server."""

    async def run():
        while True:
            # Main menu
            action = inquirer.select(
                message="What would you like to do?",
                choices=[
                    Choice(value="channels", name="Browse channels"),
                    Choice(value="threads", name="Browse threads"),
                    Choice(value="exit", name="Exit"),
                ],
            ).execute()

            if action == "exit":
                break
            elif action == "channels":
                await list_channels.callback(guild_id, interactive=True)
            elif action == "threads":
                await list_threads.callback(guild_id, None, interactive=True)

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

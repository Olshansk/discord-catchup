import os
import asyncio
import logging
from typing import Dict, List, Optional, Tuple

import click
import discord
from InquirerPy import inquirer
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_token: str
    debug_logging: bool = False

    class Config:
        env_file = ".env"


# Load settings
settings = Settings()

# Set up logging
logging_level = logging.DEBUG if settings.debug_logging else logging.WARNING
logging.basicConfig(
    level=logging_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("discord_catchup")

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
client = discord.Client(intents=intents)


@click.group()
def cli():
    """Discord CLI tool for retrieving channel information and messages."""
    pass


async def fetch_guild_channels(
    guild_id: str,
) -> Tuple[discord.Guild, List[discord.abc.GuildChannel]]:
    """Fetch a guild and its channels.

    Args:
        guild_id: The ID of the guild to fetch

    Returns:
        Tuple containing the guild object and list of channel objects
    """
    logger.debug(f"Fetching guild {guild_id}...")
    guild = await client.fetch_guild(int(guild_id))

    logger.debug("Fetching channels...")
    channels = await guild.fetch_channels()

    return guild, channels


def organize_channels_by_category(
    channels: List[discord.abc.GuildChannel],
) -> Tuple[Dict, List]:
    """Organize channels into categories.

    Args:
        channels: List of channel objects

    Returns:
        Tuple containing a dictionary of categories and a list of uncategorized channels
    """
    categories = {}
    uncategorized = []

    # First pass: identify categories
    for channel in channels:
        if isinstance(channel, discord.CategoryChannel):
            categories[channel.id] = {"name": channel.name, "channels": []}

    # Second pass: assign text channels to categories
    for channel in channels:
        if isinstance(channel, discord.TextChannel):
            if channel.category_id and channel.category_id in categories:
                categories[channel.category_id]["channels"].append(channel)
            else:
                uncategorized.append(channel)

    return categories, uncategorized


async def select_category(categories: Dict, uncategorized: List) -> Tuple[str, List]:
    """Display interactive prompt to select a category.

    Args:
        categories: Dictionary of category information
        uncategorized: List of uncategorized channels

    Returns:
        Tuple containing the selected category name and list of channels in that category
    """
    # Create category choices
    category_choices = [
        f"{cat_data['name']} ({len(cat_data['channels'])} channels)"
        for cat_id, cat_data in categories.items()
    ]

    if uncategorized:
        category_choices.append(f"Uncategorized ({len(uncategorized)} channels)")

    # Map display strings back to category IDs
    category_map = {}
    for i, (cat_id, cat_data) in enumerate(categories.items()):
        category_map[category_choices[i]] = cat_id

    if uncategorized:
        category_map[category_choices[-1]] = "uncategorized"

    # Use fuzzy search for category selection
    selected_category_display = await inquirer.fuzzy(
        message="Select a category:", choices=category_choices, max_height="70%"
    ).execute_async()

    selected_category_id = category_map[selected_category_display]

    # Get channels for selected category
    if selected_category_id == "uncategorized":
        channel_list = uncategorized
        selected_category_name = "Uncategorized"
    else:
        channel_list = categories[selected_category_id]["channels"]
        selected_category_name = categories[selected_category_id]["name"]

    return selected_category_name, channel_list


async def select_channel(
    channel_list: List[discord.TextChannel],
) -> discord.TextChannel:
    """Display interactive prompt to select a channel.

    Args:
        channel_list: List of channel objects

    Returns:
        Selected channel object
    """
    if not channel_list:
        click.echo("No channels found in this category.")
        return None

    # Create channel choices
    channel_choices = [f"# {channel.name}" for channel in channel_list]

    # Map display strings back to channel objects
    channel_map = {
        channel_choices[i]: channel for i, channel in enumerate(channel_list)
    }

    # Use fuzzy search for channel selection
    selected_channel_display = await inquirer.fuzzy(
        message="Select a channel:", choices=channel_choices, max_height="70%"
    ).execute_async()

    return channel_map[selected_channel_display]


async def get_message_limit() -> int:
    """Prompt for the number of messages to retrieve.

    Returns:
        Number of messages to retrieve
    """
    return int(
        await inquirer.number(
            message="How many messages do you want to retrieve?",
            min_allowed=1,
            max_allowed=100,
            default=10,
        ).execute_async()
    )


async def fetch_and_display_messages(channel: discord.TextChannel, limit: int) -> None:
    """Fetch and display messages from a channel.

    Args:
        channel: Channel to fetch messages from
        limit: Maximum number of messages to fetch
    """
    logger.debug(f"Fetching {limit} messages from channel {channel.id}...")
    messages = []
    async for message in channel.history(limit=limit):
        messages.append(message)

    # Display messages
    click.echo(f"\nLast {limit} messages from {channel.name}:")
    for message in messages:
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"[{timestamp}] {message.author.name}: {message.content}")


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
def thread_catchup(guild_id):
    """Interactive tool to catch up on Discord threads."""

    async def run():
        # Fetch guild and channels
        guild, channels = await fetch_guild_channels(guild_id)

        # Organize channels by category
        categories, uncategorized = organize_channels_by_category(channels)

        # Select category
        selected_category_name, channel_list = await select_category(
            categories, uncategorized
        )

        if not channel_list:
            click.echo("No channels found in this category.")
            return

        # Select channel
        selected_channel = await select_channel(channel_list)

        if not selected_channel:
            return

        # Get message limit
        limit = await get_message_limit()

        # Fetch and display messages
        await fetch_and_display_messages(selected_channel, limit)

    # Use existing event loop instead of creating a new one
    asyncio.get_event_loop().run_until_complete(run())


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
@click.option(
    "--interactive", is_flag=True, help="Use interactive mode to select channels"
)
def list_channels(guild_id, interactive):
    """List all channels in a Discord server."""

    async def run():
        guild, channels = await fetch_guild_channels(guild_id)

        if interactive:
            categories, uncategorized = organize_channels_by_category(channels)
            selected_category_name, channel_list = await select_category(
                categories, uncategorized
            )

            if not channel_list:
                click.echo("No channels found in this category.")
                return

            click.echo(f"\nChannels in {selected_category_name}:")
            for channel in sorted(channel_list, key=lambda c: c.name):
                click.echo(f"# {channel.name} (ID: {channel.id})")
        else:
            text_channels = [c for c in channels if isinstance(c, discord.TextChannel)]
            click.echo(f"\nAll text channels in {guild.name}:")
            for channel in sorted(text_channels, key=lambda c: c.name):
                category_name = (
                    channel.category.name if channel.category else "Uncategorized"
                )
                click.echo(
                    f"# {channel.name} (ID: {channel.id}, Category: {category_name})"
                )

    asyncio.get_event_loop().run_until_complete(run())


@client.event
async def on_ready():
    """Event triggered when the bot is ready."""
    logger.info(f"Logged in as {client.user.name}")


async def start_client():
    """Start the Discord client."""
    logger.debug("Starting Discord client...")
    await client.login(settings.discord_token)
    logger.debug("Logged in successfully.")


async def close_client():
    """Close the Discord client."""
    logger.debug("Closing Discord client...")
    await client.close()
    logger.debug("Discord client closed successfully.")


def main():
    """Start the Discord client and CLI."""
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

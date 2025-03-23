import os
import asyncio
import logging
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
logging.basicConfig(level=logging_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
def thread_catchup(guild_id):
    """Interactive tool to catch up on Discord threads."""

    async def run():
        logger.debug(f"Fetching guild {guild_id}...")
        guild = await client.fetch_guild(int(guild_id))

        logger.debug("Fetching channels...")
        channels = await guild.fetch_channels()

        # Organize channels by category
        categories = {}
        uncategorized = []

        for channel in channels:
            if isinstance(channel, discord.CategoryChannel):
                categories[channel.id] = {"name": channel.name, "channels": []}

        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                if channel.category_id and channel.category_id in categories:
                    categories[channel.category_id]["channels"].append(channel)
                else:
                    uncategorized.append(channel)

        # Create category choices
        category_choices = [
            f"{cat_data['name']} ({len(cat_data['channels'])} channels)" for cat_id, cat_data in categories.items()
        ]

        if uncategorized:
            category_choices.append(f"Uncategorized ({len(uncategorized)} channels)")

        # Map display strings back to category IDs
        category_map = {}
        cat_index = 0
        for cat_id, cat_data in categories.items():
            category_map[category_choices[cat_index]] = cat_id
            cat_index += 1

        if uncategorized:
            category_map[category_choices[-1]] = "uncategorized"

        # Use fuzzy search for category selection
        selected_category_display = await inquirer.fuzzy(
            message="Select a category:", choices=category_choices, max_height="70%"
        ).execute_async()

        selected_category = category_map[selected_category_display]

        # Get channels for selected category
        if selected_category == "uncategorized":
            channel_list = uncategorized
        else:
            channel_list = categories[selected_category]["channels"]

        if not channel_list:
            click.echo("No channels found in this category.")
            return

        # Create channel choices
        channel_choices = [f"# {channel.name}" for channel in channel_list]

        # Map display strings back to channel objects
        channel_map = {}
        for i, channel in enumerate(channel_list):
            channel_map[channel_choices[i]] = channel

        # Use fuzzy search for channel selection
        selected_channel_display = await inquirer.fuzzy(
            message="Select a channel:", choices=channel_choices, max_height="70%"
        ).execute_async()

        selected_channel = channel_map[selected_channel_display]

        # Ask for number of messages
        limit = int(
            await inquirer.number(
                message="How many messages do you want to retrieve?",
                min_allowed=1,
                max_allowed=100,
                default=10,
            ).execute_async()
        )

        # Get messages
        logger.debug(f"Fetching {limit} messages from channel {selected_channel.id}...")
        messages = []
        async for message in selected_channel.history(limit=limit):
            messages.append(message)

        # Display messages
        click.echo(f"\nLast {limit} messages from {selected_channel.name}:")
        for message in messages:
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"[{timestamp}] {message.author.name}: {message.content}")

    # Use existing event loop instead of creating a new one
    asyncio.get_event_loop().run_until_complete(run())


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

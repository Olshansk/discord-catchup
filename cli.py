# =============================
# Imports and Dependencies
# =============================
import asyncio
import logging
import click
import discord
from pydantic_settings import BaseSettings
from typing import Optional

import cli_prompt_handler as cph
import cli_llm_handler as clh
import cli_discord_utils as cdu


# =============================
# Settings and Configuration
# =============================
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    - discord_token: Discord bot token (required)
    - debug_logging: Enable debug logging
    - default_guild_id: Default Discord server (guild) ID
    - use_threads_cache: Use cached thread data if available
    - max_thread_age_days: Only show threads updated within this many days
    - openrouter_api_key: API key for OpenRouter (optional)
    """

    discord_token: str
    debug_logging: bool = False
    default_guild_id: str = ""
    use_threads_cache: bool = False
    max_thread_age_days: Optional[int] = None
    openrouter_api_key: Optional[str] = None

    class Config:
        env_file = ".env"


# =============================
# Initialization
# =============================

# Load settings from .env or environment
settings = Settings()

# Set up logging
logging_level = logging.DEBUG if settings.debug_logging else logging.WARNING
logging.basicConfig(level=logging_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cli")

# Configure Discord client with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
client = discord.Client(intents=intents)


# =============================
# CLI Setup
# =============================


@click.group()
def cli():
    """
    Discord CLI tool for retrieving channel information and messages.
    """
    pass


@cli.command()
@click.option("--guild-id", required=False, help="Discord server (guild) ID")
@click.option("--create-prompt", is_flag=True, help="Create a prompt file for summarization")
@click.option("--summarize", is_flag=True, help="Use LLM to summarize the conversation")
@click.option("--use-cache", is_flag=True, help="Use cached thread data if available")
@click.option("--max-age", type=int, help="Only show threads updated within this many days")
def thread_catchup(guild_id, create_prompt, summarize, use_cache, max_age):
    """
    Interactive tool to catch up on Discord threads.
    - Allows prompt creation and LLM summarization
    - Supports caching and thread age filtering
    """
    # Use default guild ID if not provided
    guild_id = guild_id or settings.default_guild_id

    # Use env settings as defaults if command line args not provided
    use_cache = use_cache or settings.use_threads_cache
    max_age = max_age if max_age is not None else settings.max_thread_age_days

    if not guild_id:
        click.echo("Error: Guild ID is required. Provide --guild-id or set DEFAULT_GUILD_ID in .env")
        return

    # If summarize is requested but create-prompt is not, set create-prompt to True
    if summarize and not create_prompt:
        create_prompt = True

    async def run():
        # Fetch guild and channels
        guild, channels = await cdu.fetch_guild_channels(client, guild_id)

        # Organize channels by category
        categories, uncategorized = cdu.organize_channels_by_category(channels)

        # Select category interactively
        selected_category_name, channel_list = await cdu.select_category(categories, uncategorized)

        if not channel_list:
            click.echo("No channels found in this category.")
            return

        # Select channel interactively
        selected_channel = await cdu.select_channel(channel_list, count_threads=(not use_cache))

        if not selected_channel:
            return

        # Fetch threads for the selected channel
        threads = await cdu.fetch_threads(selected_channel, use_cache=use_cache, max_age_days=max_age)

        # Select thread or use main channel
        selected_thread = await cdu.select_thread(threads)
        target_channel = selected_thread if selected_thread else selected_channel

        # Get message limit from user
        limit = await cdu.get_message_limit()

        # Fetch and display or summarize messages
        if create_prompt:
            prompt_file = await cph.fetch_and_create_prompt_file(target_channel, limit)

            # If summarize flag is set, use LLM to create a summary
            if summarize and prompt_file:
                summary_file = await clh.summarize_prompt_file(prompt_file)
                if summary_file:
                    click.echo(f"✅   Created summary file: {summary_file}")
                else:
                    click.echo("❌   Failed to create summary. Check logs for details.")
        else:
            await cdu.fetch_and_display_messages(target_channel, limit)

    # Use existing event loop instead of creating a new one
    asyncio.get_event_loop().run_until_complete(run())


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
@click.option("--interactive", is_flag=True, help="Use interactive mode to select channels")
def list_channels(guild_id, interactive):
    """
    List all channels in a Discord server.
    - Interactive mode allows category/channel selection
    - Otherwise, lists all text channels
    """

    async def run():
        guild, channels = await cdu.fetch_guild_channels(client, guild_id)

        if interactive:
            categories, uncategorized = cdu.organize_channels_by_category(channels)
            selected_category_name, channel_list = await cdu.select_category(categories, uncategorized)

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
                category_name = channel.category.name if channel.category else "Uncategorized"
                click.echo(f"# {channel.name} (ID: {channel.id}, Category: {category_name})")

    asyncio.get_event_loop().run_until_complete(run())


# =============================
# Discord Client Events & Lifecycle
# =============================


@client.event
async def on_ready():
    """
    Event triggered when the bot is ready.
    - Logs bot login
    """
    logger.info(f"Logged in as {client.user.name}")


async def start_client():
    """
    Start the Discord client.
    - Logs in with the provided token
    """
    logger.debug("Starting Discord client...")
    await client.login(settings.discord_token)
    logger.debug("Logged in successfully.")


async def close_client():
    """
    Close the Discord client.
    - Ensures client is properly closed
    """
    logger.debug("Closing Discord client...")
    await client.close()
    logger.debug("Discord client closed successfully.")


# =============================
# Main Entry Point
# =============================


def main():
    """
    Start the Discord client and CLI.
    - Initializes event loop
    - Runs CLI commands
    - Ensures Discord client is closed on exit
    """
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

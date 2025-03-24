import asyncio
import logging
import click
import discord
from pydantic_settings import BaseSettings
import cli_prompt_handler as cph
import cli_discord_utils as cdu


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
logger = logging.getLogger("cli")

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
@click.option("--create-prompt", is_flag=True, help="Create a prompt file for summarization")
def thread_catchup(guild_id, create_prompt):
    """Interactive tool to catch up on Discord threads."""

    async def run():
        # Fetch guild and channels
        guild, channels = await cdu.fetch_guild_channels(client, guild_id)

        # Organize channels by category
        categories, uncategorized = cdu.organize_channels_by_category(channels)

        # Select category
        selected_category_name, channel_list = await cdu.select_category(categories, uncategorized)

        if not channel_list:
            click.echo("No channels found in this category.")
            return

        # Select channel
        selected_channel = await cdu.select_channel(channel_list)

        if not selected_channel:
            return

        # Fetch threads for the selected channel
        threads = await cdu.fetch_threads(selected_channel)

        # Select thread or main channel
        selected_thread = await cdu.select_thread(threads)

        # Use either the selected thread or the main channel
        target_channel = selected_thread if selected_thread else selected_channel

        # Get message limit
        limit = await cdu.get_message_limit()

        # Fetch and display messages
        if create_prompt:
            await cph.fetch_and_create_prompt_file(target_channel, limit)
        else:
            await cdu.fetch_and_display_messages(target_channel, limit)

    # Use existing event loop instead of creating a new one
    asyncio.get_event_loop().run_until_complete(run())


@cli.command()
@click.option("--guild-id", required=True, help="Discord server (guild) ID")
@click.option("--interactive", is_flag=True, help="Use interactive mode to select channels")
def list_channels(guild_id, interactive):
    """List all channels in a Discord server."""

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

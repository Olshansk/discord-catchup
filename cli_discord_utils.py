import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import click
import discord
from InquirerPy import inquirer
import logging

logger = logging.getLogger("cli.cli_discord_utils")


async def fetch_guild_channels(
    client: discord.Client,
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
        f"{cat_data['name']} ({len(cat_data['channels'])} channels)" for cat_id, cat_data in categories.items()
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

    # Create channel choices with thread counts
    channel_choices = []
    for channel in channel_list:
        # Get thread count
        threads = await fetch_threads(channel)
        thread_count = len(threads)
        channel_choices.append(f"# {channel.name} ({thread_count} threads)")

    # Map display strings back to channel objects
    channel_map = {channel_choices[i]: channel for i, channel in enumerate(channel_list)}

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


async def fetch_threads(
    channel: discord.TextChannel, use_cache: bool = False, max_age_days: Optional[int] = None
) -> List[discord.Thread]:
    """Fetch all threads in a channel."""
    threads = []

    # If we're using cache, try to load it
    if use_cache:
        threads = _load_threads_from_cache(channel.id, max_age_days)
        if threads:
            return threads

    # Fetch active threads
    try:
        active_threads = await channel.guild.active_threads()
        for thread in active_threads:
            if thread.parent_id == channel.id and not thread.archived and not thread.locked:
                threads.append(thread)
    except Exception as e:
        logger.warning(f"Error fetching active threads: {e}")

    # Fetch archived threads
    try:
        async for thread in channel.archived_threads(limit=100):
            if not thread.archived and not thread.locked:
                threads.append(thread)
    except Exception as e:
        logger.warning(f"Error fetching archived threads: {e}")

    # Apply age filter
    if max_age_days:
        cutoff_date = datetime.utcnow().replace(tzinfo=None)
        threads = [
            t
            for t in threads
            if t.archive_timestamp
            and t.archive_timestamp.replace(tzinfo=None) >= cutoff_date - timedelta(days=max_age_days)
        ]

    # Save to cache if needed
    if use_cache:
        _save_threads_to_cache(channel.id, threads)

    return threads


def _load_threads_from_cache(channel_id: int, max_age_days: Optional[int] = None) -> List[discord.Thread]:
    """Load threads from cache."""
    cache_file = os.path.join(".cache", f"threads_cache_{channel_id}.json")

    if not os.path.exists(cache_file) or time.time() - os.path.getmtime(cache_file) > 3600:
        return []

    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading thread cache: {e}")
        return []


def _save_threads_to_cache(channel_id: int, threads: List[discord.Thread]) -> None:
    """Save threads to cache."""
    os.makedirs(".cache", exist_ok=True)
    cache_file = os.path.join(".cache", f"threads_cache_{channel_id}.json")

    try:
        thread_data = [
            {
                "id": str(t.id),
                "parent_id": str(t.parent_id),
                "name": t.name,
                "archived": t.archived,
                "locked": getattr(t, "locked", False),
                "archive_timestamp": t.archive_timestamp.isoformat() if t.archive_timestamp else None,
            }
            for t in threads
        ]

        with open(cache_file, "w") as f:
            json.dump(thread_data, f)
    except Exception as e:
        logger.warning(f"Error saving thread cache: {e}")


async def select_thread(threads: List[discord.Thread]) -> Optional[discord.Thread]:
    """Display interactive prompt to select a thread.

    Args:
        threads: List of thread objects

    Returns:
        Selected thread object or None if no thread selected
    """
    if not threads:
        click.echo("No threads found in this channel.")
        return None

    # Add option for main channel (no thread)
    thread_choices = ["No thread (main channel)"] + [f"🧵 {thread.name}" for thread in threads]

    # Map display strings back to thread objects with None for main channel
    thread_map = {thread_choices[0]: None}
    for i, thread in enumerate(threads):
        thread_map[thread_choices[i + 1]] = thread

    # Use fuzzy search for thread selection
    selected_thread_display = await inquirer.fuzzy(
        message="Select a thread:", choices=thread_choices, max_height="70%"
    ).execute_async()

    return thread_map[selected_thread_display]

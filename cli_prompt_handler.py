import click
import discord
import logging

# Set up logger for this module
logger = logging.getLogger("cli.cli_prompt_handler")


async def fetch_and_create_prompt_file(channel: discord.TextChannel, limit: int) -> str:
    """
    Fetches the latest messages from a Discord channel and creates a prompt file.

    - Fetches up to `limit` messages from the specified channel
    - Formats messages with timestamp, author, and content
    - Reads a prompt template from prompt.md
    - Appends fetched messages to the template
    - Saves the result to a uniquely named markdown file

    Args:
        channel: The Discord TextChannel (or Thread) to fetch messages from
        limit: Maximum number of messages to fetch

    Returns:
        The filename of the created prompt file, or None if prompt.md is missing
    """

    # Fetch messages from the channel
    logger.debug(f"Fetching {limit} messages from channel {channel.id}...")
    messages = []
    async for message in channel.history(limit=limit):
        messages.append(message)

    # Format messages for prompt file (oldest first)
    message_texts = []
    for message in reversed(messages):
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        message_texts.append(f"[{timestamp}] {message.author.name}: {message.content}")

    # Extract guild (server) name
    guild_name = channel.guild.name

    # Extract channel name
    channel_name = channel.name

    # Determine thread name (if applicable), else use 'main'
    thread_name = "main"
    if isinstance(channel, discord.Thread):
        thread_name = channel.name
        parent_channel = channel.parent
        if parent_channel:
            channel_name = parent_channel.name

    # Generate timestamp for filename (UTC)
    timestamp = discord.utils.utcnow().strftime("%Y_%m_%d_%H%M%S")

    # Build filename in snake_case, removing special characters
    filename = f"prompt_{timestamp}_{guild_name}_{channel_name}_{thread_name}_{limit}.md"
    filename = "".join(c.lower() if c.isalnum() or c in "._- " else "_" for c in filename)
    filename = filename.replace(" ", "_")

    # Read prompt template from prompt.md
    try:
        with open("prompt.md", "r", encoding="utf-8") as f:
            prompt_content = f.read()
    except FileNotFoundError:
        click.echo("Error: prompt.md not found. Please create this file with your prompt template.")
        return None

    # Append fetched messages to the prompt template
    prompt_content += "\n\n"
    prompt_content += "\n".join(message_texts)

    # Write final prompt to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(prompt_content)

    # Output to user
    click.echo(f"\n✅   Created prompt file: {filename}")
    click.echo(f"✅   Last {limit} messages from {channel.name} saved.")

    return filename

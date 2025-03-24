import click
import discord
import logging

logger = logging.getLogger("cli.cli_prompt_handler")


async def fetch_and_create_prompt_file(channel: discord.TextChannel, limit: int) -> str:
    """Fetch messages and create a prompt file.

    Args:
        channel: Channel to fetch messages from
        limit: Maximum number of messages to fetch
    """
    logger.debug(f"Fetching {limit} messages from channel {channel.id}...")
    messages = []
    async for message in channel.history(limit=limit):
        messages.append(message)

    # Format messages for the prompt file
    message_texts = []
    for message in reversed(messages):  # Show oldest messages first
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        message_texts.append(f"[{timestamp}] {message.author.name}: {message.content}")

    # Get server/guild name
    guild_name = channel.guild.name

    # Get channel name
    channel_name = channel.name

    # Get thread name if applicable, otherwise use "main"
    thread_name = "main"
    if isinstance(channel, discord.Thread):
        thread_name = channel.name
        parent_channel = channel.parent
        if parent_channel:
            channel_name = parent_channel.name

    # Create timestamp for filename
    timestamp = discord.utils.utcnow().strftime("%Y_%m_%d_%H%M%S")

    # Create filename with snake_case
    filename = f"prompt_{timestamp}_{guild_name}_{channel_name}_{thread_name}_{limit}.md"
    # Convert to snake_case and remove special characters
    filename = "".join(c.lower() if c.isalnum() or c in "._- " else "_" for c in filename)
    filename = filename.replace(" ", "_")

    # Read prompt template from prompt.md
    try:
        with open("prompt.md", "r", encoding="utf-8") as f:
            prompt_content = f.read()
    except FileNotFoundError:
        click.echo("Error: prompt.md not found. Please create this file with your prompt template.")
        return None

    # Add messages to the prompt content
    prompt_content += "\n\n"
    prompt_content += "\n".join(message_texts)

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(prompt_content)

    click.echo(f"\n✅   Created prompt file: {filename}")
    click.echo(f"✅   Last {limit} messages from {channel.name} saved.")

    return filename

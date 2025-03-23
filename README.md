# Discord CLI Tool

A command-line utility for interacting with Discord servers to easily retrieve information about channels, threads, and messages.

## Features

- List all channels in a Discord server
- List all threads in a server with optional channel filtering
- Retrieve the last N messages from any channel or thread
- Easy-to-use command-line interface using Click

## Installation

1. **Important**: Save the script as `discord_cli.py` (not `discord.py`) to avoid naming conflicts with the discord.py library.

2. Install dependencies using `uv`:

   ```bash
   uv pip install discord.py click python-dotenv
   ```

3. Create a `.env` file in the same directory as the script with your Discord bot token:

   ```bash
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

## Getting a Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click `New Application` and provide a name
3. Navigate to the `Bot`
4. Update permissions (TODO: Add more details)
5. Under the `TOKEN` section, click "Copy" to copy your bot token
6. Navigate to the `OAuth2` tab, then `URL Generator`
7. Select the following scopes: `bot`, `applications.commands`
8. Select bot permissions: `Read Messages/View Channels`, `Read Message History`
9. Use the generated URL to invite the bot to your server

## Usage

Run the script using `uv run`:

```bash
uv run discord_cli.py COMMAND [OPTIONS]
```

### Available Commands

#### List all channels in a server:

```bash
uv run discord_cli.py list-channels --guild-id YOUR_GUILD_ID
```

#### List all threads in a server:

```bash
uv run discord_cli.py list-threads --guild-id YOUR_GUILD_ID
```

#### List threads in a specific channel:

```bash
uv run discord_cli.py list-threads --guild-id YOUR_GUILD_ID --channel-id YOUR_CHANNEL_ID
```

#### Get the last N messages from a channel or thread:

```bash
uv run discord_cli.py get-messages-cmd --channel-id YOUR_CHANNEL_ID --limit 20
```

## Finding Guild and Channel IDs

1. Open Discord settings
2. Go to "Advanced" and enable "Developer Mode"
3. Right-click on a server/guild and select "Copy ID" to get the Guild ID
4. Right-click on a channel and select "Copy ID" to get the Channel ID

## Troubleshooting

If you encounter an error about missing intents or permissions, make sure:

1. Your bot has the correct intents enabled in the Discord Developer Portal
2. Your bot has been invited to the server with the correct permissions
3. Your bot token is correct in the `.env` file

## Example

```bash
# List all channels in a server
uv run discord_cli.py list-channels --guild-id 123456789012345678

# Get the last 5 messages from a channel
uv run discord_cli.py get-messages-cmd --channel-id 987654321098765432 --limit 5
```

## Wishlist

- Pipe into an LLM and get a summary
- List of actionable commands
- Playbook
- Links
-


## Discord catchup bot

https://discord.com/oauth2/authorize?client_id=1353467311880929300
https://discord.com/oauth2/authorize?client_id=1353467311880929300
https://discord.com/developers/applications/1353467311880929300/installation
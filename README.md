# Discord CLI Tool <!-- omit in toc -->

A command-line utility for interacting with Discord servers to easily retrieve information about channels, threads, and messages.

- [Features](#features)
- [Installation](#installation)
- [Getting a Discord Bot Token](#getting-a-discord-bot-token)
- [Usage](#usage)
  - [Available Commands](#available-commands)
- [Finding Guild and Channel IDs](#finding-guild-and-channel-ids)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Discord Catchup Bot](#discord-catchup-bot)
- [ClaudeSync Setup](#claudesync-setup)

## Features

- List all channels in a Discord server
- Navigate channels and threads interactively
- Retrieve the last N messages from any channel or thread
- Easy-to-use command-line interface using Click

## Installation

1. **Important**: Save the script as `cli.py` to avoid naming conflicts with the discord.py library.

2. Create a virtual environment and install dependencies:

   ```bash
   # Create a Python 3.11 virtual environment
   make env_create

   # Activate the virtual environment
   source .venv/bin/activate

   # Install dependencies
   make uv_install
   ```

3. Create a `.env` file in the same directory as the script with your Discord bot token:

   ```bash
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

## Getting a Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click `New Application` and provide a name
3. Navigate to the `Bot` section
4. Under the `TOKEN` section, click "Copy" to copy your bot token
5. Navigate to the `OAuth2` tab, then `URL Generator`
6. Select the following scopes: `bot`, `applications.commands`
7. Select bot permissions: `Read Messages/View Channels`, `Read Message History`, `Message Content Intent`
8. Use the generated URL to invite the bot to your server

## Usage

```bash
# Get help information
make discord_help

# List channels in a server
make discord_list_channels_grove

# List channels interactively
make discord_list_channels_grove_interactive

# Or run directly with uv
uv run cli.py [COMMAND] [OPTIONS]
```

### Available Commands

See the help output for the full list of available commands:

```bash
uv run cli.py --help
```

## Finding Guild and Channel IDs

1. Open Discord settings
2. Go to "Advanced" and enable "Developer Mode"
3. Right-click on a server/guild and select "Copy ID" to get the Guild ID
4. Right-click on a channel and select "Copy ID" to get the Channel ID

## Troubleshooting

If you encounter an error about missing intents or permissions, make sure:

1. Your bot has the correct intents enabled in the Discord Developer Portal
   - Under "Bot" settings, enable "Message Content Intent" and other required intents
2. Your bot has been invited to the server with the correct permissions
3. Your bot token is correct in the `.env` file

## Development

This project uses `uv` for dependency management and `ruff` for code formatting.

```bash
# Format code
make py_format

# Update dependencies
make uv_upgrade

# Export locked dependencies
make uv_export
```

## Discord Catchup Bot

The following URLs are for the Discord Catchup bot:

- Bot authorization: https://discord.com/oauth2/authorize?client_id=1353467311880929300
- Developer portal: https://discord.com/developers/applications/1353467311880929300/installation

## ClaudeSync Setup

This repo is setup to use [ClaudeSync](https://github.com/jahwag/ClaudeSync) to help answer questions about the repo.

You can view `.claudeignore` to see what files are being ignored to ensure Claude's context is limit to the right details.

1. **Install ClaudeSync** - Ensure you have python set up on your machine

   ```shell
   pip install claudesync
   ```

1. **Authenticate** - Follow the instructions in your terminal

   ```shell
   claudesync auth login
   ```

1. **Create a Project** - Follow the instructions in your terminal

   ```shell
   make claudesync_init
   ```

1. **Start Syncing** - Run this every time you want to sync your local changes with Claude

   ```shell
   make claudesync_push
   ```

1. **Set the following system prompt**

   ```text
   You're a staff software engineer with lots of experience in python.

   You follow the most recent best practices.

   You and I will be pair coding on a small python CLI project to catch up on discord channels & servers.

   Leverage the project context to answer questions.

   Don't provide long explanations unless I explicitly as for it.

   Bias towards:
   - Code solutions
   - For major changes, show the whole file modified
   - For small changes, either:
      - Provide a `diff.diff` I'll apply via `git apply diff.diff`
      - Show the modified function which I'll copy-paste myself
   ```

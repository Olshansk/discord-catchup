# Discord CLI Tool <!-- omit in toc -->

A command-line utility for interacting with Discord servers to easily retrieve information about channels, threads, and messages.

- [Features](#features)
- [Installation](#installation)
- [Getting a Discord Bot Token](#getting-a-discord-bot-token)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Available Commands](#available-commands)
- [Finding Guild and Channel IDs](#finding-guild-and-channel-ids)
- [Thread Catchup \& Summarization](#thread-catchup--summarization)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Makefile Commands](#makefile-commands)
  - [Discord Commands](#discord-commands)
  - [Environment Management](#environment-management)
  - [Package Management](#package-management)
  - [Code Quality](#code-quality)
- [ClaudeSync Integration](#claudesync-integration)

![output](https://github.com/user-attachments/assets/c6e20da0-de33-45ad-8bd1-943a65fbfa68)

## Features

- List all channels in a Discord server, with interactive navigation
- Browse and select channels and threads with fuzzy search
- Retrieve the last N messages from any channel or thread
- Create prompt files for AI summarization
- Generate AI-powered summaries of Discord conversations using OpenRouter
- Caching of thread data for improved performance

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/discord-cli-tool.git
   cd discord-cli-tool
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   # Create a Python 3.11 virtual environment
   make env_create

   # Activate the virtual environment
   source .venv/bin/activate

   # Install dependencies
   make uv_install
   ```

3. Create a `.env` file with your configuration:

   ```bash
   DISCORD_TOKEN=your_discord_bot_token_here
   DEFAULT_GUILD_ID=your_default_guild_id_here
   DEBUG_LOGGING=false
   USE_THREADS_CACHE=true
   MAX_THREAD_AGE_DAYS=30
   OPENROUTER_API_KEY=your_openrouter_api_key_here
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

## Configuration

The tool can be configured via environment variables in a `.env` file:

| Variable              | Description                                         | Default |
| --------------------- | --------------------------------------------------- | ------- |
| `DISCORD_TOKEN`       | Discord bot token (required)                        | -       |
| `DEFAULT_GUILD_ID`    | Default Discord server ID                           | -       |
| `DEBUG_LOGGING`       | Enable debug logging                                | `false` |
| `USE_THREADS_CACHE`   | Enable thread caching                               | `false` |
| `MAX_THREAD_AGE_DAYS` | Only show threads updated within this many days     | -       |
| `OPENROUTER_API_KEY`  | API key for OpenRouter (required for summarization) | -       |

## Usage

```bash
# Get help information
make discord_help

# List channels in a server
uv run cli.py list-channels --guild-id YOUR_GUILD_ID

# Interactive channel listing
uv run cli.py list-channels --guild-id YOUR_GUILD_ID --interactive

# Thread catchup with interactive UI
uv run cli.py thread-catchup --guild-id YOUR_GUILD_ID

# Create a prompt file for summarization
uv run cli.py thread-catchup --guild-id YOUR_GUILD_ID --create-prompt

# Generate an AI summary of a conversation
uv run cli.py thread-catchup --guild-id YOUR_GUILD_ID --summarize
```

You can also use the convenience Makefile commands:

```bash
# Get help for all commands
make discord_help

# Thread catchup with prompt creation (using default guild)
make discord_thread_catchup_with_prompt_use_env

# Thread catchup with AI summarization (using default guild)
make discord_thread_catchup_with_summary_use_env
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

## Thread Catchup & Summarization

The `thread-catchup` command provides an interactive way to catch up on Discord conversations:

1. Select a category
2. Select a channel
3. Select a thread (or main channel)
4. Choose how many messages to retrieve
5. View messages or create a prompt file for summarization
6. Optionally generate an AI summary of the conversation

For summarization to work, you need an OpenRouter API key in your `.env` file.

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

## Makefile Commands

The project includes several helpful Makefile commands for common operations:

### Discord Commands

```bash
# Show CLI help
make discord_help

# Catch up on threads with prompt creation (Grove guild)
make discord_thread_catchup_with_prompt_grove

# Catch up on threads with prompt creation (default guild)
make discord_thread_catchup_with_prompt_use_env

# Catch up on threads with AI summarization (default guild)
make discord_thread_catchup_with_summary_use_env
```

### Environment Management

```bash
# Check if virtual environment is active
make env_check

# Create Python 3.11 virtual environment
make env_create

# Source the environment
source .venv/bin/activate
```

### Package Management

```bash
# Install dependencies
make uv_install

# Update and upgrade all dependencies
make uv_upgrade

# Export locked dependencies
make uv_export
```

### Code Quality

```bash
# Format code with ruff
make py_format
```

## ClaudeSync Integration

This repo is set up to use [ClaudeSync](https://github.com/jahwag/ClaudeSync) to help answer questions about the codebase.

You can view `.claudeignore` to see what files are being ignored to ensure Claude's context is limited to the relevant details.

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

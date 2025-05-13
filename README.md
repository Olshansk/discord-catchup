# Discord CLI Tool <!-- omit in toc -->

A CLI for interacting with Discord to easily catch up on a thread or server without reading the whole thing.

- [Features](#features)
- [Installation from Source](#installation-from-source)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Finding Guild and Channel IDs](#finding-guild-and-channel-ids)
  - [Getting a Discord Bot Token](#getting-a-discord-bot-token)
- [Bonus: ClaudeSync Integration](#bonus-claudesync-integration)

![output](https://github.com/user-attachments/assets/c6e20da0-de33-45ad-8bd1-943a65fbfa68)

## Features

- List all channels in a Discord server, with interactive navigation
- Browse and select channels and threads with fuzzy search
- Retrieve the last N messages from any channel or thread
- Create prompt files for AI summarization
- Generate AI-powered summaries of Discord conversations using OpenRouter
- Caching of thread data for improved performance

## Installation from Source

> [!IMPORTANT]
> The only way to install it (for now) is from source

1. Clone the repository:

   ```bash
   git clone https://github.com/olshansk/discord-catchup
   cd discord-catchup
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   # Create a Python 3.11 virtual environment
   make env_create

   # Activate the virtual environment
   $(make env_source)

   # Install dependencies
   make uv_install
   ```

3. Create a `.env` file with your configuration:

   ```bash
   cp .env.example .env
   ```

   And update the values in the `.env` file:

   ```bash
   DISCORD_TOKEN=your_discord_bot_token_here
   DEFAULT_GUILD_ID=your_default_guild_id_here
   DEBUG_LOGGING=false
   USE_THREADS_CACHE=true
   MAX_THREAD_AGE_DAYS=30
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

4. Use the tool:

   ```bash
   make discord_thread_catchup_with_prompt_use_env
   ```

5. See other available commands for discord catch:

   ```bash
   make discord_catchup_help
   ```

   OR

   ```bash
   make
   ```

## Configuration

### Environment Variables

The tool can be configured via environment variables in a `.env` file:

| Variable              | Description                                         | Default |
| --------------------- | --------------------------------------------------- | ------- |
| `DISCORD_TOKEN`       | Discord bot token (required)                        | -       |
| `DEFAULT_GUILD_ID`    | Default Discord server ID                           | -       |
| `DEBUG_LOGGING`       | Enable debug logging                                | `false` |
| `USE_THREADS_CACHE`   | Enable thread caching                               | `false` |
| `MAX_THREAD_AGE_DAYS` | Only show threads updated within this many days     | -       |
| `OPENROUTER_API_KEY`  | API key for OpenRouter (required for summarization) | -       |

### Finding Guild and Channel IDs

1. Open Discord settings
2. Go to "Advanced" and enable "Developer Mode"
3. Right-click on a server/guild and select "Copy ID" to get the Guild ID
4. Right-click on a channel and select "Copy ID" to get the Channel ID

### Getting a Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click `New Application` and provide a name
3. Navigate to the `Bot` section
4. Under the `TOKEN` section, click "Copy" to copy your bot token
5. Navigate to the `OAuth2` tab, then `URL Generator`
6. Select the following scopes: `bot`, `applications.commands`
7. Select bot permissions: `Read Messages/View Channels`, `Read Message History`, `Message Content Intent`
8. Use the generated URL to invite the bot to your server

## Bonus: ClaudeSync Integration

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

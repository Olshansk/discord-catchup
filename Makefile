SHELL := /bin/bash

.SILENT:

.PHONY: help
.DEFAULT_GOAL := help
help:  ## Prints all the targets in all the Makefiles
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: list
list:  ## List all make targets
	@${MAKE} -pRrn : -f $(MAKEFILE_LIST) 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | sort

##########################
### Env Common Targets ###
##########################

.PHONY: env_check
env_check: ## Checks if the virtual environment is activated
ifndef VIRTUAL_ENV
	$(error 'Virtualenv is not activated, please activate the Python virtual environment by running "$$(make env_source)".')
endif

.PHONY: env_create
env_create:  ## Create Python 3.11 virtual environment with uv
	uv venv --python 3.11

.PHONY: env_source
env_source:  ## Source the env; must be executed like so: $$(make env_source)
	@echo 'source .venv/bin/activate'

##########################
### UV Common Targets ###
##########################

.PHONY: uv_cache_dir
## Internal helper: Create the cache directory for uv
uv_cache_dir:
	@mkdir -p .cache/uv

.PHONY: uv_compile
uv_compile: env_check uv_cache_dir ## Generate requirements.txt from pyproject.toml and requirements.in
	@echo "Compiling dependencies..."
	uv compile pyproject.toml -o requirements.txt
	uv compile --output-file=requirements.txt requirements.in

.PHONY: uv_install
uv_install: env_check uv_cache_dir ## Install dependencies from requirements.txt
	uv install -r requirements.txt

.PHONY: uv_upgrade
uv_upgrade: env_check uv_cache_dir ## Upgrade all installed packages and update requirements.txt
	uv install --upgrade -r requirements.txt
	$(MAKE) uv_export

.PHONY: uv_export
uv_export: env_check uv_cache_dir ## Export locked dependencies to requirements.txt
	@echo "Exporting dependencies to requirements.txt..."
	uv export -o requirements.txt

#############################
### Python Common Targets ###
#############################

.PHONY: py_format
py_format: env_check  ## Format the Python code with ruff
	ruff format

########################
### Discord Commands ###
########################

.PHONY: discord_list_channels_grove
discord_list_channels_grove: env_check ## List channels in Grove's Discord server
	@uv run discord_catchup.py list-channels --guild-id 824324475256438814

.PHONY: discord_list_channels_grove_interactive
discord_list_channels_grove_interactive: env_check ## Interactively browse Grove's Discord server
	@uv run discord_catchup.py list-channels --guild-id 824324475256438814 --interactive

.PHONY: discord_thread_catchup
discord_thread_catchup: env_check ## Run the thread catchup interactive tool
	@uv run discord_catchup.py thread-catchup --guild-id 824324475256438814

.PHONY: discord_help
discord_help: env_check ## Show help information for Discord CLI commands
	@uv run discord_catchup.py --help

######################
### Claude targets ###
######################

.PHONY: claudesync_check
# Internal helper: Checks if claudesync is installed locally
claudesync_check:
	@if ! command -v claudesync >/dev/null 2>&1; then \
		echo "claudesync is not installed. Make sure you review README.md before continuing"; \
		exit 1; \
	fi

.PHONY: claudesync_init
claudesync_init: claudesync_check ## Initializes a new ClaudeSync project
	@echo "###############################################"
	@echo "Initializing a new ClaudeSync project"
	@echo "When prompted, enter the following name: discord-catchup"
	@echo "When prompted, enter the following description: Claude Project for Discord Catchup"
	@echo "When prompted for an absolute path, press enter"
	@echo "Follow the Remote URL outputted and copy-paste the recommended system prompt from the README"
	@echo "###############################################"
	@claudesync project init --new

.PHONY: claudesync_push
claudesync_push: claudesync_check ## Pushes the current project to the ClaudeSync project
	@claudesync push
import os
import json
import logging
import aiohttp
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings

logger = logging.getLogger("cli.cli_llm_handler")


class LLMSettings(BaseSettings):
    openrouter_api_key: Optional[str] = None
    site_url: Optional[str] = None
    site_name: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = LLMSettings()


async def summarize_prompt_file(prompt_file_path: str) -> Optional[str]:
    """
    Summarize a prompt file using an LLM API.

    Args:
        prompt_file_path: Path to the prompt file

    Returns:
        Generated summary or None if failed
    """
    if not settings.openrouter_api_key:
        logger.error("OpenRouter API key not found in .env file")
        return None

    try:
        # Read prompt file
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()

        # Create output filename
        base_name = os.path.basename(prompt_file_path)
        summary_filename = f"summary_{base_name}"
        summary_path = os.path.join(os.path.dirname(prompt_file_path), summary_filename)

        # Call LLM API
        response_content = await call_openrouter_api(prompt_content)

        if not response_content:
            return None

        # Write summary to file
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(response_content)

        return summary_path

    except Exception as e:
        logger.error(f"Error summarizing prompt file: {e}")
        return None


async def call_openrouter_api(prompt_content: str) -> Optional[str]:
    """
    Call the OpenRouter API to generate a summary.

    Args:
        prompt_content: Content of the prompt

    Returns:
        Generated text or None if failed
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    # Build headers with proper referer information
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    if settings.site_url:
        headers["HTTP-Referer"] = settings.site_url

    if settings.site_name:
        headers["X-Title"] = settings.site_name

    # Use the Qwen model as specified
    payload = {
        "model": "deepseek/deepseek-r1-distill-qwen-32b:free",
        "messages": [{"role": "user", "content": prompt_content}],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    logger.error(
                        f"❌   API request failed with status {response.status}: {await response.text()}"
                    )
                    return None

                data = await response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content")

    except Exception as e:
        logger.error(f"❌   Error calling OpenRouter API: {e}")
        return None

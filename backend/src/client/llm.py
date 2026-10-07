"""Centralized OpenRouter LLM Client for DocPilot clinical reasoning."""

import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from client.config import settings

logger = logging.getLogger(__name__)

_openai_client: Optional[AsyncOpenAI] = None


def get_llm_client() -> AsyncOpenAI:
    """Returns singleton AsyncOpenAI client configured for OpenRouter."""
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
    return _openai_client


async def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 1500,
    response_format: Optional[Dict[str, Any]] = None,
) -> str:
    """Invokes the clinical reasoning LLM via OpenRouter.

    Args:
        messages: Conversation messages list formatted for chat completions.
        model: Model identifier override (defaults to settings.OPENROUTER_MODEL).
        temperature: Sampling temperature (low by default for clinical precision).
        max_tokens: Maximum tokens in response.
        response_format: Optional response format (e.g. {"type": "json_object"}).

    Returns:
        Generated text response.
    """
    client = get_llm_client()
    target_model = model or settings.OPENROUTER_MODEL

    try:
        kwargs: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        res = await client.chat.completions.create(**kwargs)
        content = res.choices[0].message.content or ""
        return content.strip()

    except Exception as exc:
        logger.error("LLM completion failed with model '%s': %s", target_model, exc)
        raise exc

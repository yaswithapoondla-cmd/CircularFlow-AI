import os
from typing import Optional
from openai import OpenAI
from ..config import get_settings


def get_llm_client() -> Optional[OpenAI]:
    """
    Returns an initialized OpenAI client if LLM_API_KEY is configured in the environment.
    Returns None otherwise, enabling graceful fallback mode.
    """
    settings = get_settings()
    api_key = settings.LLM_API_KEY.strip()
    if not api_key:
        return None

    base_url = settings.LLM_BASE_URL.strip() if settings.LLM_BASE_URL else None
    return OpenAI(
        api_key=api_key,
        base_url=base_url if base_url else None
    )

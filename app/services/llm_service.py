import os

from langchain_ollama import ChatOllama

from app.config import settings


def get_llm() -> ChatOllama:
    model_name = os.environ.get("CHAT_MODEL")
    base_url = os.environ.get("OLLAMA_BASE_URL")

    if not model_name:
        model_name = settings.CHAT_MODEL

    if not base_url:
        base_url = settings.OLLAMA_BASE_URL

    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=0,
    )
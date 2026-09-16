import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434"
    )

    CHAT_MODEL: str = os.getenv(
        "OLLAMA_MODEL",
        "qwen2.5:3b"
    )


settings = Settings()
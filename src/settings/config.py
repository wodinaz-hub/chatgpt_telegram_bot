import os

print(f"Змінна середовища TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')}")
print(f"Змінна середовища telegram_bot_token: {os.getenv('telegram_bot_token')}")
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Базовий шлях до кореня проєкту
BASE_DIR = Path(__file__).parent.parent.parent


class BotConfig(BaseSettings):
    """
    Конфігурація Telegram-бота.
    """
    api_key: str = Field(alias="TELEGRAM_BOT_TOKEN")


class OpenAIConfig(BaseSettings):
    """
    Конфігурація OpenAI.
    """
    api_key: str = Field(alias="OPENAI_API_KEY")
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.8


class PathConfig(BaseSettings):
    """
    Конфігурація шляхів до ресурсів.
    """
    prompts: Path = BASE_DIR / "resources" / "prompts"
    images: Path = BASE_DIR / "resources" / "images"
    menus: Path = BASE_DIR / "resources" / "menus"
    messages: Path = BASE_DIR / "resources" / "messages"
    logs: Path = BASE_DIR / "logs"
    db: Path = BASE_DIR / "storage" / "chat_sessions.db"


class Settings(BaseSettings):
    """
    Головний клас конфігурації.
    """
    bot: BotConfig
    openai: OpenAIConfig
    paths: PathConfig

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )


config = Settings()
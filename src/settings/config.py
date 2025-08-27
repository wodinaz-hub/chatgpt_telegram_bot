from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Базовий шлях до кореня проєкту
BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """
    Головний клас конфігурації.
    """
    # Конфігурація Telegram-бота
    bot_api_key: str = Field(alias="TELEGRAM_BOT_TOKEN")

    # Конфігурація OpenAI
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.8

    # Конфігурація шляхів до ресурсів
    path_prompts: Path = BASE_DIR / "resources" / "prompts"
    path_images: Path = BASE_DIR / "resources" / "images"
    path_menus: Path = BASE_DIR / "resources" / "menus"
    path_messages: Path = BASE_DIR / "resources" / "messages"
    path_logs: Path = BASE_DIR / "logs"
    path_db: Path = BASE_DIR / "storage" / "chat_sessions.db"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8"
    )


config = Settings()
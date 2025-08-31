import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Paths:
    base = BASE_DIR
    settings = BASE_DIR / 'src' / 'settings'
    bot = BASE_DIR / 'src' / 'bot'
    handlers = BASE_DIR / 'src' / 'bot' / 'handlers'
    images = BASE_DIR / 'resources' / 'images'
    prompts = BASE_DIR / 'resources' / 'prompts'
    menus = BASE_DIR / 'resources' / 'menus'
    logs = BASE_DIR / 'logs'

class OpenAI:
    api_key: str = os.getenv('OPENAI_API_KEY')
    model: str = "gpt-3.5-turbo"
    temperature: float = 1.2

class Settings:
    bot_api_key: str = os.getenv('TELEGRAM_BOT_TOKEN')
    paths: Paths = Paths()
    openai: OpenAI = OpenAI()

config = Settings()

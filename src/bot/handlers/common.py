from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from src.settings.config import config

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /start."""
    logger.info(f"Користувач {update.effective_user.id} викликав команду /start.")
    await update.message.reply_text("Вітаю! Я твій AI-асистент. Обери одну з команд, щоб почати: /random, /gpt, /talk, /quiz.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /help."""
    logger.info(f"Користувач {update.effective_user.id} викликав команду /help.")
    await update.message.reply_text("Я можу:")
    # Тут буде детальний опис кожної команди.
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from loguru import logger

from src.settings.config import config
from src.settings.logging_config import setup_logging
from src.bot.handlers.common import start, help_command
from src.bot.handlers.random_handler import get_random_fact


print(f"DEBUG: TELEGRAM_BOT_TOKEN is '{os.getenv('TELEGRAM_BOT_TOKEN')}'")
def main() -> None:
    """Основна функція для запуску бота."""
    setup_logging()

    if not config.bot.api_key:
        logger.error("Токен бота не знайдено. Перевірте файл .env.")
        return

    application = Application.builder().token(config.bot.api_key).build()

    # Реєстрація обробників команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("random", get_random_fact))

    # Реєстрація обробників кнопок
    application.add_handler(CallbackQueryHandler(get_random_fact, pattern="^random$"))
    application.add_handler(CallbackQueryHandler(start, pattern="^start$"))

    logger.info("Бот запущено!")
    application.run_polling()


if __name__ == "__main__":
    main()
# src/main.py

import os
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from src.settings.config import config
from src.settings.logging_config import setup_logging
from src.bot.handlers.random_handler import get_random_fact
from src.bot.handlers.common import start
from src.bot.handlers.menu_handler import menu_callback_handler
from src.bot.handlers.gpt_handler import start_gpt_conversation, gpt_message_handler
from loguru import logger

# Константа для стану діалогу з GPT
STATE_GPT_DIALOGUE = 1

async def post_init(application: Application):
    # ... (код без змін)
    commands = [
        BotCommand("start", "Головне меню 🏠"),
        BotCommand("random", "Отримати випадковий цікавий факт 🧠"),
        BotCommand("gpt", "Запитати у ChatGPT 🤖"),
        BotCommand("quiz", "Пройти тест ❓")
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Команди бота успішно встановлено.")

def main() -> None:
    # ... (код без змін)
    setup_logging()

    if not config.bot_api_key:
        logger.error("Токен бота не знайдено. Перевірте файл .env")
        return

    application = Application.builder().token(config.bot_api_key).post_init(post_init).build()

    # Створюємо обробник для діалогу з GPT
    gpt_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("gpt", start_gpt_conversation),
            CallbackQueryHandler(start_gpt_conversation, pattern="^gpt$")
        ],
        states={
            STATE_GPT_DIALOGUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_message_handler)
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
        ]
    )

    # Реєстрація обробників
    application.add_handler(gpt_conversation_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("random", get_random_fact))
    application.add_handler(CommandHandler("gpt", start_gpt_conversation))
    application.add_handler(CallbackQueryHandler(menu_callback_handler))

    logger.info("Бот запущено!")
    application.run_polling()

if __name__ == "__main__":
    main()
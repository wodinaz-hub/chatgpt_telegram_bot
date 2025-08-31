import os
import sys
from telegram import BotCommand, MenuButtonCommands
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from loguru import logger
from src.settings.config import config
from src.settings.logging_config import setup_logging
from src.bot.handlers import gpt_handler, talk_handler, quiz_handler, random_handler
from src.bot.handlers.common import start
from src.bot.constants import (
    GPT_DIALOGUE_STATE,
    TALK_PERSONALITY_STATE,
    TALK_CONVERSING_STATE,
    QUIZ_SELECTING_TOPIC,
    QUIZ_WAITING_FOR_ANSWER,
    QUIZ_SHOWING_RESULT
)


async def post_init(application: Application):
    """Ініціалізує команди бота та меню після запуску."""
    commands = [
        BotCommand("start", "Головне меню 🏠"),
        BotCommand("random", "Отримати випадковий цікавий факт 🧠"),
        BotCommand("gpt", "Запитати у ChatGPT 🤖"),
        BotCommand("quiz", "Пройти тест ❓"),
        BotCommand("talk", "Діалог з відомою особистістю 👤")
    ]
    await application.bot.set_my_commands(commands)
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logger.info("Команди бота та меню успішно встановлено.")


def main() -> None:
    """Основна функція для запуску бота."""
    setup_logging()

    if not config.bot_api_key:
        logger.error("Токен бота не знайдено. Перевірте файл .env")
        sys.exit(1)

    application = Application.builder().token(config.bot_api_key).post_init(post_init).build()

    # Виправлення: Зберігаємо об'єкт конфігурації в bot_data
    application.bot_data['config'] = config

    # Обробник для діалогу з GPT
    gpt_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("gpt", gpt_handler.start_gpt_conversation),
            CallbackQueryHandler(gpt_handler.start_gpt_conversation, pattern="^gpt$")
        ],
        states={
            GPT_DIALOGUE_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_handler.gpt_message_handler),
                CallbackQueryHandler(gpt_handler.end_gpt_dialogue, pattern="^end_gpt_dialogue$")
            ]
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", gpt_handler.end_gpt_dialogue)
        ]
    )

    # Обробник для діалогу з особистістю
    talk_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("talk", talk_handler.start_talk),
            CallbackQueryHandler(talk_handler.start_talk, pattern="^talk$")
        ],
        states={
            TALK_PERSONALITY_STATE: [CallbackQueryHandler(talk_handler.select_personality, pattern="^talk_.*")],
            TALK_CONVERSING_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, talk_handler.talk_with_personality),
                CallbackQueryHandler(talk_handler.end_talk, pattern="^end_talk$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", talk_handler.cancel_talk),
            CommandHandler("start", start)
        ]
    )

    # Обробник для квізу
    quiz_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("quiz", quiz_handler.start_quiz),
            CallbackQueryHandler(quiz_handler.start_quiz, pattern="^quiz$")
        ],
        states={
            QUIZ_SELECTING_TOPIC: [
                CallbackQueryHandler(quiz_handler.ask_question, pattern="^quiz_.*")
            ],
            QUIZ_WAITING_FOR_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_handler.process_answer)
            ],
            QUIZ_SHOWING_RESULT: [
                CallbackQueryHandler(quiz_handler.ask_question, pattern="^ask_another_question$"),
                CallbackQueryHandler(quiz_handler.change_topic, pattern="^change_topic$"),
                CallbackQueryHandler(quiz_handler.end_quiz, pattern="^end_quiz$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", quiz_handler.cancel_quiz),
            CommandHandler("start", start),
            CallbackQueryHandler(start, pattern="^start$")
        ]
    )

    # Реєстрація всіх обробників
    application.add_handler(gpt_conversation_handler)
    application.add_handler(talk_conversation_handler)
    application.add_handler(quiz_conversation_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("random", random_handler.get_random_fact))
    application.add_handler(CallbackQueryHandler(random_handler.get_random_fact, pattern="^random$"))

    # Обробка кнопок головного меню
    application.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    application.add_handler(CallbackQueryHandler(gpt_handler.start_gpt_conversation, pattern="^gpt$"))
    application.add_handler(CallbackQueryHandler(talk_handler.start_talk, pattern="^talk$"))
    application.add_handler(CallbackQueryHandler(quiz_handler.start_quiz, pattern="^quiz$"))

    logger.info("Бот запущено!")
    application.run_polling()


if __name__ == "__main__":
    main()

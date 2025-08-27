from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from src.bot.handlers.common import start
from src.bot.handlers.random_handler import get_random_fact
from src.bot.handlers.gpt_handler import start_gpt_conversation


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє натискання кнопок головного меню."""
    query = update.callback_query
    await query.answer()

    # Отримуємо дані з кнопки
    data = query.data

    logger.info(f"Користувач {update.effective_user.id} натиснув кнопку: {data}")

    # Викликаємо відповідний обробник залежно від даних
    if data == "start":
        await start(update, context)
    elif data == "random":
        await get_random_fact(update, context)
    elif data == "gpt":
        await start_gpt_conversation(update, context)
    elif data == "talk":
        await query.message.reply_text("Функціонал 'Поговорити зі знаменітістю' поки що не реалізовано.")
    elif data == "quiz":
        await query.message.reply_text("Функціонал 'Пройти тест' поки що не реалізовано.")
    else:
        await query.message.reply_text("Невідома команда меню.")
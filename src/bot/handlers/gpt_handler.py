# src/bot/handlers/gpt_handler.py

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
import openai
from src.settings.config import config
import json

openai.api_key = config.openai_api_key


async def start_gpt_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє команду /gpt та ініціює діалог."""

    if update.message:
        target_message = update.message
        logger.info(f"Користувач {update.effective_user.id} викликав команду /gpt.")
    elif update.callback_query:
        target_message = update.callback_query.message
        await update.callback_query.answer()
        logger.info(f"Користувач {update.effective_user.id} натиснув кнопку GPT.")
    else:
        return ConversationHandler.END

    # Відправляємо зображення
    image_path = config.path_images / "gpt.jpg"
    if not image_path.is_file():
        logger.error(f"Файл зображення не знайдено за шляхом: {image_path}")
        await target_message.reply_text("Вибачте, зображення недоступне.")
    else:
        await target_message.reply_photo(
            photo=image_path.open("rb"),
            caption="Вітаю! Я твій AI-асистент. Надішли мені свій запит."
        )

    # Не надсилаємо окремий промт у чат, бо він буде використовуватися "за кулісами"

    return 1


async def gpt_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє текстові повідомлення користувача та надсилає їх до OpenAI."""
    user_message = update.message.text
    logger.info(f"Користувач {update.effective_user.id} надіслав запит: '{user_message}'")

    # Читаємо промт із файлу
    try:
        with open(config.path_prompts / "gpt.txt", "r", encoding="utf-8") as f:
            gpt_system_prompt = f.read()
    except FileNotFoundError:
        logger.error(f"Файл промта gpt.txt не знайдено за шляхом: {config.path_prompts}")
        gpt_system_prompt = "Ви досвідчений AI асистент, що відповідає на запити користувачів."

    try:
        # Відправляємо запит до OpenAI, включаючи системний промт
        response = openai.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": gpt_system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=config.openai_temperature
        )
        chatgpt_response = response.choices[0].message.content

        await update.message.reply_text(chatgpt_response)

    except Exception as e:
        logger.error(f"Непередбачена помилка: {e}")
        await update.message.reply_text("Вибачте, сталася помилка при обробці запиту. Спробуйте ще раз.")

    return 1
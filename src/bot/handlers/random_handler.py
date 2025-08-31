import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import openai
from loguru import logger
from src.settings.config import config
from src.bot.handlers.common import get_menu_from_file

openai.api_key = config.openai.api_key

async def get_random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Генерує випадковий факт за допомогою ChatGPT та надсилає його користувачеві."""
    logger.info(f"Користувач {update.effective_user.id} викликав команду /random.")

    if update.callback_query:
        message_to_edit = update.callback_query.message
        await update.callback_query.answer()
    else:
        message_to_edit = update.message

    prompt = None
    try:
        # Завантажуємо промпт
        with open(config.paths.prompts / "random.txt", "r", encoding="utf-8") as file:
            prompt = file.read().strip()

        # Генеруємо факт за допомогою OpenAI
        response = openai.chat.completions.create(
            model=config.openai.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.openai.temperature
        )
        chatgpt_response = response.choices[0].message.content

        # Завантажуємо клавіатуру з файлу за допомогою допоміжної функції
        reply_markup = get_menu_from_file(config.paths.menus / "random.json")

        # Відправляємо фото з підписом
        image_path = config.paths.images / "random.jpg"
        with open(image_path, 'rb') as image:
            await message_to_edit.reply_photo(
                photo=image,
                caption=chatgpt_response,
                reply_markup=reply_markup
            )

    except FileNotFoundError as e:
        logger.error(f"Помилка FileNotFoundError: {e}")
        await message_to_edit.reply_text("Вибачте, деякі файли (промпт, меню або зображення) не знайдено.")
    except openai.OpenAIError as e:
        logger.error(f"Помилка OpenAI API: {e}")
        await message_to_edit.reply_text("Вибачте, сталася помилка з'єднання з AI. Спробуйте ще раз.")
    except Exception as e:
        logger.error(f"Непередбачена помилка: {e}")
        await message_to_edit.reply_text("Вибачте, сталася непередбачена помилка. Спробуйте ще раз.")

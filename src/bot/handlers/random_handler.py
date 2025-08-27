import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import openai
from loguru import logger
from src.settings.config import config

openai.api_key = config.openai_api_key


async def get_random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Генерує випадковий факт за допомогою ChatGPT та надсилає його користувачеві."""
    logger.info(f"Користувач {update.effective_user.id} викликав команду /random.")

    # Визначаємо об'єкт повідомлення, з яким будемо працювати
    if update.callback_query:
        message_to_edit = update.callback_query.message
        await update.callback_query.answer()
    else:
        message_to_edit = update.message

    prompt = None
    try:
        with open(config.path_prompts / "random.txt", "r", encoding="utf-8") as file:
            prompt = file.read().strip()
    except FileNotFoundError as e:
        logger.error(f"Помилка FileNotFoundError: {e}")
        await message_to_edit.reply_text("Вибачте, файл промпта 'random.txt' не знайдено.")
        return  # Зупиняємо виконання, якщо файл не знайдено

    try:
        with open(config.path_menus / "random.json", "r", encoding="utf-8") as file:
            menu_data = json.load(file)
            keyboard = [
                [InlineKeyboardButton(button["text"], callback_data=button["callback_data"]) for button in menu_data]]
            reply_markup = InlineKeyboardMarkup(keyboard)
    except FileNotFoundError as e:
        logger.error(f"Помилка FileNotFoundError: {e}")
        reply_markup = None
    except Exception as e:
        logger.error(f"Непередбачена помилка при завантаженні меню: {e}")
        reply_markup = None

    try:
        response = openai.chat.completions.create(
            model=config.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.openai_temperature
        )
        chatgpt_response = response.choices[0].message.content

        image_path = config.path_images / "random.jpg"
        with open(image_path, 'rb') as image:
            await message_to_edit.reply_photo(
                photo=image,
                caption=chatgpt_response,
                reply_markup=reply_markup
            )

    except FileNotFoundError as e:
        logger.error(f"Помилка FileNotFoundError: {e}")
        await message_to_edit.reply_text("Вибачте, деякі файли (зображення) не знайдено.")
    except Exception as e:
        logger.error(f"Непередбачена помилка: {e}")
        await message_to_edit.reply_text("Вибачте, сталася помилка при обробці запиту. Спробуйте ще раз.")
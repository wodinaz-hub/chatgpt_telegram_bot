import json
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import ContextTypes
from loguru import logger
from src.settings.config import config


# Увесь інший код функцій залишається без змін...
def get_menu_from_file(file_path: Path) -> InlineKeyboardMarkup:
    """Зчитує дані кнопок з JSON-файлу та формує клавіатуру."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            menu_data = json.load(file)

        keyboard = [
            [InlineKeyboardButton(text=text, callback_data=key)]
            for key, text in menu_data.items()
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except FileNotFoundError as e:
        logger.error(f"Файл меню не знайдено: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Почати", callback_data="start")]])
    except Exception as e:
        logger.error(f"Помилка при завантаженні меню: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Почати", callback_data="start")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє команду /start, надсилаючи зображення, вітальне повідомлення та кнопки.
    """
    logger.info(f"Користувач {update.effective_user.id} викликав команду /start.")

    if update.message:
        target_message = update.message
    elif update.callback_query:
        target_message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return

    image_path = config.path_images / "main.jpg"
    menu_path = config.path_menus / "main.json"
    reply_markup = get_menu_from_file(menu_path)

    try:
        # Відправляємо фото з підписом та кнопками
        with open(image_path, 'rb') as photo_file:
            await target_message.reply_photo(
                photo=InputFile(photo_file),
                caption="Вітаю! Я твій AI-асистент. Обери одну з команд, щоб почати.",
                reply_markup=reply_markup
            )
    except FileNotFoundError as e:
        logger.error(f"Помилка FileNotFoundError: {e}")
        await target_message.reply_text("Вибачте, файл зображення 'main.jpg' не знайдено.")
    except Exception as e:
        logger.error(f"Непередбачена помилка: {e}")
        await target_message.reply_text("Вибачте, сталася помилка при обробці запиту. Спробуйте ще раз.")
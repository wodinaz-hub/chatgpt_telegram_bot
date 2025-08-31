import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
from loguru import logger

def get_menu_from_file(file_path: Path) -> InlineKeyboardMarkup:
    """Завантажує та генерує клавіатуру з файлу .json, адаптуючись до структури даних."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            menu_data = json.load(file)

        keyboard = []
        if isinstance(menu_data, dict):
            # Обробка формату словника
            for key, text in menu_data.items():
                keyboard.append([InlineKeyboardButton(text=text, callback_data=key)])
        elif isinstance(menu_data, list):
            # Обробка формату списку
            for item in menu_data:
                if "text" in item and "callback_data" in item:
                    keyboard.append([InlineKeyboardButton(item["text"], callback_data=item["callback_data"])])
        else:
            logger.error(f"Невідомий формат даних у файлі {file_path}")
            return None

        return InlineKeyboardMarkup(keyboard)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Помилка при завантаженні файлу меню {file_path}: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Почати", callback_data="start")]
        ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /start та показує головне меню."""
    logger.info(f"Користувач {update.effective_user.id} викликав команду /start.")

    if update.callback_query:
        await update.callback_query.answer()
        message_to_edit = update.callback_query.message
    else:
        message_to_edit = update.message

    # Завантажуємо клавіатуру з файлу
    reply_markup = get_menu_from_file(context.bot_data['config'].paths.menus / "main.json")

    # Надсилаємо зображення
    image_path = context.bot_data['config'].paths.images / "main.jpg"
    with open(image_path, 'rb') as image:
        await message_to_edit.reply_photo(
            photo=InputFile(image),
            caption="Вітаю! Я твій AI-асистент. Обери одну з команд, щоб почати.",
            reply_markup=reply_markup
        )

import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import openai
from loguru import logger
from src.settings.config import config


async def get_random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Генерує випадковий факт за допомогою ChatGPT та надсилає його користувачеві."""
    logger.info(f"Користувач {update.effective_user.id} викликав команду /random.")

    try:
        # Завантажуємо промпт з файлу
        with open(config.paths.prompts / "random.txt", "r", encoding="utf-8") as file:
            prompt_text = file.read().strip()

        # Завантажуємо кнопки меню з файлу
        with open(config.paths.menus / "random.json", "r", encoding="utf-8") as file:
            menu_data = json.load(file)

        # Формуємо клавіатуру з кнопок
        keyboard = [
            [InlineKeyboardButton(button["text"], callback_data=button["callback_data"]) for button in menu_data]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Надсилаємо запит до OpenAI
        response = openai.chat.completions.create(
            model=config.openai.model,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=config.openai.temperature
        )
        chatgpt_response = response.choices[0].message.content

        # Надсилаємо зображення та факт користувачеві
        image_path = config.paths.images / "random.jpg"
        await update.message.reply_photo(photo=open(image_path, 'rb'))
        await update.message.reply_text(chatgpt_response, reply_markup=reply_markup)

    except FileNotFoundError as e:
        logger.error(f"Помилка FileNotFoundError: {e}")
        await update.message.reply_text("Вибачте, деякі файли не знайдено.")
    except Exception as e:
        logger.error(f"Непередбачена помилка: {e}")
        await update.message.reply_text("Вибачте, сталася помилка при обробці запиту. Спробуйте ще раз.")
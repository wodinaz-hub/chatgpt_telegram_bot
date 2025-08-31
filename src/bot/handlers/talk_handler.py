import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
import openai
from src.settings.config import config
from src.bot.handlers.common import start
from src.bot.constants import (
    TALK_PERSONALITY_STATE,
    TALK_CONVERSING_STATE
)


# Допоміжна функція для отримання клавіатури з особистостями
def _get_personalities_keyboard() -> InlineKeyboardMarkup:
    """Зчитує дані з файлу та створює клавіатуру з особистостями."""
    try:
        with open(config.paths.menus / "talk.json", "r", encoding="utf-8") as file:
            menu_data = json.load(file)

        keyboard = [[InlineKeyboardButton(button["text"], callback_data=button["callback_data"])] for button in menu_data]
        return InlineKeyboardMarkup(keyboard)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Помилка при завантаженні talk.json: {e}")
        return None


async def start_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє команду /talk і показує список особистостей та зображення."""
    if update.callback_query:
        await update.callback_query.answer()
        reply_to = update.callback_query.message
    else:
        reply_to = update.message

    logger.info(f"Користувач {update.effective_user.id} розпочав діалог з особистістю.")

    try:
        image_path = config.paths.images / "talk.jpg"
        await reply_to.reply_photo(photo=open(image_path, 'rb'))
    except FileNotFoundError:
        logger.error("Файл talk.jpg не знайдено.")

    reply_markup = _get_personalities_keyboard()
    if not reply_markup:
        await reply_to.reply_text("Вибач, сталася помилка. Спробуй ще раз.")
        return ConversationHandler.END

    await reply_to.reply_text(
        "Обери відому особистість, з якою хочеш поговорити:",
        reply_markup=reply_markup
    )
    return TALK_PERSONALITY_STATE


async def select_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Зберігає обрану особистість і починає діалог."""
    query = update.callback_query
    await query.answer()

    personality_key = query.data

    # Обробка fallback-кнопок
    if personality_key in ["end_talk", "start"]:
        if personality_key == "end_talk":
            await end_talk(update, context)
        return ConversationHandler.END

    try:
        # Динамічно завантажуємо промпт з .txt файлу
        prompt_file_path = config.paths.prompts / f"{personality_key}.txt"
        with open(prompt_file_path, "r", encoding="utf-8") as file:
            system_prompt = file.read().strip()

        context.user_data['personality_prompt'] = system_prompt
        context.user_data['dialogue_history'] = [{"role": "system", "content": system_prompt}]

        # Додаємо кнопку "Завершити розмову"
        keyboard = [[InlineKeyboardButton("Завершити розмову 🚪", callback_data="end_talk")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Надсилаємо зображення конкретної особистості
        try:
            image_path = config.paths.images / f"{personality_key}.jpg"
            await query.message.reply_photo(
                photo=open(image_path, 'rb'),
                caption="Чудово! Тепер ти можеш ставити мені питання. Я відповім як обрана особистість.",
                reply_markup=reply_markup
            )
        except FileNotFoundError:
            logger.error(f"Файл зображення {personality_key}.jpg не знайдено.")
            await query.message.reply_text(
                "Чудово! Тепер ти можеш ставити мені питання. Я відповім як обрана особистість.",
                reply_markup=reply_markup
            )

        return TALK_CONVERSING_STATE
    except FileNotFoundError:
        logger.error(f"Файл промпта {personality_key}.txt не знайдено.")
        await query.message.reply_text("Вибач, не можу знайти інформацію про цю особистість.")
        return ConversationHandler.END
    except (openai.OpenAIError, json.JSONDecodeError) as e:
        logger.error(f"Помилка при виборі особистості: {e}")
        await query.message.reply_text("Вибач, сталася помилка. Спробуй ще раз.")
        return ConversationHandler.END


async def talk_with_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Веде діалог з ChatGPT у ролі обраної особистості."""
    user_message = update.message.text
    dialogue_history = context.user_data.get('dialogue_history', [])
    personality_prompt = context.user_data.get('personality_prompt')

    if not personality_prompt:
        await update.message.reply_text("Будь ласка, спочатку оберіть особистість.")
        return ConversationHandler.END

    dialogue_history.append({"role": "user", "content": user_message})

    try:
        response = openai.chat.completions.create(
            model=config.openai.model,
            messages=dialogue_history,
            temperature=config.openai.temperature
        )

        chatgpt_response = response.choices[0].message.content
        dialogue_history.append({"role": "assistant", "content": chatgpt_response})
        context.user_data['dialogue_history'] = dialogue_history

        # Додаємо кнопку "Завершити розмову"
        keyboard = [[InlineKeyboardButton("Завершити розмову 🚪", callback_data="end_talk")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(chatgpt_response, reply_markup=reply_markup)

        return TALK_CONVERSING_STATE
    except openai.OpenAIError as e:
        logger.error(f"Помилка OpenAI API в діалозі: {e}")
        await update.message.reply_text("Вибач, сталася помилка з'єднання з AI. Спробуй ще раз.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Непередбачена помилка в діалозі: {e}")
        await update.message.reply_text("Вибач, сталася помилка. Спробуй ще раз.")
        return ConversationHandler.END


async def end_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершує діалог з особистістю та повертає в головне меню."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Розмова завершена. Повертаю до головного меню.")
    context.user_data.pop('personality_prompt', None)
    context.user_data.pop('dialogue_history', None)

    await start(update, context)

    return ConversationHandler.END


async def cancel_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершує розмову, якщо користувач викликав команду /cancel."""
    await update.message.reply_text("Розмову завершено.")
    context.user_data.pop('personality_prompt', None)
    context.user_data.pop('dialogue_history', None)
    return ConversationHandler.END

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
import openai
from src.settings.config import config
from src.bot.handlers.common import start
from src.bot.constants import GPT_DIALOGUE_STATE

openai.api_key = config.openai.api_key


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
    image_path = (config.paths.images / "gpt.jpg")
    if not image_path.is_file():
        logger.error(f"Файл зображення не знайдено за шляхом: {image_path}")
        await target_message.reply_text("Вибачте, зображення недоступне.")
    else:
        await target_message.reply_photo(
            photo=image_path.open("rb"),
            caption="Вітаю! Я твій AI-асистент. Надішли мені свій запит."
        )

    # Ініціалізуємо історію діалогу
    context.user_data['dialogue_history'] = []

    return GPT_DIALOGUE_STATE


async def gpt_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє текстові повідомлення користувача та надсилає їх до OpenAI."""
    user_message = update.message.text
    logger.info(f"Користувач {update.effective_user.id} надіслав запит: '{user_message}'")

    # Читаємо промт із файлу
    try:
        with open(config.paths.prompts / "gpt.txt", "r", encoding="utf-8") as f:
            gpt_system_prompt = f.read()
    except FileNotFoundError:
        logger.error(f"Файл промта gpt.txt не знайдено.")
        gpt_system_prompt = "Ви досвідчений AI асистент, що відповідає на запити користувачів."

    # Додаємо системний промпт та повідомлення користувача до історії
    dialogue_history = context.user_data.get('dialogue_history', [])
    if not dialogue_history or dialogue_history[0].get('role') != 'system':
        dialogue_history.insert(0, {"role": "system", "content": gpt_system_prompt})

    dialogue_history.append({"role": "user", "content": user_message})

    try:
        response = openai.chat.completions.create(
            model=config.openai.model,
            messages=dialogue_history,
            temperature=config.openai.temperature
        )
        chatgpt_response = response.choices[0].message.content

        # Додаємо відповідь асистента до історії
        dialogue_history.append({"role": "assistant", "content": chatgpt_response})
        context.user_data['dialogue_history'] = dialogue_history

        # Додаємо кнопку для завершення діалогу
        keyboard = [[InlineKeyboardButton("Завершити розмову 🚪", callback_data="end_gpt_dialogue")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(chatgpt_response, reply_markup=reply_markup)

    except openai.OpenAIError as e:
        logger.error(f"Помилка OpenAI API: {e}")
        await update.message.reply_text("Вибачте, сталася помилка з'єднання з AI. Спробуйте ще раз.")
    except Exception as e:
        logger.error(f"Непередбачена помилка: {e}")
        await update.message.reply_text("Вибачте, сталася помилка при обробці запиту. Спробуйте ще раз.")

    return GPT_DIALOGUE_STATE


async def end_gpt_dialogue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершує діалог з GPT і повертає в головне меню."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("Діалог з ChatGPT завершено. До зустрічі!")
    context.user_data.pop('dialogue_history', None)

    # Викликаємо обробник головного меню
    await start(update, context)

    return ConversationHandler.END

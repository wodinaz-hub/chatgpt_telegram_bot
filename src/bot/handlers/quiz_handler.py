import json
import openai
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from src.settings.config import config
from src.bot.handlers.common import start
from src.bot.constants import (
    QUIZ_SELECTING_TOPIC,
    QUIZ_WAITING_FOR_ANSWER,
    QUIZ_SHOWING_RESULT
)

# Завантажуємо промпт
try:
    with open(config.paths.prompts / "quiz.txt", "r", encoding="utf-8") as f:
        QUIZ_SINGLE_PROMPT = f.read().strip()
except (FileNotFoundError, IOError) as e:
    logger.error(f"Не вдалося завантажити файл промпта: {e}")
    QUIZ_SINGLE_PROMPT = ""

# Допоміжна функція для отримання клавіатури з темами квізу
def _get_quiz_topics_keyboard() -> InlineKeyboardMarkup:
    """Зчитує теми квізу з файлу та створює клавіатуру."""
    try:
        with open(config.paths.menus / "quiz_topics.json", "r", encoding="utf-8") as file:
            menu_data = json.load(file)

        quiz_topics = {k: v for k, v in menu_data.items() if k != "start"}
        keyboard = [
            [InlineKeyboardButton(text, callback_data=key)]
            for key, text in quiz_topics.items()
        ]
        keyboard.append([InlineKeyboardButton("Головне меню 🏠", callback_data="start")])
        return InlineKeyboardMarkup(keyboard)
    except (FileNotFound, json.JSONDecodeError) as e:
        logger.error(f"Помилка при завантаженні файлу quiz_topics.json: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Почати", callback_data="start")]])


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє команду /quiz або натискання кнопки, надсилає зображення та пропонує теми."""
    if update.callback_query:
        await update.callback_query.answer()
        reply_to = update.callback_query.message
        logger.info(f"Користувач {update.callback_query.from_user.id} натиснув кнопку 'quiz'.")
    else:
        reply_to = update.message
        logger.info(f"Користувач {update.effective_user.id} викликав команду /quiz.")

    context.user_data['quiz_score'] = 0

    image_path = config.paths.images / "quiz.jpg"
    await reply_to.reply_photo(photo=open(image_path, 'rb'))

    reply_markup = _get_quiz_topics_keyboard()

    await reply_to.reply_text(
        "Обери тему, щоб почати квіз:",
        reply_markup=reply_markup
    )
    return QUIZ_SELECTING_TOPIC


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерує питання для квізу за допомогою ChatGPT та надсилає його користувачу."""
    query = update.callback_query
    await query.answer()

    # Логіка для "Ще питання" або нової теми
    if query.data == "ask_another_question":
        topic_text = context.user_data.get('quiz_topic_text')
        if not topic_text:
            await query.message.reply_text("Невідома тема квізу. Будь ласка, оберіть тему знову.")
            return QUIZ_SELECTING_TOPIC

        prompt = f"{QUIZ_SINGLE_PROMPT}\nКоманда: '{topic_text}'"
    else:
        # Нова тема вибрана, зберігаємо її
        topic_key = query.data
        topic_mapping = {
            "quiz_python": "програмування мовою Python",
            "quiz_javascript": "програмування мовою JavaScript",
            "quiz_docker": "Docker",
            "quiz_web": "веб-технології"
        }
        topic_text = topic_mapping.get(topic_key)
        if not topic_text:
            await query.message.reply_text("Невідома тема квізу.")
            return ConversationHandler.END

        context.user_data['quiz_topic_text'] = topic_text
        prompt = f"{QUIZ_SINGLE_PROMPT}\nКоманда: '{topic_text}'"

    try:
        response = openai.chat.completions.create(
            model=config.openai.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        question_text = response.choices[0].message.content.strip()

        context.user_data['last_question'] = question_text

        await query.message.reply_text(question_text)

        return QUIZ_WAITING_FOR_ANSWER
    except openai.OpenAIError as e:
        logger.error(f"Помилка OpenAI API при генерації питання: {e}")
        await query.message.reply_text("Вибач, сталася помилка з'єднання з AI. Спробуй ще раз.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Непередбачена помилка при генерації питання: {e}")
        await query.message.reply_text("Вибач, сталася помилка при генерації питання. Спробуй ще раз.")
        return ConversationHandler.END


async def process_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє відповідь користувача, перевіряє її за допомогою ChatGPT."""
    user_answer = update.message.text
    last_question = context.user_data.get('last_question', '')
    score = context.user_data.get('quiz_score', 0)

    prompt = f"{QUIZ_SINGLE_PROMPT}\nПитання: '{last_question}'\nВідповідь користувача: '{user_answer}'"

    try:
        response = openai.chat.completions.create(
            model=config.openai.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        chatgpt_response = response.choices[0].message.content.strip()

        if chatgpt_response.startswith("Правильно!"):
            score += 1
            context.user_data['quiz_score'] = score
            result_text = f"✅ {chatgpt_response}\nТвій рахунок: {score}"
        else:
            result_text = f"❌ {chatgpt_response}\nТвій рахунок: {score}"

        keyboard = [
            [InlineKeyboardButton("Ще питання", callback_data="ask_another_question")],
            [InlineKeyboardButton("Змінити тему", callback_data="change_topic")],
            [InlineKeyboardButton("Завершити", callback_data="end_quiz")],
            [InlineKeyboardButton("Головне меню 🏠", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            result_text,
            reply_markup=reply_markup
        )
        return QUIZ_SHOWING_RESULT
    except openai.OpenAIError as e:
        logger.error(f"Помилка OpenAI API при перевірці відповіді: {e}")
        await update.message.reply_text("Вибач, сталася помилка з'єднання з AI.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Непередбачена помилка при перевірці відповіді: {e}")
        await update.message.reply_text("Вибач, сталася помилка при перевірці відповіді.")
        return ConversationHandler.END


async def change_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обробляє запит на зміну теми."""
    query = update.callback_query
    await query.answer()

    reply_markup = _get_quiz_topics_keyboard()

    await query.message.reply_text(
        "Обери нову тему:",
        reply_markup=reply_markup
    )
    return QUIZ_SELECTING_TOPIC


async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершує квіз."""
    query = update.callback_query
    await query.answer()

    final_score = context.user_data.get('quiz_score', 0)
    await query.message.reply_text(
        f"Квіз завершено. Твій фінальний рахунок: {final_score}. Сподіваюсь, тобі сподобалось!")

    # Викликаємо обробник головного меню, щоб показати кнопки
    await start(update, context)

    return ConversationHandler.END


async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершує квіз, якщо користувач викликав команду /cancel."""
    await update.message.reply_text("Квіз завершено.")
    return ConversationHandler.END

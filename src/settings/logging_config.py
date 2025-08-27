import os
import sys
from loguru import logger
from pathlib import Path

from .config import config


def setup_logging() -> None:
    """
    Налаштовує логування для додатка, використовуючи Loguru.

    Логи виводяться в консоль (рівень INFO), зберігаються в app.log (INFO)
    та в error.log (WARNING).
    """
    log_dir: Path = config.path_logs
    app_log_path: Path = log_dir / "app.log"
    error_log_path: Path = log_dir / "error.log"

    # Створюємо папку для логів, якщо її немає
    os.makedirs(log_dir, exist_ok=True)

    # Видаляємо стандартний обробник Loguru, щоб уникнути дублювання
    logger.remove()

    # Обробник для запису всіх логів у файл app.log
    logger.add(
        sink=app_log_path,
        level="INFO",
        rotation="5 MB",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    # Обробник для запису помилок (WARNING та вище) в error.log
    logger.add(
        sink=error_log_path,
        level="WARNING",  # Записуємо тільки попередження та помилки
        rotation="5 MB",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    # Обробник для виводу в консоль
    logger.add(
        sink=sys.stderr,
        level="INFO",
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    logger.info("Логування налаштовано.")
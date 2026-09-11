"""Конфигурация бота"""
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/it1_records")

GENRES = ["🎸 Рок", "🔊 Электроника", "🎵 Поп", "🎹 Инди"]
GENRE_MAP = {"🎸 Рок": "rock", "🔊 Электроника": "electronic", "🎵 Поп": "pop", "🎹 Инди": "indie"}
GENRE_NAMES = {v: k for k, v in GENRE_MAP.items()}

RECENT_RELEASES_LIMIT = 1  # максимум 1 последний релиз

# Компании по умолчанию
DEFAULT_COMPANIES = ["ИТ1", "ГПБ"]

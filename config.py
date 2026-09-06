"""Конфигурация бота"""
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]
DB_PATH = "it1_records.db"

GENRES = ["🎸 Рок", "🔊 Электроника", "🎵 Поп", "🎹 Инди"]
GENRE_MAP = {"🎸 Рок": "rock", "🔊 Электроника": "electronic", "🎵 Поп": "pop", "🎹 Инди": "indie"}
GENRE_NAMES = {v: k for k, v in GENRE_MAP.items()}

RECENT_RELEASES_LIMIT = 1  # максимум 1 последний релиз

"""Клавиатуры"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import GENRES, GENRE_MAP
from utils import is_admin

def genre_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g, callback_data=f"genre_{GENRE_MAP[g]}") for g in GENRES[:2]],
        [InlineKeyboardButton(text=g, callback_data=f"genre_{GENRE_MAP[g]}") for g in GENRES[2:]]
    ])

def reaction_buttons(artist_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👍 Нравится", callback_data=f"react_{artist_id}_like"),
        InlineKeyboardButton(text="🤷‍♂️ Не моё", callback_data=f"react_{artist_id}_neutral")
    ]])

def skip_button():
    """Кнопка пропуска"""
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⏭️ Пропустить")]], resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)

def main_menu(is_admin_user=False):
    kb = [
        [KeyboardButton(text="🎲 Случайный артист")],
        [KeyboardButton(text="🎼 Выбрать по жанру")],
        [KeyboardButton(text="✨ Добавить артиста")],
        [KeyboardButton(text="📋 Весь каталог")],
        [KeyboardButton(text="📀 Анонсировать релиз")],
        [KeyboardButton(text="💡 Предложить идею")]
    ]
    if is_admin_user: 
        kb.append([KeyboardButton(text="🛠️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Заявки артистов"), KeyboardButton(text="📀 Заявки релизов")],
        [KeyboardButton(text="💡 Идеи от пользователей")],
        [KeyboardButton(text="📝 Редактировать")],
        [KeyboardButton(text="🗑️ Удалить")], 
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="🧪 Создать моки"), KeyboardButton(text="❌ Удалить моки")],
        [KeyboardButton(text="⬅️ Назад")]
    ], resize_keyboard=True)

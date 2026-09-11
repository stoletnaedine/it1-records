"""Клавиатуры"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import GENRES, GENRE_MAP

def genre_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g, callback_data=f"genre_{GENRE_MAP[g]}") for g in GENRES[:2]],
        [InlineKeyboardButton(text=g, callback_data=f"genre_{GENRE_MAP[g]}") for g in GENRES[2:]]
    ])

def company_buttons():
    """Кнопки для выбора компании"""
    from database import get_all_companies
    companies = get_all_companies()
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    for company_id, company_name in companies:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=company_name, callback_data=f"company_{company_id}")
        ])
    
    # Кнопка "Другое" — переходит в текстовый ввод
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="✍️ Другое", callback_data="company_custom")
    ])
    
    return kb

def reaction_buttons(artist_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👍 Нравится", callback_data=f"react_{artist_id}_like"),
        InlineKeyboardButton(text="🤷‍♂️ Не моё", callback_data=f"react_{artist_id}_neutral")
    ]])

def skip_button():
    """Кнопка пропуска"""
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="↩️ Пропустить")]], resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)

def main_menu(is_admin_user=False):
    kb = [
        [KeyboardButton(text="🎲 Случайный артист")],
        [KeyboardButton(text="🎵 Выбрать по жанру")],
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
        [KeyboardButton(text="🏢 Компании")],
        [KeyboardButton(text="🧪 Создать моки"), KeyboardButton(text="❌ Удалить моки")],
        [KeyboardButton(text="⬅️ Назад")]
    ], resize_keyboard=True)

def artist_select_buttons(artists):
    """Кнопки для выбора артиста"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for artist_id, project_name in artists:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎵 {project_name}",
                callback_data=f"selectartist_{artist_id}"
            )
        ])
    return kb

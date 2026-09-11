"""Обработчики сообщений пользователя"""
import asyncio
from aiogram import types
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, GENRES, GENRE_MAP
from database import (
    add_bot_user, get_random_artist, get_artists_by_genre, get_all_artists,
    get_artist_by_id, get_artists_by_user_id, add_application, add_release, add_idea, add_idea_message,
    create_artist, get_all_bot_users, approve_release, get_all_companies, get_company_by_name, add_company as db_add_company
)
from keyboards import main_menu, genre_buttons, company_buttons, reaction_buttons, cancel_keyboard, skip_button, admin_menu
from utils import is_admin, format_artist_with_reactions, format_artist, normalize_links, esc
from states import AddArtistForm, AddReleaseForm, IdeaForm

# ══════════════════════════════════════════════════════════════ START ══════════════════════════════════════════════════════════════

async def cmd_start(message: types.Message, state: FSMContext):
    add_bot_user(message.from_user.id)
    await state.clear()
    is_admin_user = is_admin(message.from_user.id)
    text = """👋 Добро пожаловать в <b>it1-records</b> — музыкальный каталог нашей компании!

🎵 <b>Что здесь можно делать:</b>

🎧 <b>Слушай коллег</b>
Открывай случайных артистов или ищи по жанру — рок, электроника, поп, инди. Здесь музыка твоих коллег из офиса!

👍 <b>Голосуй за любимых</b>
Нравится трек? Поставь 👍 или 🤷‍♂️ — так другие увидят, что зашло команде.

➕ <b>Добавь артиста</b>
Делаешь музыку? Подай заявку — после модерации ты попадёшь в каталог.

📀 <b>Анонсируй новые релизы</b>
Вышел свежий трек? Расскажи всем через бота — релизы разлетаются по команде.

💡 <b>Предлагай идеи</b>
Есть мысли, как улучшить бот? Пиши прямо сюда — админ ответит.
"""
    if is_admin_user: text += "\n🛠️ <b>Админ-панель</b> — управление заявками, артистами и релизами."
    await message.answer(text, reply_markup=main_menu(is_admin_user), parse_mode="HTML")

# ══════════════════════════════════════════════════════════════ CATALOG ══════════════════════════════════════════════════════════════

async def cmd_random(message: types.Message):
    artist = get_random_artist()
    if not artist:
        await message.answer("😢 Каталог пуст!")
        return
    await message.answer(format_artist_with_reactions(artist[0], artist), parse_mode="HTML", reply_markup=reaction_buttons(artist[0]))

async def cmd_by_genre(message: types.Message):
    await message.answer("Выбери жанр:", reply_markup=genre_buttons())

async def genre_callback(callback_query: types.CallbackQuery):
    genre_code = callback_query.data.split("_")[1]
    artists = get_artists_by_genre(genre_code)
    await callback_query.answer()
    
    if not artists:
        await callback_query.message.edit_text("😢 Нет артистов в этом жанре")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for a in artists:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎵 {a[1]} ({a[4]})", callback_data=f"artist_{a[0]}")])
    
    text = f"<b>Выбери артиста:</b>\n\n{len(artists)} найдено"
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

async def cmd_all_catalog(message: types.Message):
    artists = get_all_artists()
    if not artists:
        await message.answer("😢 Каталог пуст")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for a in artists:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎵 {a[1]} ({a[4]})", callback_data=f"artist_{a[0]}")])
    
    text = f"📋 <b>Каталог ({len(artists)})</b>\n\nВыбери артиста:"
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def artist_detail(callback_query: types.CallbackQuery):
    artist_id = int(callback_query.data.split("_")[1])
    artist = get_artist_by_id(artist_id)
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    await callback_query.answer()
    await callback_query.message.edit_text(format_artist_with_reactions(artist_id, artist), parse_mode="HTML", reply_markup=reaction_buttons(artist_id))

# ══════════════════════════════════════════════════════════════ ADD ARTIST ══════════════════════════════════════════════════════════════

async def cmd_add_start(message: types.Message, state: FSMContext):
    await state.set_state(AddArtistForm.project_name)
    await message.answer("✨ <b>Добавить артиста</b>\n\nКак называется твой проект?", reply_markup=cancel_keyboard(), parse_mode="HTML")

async def add_project_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    await state.update_data(project_name=message.text)
    await state.set_state(AddArtistForm.description)
    await message.answer("Кратко опиши свою музыку:", reply_markup=cancel_keyboard())

async def add_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    await state.update_data(description=message.text)
    await state.set_state(AddArtistForm.links)
    await message.answer("Ссылки на твою музыку (можно в одну строку через запятые):\n\nНапример:\nhttps://spotify.com/mymusic\nhttps://soundcloud.com/mymusic", reply_markup=cancel_keyboard())

async def add_links(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    await state.update_data(links=message.text)
    await state.set_state(AddArtistForm.genre)
    await message.answer("🎵 Выбери жанр:", reply_markup=genre_buttons())

async def add_genre_callback(callback_query: types.CallbackQuery, state: FSMContext):
    genre_code = callback_query.data.split("_")[1]
    await state.update_data(genre=genre_code)
    await state.set_state(AddArtistForm.about)
    await callback_query.answer()
    await callback_query.message.edit_text("📝 О себе (по желанию):", reply_markup=skip_button() if skip_button() else cancel_keyboard())

async def add_about(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    if message.text == "↩️ Пропустить":
        await state.update_data(about="")
    else:
        await state.update_data(about=message.text)
    
    await state.set_state(AddArtistForm.company)
    await message.answer("🏢 Из какой ты компании?\n\n(если нет в списке, напиши текстом)", reply_markup=company_buttons())

async def add_company(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора компании из кнопок"""
    company_code = callback_query.data.split("_")[1]
    
    if company_code == "custom":
        await state.set_state(AddArtistForm.company)
        await callback_query.answer()
        await callback_query.message.edit_text("✍️ Напиши название компании:")
        return
    
    company_id = int(company_code)
    data = await state.get_data()
    
    await state.clear()
    
    success = add_application(
        callback_query.from_user.id,
        callback_query.from_user.username or "Unknown",
        data['project_name'],
        data['description'],
        normalize_links(data['links']),
        data['genre'],
        data['about'],
        company_id
    )
    
    if success:
        await callback_query.message.edit_text("✅ Заявка отправлена на модерацию! Спасибо за участие 🎵", parse_mode="HTML")
        await callback_query.bot.send_message(callback_query.from_user.id, "", reply_markup=main_menu(is_admin(callback_query.from_user.id)))
    else:
        await callback_query.answer("❌ Ошибка при добавлении заявки", show_alert=True)

async def add_company_text(message: types.Message, state: FSMContext):
    """Обработчик текстового ввода компании"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    company_name = message.text
    data = await state.get_data()
    
    # Проверяем есть ли такая компания
    company = get_company_by_name(company_name)
    if company:
        company_id = company[0]
    else:
        company_id = db_add_company(company_name)
    
    await state.clear()
    
    success = add_application(
        message.from_user.id,
        message.from_user.username or "Unknown",
        data['project_name'],
        data['description'],
        normalize_links(data['links']),
        data['genre'],
        data['about'],
        company_id
    )
    
    if success:
        await message.answer("✅ Заявка отправлена на модерацию! Спасибо за участие 🎵", reply_markup=main_menu(is_admin(message.from_user.id)))
    else:
        await message.answer("❌ Ошибка при добавлении заявки", reply_markup=main_menu(is_admin(message.from_user.id)))

# ══════════════════════════════════════════════════════════════ RELEASES ══════════════════════════════════════════════════════════════

async def cmd_release_start(message: types.Message, state: FSMContext):
    artists = get_artists_by_user_id(message.from_user.id)
    if not artists:
        await message.answer("❌ У тебя нет артистов в каталоге. Сначала добавь себя!")
        return
    
    from keyboards import artist_select_buttons
    kb = artist_select_buttons(artists)
    await message.answer("🎵 Выбери, из какого артиста анонсировать релиз:", reply_markup=kb)

async def release_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    await state.update_data(release_name=message.text)
    await state.set_state(AddReleaseForm.description)
    await message.answer("📝 Описание релиза (опционально):", reply_markup=skip_button() if skip_button() else cancel_keyboard())

async def release_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    if message.text == "↩️ Пропустить":
        await state.update_data(description="")
    else:
        await state.update_data(description=message.text)
    await state.set_state(AddReleaseForm.genre)
    await message.answer("🎵 Жанр:", reply_markup=genre_buttons())

async def release_genre_callback(callback_query: types.CallbackQuery, state: FSMContext):
    genre_code = callback_query.data.split("_")[1]
    await state.update_data(genre=genre_code)
    await state.set_state(AddReleaseForm.links)
    await callback_query.answer()
    await callback_query.message.edit_text("🔗 Ссылки на релиз:")

async def release_links(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    data = await state.get_data()
    await state.clear()
    
    success = add_release(
        data['artist_id'],
        message.from_user.id,
        data['artist_name'],
        data['release_name'],
        data.get('description', ''),
        data['genre'],
        normalize_links(message.text)
    )
    
    if success:
        await message.answer("✅ Релиз отправлен на модерацию!", reply_markup=main_menu(is_admin(message.from_user.id)))
    else:
        await message.answer("❌ Ошибка при добавлении релиза", reply_markup=main_menu(is_admin(message.from_user.id)))

# ══════════════════════════════════════════════════════════════ IDEAS ══════════════════════════════════════════════════════════════

async def cmd_idea_start(message: types.Message, state: FSMContext):
    await state.set_state(IdeaForm.text)
    await message.answer("💡 Напиши свою идею для улучшения бота:", reply_markup=cancel_keyboard())

async def idea_text(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    idea_id = add_idea(message.from_user.id, message.from_user.username or "Unknown", message.text)
    await state.clear()
    
    if idea_id:
        await message.answer("✅ Спасибо за идею! Админ рассмотрит её 🙏", reply_markup=main_menu(is_admin(message.from_user.id)))
    else:
        await message.answer("❌ Ошибка при добавлении идеи", reply_markup=main_menu(is_admin(message.from_user.id)))

async def cmd_restart(message: types.Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)

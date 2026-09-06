"""Обработчики сообщений пользователя"""
import asyncio
from aiogram import types
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, GENRES, GENRE_MAP
from database import (
    add_bot_user, get_random_artist, get_artists_by_genre, get_all_artists,
    get_artist_by_id, get_artist_by_user_id, add_application, add_release, add_idea, add_idea_message,
    create_artist, get_all_bot_users, approve_release
)
from keyboards import main_menu, genre_buttons, reaction_buttons, cancel_keyboard, skip_button, admin_menu
from utils import is_admin, format_artist_with_reactions, format_artist, normalize_links, esc
from states import AddArtistForm, AddReleaseForm, IdeaForm

# ══════════ START ══════════

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
Вышел свежий трек? Расскажи всем через бота — релизы разлетятся по команде.

💡 <b>Предлагай идеи</b>
Есть мысли, как улучшить бот? Пиши прямо сюда — админ ответит.
"""
    if is_admin_user: text += "\n🛠️ <b>Админ-панель</b> — управление заявками, артистами и релизами."
    await message.answer(text, reply_markup=main_menu(is_admin_user), parse_mode="HTML")

# ══════════ CATALOG ══════════

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
    
    # Показываем список как в "Весь каталог"
    text = f"<b>Жанр: {GENRES[list(GENRE_MAP.values()).index(genre_code)]}</b>\n\n"
    kb = callback_query.message.reply_markup
    if not kb:
        kb = None
    
    # Отправляем список артистов по аналогии с Весь каталог
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for a in artists:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎵 {a[1]} ({a[4]})", callback_data=f"artist_{a[0]}")])
    
    text += "Выбери артиста:"
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

# ══════════ ADD ARTIST ══════════

async def cmd_add_start(message: types.Message, state: FSMContext):
    await state.set_state(AddArtistForm.project_name)
    await message.answer("➕ <b>Добавить артиста</b>\n\nКак называется твой проект?", reply_markup=cancel_keyboard(), parse_mode="HTML")

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
    await message.answer("Ссылки на твою музыку (через запятую или с новой строки):", reply_markup=cancel_keyboard())

async def add_links(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    await state.update_data(links=normalize_links(message.text))
    await state.set_state(AddArtistForm.genre)
    await message.answer("Выбери главный жанр:", reply_markup=genre_buttons())

async def add_genre_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(genre=callback_query.data.split("_")[1])
    await state.set_state(AddArtistForm.about)
    await callback_query.answer()
    await callback_query.message.answer("О себе (по желанию):", reply_markup=skip_button())

async def add_about(message: types.Message, state: FSMContext):
    if message.text == "⏭️ Пропустить":
        data = await state.get_data()
        await state.clear()
        tg_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
        app_id = add_application(message.from_user.id, tg_username, data["project_name"], data["description"], data["links"], data["genre"], None)
        await message.answer(f"✅ Заявка #{app_id} отправлена на модерацию!\nАдмин проверит её в течение 24 часов. 🎉", reply_markup=main_menu(is_admin(message.from_user.id)))
        
        # Отправляем админам
        from keyboards import admin_menu
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        for admin_id in ADMIN_IDS:
            try:
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{app_id}"), InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{app_id}")]])
                msg = f"🔔 <b>Новая заявка #{app_id}</b>\n\n🎵 <b>{data['project_name']}</b>\n📝 {data['description']}\n🎼 Жанр: {data['genre']}\n🔗 Ссылки: {data['links']}"
                await message.bot.send_message(admin_id, msg, reply_markup=kb, parse_mode="HTML")
            except: pass
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    data = await state.get_data()
    await state.clear()
    
    tg_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    app_id = add_application(message.from_user.id, tg_username, data["project_name"], data["description"], data["links"], data["genre"], message.text)
    
    await message.answer(f"✅ Заявка #{app_id} отправлена на модерацию!\nАдмин проверит её в течение 24 часов. 🎉", reply_markup=main_menu(is_admin(message.from_user.id)))
    
    # Отправляем админам
    for admin_id in ADMIN_IDS:
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{app_id}"), InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{app_id}")]])
            msg = f"🔔 <b>Новая заявка #{app_id}</b>\n\n🎵 <b>{data['project_name']}</b>\n📝 {data['description']}\n🎼 Жанр: {data['genre']}\n🔗 Ссылки: {data['links']}\n\n📌 {message.text}"
            await message.bot.send_message(admin_id, msg, reply_markup=kb, parse_mode="HTML")
        except: pass

# ══════════ ADD RELEASE ══════════

async def cmd_release_start(message: types.Message, state: FSMContext):
    artist = get_artist_by_user_id(message.from_user.id)
    if not artist:
        await message.answer("❌ Сначала добавь себя в каталог через «➕ Добавить артиста»", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    await state.update_data(artist_id=artist[0])
    await state.set_state(AddReleaseForm.release_name)
    await message.answer("📀 <b>Анонс нового релиза</b>\n\nНазвание релиза:", reply_markup=cancel_keyboard(), parse_mode="HTML")

async def release_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    await state.update_data(release_name=message.text)
    await state.set_state(AddReleaseForm.description)
    await message.answer("Описание релиза:", reply_markup=skip_button())

async def release_description(message: types.Message, state: FSMContext):
    if message.text == "⏭️ Пропустить":
        await state.update_data(description=None)
    else:
        if message.text == "❌ Отмена":
            await state.clear()
            await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
            return
        await state.update_data(description=message.text)
    
    await state.set_state(AddReleaseForm.genre)
    await message.answer("Жанр релиза:", reply_markup=genre_buttons())

async def release_genre_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(genre=callback_query.data.split("_")[1])
    await state.set_state(AddReleaseForm.links)
    await callback_query.answer()
    await callback_query.message.answer("Ссылки на релиз (через запятую или с новой строки):", reply_markup=cancel_keyboard())

async def release_links(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    data = await state.get_data()
    await state.clear()
    
    links = normalize_links(message.text)
    release_id = add_release(data['artist_id'], message.from_user.id, data['release_name'], data.get('description'), data['genre'], links)
    
    await message.answer(f"✅ Заявка на релиз #{release_id} отправлена админу!\nПосле одобрения всем придёт уведомление. 🎉", reply_markup=main_menu(is_admin(message.from_user.id)))
    
    for admin_id in ADMIN_IDS:
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            artist = get_artist_by_id(data['artist_id'])
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_rel_{release_id}"), InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_rel_{release_id}")]])
            msg = f"📀 <b>Новый релиз #{release_id}</b>\n\n🎵 Артист: <b>{artist[1]}</b>\n🎶 Релиз: <b>{data['release_name']}</b>\n🎼 Жанр: {data['genre']}\n🔗 Ссылки: {links}"
            if data.get('description'):
                msg += f"\n📝 Описание: {data['description']}"
            await message.bot.send_message(admin_id, msg, reply_markup=kb, parse_mode="HTML")
        except: pass

# ══════════ IDEAS ══════════

async def cmd_idea_start(message: types.Message, state: FSMContext):
    await state.set_state(IdeaForm.text)
    await message.answer("💡 <b>Предложить идею</b>\n\nОпиши свою идею для улучшения it1-records:", reply_markup=cancel_keyboard(), parse_mode="HTML")

async def idea_text(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
        return
    
    await state.clear()
    tg_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    idea_id = add_idea(message.from_user.id, tg_username, message.text)
    add_idea_message(idea_id, message.from_user.id, message.text)
    
    await message.answer(f"✅ Твоя идея #{idea_id} отправлена админам!\nОни смогут ответить тебе прямо в боте. 💡", reply_markup=main_menu(is_admin(message.from_user.id)))
    
    for admin_id in ADMIN_IDS:
        try:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Ответить", callback_data=f"idea_reply_{idea_id}")], [InlineKeyboardButton(text="✅ Закрыть идею", callback_data=f"idea_close_{idea_id}")]])
            msg = f"💡 <b>Новая идея #{idea_id}</b>\n\nОт: {tg_username}\n\n{message.text}"
            await message.bot.send_message(admin_id, msg, reply_markup=kb, parse_mode="HTML")
        except: pass

# ══════════════════ RESTART ══════════════════

async def cmd_restart(message: types.Message, state: FSMContext):
    """Перезагрузить бота для пользователя (очистить состояние и вернуться в главное меню)"""
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
Вышел свежий трек? Расскажи всем через бота — релизы разлетяются по команде.

💡 <b>Предлагай идеи</b>
Есть мысли, как улучшить бот? Пиши прямо сюда — админ ответит.
"""
    if is_admin_user: text += "\n🛠️ <b>Админ-панель</b> — управление заявками, артистами и релизами."
    await message.answer(text, reply_markup=main_menu(is_admin_user), parse_mode="HTML")

"""Точка входа бота с обработкой ошибок"""
import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from aiogram.filters import StateFilter

from config import TELEGRAM_TOKEN, ADMIN_IDS
from database import init_db
from error_handler import BotErrorHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорты обработчиков
from states import *
from handlers import (
    cmd_start, cmd_restart, cmd_random, cmd_by_genre, genre_callback, cmd_all_catalog, artist_detail,
    cmd_add_start, add_project_name, add_description, add_links, add_genre_callback, add_about,
    cmd_release_start, release_name, release_description, release_genre_callback, release_links,
    cmd_idea_start, idea_text
)
from callbacks import (
    add_reaction_callback, admin_app_detail, approve_app_callback, reject_app_callback, reject_reason,
    admin_release_detail, approve_release_callback, reject_release_callback, reject_release_reason,
    admin_idea_detail, admin_idea_reply, admin_idea_reply_message, admin_idea_close,
    admin_edit_select, admin_edit_field, admin_edit_value, admin_edit_genre_callback, admin_edit_cancel,
    admin_delete_confirm, admin_delete_exec, admin_delete_cancel, admin_create_mocks, admin_delete_mocks,
    select_artist_for_release
)
from keyboards import main_menu, admin_menu, cancel_keyboard, genre_buttons, skip_button
from utils import is_admin, normalize_links
from database import (
    get_pending_applications, get_pending_releases, get_open_ideas, get_all_artists,
    create_artist, get_artists_by_user_id, add_application
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
from config import DATABASE_URL

# Глобальный error handler
error_handler = None
bot = None

# ══════════ ADMIN MENU HANDLERS ══════════

async def admin_panel(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    await message.answer("🛠️ Админ-панель it1-records", reply_markup=admin_menu())

async def admin_applications(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    apps = get_pending_applications()
    if not apps:
        await message.answer("✅ Нет заявок на артистов", reply_markup=admin_menu())
        return
    text = f"📋 <b>Заявки на модерацию ({len(apps)})</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for aid, uid, uname, pn, desc, links, genre, about in apps:
        text += f"#{aid}: <b>{pn}</b> от {uname}\n"
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"#{aid}: {pn[:20]}", callback_data=f"app_{aid}")])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def admin_releases(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    releases = get_pending_releases()
    if not releases:
        await message.answer("✅ Нет заявок на релизы", reply_markup=admin_menu())
        return
    text = f"📀 <b>Заявки на релизы ({len(releases)})</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for rid, aid, artist_name, rel_name, desc, genre, links, uid in releases:
        text += f"#{rid}: <b>{rel_name}</b> от {artist_name}\n"
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"#{rid}: {rel_name[:20]}", callback_data=f"release_{rid}")])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def admin_ideas(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    ideas = get_open_ideas()
    if not ideas:
        await message.answer("✅ Нет открытых идей", reply_markup=admin_menu())
        return
    text = f"💡 <b>Идеи от пользователей ({len(ideas)})</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for iid, uname, itext, created in ideas:
        text += f"#{iid} от {uname}: {itext[:30]}...\n"
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"💡 #{iid}", callback_data=f"idea_detail_{iid}")])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def admin_stats(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM artists")
        total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'")
        pending = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM applications WHERE status = 'approved'")
        approved = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM applications WHERE status = 'rejected'")
        rejected = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM releases WHERE status = 'pending'")
        releases_pending = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM releases WHERE status = 'approved'")
        releases_approved = c.fetchone()[0]
        
        c.execute("SELECT genre, COUNT(*) FROM artists GROUP BY genre")
        genres = c.fetchall()
        
        c.execute("SELECT COUNT(*) FROM ideas WHERE status = 'open'")
        open_ideas = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM bot_users")
        bot_users_count = c.fetchone()[0]
        
        c.close()
        conn.close()
        
        text = f"📊 <b>Статистика it1-records</b>\n\n🎵 Всего артистов: <b>{total}</b>\n📋 Заявок артистов (ожидают): <b>{pending}</b>\n✅ Одобрено: <b>{approved}</b>\n❌ Отклонено: <b>{rejected}</b>\n\n📀 Заявок релизов (ожидают): <b>{releases_pending}</b>\n✅ Релизов одобрено: <b>{releases_approved}</b>\n\n👥 Пользователей бота: <b>{bot_users_count}</b>\n💡 Открытых идей: <b>{open_ideas}</b>\n\n<b>По жанрам:</b>\n"
        for g, cnt in genres:
            text += f"{g}: {cnt}\n"
        
        await message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in admin_stats: {e}")
        await message.answer("❌ Ошибка при загрузке статистики")

async def create_project_name(message, state):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=admin_menu())
        return
    await state.update_data(project_name=message.text)
    await state.set_state(CreateArtistForm.description)
    await message.answer("Описание музыки:", reply_markup=cancel_keyboard())

async def create_description(message, state):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=admin_menu())
        return
    await state.update_data(description=message.text)
    await state.set_state(CreateArtistForm.links)
    await message.answer("Ссылки на музыку (через запятую или с новой строки):", reply_markup=cancel_keyboard())

async def create_links(message, state):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=admin_menu())
        return
    await state.update_data(links=normalize_links(message.text))
    await state.set_state(CreateArtistForm.genre)
    await message.answer("Жанр:", reply_markup=genre_buttons())

async def create_genre_callback(callback_query, state):
    await state.update_data(genre=callback_query.data.split("_")[1])
    await state.set_state(CreateArtistForm.about)
    await callback_query.answer()
    await callback_query.message.answer("О себе (по желанию):", reply_markup=skip_button())

async def create_about(message, state):
    if message.text == "⏭️ Пропустить":
        data = await state.get_data()
        await state.clear()
        tg_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
        if create_artist(message.from_user.id, tg_username, data["project_name"], data["description"], data["links"], data["genre"], None):
            await message.answer(f"✅ Артист <b>{data['project_name']}</b> добавлен в каталог!", reply_markup=admin_menu(), parse_mode="HTML")
        else:
            await message.answer("❌ Ошибка: проект с таким названием уже существует", reply_markup=admin_menu())
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=admin_menu())
        return
    
    data = await state.get_data()
    await state.clear()
    tg_username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    if create_artist(message.from_user.id, tg_username, data["project_name"], data["description"], data["links"], data["genre"], message.text):
        await message.answer(f"✅ Артист <b>{data['project_name']}</b> добавлен в каталог!", reply_markup=admin_menu(), parse_mode="HTML")
    else:
        await message.answer("❌ Ошибка: проект с таким названием уже существует", reply_markup=admin_menu())

async def admin_edit_start(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    artists = get_all_artists()
    if not artists:
        await message.answer("❌ Нет артистов для редактирования", reply_markup=admin_menu())
        return
    text = "📝 <b>Выбери артиста для редактирования:</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for aid, pn, desc, links, genre, about in artists:
        text += f"#{aid}: <b>{pn}</b>\n"
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"📝 #{aid}: {pn[:18]}", callback_data=f"edit_{aid}")])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def admin_delete_start(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    artists = get_all_artists()
    if not artists:
        await message.answer("❌ Нет артистов для удаления", reply_markup=admin_menu())
        return
    text = "🗑️ <b>Выбери артиста для удаления:</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for aid, pn, desc, links, genre, about in artists:
        text += f"#{aid}: <b>{pn}</b>\n"
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🗑️ #{aid}: {pn[:18]}", callback_data=f"del_{aid}")])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# ══════════ MAIN MESSAGE ROUTER ══════════

async def message_handler(message, state):
    try:
        current_state = await state.get_state()
        
        if message.text == "🎲 Случайный артист":
            await cmd_random(message)
        elif message.text == "🎼 Выбрать по жанру":
            await cmd_by_genre(message)
        elif message.text == "✨ Добавить артиста":
            await cmd_add_start(message, state)
        elif message.text == "⬅️ Назад":
            if is_admin(message.from_user.id):
                await admin_panel(message)
            else:
                await cmd_start(message, state)
        elif message.text == "📋 Весь каталог":
            await cmd_all_catalog(message)
        elif message.text == "📀 Анонсировать релиз":
            await cmd_release_start(message, state)
        elif message.text == "💡 Предложить идею":
            await cmd_idea_start(message, state)
        elif message.text == "⬅️ Назад":
            await cmd_start(message, state)
        elif message.text == "🛠️ Админ-панель":
            await admin_panel(message)
        elif message.text == "📋 Заявки артистов":
            await admin_applications(message)
        elif message.text == "📀 Заявки релизов":
            await admin_releases(message)
        elif message.text == "💡 Идеи от пользователей":
            await admin_ideas(message)
        elif message.text == "📊 Статистика":
            await admin_stats(message)
        elif message.text == "📝 Редактировать":
            await admin_edit_start(message)
        elif message.text == "🗑️ Удалить":
            await admin_delete_start(message)
        elif message.text == "🧪 Создать моки":
            from callbacks import admin_create_mocks
            await admin_create_mocks(message)
        elif message.text == "❌ Удалить моки":
            from callbacks import admin_delete_mocks
            await admin_delete_mocks(message)
        elif current_state == AddArtistForm.project_name.state:
            await add_project_name(message, state)
        elif current_state == AddArtistForm.description.state:
            await add_description(message, state)
        elif current_state == AddArtistForm.links.state:
            await add_links(message, state)
        elif current_state == AddArtistForm.about.state:
            await add_about(message, state)
        elif current_state == AddReleaseForm.release_name.state:
            await release_name(message, state)
        elif current_state == AddReleaseForm.description.state:
            await release_description(message, state)
        elif current_state == AddReleaseForm.links.state:
            await release_links(message, state)
        elif current_state == CreateArtistForm.project_name.state:
            await create_project_name(message, state)
        elif current_state == CreateArtistForm.description.state:
            await create_description(message, state)
        elif current_state == CreateArtistForm.links.state:
            await create_links(message, state)
        elif current_state == CreateArtistForm.about.state:
            await create_about(message, state)
        elif current_state == EditArtistForm.value.state:
            await admin_edit_value(message, state)
        elif current_state == RejectForm.reason.state:
            await reject_reason(message, state)
        elif current_state == RejectReleaseForm.reason.state:
            await reject_release_reason(message, state)
        elif current_state == IdeaForm.text.state:
            await idea_text(message, state)
        elif current_state == IdeaReplyForm.message.state:
            await admin_idea_reply_message(message, state)
        else:
            await message.answer("Выбери из меню 👇", reply_markup=main_menu(is_admin(message.from_user.id)))
    except Exception as e:
        logger.error(f"Error in message_handler: {e}\n{traceback.format_exc()}")
        if error_handler:
            await error_handler.handle_exception(e, "message_handler")
        await message.answer("❌ Произошла ошибка. Админы уведомлены.")

async def cancel_any(message, state):
    try:
        await state.clear()
        if message.text == "⬅️ Назад":
            await cmd_start(message, state)
            return
        await message.answer("Отмена 👋", reply_markup=main_menu(is_admin(message.from_user.id)))
    except Exception as e:
        logger.error(f"Error in cancel_any: {e}")
        if error_handler:
            await error_handler.handle_exception(e, "cancel_any")

# ══════════ MAIN ══════════

async def main():
    global error_handler, bot
    
    try:
        init_db()
        bot = Bot(token=TELEGRAM_TOKEN)
        error_handler = BotErrorHandler(bot, ADMIN_IDS)
        
        dp = Dispatcher(storage=MemoryStorage())
        
        # COMMANDS
        dp.message.register(cmd_start, Command("start"))
        dp.message.register(cmd_restart, Command("restart"))
        dp.message.register(cancel_any, F.text.in_({"❌ Отмена", "⬅️ Назад"}))
        
        # CALLBACKS: GENRES
        dp.callback_query.register(add_genre_callback, StateFilter(AddArtistForm.genre), F.data.startswith("genre_"))
        dp.callback_query.register(create_genre_callback, StateFilter(CreateArtistForm.genre), F.data.startswith("genre_"))
        dp.callback_query.register(release_genre_callback, StateFilter(AddReleaseForm.genre), F.data.startswith("genre_"))
        dp.callback_query.register(admin_edit_genre_callback, StateFilter(EditArtistForm.value), F.data.startswith("genre_"))
        dp.callback_query.register(genre_callback, F.data.startswith("genre_"))
        
        # CALLBACKS: REACTIONS
        dp.callback_query.register(add_reaction_callback, F.data.startswith("react_"))
        
        # CALLBACKS: ARTIST DETAIL
        dp.callback_query.register(artist_detail, F.data.startswith("artist_"))
        
        # CALLBACKS: APPLICATIONS (регистрируй ПОСЛЕ специфичных!)
        dp.callback_query.register(admin_app_detail, F.data.startswith("app_"))
        dp.callback_query.register(approve_app_callback, F.data.startswith("approve_") & ~F.data.startswith("approve_rel_"))
        dp.callback_query.register(reject_app_callback, F.data.startswith("reject_") & ~F.data.startswith("reject_rel_"))
        
        # CALLBACKS: RELEASES (регистрируй ПЕРВЫМИ - более специфичные!)
        dp.callback_query.register(admin_release_detail, F.data.startswith("release_"))
        dp.callback_query.register(approve_release_callback, F.data.startswith("approve_rel_"))
        dp.callback_query.register(reject_release_callback, F.data.startswith("reject_rel_"))
        
        # CALLBACKS: IDEAS
        dp.callback_query.register(admin_idea_detail, F.data.startswith("idea_detail_"))
        dp.callback_query.register(admin_idea_reply, F.data.startswith("idea_reply_"))
        dp.callback_query.register(admin_idea_close, F.data.startswith("idea_close_"))
        
        # CALLBACKS: EDIT
        dp.callback_query.register(admin_edit_select, F.data.startswith("edit_") & ~F.data.startswith("editfield_") & ~F.data.startswith("edit_cancel"))
        dp.callback_query.register(admin_edit_field, F.data.startswith("editfield_"))
        dp.callback_query.register(admin_edit_cancel, F.data == "edit_cancel")
        
        # CALLBACKS: DELETE
        dp.callback_query.register(admin_delete_confirm, F.data.startswith("del_") & ~F.data.startswith("del_exec_") & ~F.data.startswith("del_cancel"))
        dp.callback_query.register(admin_delete_exec, F.data.startswith("del_exec_"))
        dp.callback_query.register(admin_delete_cancel, F.data == "del_cancel")
        
        # FSM: ADD ARTIST
        dp.message.register(add_project_name, AddArtistForm.project_name)
        dp.message.register(add_description, AddArtistForm.description)
        dp.message.register(add_links, AddArtistForm.links)
        dp.message.register(add_about, AddArtistForm.about)
        
        # FSM: ADD RELEASE
        dp.message.register(release_name, AddReleaseForm.release_name)
        dp.message.register(release_description, AddReleaseForm.description)
        dp.message.register(release_links, AddReleaseForm.links)
        
        # FSM: CREATE ARTIST
        dp.message.register(create_project_name, CreateArtistForm.project_name)
        dp.message.register(create_description, CreateArtistForm.description)
        dp.message.register(create_links, CreateArtistForm.links)
        dp.message.register(create_about, CreateArtistForm.about)
        
        # FSM: EDIT/REJECT
        dp.message.register(admin_edit_value, EditArtistForm.value)
        dp.message.register(reject_reason, RejectForm.reason)
        dp.message.register(reject_release_reason, RejectReleaseForm.reason)
        
        # FSM: IDEAS
        dp.message.register(idea_text, IdeaForm.text)
        dp.message.register(admin_idea_reply_message, IdeaReplyForm.message)
        
        # MAIN ROUTER
        dp.message.register(message_handler)
        
        print("✅ it1-records запущен!")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical error: {e}\n{traceback.format_exc()}")
        if error_handler and bot:
            await error_handler.handle_exception(e, "main")
        raise

if __name__ == "__main__":
    asyncio.run(main())

"""Точка входа бота с обработкой ошибок"""
import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from aiogram.filters import StateFilter

from config import TELEGRAM_TOKEN, ADMIN_IDS
from database import init_db, init_companies
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
    cmd_add_start, add_project_name, add_description, add_links, add_genre_callback, add_about, add_company, add_company_text,
    cmd_release_start, release_name, release_description, release_genre_callback, release_links,
    cmd_idea_start, idea_text
)
from callbacks import (
    add_reaction_callback, admin_app_detail, approve_app_callback, reject_app_callback, reject_reason,
    admin_release_detail, approve_release_callback, reject_release_callback, reject_release_reason,
    admin_idea_detail, admin_idea_reply, admin_idea_reply_message, admin_idea_close,
    admin_edit_select, admin_edit_field, admin_edit_value, admin_edit_genre_callback, admin_edit_company_callback, admin_edit_company_text, admin_edit_cancel,
    admin_delete_confirm, admin_delete_exec, admin_delete_cancel, admin_create_mocks, admin_delete_mocks,
    select_artist_for_release, admin_add_company_start, admin_add_company_name
)
from keyboards import main_menu, admin_menu, cancel_keyboard, genre_buttons, company_buttons, skip_button
from utils import is_admin, normalize_links
from database import (
    get_pending_applications, get_pending_releases, get_open_ideas, get_all_artists,
    create_artist, get_artists_by_user_id, add_application, get_all_companies
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import psycopg2
from config import DATABASE_URL

# Глобальный error handler
error_handler = None
bot = None

# ══════════════════════════════════════════════════════════════ ADMIN MENU HANDLERS ══════════════════════════════════════════════════════════════

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
    for app in apps:
        aid, uid, uname, pn, desc, links, genre, about, company_name = app[:9]
        text += f"#{aid}: <b>{pn}</b> от {uname} ({company_name})\n"
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
        
        c.execute("SELECT COUNT(*) FROM companies")
        companies_count = c.fetchone()[0]
        
        c.close()
        conn.close()
        
        text = f"📊 <b>Статистика it1-records</b>\n\n🎵 Всего артистов: <b>{total}</b>\n📋 Заявок артистов (ожидают): <b>{pending}</b>\n✅ Одобрено: <b>{approved}</b>\n❌ Отклонено: <b>{rejected}</b>\n\n📀 Заявок релизов (ожидают): <b>{releases_pending}</b>\n✅ Релизов одобрено: <b>{releases_approved}</b>\n\n👥 Пользователей бота: <b>{bot_users_count}</b>\n💡 Открытых идей: <b>{open_ideas}</b>\n🏢 Компаний: <b>{companies_count}</b>\n\n<b>По жанрам:</b>\n"
        for g, cnt in genres:
            text += f"{g}: {cnt}\n"
        
        await message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in admin_stats: {e}")
        await message.answer("❌ Ошибка при загрузке статистики")

async def admin_edit_start(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    artists = get_all_artists()
    if not artists:
        await message.answer("❌ Нет артистов для редактирования", reply_markup=admin_menu())
        return
    
    text = f"📝 <b>Выбери артиста для редактирования ({len(artists)})</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for a in artists:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎵 {a[1]}", callback_data=f"edit_select_{a[0]}")])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def admin_delete_start(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    artists = get_all_artists()
    if not artists:
        await message.answer("❌ Нет артистов для удаления", reply_markup=admin_menu())
        return
    
    text = f"🗑️ <b>Выбери артиста для удаления ({len(artists)})</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for a in artists:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"🎵 {a[1]}", callback_data=f"delete_confirm_{a[0]}")])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

async def admin_company_menu(message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    companies = get_all_companies()
    
    text = f"🏢 <b>Управление компаниями ({len(companies)})</b>\n\n"
    for cid, cname in companies:
        text += f"• {cname}\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить новую", callback_data="add_company")]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# ══════════════════════════════════════════════════════════════ ROUTER SETUP ══════════════════════════════════════════════════════════════

async def main():
    global bot, error_handler
    
    # Инициализация БД
    init_db()
    init_companies()
    
    # Создание бота и диспетчера
    bot = Bot(token=TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Error handler
    error_handler = BotErrorHandler(bot, ADMIN_IDS)
    
    # ═════════════════════════════════════════════════════════════════ COMMANDS ═════════════════════════════════════════════════════════════════
    
    # Start
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_restart, Command("restart"))
    
    # Catalog
    dp.message.register(cmd_random, F.text == "🎲 Случайный артист")
    dp.message.register(cmd_by_genre, F.text == "🎵 Выбрать по жанру")
    dp.message.register(cmd_all_catalog, F.text == "📋 Весь каталог")
    
    # Add artist
    dp.message.register(cmd_add_start, F.text == "✨ Добавить артиста")
    dp.message.register(add_project_name, AddArtistForm.project_name)
    dp.message.register(add_description, AddArtistForm.description)
    dp.message.register(add_links, AddArtistForm.links)
    dp.message.register(add_about, AddArtistForm.about)
    dp.message.register(add_company_text, AddArtistForm.company)
    
    # Release
    dp.message.register(cmd_release_start, F.text == "📀 Анонсировать релиз")
    dp.message.register(release_name, AddReleaseForm.release_name)
    dp.message.register(release_description, AddReleaseForm.description)
    dp.message.register(release_links, AddReleaseForm.links)
    
    # Ideas
    dp.message.register(cmd_idea_start, F.text == "💡 Предложить идею")
    dp.message.register(idea_text, IdeaForm.text)
    
    # Admin
    dp.message.register(admin_panel, F.text == "🛠️ Админ-панель")
    dp.message.register(admin_applications, F.text == "📋 Заявки артистов")
    dp.message.register(admin_releases, F.text == "📀 Заявки релизов")
    dp.message.register(admin_ideas, F.text == "💡 Идеи от пользователей")
    dp.message.register(admin_edit_start, F.text == "📝 Редактировать")
    dp.message.register(admin_delete_start, F.text == "🗑️ Удалить")
    dp.message.register(admin_stats, F.text == "📊 Статистика")
    dp.message.register(admin_company_menu, F.text == "🏢 Компании")
    
    async def admin_create_mocks_handler(message):
        await admin_create_mocks(type('obj', (object,), {'data': 'admin_create_mocks', 'answer': message.answer, 'message': message, 'from_user': message.from_user})())
    
    async def admin_delete_mocks_handler(message):
        await admin_delete_mocks(type('obj', (object,), {'data': 'admin_delete_mocks', 'answer': message.answer, 'message': message, 'from_user': message.from_user})())
    
    dp.message.register(admin_create_mocks_handler, F.text == "🧪 Создать моки")
    dp.message.register(admin_delete_mocks_handler, F.text == "❌ Удалить моки")
    
    async def go_back(message):
        await cmd_start(message, dp.fsm_context)
    
    dp.message.register(go_back, F.text == "⬅️ Назад")
    
    # ═════════════════════════════════════════════════════════════════ CALLBACKS ═════════════════════════════════════════════════════════════════
    
    # Reactions
    dp.callback_query.register(add_reaction_callback, F.data.startswith("react_"))
    
    # Genre
    dp.callback_query.register(genre_callback, F.data.startswith("genre_"))
    dp.callback_query.register(add_genre_callback, F.data.startswith("genre_"))
    dp.callback_query.register(release_genre_callback, F.data.startswith("genre_"))
    
    # Company
    dp.callback_query.register(add_company, F.data.startswith("company_"))
    dp.callback_query.register(admin_edit_company_callback, F.data.startswith("company_"))
    dp.callback_query.register(admin_add_company_start, F.data == "add_company")
    
    # Artist detail
    dp.callback_query.register(artist_detail, F.data.startswith("artist_"))
    
    # Applications
    dp.callback_query.register(admin_app_detail, F.data.startswith("app_"))
    dp.callback_query.register(approve_app_callback, F.data.startswith("approve_") & ~F.data.startswith("approve_rel_"))
    dp.callback_query.register(reject_app_callback, F.data.startswith("reject_") & ~F.data.startswith("reject_rel_"))
    
    # Releases
    dp.callback_query.register(admin_release_detail, F.data.startswith("release_"))
    dp.callback_query.register(approve_release_callback, F.data.startswith("approve_rel_"))
    dp.callback_query.register(reject_release_callback, F.data.startswith("reject_rel_"))
    
    # Ideas
    dp.callback_query.register(admin_idea_detail, F.data.startswith("idea_detail_"))
    dp.callback_query.register(admin_idea_reply, F.data.startswith("idea_reply_"))
    dp.callback_query.register(admin_idea_close, F.data.startswith("idea_close_"))
    
    # Edit
    dp.callback_query.register(admin_edit_select, F.data.startswith("edit_select_"))
    dp.callback_query.register(admin_edit_field, F.data.startswith("edit_"))
    dp.callback_query.register(admin_edit_genre_callback, F.data.startswith("genre_") & StateFilter(EditArtistForm.value))
    dp.callback_query.register(admin_edit_cancel, F.data == "edit_cancel")
    
    # Delete
    dp.callback_query.register(admin_delete_confirm, F.data.startswith("delete_confirm_"))
    dp.callback_query.register(admin_delete_exec, F.data.startswith("delete_exec_"))
    dp.callback_query.register(admin_delete_cancel, F.data == "delete_cancel")
    
    # Release artist select
    dp.callback_query.register(select_artist_for_release, F.data.startswith("selectartist_"))
    
    # Mocks
    dp.callback_query.register(admin_create_mocks, F.data == "admin_create_mocks")
    dp.callback_query.register(admin_delete_mocks, F.data == "admin_delete_mocks")
    
    # ═════════════════════════════════════════════════════════════════ STATES ═════════════════════════════════════════════════════════════════
    
    dp.message.register(reject_reason, RejectForm.reason)
    dp.message.register(reject_release_reason, RejectReleaseForm.reason)
    dp.message.register(admin_idea_reply_message, IdeaReplyForm.message)
    dp.message.register(admin_edit_value, EditArtistForm.value)
    dp.message.register(admin_edit_company_text, EditArtistForm.value, StateFilter(EditArtistForm.value))
    dp.message.register(admin_add_company_name, EditArtistForm.value)
    
    # ═════════════════════════════════════════════════════════════════ START ═════════════════════════════════════════════════════════════════
    
    logger.info("Бот запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}\n{traceback.format_exc()}")

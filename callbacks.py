"""Обработчики callback queries (кнопки)"""
import asyncio
from aiogram import types
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import (
    get_all_bot_users, approve_application, reject_application, approve_release, reject_release,
    get_application_by_id, get_release_by_id, get_artist_by_id, get_all_artists, delete_artist,
    get_open_ideas, get_idea_by_id, get_idea_messages, add_idea_message, close_idea, update_artist_field, add_reaction,
    get_all_companies, get_company_by_name, add_company as db_add_company
)
from keyboards import admin_menu, company_buttons
from utils import is_admin, format_artist, esc
from states import RejectForm, RejectReleaseForm, IdeaReplyForm, EditArtistForm

# ══════════════════════════════════════════════════════════════ REACTIONS ══════════════════════════════════════════════════════════════

async def add_reaction_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    artist_id = int(parts[1])
    reaction = parts[2]
    add_reaction(artist_id, callback_query.from_user.id, reaction)
    emoji_map = {"like": "👍", "neutral": "🤷‍♂️"}
    await callback_query.answer(f"✅ Твоя оценка: {emoji_map[reaction]}")

# ══════════════════════════════════════════════════════════════ ADMIN: APPLICATIONS ══════════════════════════════════════════════════════════════

async def admin_app_detail(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    app_id = int(callback_query.data.split("_")[1])
    app = get_application_by_id(app_id)
    if not app:
        await callback_query.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    msg = f"<b>Заявка #{app[0]}</b>\n\n🎵 <b>{esc(app[3])}</b>\n📝 {esc(app[4])}\n🎵 {app[6]}\n🔗 {esc(app[5])}"
    if app[7]:
        msg += f"\n📌 {esc(app[7])}"
    msg += f"\n🏢 Компания: {esc(app[10])}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{app_id}"), 
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{app_id}")]
    ])
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def approve_app_callback(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    app_id = int(callback_query.data.split("_")[1])
    success, user_id = approve_application(app_id)
    
    if success:
        await callback_query.answer("✅ Одобрено!")
        await callback_query.message.edit_text(callback_query.message.text + "\n\n✅ <b>ОДОБРЕНО И ДОБАВЛЕНО В КАТАЛОГ</b>", parse_mode="HTML")
        if user_id:
            try:
                await callback_query.bot.send_message(user_id, f"✅ <b>Твоя заявка #{app_id} одобрена!</b>\n\nТеперь ты в каталоге it1-records 🎉\n\nМожешь анонсировать свои релизы через «📀 Анонсировать релиз»", parse_mode="HTML")
            except: pass
    else:
        await callback_query.answer("❌ Ошибка (возможно, дубль имени)", show_alert=True)

async def reject_app_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    app_id = int(callback_query.data.split("_")[1])
    await state.update_data(app_id=app_id)
    await state.set_state(RejectForm.reason)
    await callback_query.answer()
    await callback_query.message.edit_text("❌ <b>Причина отклонения:</b>\n\nНапиши причину, которую увидит пользователь:", parse_mode="HTML")

async def reject_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    app_id = data['app_id']
    reason = message.text
    await state.clear()
    
    user_id = reject_application(app_id, reason)
    await message.answer(f"✅ Заявка #{app_id} отклонена с причиной:\n\n{reason}", reply_markup=admin_menu())
    
    if user_id:
        try:
            await message.bot.send_message(user_id, f"❌ <b>Твоя заявка #{app_id} отклонена</b>\n\n<b>Причина:</b>\n{reason}\n\nТы можешь подать новую заявку.", parse_mode="HTML")
        except: pass

# ══════════════════════════════════════════════════════════════ ADMIN: RELEASES ══════════════════════════════════════════════════════════════

async def admin_release_detail(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    release_id = int(callback_query.data.split("_")[1])
    release = get_release_by_id(release_id)
    if not release:
        await callback_query.answer("❌ Релиз не найден", show_alert=True)
        return
    
    rid, aid, artist_name, rel_name, desc, genre, links, status = release
    msg = f"<b>Заявка на релиз #{rid}</b>\n\n🎵 Артист: <b>{esc(artist_name)}</b>\n🎶 Релиз: <b>{esc(rel_name)}</b>\n🎵 {genre}\n🔗 {esc(links)}"
    if desc:
        msg += f"\n📝 {esc(desc)}"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_rel_{rid}"), 
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_rel_{rid}")
    ]])
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def approve_release_callback(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    release_id = int(callback_query.data.split("_")[2])
    artist_id, author_id = approve_release(release_id)
    
    if not artist_id:
        await callback_query.answer("❌ Ошибка", show_alert=True)
        return
    
    await callback_query.answer("✅ Одобрено и разослано!")
    await callback_query.message.edit_text(callback_query.message.text + "\n\n✅ <b>ОДОБРЕНО И РАЗОСЛАНО ВСЕМ</b>", parse_mode="HTML")
    
    if author_id:
        try:
            await callback_query.bot.send_message(author_id, f"✅ <b>Твой релиз одобрен и разослан всем участникам бота!</b>\n\n🎉 Спасибо за новую музыку!", parse_mode="HTML")
        except: pass

async def reject_release_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    release_id = int(callback_query.data.split("_")[2])
    await state.update_data(release_id=release_id)
    await state.set_state(RejectReleaseForm.reason)
    await callback_query.answer()
    await callback_query.message.edit_text("❌ <b>Причина отклонения:</b>", parse_mode="HTML")

async def reject_release_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    release_id = data['release_id']
    reason = message.text
    await state.clear()
    
    user_id = reject_release(release_id, reason)
    await message.answer(f"✅ Релиз #{release_id} отклонен", reply_markup=admin_menu())
    
    if user_id:
        try:
            await message.bot.send_message(user_id, f"❌ <b>Твой релиз отклонен</b>\n\n<b>Причина:</b>\n{reason}", parse_mode="HTML")
        except: pass

# ══════════════════════════════════════════════════════════════ ADMIN: IDEAS ══════════════════════════════════════════════════════════════

async def admin_idea_detail(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    idea_id = int(callback_query.data.split("_")[2])
    idea = get_idea_by_id(idea_id)
    if not idea:
        await callback_query.answer("❌ Идея не найдена", show_alert=True)
        return
    
    iid, user_id, username, text, created, status = idea
    msg = f"💡 <b>Идея #{iid}</b> от {username}\n\n{esc(text)}"
    
    messages = get_idea_messages(idea_id)
    if messages:
        msg += "\n\n<b>Ответы:</b>\n"
        for from_user, msg_text, created_at in messages:
            msg += f"• {esc(msg_text)}\n"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"idea_reply_{idea_id}")],
        [InlineKeyboardButton(text="✅ Закрыть", callback_data=f"idea_close_{idea_id}")]
    ])
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def admin_idea_reply(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    idea_id = int(callback_query.data.split("_")[2])
    await state.update_data(idea_id=idea_id)
    await state.set_state(IdeaReplyForm.message)
    await callback_query.answer()
    await callback_query.message.edit_text("Напиши ответ:")

async def admin_idea_reply_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idea_id = data['idea_id']
    await state.clear()
    
    add_idea_message(idea_id, message.from_user.id, message.text)
    await message.answer("✅ Ответ добавлен!", reply_markup=admin_menu())

async def admin_idea_close(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    idea_id = int(callback_query.data.split("_")[2])
    close_idea(idea_id)
    await callback_query.answer("✅ Идея закрыта")
    await callback_query.message.edit_text(callback_query.message.text + "\n\n✅ <b>ЗАКРЫТО</b>", parse_mode="HTML")

# ══════════════════════════════════════════════════════════════ ADMIN: EDIT ARTIST ══════════════════════════════════════════════════════════════

async def admin_edit_select(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Кнопка может быть от списка артистов для редактирования
    artist_id = int(callback_query.data.split("_")[1])
    artist = get_artist_by_id(artist_id)
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    await state.update_data(artist_id=artist_id)
    await state.set_state(EditArtistForm.field)
    
    msg = f"<b>Редактирование артиста #{artist_id}</b>\n\n{format_artist(artist, show_id=True)}\n\nЧто редактировать?"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Описание", callback_data="edit_description")],
        [InlineKeyboardButton(text="🎵 Жанр", callback_data="edit_genre")],
        [InlineKeyboardButton(text="🏢 Компания", callback_data="edit_company")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="edit_cancel")]
    ])
    
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def admin_edit_field(callback_query: types.CallbackQuery, state: FSMContext):
    field_type = callback_query.data.split("_")[1]
    
    if field_type == "description":
        await state.set_state(EditArtistForm.value)
        await state.update_data(field="description")
        await callback_query.answer()
        await callback_query.message.edit_text("Напиши новое описание:")
    
    elif field_type == "genre":
        from keyboards import genre_buttons
        await state.set_state(EditArtistForm.value)
        await state.update_data(field="genre")
        await callback_query.answer()
        await callback_query.message.edit_text("🎵 Выбери жанр:", reply_markup=genre_buttons())
    
    elif field_type == "company":
        await state.set_state(EditArtistForm.value)
        await state.update_data(field="company_id")
        await callback_query.answer()
        await callback_query.message.edit_text("🏢 Выбери компанию:", reply_markup=company_buttons())
    
    elif field_type == "cancel":
        await state.clear()
        await callback_query.answer()
        await callback_query.message.edit_text("Отмена", reply_markup=admin_menu())

async def admin_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    artist_id = data.get('artist_id')
    field = data.get('field')
    
    if not artist_id or not field:
        await state.clear()
        await message.answer("❌ Ошибка", reply_markup=admin_menu())
        return
    
    success = update_artist_field(artist_id, field, message.text)
    
    if success:
        artist = get_artist_by_id(artist_id)
        await state.clear()
        await message.answer(f"✅ Поле обновлено!\n\n{format_artist(artist, show_id=True)}", parse_mode="HTML", reply_markup=admin_menu())
    else:
        await message.answer("❌ Ошибка при обновлении", reply_markup=admin_menu())

async def admin_edit_genre_callback(callback_query: types.CallbackQuery, state: FSMContext):
    genre_code = callback_query.data.split("_")[1]
    data = await state.get_data()
    artist_id = data.get('artist_id')
    
    success = update_artist_field(artist_id, 'genre', genre_code)
    
    if success:
        artist = get_artist_by_id(artist_id)
        await state.clear()
        await callback_query.answer("✅ Жанр обновлен!")
        await callback_query.message.edit_text(f"✅ Поле обновлено!\n\n{format_artist(artist, show_id=True)}", parse_mode="HTML")
    else:
        await callback_query.answer("❌ Ошибка", show_alert=True)

async def admin_edit_company_callback(callback_query: types.CallbackQuery, state: FSMContext):
    company_code = callback_query.data.split("_")[1]
    data = await state.get_data()
    artist_id = data.get('artist_id')
    
    if company_code == "custom":
        await state.set_state(EditArtistForm.value)
        await callback_query.answer()
        await callback_query.message.edit_text("✍️ Напиши название компании:")
        return
    
    company_id = int(company_code)
    success = update_artist_field(artist_id, 'company_id', company_id)
    
    if success:
        artist = get_artist_by_id(artist_id)
        await state.clear()
        await callback_query.answer("✅ Компания обновлена!")
        await callback_query.message.edit_text(f"✅ Поле обновлено!\n\n{format_artist(artist, show_id=True)}", parse_mode="HTML")
    else:
        await callback_query.answer("❌ Ошибка", show_alert=True)

async def admin_edit_company_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    artist_id = data.get('artist_id')
    company_name = message.text
    
    company = get_company_by_name(company_name)
    if company:
        company_id = company[0]
    else:
        company_id = db_add_company(company_name)
    
    success = update_artist_field(artist_id, 'company_id', company_id)
    
    if success:
        artist = get_artist_by_id(artist_id)
        await state.clear()
        await message.answer(f"✅ Компания обновлена!\n\n{format_artist(artist, show_id=True)}", parse_mode="HTML", reply_markup=admin_menu())
    else:
        await message.answer("❌ Ошибка", reply_markup=admin_menu())

async def admin_edit_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer()
    await callback_query.message.edit_text("Отмена", reply_markup=admin_menu())

# ══════════════════════════════════════════════════════════════ ADMIN: DELETE ══════════════════════════════════════════════════════════════

async def admin_delete_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    artist_id = int(callback_query.data.split("_")[1])
    artist = get_artist_by_id(artist_id)
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    await state.update_data(artist_id=artist_id)
    msg = f"⚠️ <b>Удалить артиста?</b>\n\n{format_artist(artist, show_id=True)}\n\n⚠️ <b>Это удалит артиста, все релизы и реакции!</b>"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_exec_{artist_id}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="delete_cancel")]
    ])
    
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def admin_delete_exec(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    artist_id = int(callback_query.data.split("_")[2])
    success = delete_artist(artist_id)
    
    if success:
        await state.clear()
        await callback_query.answer("✅ Удалено!")
        await callback_query.message.edit_text("✅ <b>Артист удален</b>", parse_mode="HTML")
    else:
        await callback_query.answer("❌ Ошибка при удалении", show_alert=True)

async def admin_delete_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer()
    await callback_query.message.edit_text("Отмена", reply_markup=admin_menu())

# ══════════════════════════════════════════════════════════════ ADMIN: COMPANY ══════════════════════════════════════════════════════════════

async def admin_add_company_start(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await state.set_state(EditArtistForm.value)
    await state.update_data(field="new_company")
    await callback_query.answer()
    await callback_query.message.edit_text("✍️ Напиши название новой компании:")

async def admin_add_company_name(message: types.Message, state: FSMContext):
    company_name = message.text.strip()
    
    company = get_company_by_name(company_name)
    if company:
        await message.answer("❌ Такая компания уже существует!", reply_markup=admin_menu())
        return
    
    company_id = db_add_company(company_name)
    
    if company_id:
        await state.clear()
        await message.answer(f"✅ Компания '{company_name}' добавлена!", reply_markup=admin_menu())
    else:
        await message.answer("❌ Ошибка при добавлении компании", reply_markup=admin_menu())

# ══════════════════════════════════════════════════════════════ ADMIN: MOCKS ══════════════════════════════════════════════════════════════

async def admin_create_mocks(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    from mocks import create_mock_artists
    added = create_mock_artists()
    await callback_query.answer(f"✅ Добавлено {added} тестовых артистов")
    await callback_query.message.edit_text(f"✅ <b>Добавлено {added} тестовых артистов</b>\n\nТеперь можно тестировать бот!", parse_mode="HTML", reply_markup=admin_menu())

async def admin_delete_mocks(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    from mocks import delete_mock_artists
    deleted = delete_mock_artists()
    await callback_query.answer(f"✅ Удалено {deleted} тестовых артистов")
    await callback_query.message.edit_text(f"✅ <b>Удалено {deleted} тестовых артистов</b>", parse_mode="HTML", reply_markup=admin_menu())

# ══════════════════════════════════════════════════════════════ RELEASES: SELECT ARTIST ══════════════════════════════════════════════════════════════

async def select_artist_for_release(callback_query: types.CallbackQuery, state: FSMContext):
    artist_id = int(callback_query.data.split("_")[1])
    artist = get_artist_by_id(artist_id)
    
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    from states import AddReleaseForm
    await state.update_data(artist_id=artist_id, artist_name=artist[1])
    await state.set_state(AddReleaseForm.release_name)
    await callback_query.answer()
    await callback_query.message.edit_text(f"🎵 <b>{esc(artist[1])}</b>\n\nНазвание релиза?", parse_mode="HTML")

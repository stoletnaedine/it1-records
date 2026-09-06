"""Обработчики callback queries (кнопки)"""
import asyncio
from aiogram import types
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import (
    get_all_bot_users, approve_application, reject_application, approve_release, reject_release,
    get_application_by_id, get_release_by_id, get_artist_by_id, get_all_artists, delete_artist,
    get_open_ideas, get_idea_by_id, get_idea_messages, add_idea_message, close_idea, update_artist_field, add_reaction
)
from keyboards import admin_menu
from utils import is_admin, format_artist, esc
from states import RejectForm, RejectReleaseForm, IdeaReplyForm, EditArtistForm

# ══════════ REACTIONS ══════════

async def add_reaction_callback(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    artist_id = int(parts[1])
    reaction = parts[2]
    add_reaction(artist_id, callback_query.from_user.id, reaction)
    emoji_map = {"like": "👍", "neutral": "🤷‍♂️"}
    await callback_query.answer(f"✅ Твоя оценка: {emoji_map[reaction]}")

# ══════════ ADMIN: APPLICATIONS ══════════

async def admin_app_detail(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    app_id = int(callback_query.data.split("_")[1])
    app = get_application_by_id(app_id)
    if not app:
        await callback_query.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    msg = f"<b>Заявка #{app[0]}</b>\n\n🎵 <b>{esc(app[3])}</b>\n📝 {esc(app[4])}\n🎼 Жанр: {app[6]}\n🔗 Ссылки: {esc(app[5])}"
    if app[7]:
        msg += f"\n📌 {esc(app[7])}"
    
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

# ══════════ ADMIN: RELEASES ══════════

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
    msg = f"<b>Заявка на релиз #{rid}</b>\n\n🎵 Артист: <b>{esc(artist_name)}</b>\n🎶 Релиз: <b>{esc(rel_name)}</b>\n🎼 Жанр: {genre}\n🔗 Ссылки: {esc(links)}"
    if desc:
        msg += f"\n📝 Описание: {esc(desc)}"
    
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
    
    release = get_release_by_id(release_id)
    artist = get_artist_by_id(artist_id)
    
    if author_id:
        try:
            await callback_query.bot.send_message(author_id, f"✅ <b>Твой релиз одобрен и разослан всем участникам бота!</b>\n\n📀 {esc(release[3])}", parse_mode="HTML")
        except: pass
    
    all_users = get_all_bot_users()
    msg = f"📀 <b>Новый релиз!</b>\n\n🎵 Артист: <b>{esc(artist[1])}</b>\n🎶 Релиз: <b>{esc(release[3])}</b>\n🎼 Жанр: {release[5]}\n\n"
    if release[4]:
        msg += f"📝 {esc(release[4])}\n\n"
    msg += f"🔗 Слушать:\n{esc(release[6])}"
    
    for user_id in all_users:
        if user_id == author_id:
            continue
        try:
            await callback_query.bot.send_message(user_id, msg, parse_mode="HTML")
            await asyncio.sleep(0.05)
        except: pass

async def reject_release_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    release_id = int(callback_query.data.split("_")[2])
    await state.update_data(release_id=release_id)
    await state.set_state(RejectReleaseForm.reason)
    await callback_query.answer()
    await callback_query.message.edit_text("❌ <b>Причина отклонения релиза:</b>\n\nНапиши причину, которую увидит автор:", parse_mode="HTML")

async def reject_release_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    release_id = data['release_id']
    reason = message.text
    await state.clear()
    
    user_id = reject_release(release_id, reason)
    await message.answer(f"✅ Релиз #{release_id} отклонён с причиной:\n\n{reason}", reply_markup=admin_menu())
    
    if user_id:
        try:
            await message.bot.send_message(user_id, f"❌ <b>Твоя заявка на релиз #{release_id} отклонена</b>\n\n<b>Причина:</b>\n{reason}", parse_mode="HTML")
        except: pass

# ══════════ ADMIN: IDEAS ══════════

async def admin_idea_detail(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    idea_id = int(callback_query.data.split("_")[2])
    idea = get_idea_by_id(idea_id)
    if not idea:
        await callback_query.answer("❌ Идея не найдена", show_alert=True)
        return
    
    messages = get_idea_messages(idea_id)
    msg = f"💡 <b>Идея #{idea[0]}</b>\n\nОт: {esc(idea[2])}\nСтатус: {idea[4]}\n\n<b>История переписки:</b>\n\n"
    for from_uid, mtext, created in messages:
        sender = "Админ" if from_uid in ADMIN_IDS else idea[2]
        msg += f"<b>{sender}:</b> {esc(mtext)}\n\n"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"idea_reply_{idea_id}")],
        [InlineKeyboardButton(text="✅ Закрыть идею", callback_data=f"idea_close_{idea_id}")]
    ])
    await callback_query.message.edit_text(msg[:4000], reply_markup=kb, parse_mode="HTML")

async def admin_idea_reply(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    idea_id = int(callback_query.data.split("_")[2])
    await state.update_data(idea_id=idea_id)
    await state.set_state(IdeaReplyForm.message)
    await callback_query.answer()
    await callback_query.message.edit_text(f"💬 Ответ на идею #{idea_id}\n\nНапиши сообщение пользователю:")

async def admin_idea_reply_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    idea_id = data['idea_id']
    await state.clear()
    
    idea = get_idea_by_id(idea_id)
    if not idea:
        await message.answer("❌ Идея не найдена", reply_markup=admin_menu())
        return
    
    add_idea_message(idea_id, message.from_user.id, message.text)
    await message.answer(f"✅ Ответ отправлен пользователю!", reply_markup=admin_menu())
    
    try:
        await message.bot.send_message(idea[1], f"💡 <b>Ответ на твою идею #{idea_id}</b>\n\n{esc(message.text)}", parse_mode="HTML")
    except: pass

async def admin_idea_close(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    idea_id = int(callback_query.data.split("_")[2])
    close_idea(idea_id)
    await callback_query.answer("✅ Идея закрыта!")
    await callback_query.message.edit_text(f"✅ Идея #{idea_id} закрыта")

# ══════════ ADMIN: EDIT ARTIST ══════════

async def admin_edit_select(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    artist_id = int(callback_query.data.split("_")[1])
    artist = get_artist_by_id(artist_id)
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    msg = format_artist(artist, show_id=True) + "\n\n<b>Что редактировать?</b>"
    
    field_names = {
        'project_name': '📝 Название',
        'description': '📝 Описание',
        'links': '🔗 Ссылки',
        'genre': '🎼 Жанр',
        'about': '📌 О себе'
    }
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=field_names[f], callback_data=f"editfield_{artist_id}_{f}") for f in ['project_name', 'description']],
        [InlineKeyboardButton(text=field_names[f], callback_data=f"editfield_{artist_id}_{f}") for f in ['links', 'genre']],
        [InlineKeyboardButton(text=field_names['about'], callback_data=f"editfield_{artist_id}_about")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="edit_cancel")]
    ])
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def admin_edit_field(callback_query: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    parts = callback_query.data.split("_")
    artist_id = int(parts[1])
    field = parts[2]
    
    await state.update_data(artist_id=artist_id, field=field)
    await state.set_state(EditArtistForm.value)
    
    field_names = {
        'project_name': 'Название проекта',
        'description': 'Описание',
        'links': 'Ссылки',
        'genre': 'Жанр',
        'about': 'О себе'
    }
    
    await callback_query.answer()
    if field == 'genre':
        from keyboards import genre_buttons
        await callback_query.message.edit_text(f"Выбери новый жанр:", reply_markup=genre_buttons())
    else:
        await callback_query.message.edit_text(f"<b>{field_names[field]}</b>\n\nВведи новое значение:", parse_mode="HTML")

async def admin_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    artist_id = data['artist_id']
    field = data['field']
    value = message.text if field != 'links' else message.text.replace('\n', ', ').strip()
    await state.clear()
    
    if update_artist_field(artist_id, field, value):
        await message.answer(f"✅ Поле <b>{field}</b> обновлено!", reply_markup=admin_menu(), parse_mode="HTML")
    else:
        await message.answer("❌ Ошибка обновления", reply_markup=admin_menu())

async def admin_edit_genre_callback(callback_query: types.CallbackQuery, state: FSMContext):
    genre_code = callback_query.data.split("_")[1]
    data = await state.get_data()
    artist_id = data['artist_id']
    await state.clear()
    
    if update_artist_field(artist_id, 'genre', genre_code):
        await callback_query.answer("✅ Жанр обновлен!")
        await callback_query.message.edit_text(f"✅ Жанр обновлен на: {genre_code}")
    else:
        await callback_query.answer("❌ Ошибка", show_alert=True)

async def admin_edit_cancel(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("❌ Редактирование отменено")

# ══════════ ADMIN: DELETE ARTIST ══════════

async def admin_delete_confirm(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    artist_id = int(callback_query.data.split("_")[1])
    artist = get_artist_by_id(artist_id)
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    msg = format_artist(artist, show_id=True) + "\n\n⚠️ <b>Вы уверены? Это действие необратимо!</b>"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ УДАЛИТЬ", callback_data=f"del_exec_{artist_id}"), 
         InlineKeyboardButton(text="❌ Отмена", callback_data=f"del_cancel")]
    ])
    await callback_query.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")

async def admin_delete_exec(callback_query: types.CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    artist_id = int(callback_query.data.split("_")[2])
    
    # Получаем данные артиста ПЕРЕД удалением
    artist = get_artist_by_id(artist_id)
    if not artist:
        await callback_query.answer("❌ Артист не найден", show_alert=True)
        return
    
    artist_name = artist[1]  # project_name
    author_id = artist[7]     # tg_user_id
    
    # Удаляем артиста
    delete_artist(artist_id)
    
    await callback_query.answer("✅ Удалено!")
    await callback_query.message.edit_text("✅ <b>Артист удален из каталога</b>", parse_mode="HTML")
    
    # Отправляем уведомление автору
    if author_id:
        try:
            await callback_query.bot.send_message(
                author_id,
                f"❌ <b>Твой артист удален из каталога</b>\n\n"
                f"📀 <b>{esc(artist_name)}</b> был удален админом из it1-records.\n\n"
                f"Если у тебя есть вопросы, напиши админу.",
                parse_mode="HTML"
            )
        except:
            pass

async def admin_delete_cancel(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("❌ Удаление отменено")

# ══════════ ADMIN: MOCKS ══════════

async def admin_create_mocks(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from mocks import create_mock_artists
        count = create_mock_artists()
        await message.answer(f"✅ <b>Создано {count} тестовых артистов!</b>\n\nТеперь ты можешь тестировать бот.", reply_markup=admin_menu(), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании моков: {str(e)}", reply_markup=admin_menu())

async def admin_delete_mocks(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        from mocks import delete_mock_artists
        count = delete_mock_artists()
        if count == 0:
            await message.answer("✅ Нет моков для удаления", reply_markup=admin_menu())
        else:
            await message.answer(f"✅ <b>Удалено {count} тестовых артистов</b>\n\nКаталог очищен!", reply_markup=admin_menu(), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка при удалении моков: {str(e)}", reply_markup=admin_menu())

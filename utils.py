"""Утилиты"""
from config import ADMIN_IDS, GENRE_MAP, RECENT_RELEASES_LIMIT
from database import get_reactions_stats, get_artist_releases
import html

def is_admin(user_id):
    return user_id in ADMIN_IDS

def esc(text):
    return html.escape(str(text)) if text else ""

def normalize_links(text):
    """Нормализовать ссылки: заменить переносы строк на запятые"""
    return text.replace('\n', ', ').strip()

def format_artist(data, show_id=False):
    """Форматирование профиля артиста"""
    aid, project_name, description, links, genre, about = data[:6]
    card = f"🎵 <b>{project_name}</b>"
    if show_id: 
        card += f" <code>#{aid}</code>"
    card += f"\n📝 {esc(description)}\n🎼 {genre}"
    if about:
        card += f"\n📌 {esc(about)}"
    card += "\n\n"
    for link in links.split(","):
        if link.strip():
            card += f"🔗 {esc(link.strip())}\n"
    return card.strip()

def format_artist_with_reactions(artist_id, data):
    """Форматирование артиста с реакциями и релизами"""
    aid, project_name, description, links, genre, about = data[:6]
    card = f"🎵 <b>{project_name}</b> <code>#{aid}</code>\n"
    card += f"📝 {esc(description)}\n🎼 {genre}"
    if about:
        card += f"\n📌 {esc(about)}"
    card += "\n\n"
    
    for link in links.split(","):
        if link.strip():
            card += f"🔗 {esc(link.strip())}\n"
    
    # Статистика реакций
    stats = get_reactions_stats(artist_id)
    if stats:
        card += "\n<b>Реакции:</b>\n"
        card += f"👍 {stats.get('like', 0)} "
        card += f"🤷‍♂️ {stats.get('neutral', 0)}"
    
    # Последний релиз (максимум 1)
    releases = get_artist_releases(artist_id, limit=RECENT_RELEASES_LIMIT)
    if releases:
        card += "\n\n<b>📀 Последний релиз:</b>\n"
        rel = releases[0]
        rel_id, rel_name, rel_desc, rel_genre, rel_links, rel_date = rel
        card += f"🎶 <b>{esc(rel_name)}</b> ({rel_genre})\n"
        if rel_desc:
            card += f"   {esc(rel_desc)}\n"
        for link in rel_links.split(","):
            if link.strip():
                card += f"   🔗 {esc(link.strip())}\n"
    
    return card.strip()

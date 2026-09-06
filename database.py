"""Операции с БД (PostgreSQL)"""
import psycopg2
from psycopg2.extras import DictCursor
import os

# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/it1_records")

def get_connection():
    """Получить подключение к БД"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Инициализация БД"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        tg_user_id BIGINT,
        tg_username TEXT,
        project_name TEXT,
        description TEXT,
        links TEXT,
        genre TEXT,
        about TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        rejection_reason TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS artists (
        id SERIAL PRIMARY KEY,
        tg_user_id BIGINT,
        tg_username TEXT,
        project_name TEXT UNIQUE,
        description TEXT,
        links TEXT,
        genre TEXT,
        about TEXT,
        approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS reactions (
        id SERIAL PRIMARY KEY,
        artist_id INTEGER,
        user_id BIGINT,
        reaction TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(artist_id, user_id)
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS releases (
        id SERIAL PRIMARY KEY,
        artist_id INTEGER,
        tg_user_id BIGINT,
        project_name TEXT,
        release_name TEXT,
        description TEXT,
        genre TEXT,
        links TEXT,
        release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',
        rejection_reason TEXT,
        FOREIGN KEY(artist_id) REFERENCES artists(id)
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS bot_users (
        id SERIAL PRIMARY KEY,
        tg_user_id BIGINT UNIQUE,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS ideas (
        id SERIAL PRIMARY KEY,
        tg_user_id BIGINT,
        tg_username TEXT,
        idea_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'open'
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS idea_messages (
        id SERIAL PRIMARY KEY,
        idea_id INTEGER,
        from_user_id BIGINT,
        message_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(idea_id) REFERENCES ideas(id)
    )""")
    
    conn.commit()
    c.close()
    conn.close()

# ══════════════════ BOT USERS ══════════════════

def add_bot_user(tg_user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO bot_users (tg_user_id) VALUES (%s) ON CONFLICT DO NOTHING", (tg_user_id,))
    conn.commit()
    c.close()
    conn.close()

def get_all_bot_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT tg_user_id FROM bot_users")
    users = [row[0] for row in c.fetchall()]
    c.close()
    conn.close()
    return users

# ══════════════════ APPLICATIONS ══════════════════

def add_application(tg_user_id, tg_username, project_name, description, links, genre, about):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO applications (tg_user_id, tg_username, project_name, description, links, genre, about) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
              (tg_user_id, tg_username, project_name, description, links, genre, about))
    app_id = c.fetchone()[0]
    conn.commit()
    c.close()
    conn.close()
    return app_id

def get_pending_applications():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, tg_user_id, tg_username, project_name, description, links, genre, about FROM applications WHERE status = 'pending'")
    apps = c.fetchall()
    c.close()
    conn.close()
    return apps

def get_application_by_id(app_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, tg_user_id, tg_username, project_name, description, links, genre, about, status FROM applications WHERE id = %s", (app_id,))
    app = c.fetchone()
    c.close()
    conn.close()
    return app

def approve_application(app_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT tg_user_id, tg_username, project_name, description, links, genre, about FROM applications WHERE id = %s", (app_id,))
    row = c.fetchone()
    
    if row:
        try:
            c.execute("INSERT INTO artists (tg_user_id, tg_username, project_name, description, links, genre, about) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                      row)
            c.execute("UPDATE applications SET status = 'approved' WHERE id = %s", (app_id,))
            conn.commit()
            user_id = row[0]
            c.close()
            conn.close()
            return True, user_id
        except Exception:
            conn.rollback()
            c.close()
            conn.close()
            return False, None
    c.close()
    conn.close()
    return False, None

def reject_application(app_id, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT tg_user_id FROM applications WHERE id = %s", (app_id,))
    row = c.fetchone()
    
    if row:
        user_id = row[0]
        c.execute("UPDATE applications SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason, app_id))
        conn.commit()
        c.close()
        conn.close()
        return user_id
    c.close()
    conn.close()
    return None

# ══════════════════ ARTISTS ══════════════════

def get_artists_by_genre(genre):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, project_name, description, links, genre, about FROM artists WHERE genre = %s ORDER BY project_name", (genre,))
    artists = c.fetchall()
    c.close()
    conn.close()
    return artists

def get_random_artist():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, project_name, description, links, genre, about FROM artists ORDER BY RANDOM() LIMIT 1")
    artist = c.fetchone()
    c.close()
    conn.close()
    return artist

def get_all_artists():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, project_name, description, links, genre, about FROM artists ORDER BY project_name")
    artists = c.fetchall()
    c.close()
    conn.close()
    return artists

def get_artist_by_id(artist_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, project_name, description, links, genre, about, tg_username, tg_user_id FROM artists WHERE id = %s", (artist_id,))
    artist = c.fetchone()
    c.close()
    conn.close()
    return artist

def get_artist_by_user_id(tg_user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, project_name, description, links, genre, about, tg_username, tg_user_id FROM artists WHERE tg_user_id = %s", (tg_user_id,))
    artist = c.fetchone()
    c.close()
    conn.close()
    return artist

def create_artist(tg_user_id, tg_username, project_name, description, links, genre, about):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO artists (tg_user_id, tg_username, project_name, description, links, genre, about) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                  (tg_user_id, tg_username, project_name, description, links, genre, about))
        conn.commit()
        c.close()
        conn.close()
        return True
    except Exception:
        conn.rollback()
        c.close()
        conn.close()
        return False

def delete_artist(artist_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM artists WHERE id = %s", (artist_id,))
    conn.commit()
    c.close()
    conn.close()

def update_artist_field(artist_id, field, value):
    conn = get_connection()
    c = conn.cursor()
    if field in ['project_name', 'description', 'links', 'genre', 'about']:
        c.execute(f"UPDATE artists SET {field} = %s WHERE id = %s", (value, artist_id))
        conn.commit()
        c.close()
        conn.close()
        return True
    c.close()
    conn.close()
    return False

# ══════════════════ REACTIONS ══════════════════

def add_reaction(artist_id, user_id, reaction):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO reactions (artist_id, user_id, reaction) VALUES (%s, %s, %s) ON CONFLICT (artist_id, user_id) DO UPDATE SET reaction = %s",
              (artist_id, user_id, reaction, reaction))
    conn.commit()
    c.close()
    conn.close()

def get_reactions_stats(artist_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT reaction, COUNT(*) FROM reactions WHERE artist_id = %s GROUP BY reaction", (artist_id,))
    stats = dict(c.fetchall())
    c.close()
    conn.close()
    return stats if stats else {}

# ══════════════════ RELEASES ══════════════════

def add_release(artist_id, tg_user_id, release_name, description, genre, links):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO releases (artist_id, tg_user_id, release_name, description, genre, links) 
                 VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
              (artist_id, tg_user_id, release_name, description, genre, links))
    release_id = c.fetchone()[0]
    conn.commit()
    c.close()
    conn.close()
    return release_id

def get_pending_releases():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT r.id, r.artist_id, a.project_name, r.release_name, r.description, r.genre, r.links, r.tg_user_id
                 FROM releases r
                 JOIN artists a ON r.artist_id = a.id
                 WHERE r.status = 'pending'""")
    releases = c.fetchall()
    c.close()
    conn.close()
    return releases

def get_release_by_id(release_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, artist_id, project_name, release_name, description, genre, links, status FROM releases WHERE id = %s", (release_id,))
    release = c.fetchone()
    c.close()
    conn.close()
    return release

def approve_release(release_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT artist_id, tg_user_id FROM releases WHERE id = %s", (release_id,))
    row = c.fetchone()
    
    if row:
        c.execute("UPDATE releases SET status = 'approved' WHERE id = %s", (release_id,))
        conn.commit()
        c.close()
        conn.close()
        return row[0], row[1]
    c.close()
    conn.close()
    return None, None

def reject_release(release_id, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT tg_user_id FROM releases WHERE id = %s", (release_id,))
    row = c.fetchone()
    
    if row:
        user_id = row[0]
        c.execute("UPDATE releases SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason, release_id))
        conn.commit()
        c.close()
        conn.close()
        return user_id
    c.close()
    conn.close()
    return None

# ══════════════════ IDEAS ══════════════════

def add_idea(tg_user_id, tg_username, idea_text):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO ideas (tg_user_id, tg_username, idea_text) VALUES (%s, %s, %s) RETURNING id",
              (tg_user_id, tg_username, idea_text))
    idea_id = c.fetchone()[0]
    conn.commit()
    c.close()
    conn.close()
    return idea_id

def get_open_ideas():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, tg_username, idea_text, created_at FROM ideas WHERE status = 'open'")
    ideas = c.fetchall()
    c.close()
    conn.close()
    return ideas

def get_idea_by_id(idea_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, tg_user_id, tg_username, idea_text, status FROM ideas WHERE id = %s", (idea_id,))
    idea = c.fetchone()
    c.close()
    conn.close()
    return idea

def add_idea_message(idea_id, from_user_id, message_text):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO idea_messages (idea_id, from_user_id, message_text) VALUES (%s, %s, %s)",
              (idea_id, from_user_id, message_text))
    conn.commit()
    c.close()
    conn.close()

def get_idea_messages(idea_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT from_user_id, message_text, created_at FROM idea_messages WHERE idea_id = %s ORDER BY created_at", (idea_id,))
    messages = c.fetchall()
    c.close()
    conn.close()
    return messages

def close_idea(idea_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE ideas SET status = 'closed' WHERE id = %s", (idea_id,))
    conn.commit()
    c.close()
    conn.close()

def get_artist_releases(artist_id, limit=None):
    """Получить релизы артиста"""
    conn = get_connection()
    c = conn.cursor()
    if limit:
        c.execute("SELECT id, release_name, description, genre, links, created_at FROM releases WHERE artist_id = %s AND status = 'approved' ORDER BY created_at DESC LIMIT %s", (artist_id, limit))
    else:
        c.execute("SELECT id, release_name, description, genre, links, created_at FROM releases WHERE artist_id = %s AND status = 'approved' ORDER BY created_at DESC", (artist_id,))
    releases = c.fetchall()
    c.close()
    conn.close()
    return releases
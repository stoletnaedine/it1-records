"""Операции с БД"""
import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY, 
        tg_user_id INTEGER, tg_username TEXT,
        project_name TEXT, description TEXT, links TEXT, genre TEXT, about TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        status TEXT DEFAULT 'pending', rejection_reason TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY, 
        tg_user_id INTEGER, tg_username TEXT,
        project_name TEXT UNIQUE, description TEXT, links TEXT, genre TEXT, about TEXT,
        approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY,
        artist_id INTEGER, user_id INTEGER, reaction TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(artist_id, user_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS releases (
        id INTEGER PRIMARY KEY,
        artist_id INTEGER, tg_user_id INTEGER,
        release_name TEXT, description TEXT, genre TEXT, links TEXT,
        release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending', rejection_reason TEXT,
        FOREIGN KEY(artist_id) REFERENCES artists(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS bot_users (
        id INTEGER PRIMARY KEY,
        tg_user_id INTEGER UNIQUE,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ideas (
        id INTEGER PRIMARY KEY,
        tg_user_id INTEGER, tg_username TEXT, idea_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'open'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS idea_messages (
        id INTEGER PRIMARY KEY,
        idea_id INTEGER, from_user_id INTEGER, message_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(idea_id) REFERENCES ideas(id)
    )""")
    conn.commit()
    conn.close()

# ══════════ BOT USERS ══════════

def add_bot_user(tg_user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("INSERT OR IGNORE INTO bot_users (tg_user_id) VALUES (?)", (tg_user_id,))
    conn.commit()
    conn.close()

def get_all_bot_users():
    conn = sqlite3.connect(DB_PATH)
    users = conn.cursor().execute("SELECT tg_user_id FROM bot_users").fetchall()
    conn.close()
    return [u[0] for u in users]

# ══════════ APPLICATIONS ══════════

def add_application(tg_user_id, tg_username, project_name, description, links, genre, about):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO applications (tg_user_id, tg_username, project_name, description, links, genre, about) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (tg_user_id, tg_username, project_name, description, links, genre, about))
    app_id = c.lastrowid
    conn.commit()
    conn.close()
    return app_id

def get_pending_applications():
    conn = sqlite3.connect(DB_PATH)
    apps = conn.cursor().execute("SELECT id, tg_user_id, tg_username, project_name, description, links, genre, about FROM applications WHERE status = 'pending'").fetchall()
    conn.close()
    return apps

def get_application_by_id(app_id):
    conn = sqlite3.connect(DB_PATH)
    app = conn.cursor().execute("SELECT id, tg_user_id, tg_username, project_name, description, links, genre, about, status FROM applications WHERE id = ?", (app_id,)).fetchone()
    conn.close()
    return app

def approve_application(app_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT tg_user_id, tg_username, project_name, description, links, genre, about FROM applications WHERE id = ?", (app_id,))
    row = c.fetchone()
    if row:
        try:
            c.execute("INSERT INTO artists (tg_user_id, tg_username, project_name, description, links, genre, about) VALUES (?, ?, ?, ?, ?, ?, ?)", row)
            c.execute("UPDATE applications SET status = 'approved' WHERE id = ?", (app_id,))
            conn.commit()
            user_id = row[0]
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, None
    conn.close()
    return False, None

def reject_application(app_id, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT tg_user_id FROM applications WHERE id = ?", (app_id,))
    row = c.fetchone()
    if row:
        user_id = row[0]
        c.execute("UPDATE applications SET status = 'rejected', rejection_reason = ? WHERE id = ?", (reason, app_id))
        conn.commit()
        conn.close()
        return user_id
    conn.close()
    return None

# ══════════ ARTISTS ══════════

def get_artists_by_genre(genre):
    conn = sqlite3.connect(DB_PATH)
    artists = conn.cursor().execute("SELECT id, project_name, description, links, genre, about FROM artists WHERE genre = ? ORDER BY project_name", (genre,)).fetchall()
    conn.close()
    return artists

def get_random_artist():
    conn = sqlite3.connect(DB_PATH)
    artist = conn.cursor().execute("SELECT id, project_name, description, links, genre, about FROM artists ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    return artist

def get_all_artists():
    conn = sqlite3.connect(DB_PATH)
    artists = conn.cursor().execute("SELECT id, project_name, description, links, genre, about FROM artists ORDER BY project_name").fetchall()
    conn.close()
    return artists

def get_artist_by_id(artist_id):
    conn = sqlite3.connect(DB_PATH)
    artist = conn.cursor().execute("SELECT id, project_name, description, links, genre, about, tg_username, tg_user_id FROM artists WHERE id = ?", (artist_id,)).fetchone()
    conn.close()
    return artist

def get_artist_by_user_id(tg_user_id):
    conn = sqlite3.connect(DB_PATH)
    artist = conn.cursor().execute("SELECT id, project_name, description, links, genre, about, tg_username, tg_user_id FROM artists WHERE tg_user_id = ?", (tg_user_id,)).fetchone()
    conn.close()
    return artist

def create_artist(tg_user_id, tg_username, project_name, description, links, genre, about):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO artists (tg_user_id, tg_username, project_name, description, links, genre, about) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tg_user_id, tg_username, project_name, description, links, genre, about))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_artist(artist_id):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("DELETE FROM artists WHERE id = ?", (artist_id,))
    conn.commit()
    conn.close()

def update_artist_field(artist_id, field, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if field in ['project_name', 'description', 'links', 'genre', 'about']:
        c.execute(f"UPDATE artists SET {field} = ? WHERE id = ?", (value, artist_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# ══════════ REACTIONS ══════════

def add_reaction(artist_id, user_id, reaction):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("INSERT OR REPLACE INTO reactions (artist_id, user_id, reaction) VALUES (?, ?, ?)", (artist_id, user_id, reaction))
    conn.commit()
    conn.close()

def get_reactions_stats(artist_id):
    conn = sqlite3.connect(DB_PATH)
    stats = conn.cursor().execute("SELECT reaction, COUNT(*) FROM reactions WHERE artist_id = ? GROUP BY reaction", (artist_id,)).fetchall()
    conn.close()
    return dict(stats) if stats else {}

# ══════════ RELEASES ══════════

def add_release(artist_id, tg_user_id, release_name, description, genre, links):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO releases (artist_id, tg_user_id, release_name, description, genre, links) VALUES (?, ?, ?, ?, ?, ?)",
              (artist_id, tg_user_id, release_name, description, genre, links))
    release_id = c.lastrowid
    conn.commit()
    conn.close()
    return release_id

def get_pending_releases():
    conn = sqlite3.connect(DB_PATH)
    releases = conn.cursor().execute("""
        SELECT r.id, r.artist_id, a.project_name, r.release_name, r.description, r.genre, r.links, r.tg_user_id
        FROM releases r
        JOIN artists a ON r.artist_id = a.id
        WHERE r.status = 'pending'
    """).fetchall()
    conn.close()
    return releases

def approve_release(release_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT artist_id, tg_user_id FROM releases WHERE id = ?", (release_id,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE releases SET status = 'approved' WHERE id = ?", (release_id,))
        conn.commit()
        conn.close()
        return row[0], row[1]
    conn.close()
    return None, None

def reject_release(release_id, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT tg_user_id FROM releases WHERE id = ?", (release_id,))
    row = c.fetchone()
    if row:
        user_id = row[0]
        c.execute("UPDATE releases SET status = 'rejected', rejection_reason = ? WHERE id = ?", (reason, release_id))
        conn.commit()
        conn.close()
        return user_id
    conn.close()
    return None

def get_release_by_id(release_id):
    conn = sqlite3.connect(DB_PATH)
    release = conn.cursor().execute("""
        SELECT r.id, r.artist_id, a.project_name, r.release_name, r.description, r.genre, r.links, r.status
        FROM releases r
        JOIN artists a ON r.artist_id = a.id
        WHERE r.id = ?
    """, (release_id,)).fetchone()
    conn.close()
    return release

def get_artist_releases(artist_id, limit=1):
    conn = sqlite3.connect(DB_PATH)
    releases = conn.cursor().execute("""
        SELECT id, release_name, description, genre, links, release_date
        FROM releases
        WHERE artist_id = ? AND status = 'approved'
        ORDER BY release_date DESC
        LIMIT ?
    """, (artist_id, limit)).fetchall()
    conn.close()
    return releases

# ══════════ IDEAS ══════════

def add_idea(tg_user_id, tg_username, idea_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO ideas (tg_user_id, tg_username, idea_text) VALUES (?, ?, ?)", (tg_user_id, tg_username, idea_text))
    idea_id = c.lastrowid
    conn.commit()
    conn.close()
    return idea_id

def get_open_ideas():
    conn = sqlite3.connect(DB_PATH)
    ideas = conn.cursor().execute("SELECT id, tg_username, idea_text, created_at FROM ideas WHERE status = 'open' ORDER BY created_at DESC").fetchall()
    conn.close()
    return ideas

def get_idea_by_id(idea_id):
    conn = sqlite3.connect(DB_PATH)
    idea = conn.cursor().execute("SELECT id, tg_user_id, tg_username, idea_text, status FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    conn.close()
    return idea

def add_idea_message(idea_id, from_user_id, message_text):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("INSERT INTO idea_messages (idea_id, from_user_id, message_text) VALUES (?, ?, ?)", (idea_id, from_user_id, message_text))
    conn.commit()
    conn.close()

def get_idea_messages(idea_id):
    conn = sqlite3.connect(DB_PATH)
    messages = conn.cursor().execute("SELECT from_user_id, message_text, created_at FROM idea_messages WHERE idea_id = ? ORDER BY created_at", (idea_id,)).fetchall()
    conn.close()
    return messages

def close_idea(idea_id):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("UPDATE ideas SET status = 'closed' WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()

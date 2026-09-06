"""Функции для работы с мокаками (тестовые данные)"""
import psycopg2
from config import DATABASE_URL

MOCK_PREFIX = "MOCK_TEST_"

def get_connection():
    """Получить подключение к БД"""
    return psycopg2.connect(DATABASE_URL)

def create_mock_artists():
    """Создать 10 тестовых артистов"""
    mock_data = [
        ("Luna Echo", "Синтвейв и электроника", "https://soundcloud.com/luna-echo, https://spotify.com/luna-echo", "electronic", "Экспериментирую с синтезаторами и звуком"),
        ("Pixel Dreams", "Ретро-гейм музыка", "https://youtube.com/@pixeldreams, https://bandcamp.com/pixel-dreams", "pop", "Создаю музыку вдохновленную 8-бит играми"),
        ("Stone Ground", "Альтернативный рок", "https://instagram.com/stonegroundband, https://soundcloud.com/stoneground", "rock", "Четыре друга из офиса, которые любят громкий звук"),
        ("Neon Lights", "Синтпоп", "https://tiktok.com/@neonlights, https://spotify.com/neonlights", "pop", None),
        ("Desert Wind", "Инди-фолк", "https://youtube.com/@desertwind, https://bandcamp.com/desertwind", "indie", "Акустическая гитара и естественные звуки"),
        ("Cyber Nova", "Электронная музыка", "https://soundcloud.com/cybernova, https://beatport.com/cybernova", "electronic", None),
        ("Velvet Storm", "Альтернативный рок", "https://spotify.com/velvetstorm, https://youtube.com/@velvetstorm", "rock", "Энергичный рок из нашего офиса"),
        ("Golden Hour", "Инди-поп", "https://instagram.com/goldenhourmusic, https://tiktok.com/@goldenhour", "indie", "Музыка про жизнь, любовь и мечты"),
        ("Quantum Jump", "Электроника", "https://soundcloud.com/quantumjump, https://spotify.com/quantumjump", "electronic", "Экспериментальная электроника и бит-метейкинг"),
        ("Crimson Waves", "Альтернативный поп", "https://bandcamp.com/crimsonwaves, https://youtube.com/@crimsonwaves", "pop", "Авторская музыка с глубокими текстами"),
    ]
    
    conn = get_connection()
    c = conn.cursor()
    added = 0
    
    for i, (project_name, description, links, genre, about) in enumerate(mock_data):
        try:
            tg_username = f"{MOCK_PREFIX}{i+1}"
            tg_user_id = -1000 - i  # Отрицательные ID для моков
            c.execute(
                "INSERT INTO artists (tg_user_id, tg_username, project_name, description, links, genre, about) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (tg_user_id, tg_username, project_name, description, links, genre, about)
            )
            added += 1
        except psycopg2.IntegrityError:
            conn.rollback()
    
    conn.commit()
    c.close()
    conn.close()
    return added

def delete_mock_artists():
    """Удалить все тестовые артистов"""
    conn = get_connection()
    c = conn.cursor()
    
    # Найди все моки по префиксу
    c.execute("SELECT id FROM artists WHERE tg_username LIKE %s", (f"{MOCK_PREFIX}%",))
    mocks = c.fetchall()
    
    # Удали реакции на моков
    for (mock_id,) in mocks:
        c.execute("DELETE FROM reactions WHERE artist_id = %s", (mock_id,))
    
    # Удали моков
    c.execute("DELETE FROM artists WHERE tg_username LIKE %s", (f"{MOCK_PREFIX}%",))
    
    conn.commit()
    c.close()
    conn.close()
    return len(mocks)

def get_mock_count():
    """Получить количество текущих моков"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM artists WHERE tg_username LIKE %s", (f"{MOCK_PREFIX}%",))
    count = c.fetchone()[0]
    c.close()
    conn.close()
    return count
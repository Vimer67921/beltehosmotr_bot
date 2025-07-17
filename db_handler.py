import sqlite3
import os
import requests
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Создание папки database, если не существует
if not os.path.exists('database'):
    os.makedirs('database')

# Подключение к базе данных
DB_PATH = os.path.join('database', 'bookings.db')
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Проверка наличия столбца в таблице
def check_column_exists(table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    return column_name in columns

# Создание и миграция таблиц
def create_tables():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            phone TEXT,
            car TEXT,
            date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            username TEXT,
            feedback_text TEXT NOT NULL,
            rating TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            url TEXT UNIQUE,
            content TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_users (
            chat_id INTEGER PRIMARY KEY,
            last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

# Очистка таблицы новостей
def clear_news_table():
    try:
        cursor.execute("DELETE FROM news")
        conn.commit()
        logging.info("Таблица новостей очищена.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при очистке таблицы новостей: {e}")

# Закрытие соединения
def close_connection():
    conn.close()

# Добавление записи на техосмотр
def add_booking(chat_id, phone, car, date):
    cursor.execute(
        'INSERT INTO bookings (chat_id, phone, car, date) VALUES (?, ?, ?, ?)',
        (chat_id, phone, car, date)
    )
    add_active_user(chat_id)
    conn.commit()

# Получение всех записей на техосмотр
def get_all_bookings():
    cursor.execute('SELECT chat_id, phone, car, date FROM bookings')
    return cursor.fetchall()

# Добавление активного пользователя
def add_active_user(chat_id):
    cursor.execute(
        'INSERT OR REPLACE INTO active_users (chat_id, last_interaction) VALUES (?, ?)',
        (chat_id, datetime.now())
    )
    conn.commit()

# Получение активных пользователей
def get_active_users():
    cursor.execute('SELECT chat_id FROM active_users')
    return [row[0] for row in cursor.fetchall()]

# Получение истории пользователя
def get_user_history(chat_id, limit=3):
    cursor.execute(
        'SELECT "Запись", id, date, phone, car, NULL, NULL, NULL FROM bookings WHERE chat_id = ? ORDER BY id DESC LIMIT ?',
        (chat_id, limit)
    )
    bookings = cursor.fetchall()
    history = bookings[:limit]
    return history

# Добавление отзыва
def add_feedback(chat_id, feedback_text, rating=None, username=None):
    cursor.execute(
        'INSERT INTO feedbacks (chat_id, username, feedback_text, rating) VALUES (?, ?, ?, ?)',
        (chat_id, username, feedback_text, rating)
    )
    add_active_user(chat_id)
    conn.commit()

# Получение времени последнего отзыва
def get_last_feedback_time(chat_id):
    cursor.execute('SELECT timestamp FROM feedbacks WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 1', (chat_id,))
    result = cursor.fetchone()
    if result:
        try:
            return datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                return datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
    return None

# Получение всех новостей
def get_all_news():
    cursor.execute("SELECT id, title, date, url, content FROM news ORDER BY id DESC")
    rows = cursor.fetchall()
    return [{'id': r[0], 'title': r[1], 'date': r[2], 'url': r[3], 'content': r[4] or ''} for r in rows]

# Поиск новостей по датам
def get_news_by_period(start_date, end_date):
    try:
        start = datetime.strptime(start_date, '%d.%m.%Y')
        end = datetime.strptime(end_date, '%d.%m.%Y')
    except ValueError:
        logging.error(f"Неверный формат дат: {start_date} или {end_date}")
        return []

    news_list = get_all_news()
    filtered = []
    for news in news_list:
        try:
            news_date = datetime.strptime(news['date'], '%d.%m.%Y')
            if start <= news_date <= end:
                filtered.append(news)
        except ValueError:
            logging.warning(f"Неверный формат даты в новости: {news['date']}")
            continue
    return filtered

# Поиск новостей по ключевому слову
def search_news(keyword):
    keyword = f"%{keyword.lower()}%"
    cursor.execute(
        'SELECT id, title, date, url, content FROM news WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ? ORDER BY id DESC',
        (keyword, keyword)
    )
    rows = cursor.fetchall()
    return [{'id': r[0], 'title': r[1], 'date': r[2], 'url': r[3], 'content': r[4] or ''} for r in rows]

# Получение новостей из API и сохранение в базу
def parse_news_from_gto():
    api_url = 'https://gto.by/api/v2/news/list.php'
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        news_data = response.json()

        # Очистка таблицы новостей перед добавлением новых
        clear_news_table()

        news_list = []
        added = 0
        for item in news_data:
            try:
                news_item = {
                    'title': item.get('title', 'Без заголовка'),
                    'date': item.get('date', datetime.now().strftime('%d.%m.%Y')),
                    'url': item.get('url', ''),
                    'content': item.get('content', 'Контент недоступен')
                }
                # Проверка и форматирование даты
                try:
                    parsed_date = datetime.strptime(news_item['date'], '%Y-%m-%d')
                    news_item['date'] = parsed_date.strftime('%d.%m.%Y')
                except (ValueError, TypeError):
                    logging.warning(
                        f"Неверный формат даты для новости '{news_item['title']}': {news_item['date']}. Использую текущую дату.")
                    news_item['date'] = datetime.now().strftime('%d.%m.%Y')

                # Сохранение в базу
                cursor.execute(
                    'INSERT OR IGNORE INTO news (title, date, url, content) VALUES (?, ?, ?, ?)',
                    (news_item['title'], news_item['date'], news_item['url'], news_item['content'])
                )
                if cursor.rowcount > 0:
                    added += 1
                news_list.append(news_item)
            except Exception as e:
                logging.error(f"Ошибка обработки новости из API: {e}")
                continue

        conn.commit()
        logging.info(f"Добавлено {added} новых новостей из API.")
        return news_list

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP ошибка при запросе к API: {e.response.status_code} - {e.response.text}")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("Ошибка подключения к API новостей.")
        return []
    except requests.exceptions.Timeout:
        logging.error("Тайм-аут запроса к API новостей.")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса к API новостей: {e}")
        return []
    except ValueError as e:
        logging.error(f"Ошибка обработки JSON ответа API: {e}")
        return []
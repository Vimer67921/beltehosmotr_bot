import sqlite3
import os
import requests
from datetime import datetime, timedelta
import logging
import json

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Установим уровень DEBUG для максимальной детализации
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_logs.log'),  # Логи будут записываться в файл
        logging.StreamHandler()  # Вывод в консоль
    ]
)

# Создание директории для базы данных, если она не существует
DATABASE_DIR = 'database'
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# Путь к базе данных
DB_PATH = os.path.join(DATABASE_DIR, 'bookings.db')

# Получение соединения с базой данных
def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute('PRAGMA foreign_keys = ON')
        logging.debug(f"Успешное подключение к базе данных: {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Не удалось подключиться к базе данных: {e}")
        raise

# Проверка существования столбца в таблице
def check_column_exists(table_name, column_name):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in cursor.fetchall()]
            logging.debug(f"Проверка столбца {column_name} в таблице {table_name}: {column_name in columns}")
            return column_name in columns
    except sqlite3.Error as e:
        logging.error(f"Ошибка при проверке столбца {column_name} в таблице {table_name}: {e}")
        return False

# Создание и миграция таблиц
def create_tables():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    phone TEXT NOT NULL,
                    car TEXT NOT NULL,
                    date TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
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
                    last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                    state TEXT DEFAULT '{}'
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather_cache (
                    city TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookings_chat_id ON bookings(chat_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_id ON news(id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_active_users_chat_id ON active_users(chat_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_weather_cache_city ON weather_cache(city)')
            conn.commit()
            logging.info("Таблицы базы данных и индексы успешно созданы.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при создании таблиц: {e}")
        raise

# Очистка таблицы новостей
def clear_news_table():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM news")
            conn.commit()
            logging.info("Таблица новостей успешно очищена.")
            return True
    except sqlite3.Error as e:
        logging.error(f"Ошибка при очистке таблицы новостей: {e}")
        return False

# Добавление записи на техосмотр
def add_booking(chat_id, phone, car, date):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO bookings (chat_id, phone, car, date) VALUES (?, ?, ?, ?)',
                (chat_id, phone, car, date)
            )
            add_active_user(chat_id)
            conn.commit()
            logging.info(f"Запись добавлена для chat_id {chat_id}")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении записи для chat_id {chat_id}: {e}")
        raise

# Получение всех записей
def get_all_bookings():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT chat_id, phone, car, date FROM bookings')
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении записей: {e}")
        return []

# Добавление или обновление активного пользователя
def add_active_user(chat_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO active_users (chat_id, last_interaction) VALUES (?, ?)',
                (chat_id, datetime.now())
            )
            conn.commit()
            logging.info(f"Активный пользователь обновлен: {chat_id}")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при обновлении активного пользователя {chat_id}: {e}")
        raise

# Получение активных пользователей
def get_active_users():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT chat_id FROM active_users')
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении активных пользователей: {e}")
        return []

# Получение истории пользователя
def get_user_history(chat_id, limit=3):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT "Запись", id, date, phone, car, NULL, NULL, NULL FROM bookings WHERE chat_id = ? ORDER BY id DESC LIMIT ?',
                (chat_id, limit)
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении истории для chat_id {chat_id}: {e}")
        return []

# Добавление отзыва
def add_feedback(chat_id, feedback_text, rating=None, username=None):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO feedbacks (chat_id, username, feedback_text, rating) VALUES (?, ?, ?, ?)',
                (chat_id, username, feedback_text, rating)
            )
            add_active_user(chat_id)
            conn.commit()
            logging.info(f"Отзыв добавлен для chat_id {chat_id}")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении отзыва для chat_id {chat_id}: {e}")
        raise

# Получение времени последнего отзыва
def get_last_feedback_time(chat_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT timestamp FROM feedbacks WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 1', (chat_id,))
            result = cursor.fetchone()
            if result:
                try:
                    return datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    try:
                        return datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        logging.warning(f"Неверный формат временной метки для chat_id {chat_id}")
                        return None
            return None
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении времени последнего отзыва для chat_id {chat_id}: {e}")
        return None

# Получение всех новостей с пагинацией
def get_all_news(page=1, per_page=10):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            cursor.execute(
                "SELECT id, title, date, url, content FROM news ORDER BY id DESC LIMIT ? OFFSET ?",
                (per_page, offset)
            )
            rows = cursor.fetchall()
            news = [{'id': r[0], 'title': r[1], 'date': r[2], 'url': r[3], 'content': r[4] or ''} for r in rows]
            logging.debug(f"Получено {len(news)} новостей для страницы {page}")
            return news
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении новостей: {e}")
        return []

# Получение новостей за период
def get_news_by_period(start_date, end_date):
    try:
        start = datetime.strptime(start_date, '%d.%m.%Y')
        end = datetime.strptime(end_date, '%d.%m.%Y')
    except ValueError as e:
        logging.error(f"Неверный формат даты: {start_date} или {end_date} - {e}")
        return []

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
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
            logging.debug(f"Найдено {len(filtered)} новостей за период {start_date} - {end_date}")
            return filtered
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении новостей за период: {e}")
        return []

# Поиск новостей по ключевому слову
def search_news(keyword):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            keyword = f"%{keyword.lower()}%"
            cursor.execute(
                'SELECT id, title, date, url, content FROM news WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ? ORDER BY id DESC',
                (keyword, keyword)
            )
            rows = cursor.fetchall()
            news = [{'id': r[0], 'title': r[1], 'date': r[2], 'url': r[3], 'content': r[4] or ''} for r in rows]
            logging.debug(f"Найдено {len(news)} новостей по ключевому слову '{keyword}'")
            return news
    except sqlite3.Error as e:
        logging.error(f"Ошибка при поиске новостей с ключевым словом '{keyword}': {e}")
        return []

# Парсинг новостей с API GTO
def parse_news_from_gto():
    api_url = 'https://gto.by/api/v2/news/list.php'
    try:
        logging.info(f"Начало запроса новостей с {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        news_data = response.json()
        logging.debug(f"Получено данных от API: {len(news_data)} записей")
        if not isinstance(news_data, list):
            logging.error("API вернул неверный формат данных")
            return []

        if not clear_news_table():
            logging.error("Не удалось очистить таблицу новостей")
            return []

        news_list = []
        added = 0
        with get_connection() as conn:
            cursor = conn.cursor()
            for item in news_data:
                try:
                    news_item = {
                        'title': item.get('title', 'Без заголовка'),
                        'date': item.get('date', datetime.now().strftime('%d.%m.%Y')),
                        'url': item.get('url', ''),
                        'content': item.get('content', 'Контент недоступен')
                    }
                    try:
                        parsed_date = datetime.strptime(news_item['date'], '%Y-%m-%d')
                        news_item['date'] = parsed_date.strftime('%d.%m.%Y')
                    except (ValueError, TypeError):
                        logging.warning(f"Неверный формат даты для новости '{news_item['title']}': {news_item['date']}")
                        news_item['date'] = datetime.now().strftime('%d.%m.%Y')

                    cursor.execute(
                        'INSERT OR IGNORE INTO news (title, date, url, content) VALUES (?, ?, ?, ?)',
                        (news_item['title'], news_item['date'], news_item['url'], news_item['content'])
                    )
                    if cursor.rowcount > 0:
                        added += 1
                    news_list.append(news_item)
                except KeyError as e:
                    logging.error(f"Отсутствует ключ в данных новости: {e}")
                    continue
            conn.commit()
            logging.info(f"Добавлено {added} новых новостей из API.")
        return news_list

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP ошибка API: {e.response.status_code} - {e.response.text}")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("Ошибка соединения при получении новостей с API.")
        return []
    except requests.exceptions.Timeout:
        logging.error("Тайм-аут при получении новостей с API.")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса к API: {e}")
        return []
    except ValueError as e:
        logging.error(f"Ошибка парсинга JSON-ответа API: {e}")
        return []

# Получение кэшированных данных о погоде
def get_cached_weather(city):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data, timestamp FROM weather_cache WHERE city = ?', (city,))
            result = cursor.fetchone()
            if result:
                data, timestamp = result
                logging.debug(f"Кэшированные данные погоды для {city} найдены: {timestamp}")
                return {'data': json.loads(data), 'timestamp': timestamp}
            logging.debug(f"Кэшированных данных для {city} не найдено")
            return None
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении кэшированных данных погоды для {city}: {e}")
        return None

# Кэширование данных о погоде
def cache_weather(city, weather_data):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO weather_cache (city, data, timestamp) VALUES (?, ?, ?)',
                (city, json.dumps(weather_data), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            logging.info(f"Погода для {city} закэширована.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при кэшировании погоды для {city}: {e}")
        raise

# Очистка старых активных пользователей
def clean_old_active_users(hours=1):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM active_users WHERE last_interaction < ?',
                (datetime.now() - timedelta(hours=hours),)
            )
            conn.commit()
            logging.info(f"Очищено {cursor.rowcount} старых активных пользователей.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при очистке старых активных пользователей: {e}")

import telebot
import db_handler
import re
import requests
import random
import datetime
import logging
from datetime import datetime
import random
from dotenv import load_dotenv
import os
import json

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Токен бота и API-ключи
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8133560465:AAGDwkX86Pegjmd6WZqBwg6-5qjfaC9gsgY')
EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY', '6e48c92c9426cd2dfd7d0d0e')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '81f986beb7a5b44cb6ff318dc9d06af9')
bot = telebot.TeleBot(TOKEN)

# Настройки для ИИ API
AI_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
AI_API_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjMyOWYyYjFlLWZkZGEtNGY4NC1iYzI2LTIxNjc3OGU5MzVkZiIsImV4cCI6NDkwNDYxMjY5Mn0.ibI8tb4tC9nUOEoaEA63tkkvYWExAf6Q94xPVY7Ob19ue1DD56XXSpXMjWkAg1nO0MhBLxbb9LQwNumyU2vnQA"
}

# Список советов дня
tips = {
    "🔧 Подготовка к ТО": [
        {"text": "Проверьте давление в шинах перед техосмотром — правильное давление улучшает безопасность.", "details": "Давление должно соответствовать рекомендациям производителя (указано на двери водителя или в мануале). На станциях ТО в Беларуси проверяют шины на износ и повреждения. Подробнее: https://gto.by"},
        {"text": "Убедитесь, что аптечка, огнетушитель и знак аварийной остановки в наличии и не просрочены.", "details": "Согласно ПДД РБ, эти элементы обязательны. Аптечка должна быть укомплектована, а огнетушитель — заправлен и с действующим сроком годности."},
        {"text": "Протрите фары и стекла для лучшей видимости и успешного прохождения ТО.", "details": "Грязные фары могут снизить световой поток, что приведет к отказу в ТО. Используйте очищающие средства для стекол и проверьте регулировку фар."},
        {"text": "Проверьте все лампочки в фарах, стоп-сигналах и поворотниках.", "details": "Неисправные лампочки — частая причина отказа на ТО. Замените их заранее, чтобы избежать повторного визита."},
        {"text": "Очистите номерные знаки от грязи, чтобы они были читаемы.", "details": "Грязные номера могут стать причиной отказа. Убедитесь, что номера четко видны и не повреждены."},
        {"text": "Проверьте работу стеклоочистителей и наличие жидкости в бачке омывателя.", "details": "Неисправные дворники или пустой бачок омывателя могут привести к отказу на ТО. Используйте незамерзающую жидкость в холодное время года."},
        {"text": "Убедитесь, что ремень безопасности работает корректно.", "details": "На ТО проверяют ремни на износ и исправность замков. Замените повреждённые ремни заранее."},
        {"text": "Проверьте уровень тормозной жидкости.", "details": "Низкий уровень или загрязнённая тормозная жидкость может повлиять на работу тормозов, что проверяется на ТО."},
        {"text": "Проверьте состояние выхлопной системы.", "details": "Дыры или чрезмерный шум в выхлопной системе могут привести к отказу на ТО. Проверьте глушитель и трубы на коррозию."},
        {"text": "Убедитесь, что ручной тормоз работает эффективно.", "details": "На ТО проверяют эффективность ручного тормоза. Если он слабый, отрегулируйте или замените трос."}
    ],
    "🚗 Обслуживание авто": [
        {"text": "Проверяйте уровень масла в двигателе каждые 1–2 месяца.", "details": "Низкий уровень масла может повредить двигатель. Используйте масло, рекомендованное производителем, и меняйте его каждые 10–15 тыс. км."},
        {"text": "Заменяйте воздушный фильтр каждые 15–20 тыс. км для экономии топлива.", "details": "Засоренный фильтр снижает мощность двигателя и увеличивает расход. Проверьте фильтр при очередном ТО."},
        {"text": "Проверяйте тормозные колодки на износ каждые 20 тыс. км.", "details": "Изношенные колодки увеличивают тормозной путь. На ТО в Беларуси тормоза проверяют на стенде, так что замените их заранее."},
        {"text": "Проверяйте уровень охлаждающей жидкости регулярно.", "details": "Недостаток антифриза может привести к перегреву двигателя. Доливайте жидкость, рекомендованную производителем."},
        {"text": "Проверяйте состояние дворников — изношенные щетки ухудшают обзор.", "details": "Замените щетки, если они оставляют полосы или скрипят. Это важно для безопасности и ТО."},
        {"text": "Проверяйте состояние аккумулятора перед зимой.", "details": "Слабый аккумулятор может не запустить двигатель в холод. Проверьте клеммы на коррозию и заряд батареи."},
        {"text": "Меняйте свечи зажигания каждые 30–50 тыс. км.", "details": "Изношенные свечи увеличивают расход топлива и снижают мощность. Используйте свечи, рекомендованные производителем."},
        {"text": "Проверяйте состояние ремня ГРМ.", "details": "Обрыв ремня ГРМ может привести к серьёзной поломке двигателя. Меняйте ремень согласно регламенту (обычно каждые 60–100 тыс. км)."},
        {"text": "Очищайте радиатор от грязи и насекомых.", "details": "Засорённый радиатор ухудшает охлаждение двигателя, что может привести к перегреву. Используйте сжатый воздух или мягкую щётку."},
        {"text": "Проверяйте состояние подвески каждые 20 тыс. км.", "details": "Изношенные амортизаторы или шаровые опоры снижают управляемость. Проверьте на СТО перед ТО."}
    ],
    "📜 Правила РБ": [
        {"text": "Техосмотр обязателен раз в год для авто старше 10 лет.", "details": "Согласно Указу №349, легковые авто старше 10 лет проходят ТО ежегодно, до 10 лет — раз в 2 года. Штраф за просрочку — до 120 BYN в 2025."},
        {"text": "Страховка ОСГО обязательна перед ТО.", "details": "Без действующей страховки ТО не пройти. Оформите ОСГО через Белгосстрах или онлайн на их сайте: https://bgs.by"},
        {"text": "Штраф за отсутств ие ТО — до 3 базовых величин.", "details": "В 2025 году это до 120 BYN. При повторном нарушении штраф выше или возможно лишение прав. Пройдите ТО вовремя!"},
        {"text": "Периодичность ТО для такси — каждые 6 месяцев.", "details": "Согласно законодательству РБ, автомобили, используемые для перевозки пассажиров, проходят ТО дважды в год."},
        {"text": "Документы для ТО: паспорт, техпаспорт, страховка.", "details": "Также нужна квитанция об оплате госпошлины. Оплатить можно через ЕРИП или на сайте https://gto.by/pay/?step=1."},
        {"text": "Запрещено тонировать лобовое стекло и передние боковые стёкла.", "details": "Согласно ПДД РБ, светопропускание этих стёкол должно быть не менее 70%. Нарушение может привести к отказу на ТО."},
        {"text": "Детское кресло обязательно для детей до 12 лет или роста до 150 см.", "details": "Штраф за отсутствие кресла — до 4 базовых величин (160 BYN в 2025). Проверьте крепление кресла перед ТО."},
        {"text": "Зимние шины обязательны с 1 декабря по 1 марта.", "details": "Штраф за нарушение — до 1 базовой величины (40 BYN в 2025). Убедитесь, что шины соответствуют требованиям перед ТО."},
        {"text": "Перевозка грузов должна соответствовать нормам.", "details": "Груз не должен выступать более чем на 1 м сзади или 0,4 м по бокам без специальной маркировки. Нарушение проверяется на ТО."},
        {"text": "Запрещено использовать авто с неисправными тормозами или рулевым управлением.", "details": "Такие неисправности выявляются на ТО, и эксплуатация авто запрещается до устранения. Проверьте системы заранее."}
    ]
}

# Меню выбора категории совета
tip_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
tip_menu.row("🔧 Подготовка к ТО", "🚗 Обслуживание авто")
tip_menu.row("📜 Правила РБ")
tip_menu.row("⬅️ Назад в главное меню")

# Меню после совета
tip_followup_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
tip_followup_menu.row("ℹ️ Подробнее", "➡️ Новый совет")
tip_followup_menu.row("⬅️ Назад в главное меню")

# Обработчик совета дня
@bot.message_handler(func=lambda msg: msg.text == "💡 Совет дня")
def send_tip(msg):
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(
        msg.chat.id,
        "Выберите категорию совета:",
        reply_markup=tip_menu
    )
    user_states[msg.chat.id] = {'state': 'awaiting_tip_category'}

# Обработчик выбора категории совета
@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('state') == 'awaiting_tip_category')
def handle_tip_category(msg):
    db_handler.add_active_user(msg.chat.id)
    chat_id = msg.chat.id
    category = msg.text
    if category in tips and tips[category]:
        tip = random.choice(tips[category])
        logging.info(f"Выбран совет из категории {category}: {tip['text']}")
        bot.send_message(
            chat_id,
            f"{tip['text']}\n\nℹ️ Хотите узнать больше или получить новый совет?",
            reply_markup=tip_followup_menu
        )
        user_states[chat_id] = {'tip': tip, 'category': category}
    elif msg.text == "⬅️ Назад в главное меню":
        bot.send_message(
            chat_id,
            "Вы вернулись в главное меню.",
            reply_markup=main_menu
        )
        user_states.pop(chat_id, None)
    else:
        bot.send_message(
            chat_id,
            "⚠️ Пожалуйста, выберите категорию из предложенных.",
            reply_markup=tip_menu
        )

# Обработчик действий после совета
@bot.message_handler(func=lambda msg: msg.text in ["ℹ️ Подробнее", "➡️ Новый совет", "⬅️ Назад в главное меню"])
def handle_tip_followup(msg):
    db_handler.add_active_user(msg.chat.id)
    chat_id = msg.chat.id
    if msg.text == "➡️ Новый совет":
        if chat_id in user_states and 'category' in user_states[chat_id]:
            category = user_states[chat_id]['category']
            if tips[category]:
                tip = random.choice(tips[category])
                logging.info(f"Выбран новый совет из категории {category}: {tip['text']}")
                bot.send_message(
                    chat_id,
                    f"{tip['text']}\n\nℹ️ Хотите узнать больше или получить новый совет?",
                    reply_markup=tip_followup_menu
                )
                user_states[chat_id] = {'tip': tip, 'category': category}
            else:
                bot.send_message(
                    chat_id,
                    "⚠️ Советы в этой категории закончились. Выберите другую категорию.",
                    reply_markup=tip_menu
                )
                user_states[chat_id] = {'state': 'awaiting_tip_category'}
        else:
            bot.send_message(
                chat_id,
                "⚠️ Выберите категорию совета.",
                reply_markup=tip_menu
            )
            user_states[chat_id] = {'state': 'awaiting_tip_category'}
    elif msg.text == "ℹ️ Подробнее":
        if chat_id in user_states and 'tip' in user_states[chat_id]:
            tip = user_states[chat_id]['tip']
            bot.send_message(
                chat_id,
                f"{tip['text']}\n\n📋 <b>Подробности:</b>\n{tip['details']}",
                parse_mode="HTML",
                reply_markup=tip_followup_menu,
                disable_web_page_preview=True
            )
        else:
            bot.send_message(
                chat_id,
                "⚠️ Информация о совете устарела. Выберите категорию для нового совета.",
                reply_markup=tip_menu
            )
            user_states[chat_id] = {'state': 'awaiting_tip_category'}
    elif msg.text == "⬅️ Назад в главное меню":
        bot.send_message(
            chat_id,
            "Вы вернулись в главное меню.",
            reply_markup=main_menu
        )
        user_states.pop(chat_id, None)

user_states = {}

# Главное меню
main_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.row("📝 Запись на техосмотр", "📰 Новости")
main_menu.row("💬 FAQ", "☁️ Погода")
main_menu.row("🛠️ Услуги", "📄 О страховке")
main_menu.row("✨ Оставить отзыв", "ℹ️ О компании")
main_menu.row("📞 Контакты", "🤖 Спросить ИИ")
main_menu.row("💡 Совет дня", "💸 Курсы валют")

# Меню выбора типа ремонта
repair_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
repair_menu.row("Замена тормозных колодок", "Замена тормозных дисков")
repair_menu.row("Замена масла", "Замена масляного фильтра")
repair_menu.row("Ремонт стартера", "Замена стартера")
repair_menu.row("Замена свечей зажигания", "Ремонт подвески")
repair_menu.row("Замена амортизаторов", "Замена аккумулятора")
repair_menu.row("Ремонт рулевого управления", "Замена рулевых тяг")
repair_menu.row("Диагностика", "Замена воздушного фильтра")
repair_menu.row("Ремонт генератора", "Замена ремня ГРМ")
repair_menu.row("Ремонт выхлопной системы", "Замена охлаждающей жидкости")
repair_menu.row("Ремонт радиатора", "Замена стеклоочистителей")
repair_menu.row("Ремонт коробки передач", "Замена сцепления")
repair_menu.row("Ремонт тормозной системы", "Замена глушителя")
repair_menu.row("Ремонт электрики", "Другое")
repair_menu.row("❌ Отмена")

# Меню новостей
news_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
news_menu.row("📰 Свежие новости", "📅 Новости за период")
news_menu.row("🔍 Поиск новостей", "⬅️ Назад в главное меню")

# Меню FAQ
faq_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
faq_menu.row("📄 Документы на ТО", "❓ ТО без страховки")
faq_menu.row("⚠️ Штрафы за просрочку", "💸 Стоимость ТО")
faq_menu.row("📆 Периодичность ТО", "🔄 Изменить запись")
faq_menu.row("🚫 Если не прошел ТО", "🧾 Онлайн-оплата")
faq_menu.row("⬅️ Назад в главное меню")

# Меню отзывов
feedback_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
feedback_menu.row("⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐")
feedback_menu.row("✍️ Оставить без оценки", "❌ Отмена")

# Кнопка отмены
cancel_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cancel_menu.row("❌ Отмена")

# Меню для выбора города
city_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
city_menu.row("Минск", "Гомель", "Брест")
city_menu.row("Витебск", "Гродно", "Могилёв")
city_menu.row("Бобруйск", "Пинск", "Орша")
city_menu.row("Мозырь", "Солигорск", "Новополоцк")
city_menu.row("❌ Отмена")

# Меню для ИИ помощника
ai_mode_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
ai_mode_menu.row("⬅️ Назад в главное меню")

# Функция для получения ответа от ИИ
def get_ai_response(user_message_text, conversation_history=None):
    lower_user_message = user_message_text.lower().strip()
    greetings = ["привет", "здравствуйте", "добрый день", "как дела?", "привет!", "здравствуйте!",
                 "добрый день!", "добрый вечер", "доброе утро", "хай", "хелло", "hi", "hello"]
    if lower_user_message in greetings:
        return "Здравствуйте! Чем могу помочь?"

    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — виртуальный помощник БЕЛТЕХОСМОТР (Республика Беларусь). Строго соблюдай правила:\n\n"
                    "1. КОНТЕКСТ И ПАМЯТЬ:\n"
                    "- Запоминай всю историю диалога в рамках текущей сессии\n"
                    "- Учитывай предыдущие вопросы и ответы при формировании новых\n"
                    "- Если вопрос уточняет предыдущий - отвечай с учетом контекста\n\n"
                    "2. ФОРМАТ ОТВЕТОВ:\n"
                    "- Только факты, без вводных фраз и эмоций\n"
                    "- 1-3 предложения (максимум 50 слов)\n"
                    "- Если нужно больше данных - разбивай ответ на несколько сообщений\n\n"
                    "3. ТЕМАТИКА:\n"
                    "- Только законодательство, процедуры и услуги Беларуси\n"
                    "- Техосмотр, ПДД, штрафы, ГОСТы, техрегламенты РБ\n"
                    "- Если вопрос не по Беларуси: 'Информация доступна только по РБ. Уточните запрос.'\n\n"
                    "4. ТОЧНОСТЬ:\n"
                    "- Не предполагай и не додумывай\n"
                    "- Если не уверен - говори: 'Точные данные уточните в БЕЛТЕХОСМОТР по телефону...'\n"
                    "- Даты и суммы указывай точно (на 2025 год)\n\n"
                    "5. КРИТИЧЕСКИЕ СЛУЧАИ:\n"
                    "- При угрозах жизни/здоровью: 'Немедленно звоните 103!'"
                )
            }
        ]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({
            "role": "user",
            "content": user_message_text
        })

        data = {
            "model": "deepseek-ai/DeepSeek-R1-0528",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.3,
            "top_p": 0.9
        }

        response = requests.post(AI_API_URL, headers=AI_API_HEADERS, json=data, timeout=10)
        response.raise_for_status()
        response_data = response.json()

        if not response_data.get('choices'):
            logging.error(f"Ошибка API: Пустой ответ или отсутствует 'choices'. Ответ: {json.dumps(response_data, ensure_ascii=False)}")
            return "Ошибка API: пустой ответ. Попробуйте позже."

        text = response_data['choices'][0]['message']['content'].strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
        sentences = re.split(r'(?<=[.!?])\s+', text)
        unique_sentences = []
        for sent in sentences:
            if sent not in unique_sentences:
                unique_sentences.append(sent)
        text = ' '.join(unique_sentences[:3])

        stop_phrases = [
            "если у вас есть еще вопросы",
            "обращайтесь",
            "чем еще могу помочь",
            "уточните ваш вопрос",
            "надеюсь, это помогло",
            "с радостью помогу",
            "как виртуальный помощник",
            "в моей компетенции",
            "я могу помочь только"
        ]
        for phrase in stop_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^[.,;:!?]+', '', text)
        text = re.sub(r'[.,;:!?]+$', '', text)

        if not text:
            logging.warning(f"Пустой текст после обработки: {user_message_text}")
            return "Не могу дать точный ответ. Сформулируйте вопрос иначе."

        return text

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_text = e.response.text if hasattr(e.response, 'text') else 'Нет текста ответа'
        logging.error(f"HTTP ошибка API: {status_code} - {error_text}")
        if status_code == 401:
            return "Ошибка авторизации API. Пожалуйста, свяжитесь с поддержкой."
        elif status_code == 429:
            return "Слишком много запросов к API. Попробуйте позже."
        elif status_code == 400:
            return f"Неверный запрос к API: {error_text}. Уточните параметры запроса."
        return f"Ошибка API ({status_code}). Попробуйте позже."

    except requests.exceptions.ConnectionError:
        logging.error("Ошибка подключения к API: нет соединения")
        return "Ошибка подключения к API. Проверьте интернет и попробуйте снова."

    except requests.exceptions.Timeout:
        logging.error("Тайм-аут запроса к API")
        return "Запрос к API занял слишком много времени. Попробуйте позже."

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса к API: {str(e)}")
        return "Техническая ошибка API. Попробуйте позже."

    except Exception as e:
        logging.error(f"Неожиданная ошибка в get_ai_response: {str(e)}")
        return "Ошибка обработки запроса. Попробуйте позже."

# Проверка номера телефона
def check_phone(phone):
    phone = re.sub(r'[^\d+]', '', phone)
    pattern = r'^(\+375|80)(29|25|44|33)(\d{7})$'
    if not re.match(pattern, phone):
        return False, "❗ Неверный формат телефона. Используйте +375XXYYYYYYY или 80XXYYYYYYY"
    return True, ""

# Проверка модели автомобиля
def check_car_model(model):
    if len(model) < 2 or len(model) > 50:
        return False, "❗ Название авто должно быть от 2 до 50 символов"
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ]', model):
        return False, "❗ Название авто должно содержать буквы"
    if not re.fullmatch(r'^[a-zA-Zа-яА-ЯёЁ0-9\s\-]+$', model):
        return False, "❗ Используйте буквы, цифры, пробелы или дефисы"
    return True, ""

# Проверка года выпуска
def check_year(year):
    if not year.isdigit() or len(year) != 4:
        return False, "❗ Год должен быть 4 цифрами (например, 2020)"
    year_num = int(year)
    current_year = datetime.now().year
    if not (1900 <= year_num <= current_year + 1):
        return False, f"❗ Год должен быть от 1900 до {current_year + 1}"
    return True, ""

# Проверка даты записи
def check_booking_date(date_str):
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_str):
        return False, "❗ Формат даты: ДД.ММ.ГГГГ"
    try:
        selected_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        if selected_date < datetime.now().date():
            return False, "❗ Дата не может быть в прошлом"
        return True, ""
    except ValueError:
        return False, "❗ Неверная дата"

# Проверка даты для поиска новостей
def check_search_date(date_str):
    try:
        datetime.strptime(date_str, '%d.%m.%Y')
        return True
    except ValueError:
        return False

# Функция для получения курсов валют
@bot.message_handler(commands=['currency'])
@bot.message_handler(func=lambda msg: msg.text == "💸 Курсы валют")
def get_currency(msg):
    db_handler.add_active_user(msg.chat.id)
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/BYN"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data['result'] == 'success':
            rates = data['conversion_rates']
            update_time = datetime.fromtimestamp(data['time_last_update_unix']).strftime('%d.%m.%Y %H:%M')
            user_states[msg.chat.id] = {'rates': rates, 'update_time': update_time}

            response_text = (
                "💰 <b>Курсы валют (BYN)</b>\n"
                f"📅 Обновлено: {update_time}\n"
                "━━━━━━━━━━━━━━━\n"
                "Выберите действие:\n"
                "1️⃣ Посмотреть курсы\n"
                "2️⃣ Конвертировать валюту"
            )
            buttons = telebot.types.InlineKeyboardMarkup()
            buttons.add(telebot.types.InlineKeyboardButton("1️⃣ Курсы", callback_data="show_rates"))
            buttons.add(telebot.types.InlineKeyboardButton("2️⃣ Конвертер", callback_data="convert_currency"))
            bot.send_message(
                msg.chat.id,
                response_text,
                parse_mode="HTML",
                reply_markup=buttons
            )
            logging.info(f"Курсы валют доступны для выбора пользователю {msg.chat.id}")
        else:
            bot.send_message(
                msg.chat.id,
                "⚠️ Ошибка получения данных о валютах. Попробуйте позже.",
                reply_markup=main_menu
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса курса валют: {e}")
        bot.send_message(
            msg.chat.id,
            "⚠️ Не удалось получить курсы валют. Проверьте подключение к интернету и попробуйте позже.",
            reply_markup=main_menu
        )

# Обработчик inline-кнопок
@bot.callback_query_handler(func=lambda call: call.data in ["show_rates", "convert_currency", "refresh_currency"])
def handle_currency_actions(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    if chat_id not in user_states or 'rates' not in user_states[chat_id]:
        bot.send_message(chat_id, "⚠️ Данные о курсах устарели. Запросите курсы заново.", reply_markup=main_menu)
        return

    rates = user_states[chat_id]['rates']
    update_time = user_states[chat_id]['update_time']

    if call.data == "show_rates":
        currency_list = {
            'USD': '🇺🇸 Доллар США',
            'EUR': '🇪🇺 Евро',
            'RUB': '🇷🇺 Российский рубль',
            'PLN': '🇵🇱 Польский злотый',
            'UAH': '🇺🇦 Украинская гривна'
        }
        response_text = (
            "💰 <b>Курсы валют (BYN)</b>\n"
            f"📅 Обновлено: {update_time}\n"
            "━━━━━━━━━━━━━━━\n"
        )
        for code, name in currency_list.items():
            rate = rates.get(code, 'N/A')
            if rate != 'N/A':
                response_text += f"{name}: {rate:.2f} {code}\n"
            else:
                response_text += f"{name}: Данные недоступны\n"
        response_text += (
            "━━━━━━━━━━━━━━━\n"
            "🌐 Источник: ExchangeRate-API\n"
            "💡 Используйте конвертер для расчетов!"
        )
        buttons = telebot.types.InlineKeyboardMarkup()
        buttons.add(telebot.types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_currency"))
        buttons.add(telebot.types.InlineKeyboardButton("2️⃣ Конвертер", callback_data="convert_currency"))
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=response_text,
            parse_mode="HTML",
            reply_markup=buttons
        )
    elif call.data == "convert_currency":
        response_text = (
            "💱 <b>Конвертер валют</b>\n"
            f"📅 Обновлено: {update_time}\n"
            "━━━━━━━━━━━━━━━\n"
            "Введите сумму и валюту (например, '100 USD в EUR'):"
        )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=response_text,
            parse_mode="HTML"
        )
        bot.register_next_step_handler(call.message, process_conversion)
    elif call.data == "refresh_currency":
        get_currency(call.message)

def process_conversion(message):
    chat_id = message.chat.id
    if chat_id not in user_states or 'rates' not in user_states[chat_id]:
        bot.send_message(chat_id, "⚠️ Данные о курсах устарели. Запросите курсы заново.", reply_markup=main_menu)
        return

    rates = user_states[chat_id]['rates']
    try:
        input_text = message.text.strip().lower()
        parts = re.match(r'(\d+\.?\d*)\s*(\w+)\s*в\s*(\w+)', input_text)
        if not parts:
            raise ValueError("Неверный формат. Введите, например, '100 USD в EUR'.")
        amount = float(parts.group(1))
        from_currency = parts.group(2).upper()
        to_currency = parts.group(3).upper()

        if from_currency not in rates or to_currency not in rates:
            raise ValueError("Одна из валют недоступна.")

        rate_from = rates[from_currency]
        rate_to = rates[to_currency]
        converted_amount = (amount / rate_from) * rate_to

        response_text = (
            f"💱 <b>Конвертация валют</b>\n"
            f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}\n"
            "━━━━━━━━━━━━━━━\n"
            f"🌐 Курсы обновлены: {user_states[chat_id]['update_time']}\n"
            "💡 Хотите конвертировать еще?"
        )
        buttons = telebot.types.InlineKeyboardMarkup()
        buttons.add(telebot.types.InlineKeyboardButton("🔄 Ещё раз", callback_data="convert_currency"))
        buttons.add(telebot.types.InlineKeyboardButton("⬅️ Назад", callback_data="show_rates"))
        bot.send_message(
            chat_id,
            response_text,
            parse_mode="HTML",
            reply_markup=buttons
        )
    except ValueError as e:
        bot.send_message(
            chat_id,
            f"⚠️ {str(e)} Попробуйте снова (например, '100 USD в EUR').",
            reply_markup=main_menu
        )
    except Exception as e:
        logging.error(f"Ошибка обработки конвертации: {e}")
        bot.send_message(
            chat_id,
            "⚠️ Ошибка при конвертации. Попробуйте позже.",
            reply_markup=main_menu
        )

# Меню выбора региона для погоды
region_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
region_menu.row("Минская область", "Брестская область")
region_menu.row("Витебская область", "Гомельская область")
region_menu.row("Гродненская область", "Могилёвская область")
region_menu.row("❌ Отмена")

# Меню городов по регионам
minsk_cities = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
minsk_cities.row("Минск", "Борисов", "Молодечно", "Жодино")
minsk_cities.row("Слуцк", "Солигорск")
minsk_cities.row("⬅️ Назад к регионам", "❌ Отмена")

brest_cities = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
brest_cities.row("Брест", "Барановичи", "Пинск", "Кобрин")
brest_cities.row("⬅️ Назад к регионам", "❌ Отмена")

vitebsk_cities = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
vitebsk_cities.row("Витебск", "Орша", "Новополоцк", "Полоцк")
vitebsk_cities.row("⬅️ Назад к регионам", "❌ Отмена")

gomel_cities = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
gomel_cities.row("Гомель", "Мозырь", "Жлобин", "Речица")
gomel_cities.row("Светлогорск")
gomel_cities.row("⬅️ Назад к регионам", "❌ Отмена")

grodno_cities = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
grodno_cities.row("Гродно", "Лида", "Слоним", "Волковыск")
grodno_cities.row("⬅️ Назад к регионам", "❌ Отмена")

mogilev_cities = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
mogilev_cities.row("Могилёв", "Бобруйск")
mogilev_cities.row("⬅️ Назад к регионам", "❌ Отмена")

# Словарь для маппинга русских названий на английские для API
city_mapping = {
    "Минск": "Minsk",
    "Брест": "Brest",
    "Витебск": "Vitebsk",
    "Гомель": "Gomel",
    "Гродно": "Grodno",
    "Могилёв": "Mogilev",
    "Бобруйск": "Bobruisk",
    "Барановичи": "Baranovichi",
    "Пинск": "Pinsk",
    "Орша": "Orsha",
    "Мозырь": "Mozyr",
    "Солигорск": "Soligorsk",
    "Новополоцк": "Novopolotsk",
    "Лида": "Lida",
    "Жлобин": "Zhlobin",
    "Слуцк": "Slutsk",
    "Речица": "Rechitsa",
    "Светлогорск": "Svetlogorsk",
    "Кобрин": "Kobrin",
    "Борисов": "Borisov",
    "Молодечно": "Molodechno",
    "Полоцк": "Polotsk",
    "Жодино": "Zhodino",
    "Слоним": "Slonim",
    "Волковыск": "Volkovysk",
    "Несвиж": "Nesvizh"
}

# Обработчик команды /weather и кнопки "Погода"
@bot.message_handler(commands=['weather'])
@bot.message_handler(func=lambda msg: msg.text == "☁️ Погода")
def start_weather_check(msg):
    db_handler.add_active_user(msg.chat.id)
    sent_msg = bot.send_message(
        msg.chat.id,
        "Выберите регион:",
        reply_markup=region_menu
    )
    bot.register_next_step_handler(sent_msg, handle_region_selection)

# Обработчик выбора региона
def handle_region_selection(msg):
    if msg.text == "❌ Отмена":
        return_to_main(msg)
        return
    region = msg.text.strip()
    region_menus = {
        "Минская область": minsk_cities,
        "Брестская область": brest_cities,
        "Витебская область": vitebsk_cities,
        "Гомельская область": gomel_cities,
        "Гродненская область": grodno_cities,
        "Могилёвская область": mogilev_cities
    }
    if region not in region_menus:
        sent_msg = bot.send_message(
            msg.chat.id,
            "❗ Пожалуйста, выберите регион из списка.",
            reply_markup=region_menu
        )
        bot.register_next_step_handler(sent_msg, handle_region_selection)
        return
    sent_msg = bot.send_message(
        msg.chat.id,
        f"Выберите город в {region}:",
        reply_markup=region_menus[region]
    )
    bot.register_next_step_handler(sent_msg, get_weather)

# Функция для получения рекомендаций по вождению
def get_driving_advice(weather_desc, temp, wind_speed, humidity):
    weather_desc = weather_desc.lower()
    if "снег" in weather_desc or "гололед" in weather_desc or temp < 0:
        return "❄️ Возможен гололед! Снизьте скорость, увеличьте дистанцию, используйте зимние шины."
    elif "дождь" in weather_desc or humidity > 80:
        return "🌧 Дождь. Включите дворники, избегайте резких маневров, держите дистанцию."
    elif "туман" in weather_desc:
        return "🌫 Туман. Включите противотуманные фары, двигайтесь медленно."
    elif wind_speed > 10:
        return "💨 Сильный ветер. Держите руль крепче, избегайте высоких скоростей."
    elif temp > 30:
        return "☀️ Жарко. Убедитесь, что кондиционер работает, пейте воду."
    else:
        return "🚗 Погода благоприятная. Соблюдайте правила дорожного движения."

# Функция получения погоды (текущая + прогноз на 5 дней)
def get_weather(msg):
    if msg.text == "❌ Отмена":
        return_to_main(msg)
        return
    if msg.text == "⬅️ Назад к регионам":
        sent_msg = bot.send_message(
            msg.chat.id,
            "Выберите регион:",
            reply_markup=region_menu
        )
        bot.register_next_step_handler(sent_msg, handle_region_selection)
        return
    city = msg.text.strip()
    valid_cities = list(city_mapping.keys())
    if city not in valid_cities:
        sent_msg = bot.send_message(
            msg.chat.id,
            "❗ Пожалуйста, выберите город из списка.",
            reply_markup=region_menu
        )
        bot.register_next_step_handler(sent_msg, handle_region_selection)
        return

    current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_mapping[city]},BY&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_mapping[city]},BY&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"

    try:
        current_response = requests.get(current_url, timeout=5)
        current_response.raise_for_status()
        current_data = current_response.json()
        weather_desc = current_data['weather'][0]['description'].capitalize()
        temp = current_data['main']['temp']
        wind_speed = current_data['wind']['speed']
        humidity = current_data['main']['humidity']
        current_advice = get_driving_advice(weather_desc, temp, wind_speed, humidity)

        forecast_response = requests.get(forecast_url, timeout=5)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        daily_forecasts = {}
        for forecast in forecast_data["list"]:
            date = datetime.fromtimestamp(forecast["dt"]).strftime("%Y-%m-%d")
            if date not in daily_forecasts and len(daily_forecasts) < 5:
                daily_forecasts[date] = {
                    "temp": forecast["main"]["temp"],
                    "weather": forecast["weather"][0]["description"].capitalize(),
                    "wind_speed": forecast["wind"]["speed"],
                    "humidity": forecast["main"]["humidity"]
                }

        response_text = f"☁️ Погода в {city}:\n\n"
        response_text += "📅 Сегодня:\n"
        response_text += f"Описание: {weather_desc}\n"
        response_text += f"Температура: {temp:.1f}°C\n"
        response_text += f"Ветер: {wind_speed} м/с\n"
        response_text += f"Влажность: {humidity}%\n"
        response_text += f"{current_advice}\n\n"

        response_text += "📅 Прогноз на 5 дней:\n"
        for date, info in daily_forecasts.items():
            advice = get_driving_advice(info["weather"], info["temp"], info["wind_speed"], info["humidity"])
            response_text += f"\n📅 {date}\n"
            response_text += f"Описание: {info['weather']}\n"
            response_text += f"Температура: {info['temp']:.1f}°C\n"
            response_text += f"Ветер: {info['wind_speed']} м/с\n"
            response_text += f"Влажность: {info['humidity']}%\n"
            response_text += f"{advice}\n"

        bot.send_message(
            msg.chat.id,
            response_text,
            reply_markup=main_menu
        )
        logging.info(f"Успешно получена погода для {city}: {weather_desc}, {temp}°C и прогноз на 5 дней")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса погоды для {city}: {e}")
        bot.send_message(
            msg.chat.id,
            f"Не удалось получить данные о погоде для {city}. Попробуйте позже.",
            reply_markup=main_menu
        )

@bot.message_handler(commands=['start'])
def welcome(message):
    db_handler.add_active_user(message.chat.id)
    username = message.from_user.first_name or message.from_user.username or "Пользователь"
    text = (
        f"🚗 <b>Привет, {username}!</b> Добро пожаловать в БЕЛТЕХОСМОТР! \n\n"
        "Я твой верный спутник на дороге: помогу подготовиться к техосмотру, избежать штрафов и быть в курсе всего, что важно для водителя в Беларуси! 🚘\n\n"
        "🔥 <b>Что я могу для тебя?</b>\n"
        "• Записаться на ТО за пару кликов\n"
        "• Узнать, как сэкономить на ремонте\n"
        "• Проверить погоду перед поездкой\n"
        "• Получить свежие советы и новости\n"
        "• Задать любой вопрос нашему умному ИИ\n\n"
        "👉 <b>Начни прямо сейчас!</b> Выбери нужную функцию в меню или нажми кнопки ниже!"
    )
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        telebot.types.InlineKeyboardButton("📝 Записаться на ТО", callback_data="start_booking"),
        telebot.types.InlineKeyboardButton("💬 FAQ", callback_data="show_faq")
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=main_menu
    )

@bot.message_handler(commands=['help'])
def help_message(message):
    db_handler.add_active_user(message.chat.id)
    username = message.from_user.first_name or message.from_user.username or "Пользователь"
    text = (
        f"ℹ️ <b>Как пользоваться ботом БЕЛТЕХОСМОТР, {username}</b>\n\n"
        "Я помогу вам быстро разобраться с техосмотром, страховкой и другими услугами. Вот как использовать мои функции:\n\n"
        "📋 <b>Команды:</b>\n"
        "• /start — начать работу с ботом\n"
        "• /help — получить эту справку\n"
        "• /info — узнать о компании БелТехосмотр\n"
        "• /history — просмотреть историю ваших действий\n"
        "• /update_news — обновить новости\n"
        "📱 <b>Популярные действия в меню:</b>\n"
        "• <b>📝 Запись на техосмотр</b>: Укажите телефон, авто и дату.\n"
        "• <b>💬 FAQ</b>: Ответы на вопросы о документах, штрафах и не только.\n"
        "• <b>🤖 Спросить ИИ</b>: Задайте вопрос, например, «Какие фары нужны для ТО?»\n\n"
        "💡 <b>Совет:</b> Используйте кнопки ниже для быстрого доступа или задайте вопрос в «🤖 Спросить ИИ»!"
    )
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        telebot.types.InlineKeyboardButton("📝 Записаться", callback_data="start_booking"),
        telebot.types.InlineKeyboardButton("💬 FAQ", callback_data="show_faq")
    )
    buttons.add(
        telebot.types.InlineKeyboardButton("📞 Контакты", callback_data="show_contacts")
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=buttons
    )

@bot.message_handler(commands=['info'])
def show_info(message):
    db_handler.add_active_user(message.chat.id)
    text = (
        "🏢 <b>О компании БЕЛТЕХОСМОТР</b>\n\n"
        "Мы — ваш надежный партнер в прохождении техосмотра и страховании в Беларуси!\n\n"
        "🔧 <b>Что мы делаем:</b>\n"
        "• Проверяем безопасность вашего авто: тормоза, фары, шины и другое.\n"
        "• Выдаем разрешение на эксплуатацию.\n"
        "• Предоставляем услуги страхования и консультации.\n"
        "• Используем современное оборудование для точной диагностики.\n\n"
        "📅 <b>Правила ТО в 2025 году:</b>\n"
        "• Новые авто (до 3 лет): раз в 3 года\n"
        "• Авто 3–10 лет: раз в 2 года\n"
        "• Авто старше 10 лет: ежегодно\n\n"
        "🌟 <b>Почему выбирают нас?</b>\n"
        "• Быстрое обслуживание без очередей\n"
        "• Прозрачные цены\n"
        "• Удобное расположение в Минске\n\n"
        "👉 Узнайте больше или свяжитесь с нами по кнопкам ниже!"
    )
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        telebot.types.InlineKeyboardButton("🌐 Сайт", url="https://gto.by/"),
        telebot.types.InlineKeyboardButton("📍 Карта", url="https://yandex.by/maps/-/CDuX9f~Y")
    )
    buttons.add(
        telebot.types.InlineKeyboardButton("📞 Контакты", callback_data="show_contacts")
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=buttons
    )

@bot.message_handler(commands=['update_news'])
def update_news(message):
    db_handler.add_active_user(message.chat.id)
    text = "⏳ <b>Обновляю новости...</b>\n\nПожалуйста, подождите, я загружаю самые свежие новости о техосмотре и авто в Беларуси."
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="HTML")
    try:
        db_handler.parse_news_from_gto()
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sent_msg.message_id,
            text=(
                "✅ <b>Новости успешно обновлены!</b>\n\n"
                "Теперь вы можете посмотреть актуальные новости в разделе «📰 Новости».\n\n"
                "👉 Хотите узнать, что нового?"
            ),
            parse_mode="HTML",
            reply_markup=telebot.types.InlineKeyboardMarkup().add(
                telebot.types.InlineKeyboardButton("📰 Посмотреть новости", callback_data="show_news")
            )
        )
    except Exception as e:
        logging.error(f"Ошибка при обновлении новостей: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sent_msg.message_id,
            text=(
                "❌ <b>Не удалось обновить новости</b>\n\n"
                "Попробуйте снова позже или свяжитесь с нами.\n\n"
                "👉 Вернитесь в меню или задайте вопрос ИИ!"
            ),
            parse_mode="HTML",
            reply_markup=telebot.types.InlineKeyboardMarkup().add(
                telebot.types.InlineKeyboardButton("🤖 Спросить ИИ", callback_data="start_ai_mode")
            )
        )

# Обработчик inline-кнопок для команд
@bot.callback_query_handler(func=lambda call: call.data in ["start_booking", "show_faq", "show_contacts", "open_calculator", "show_news", "start_ai_mode"])
def handle_command_actions(call):
    bot.answer_callback_query(call.id)
    if call.data == "start_booking":
        text = (
            "🚗 <b>Запишитесь на техосмотр быстро и удобно!</b>\n\n"
            "С БЕЛТЕХОСМОТР ваш автомобиль всегда готов к дороге! "
            "Перейдите на наш официальный сайт, чтобы выбрать удобное время и станцию для прохождения техосмотра. "
            "Мы обеспечим профессиональную проверку и комфортное обслуживание.\n\n"
            "👉 <b>Записаться сейчас:</b>"
        )
        buttons = telebot.types.InlineKeyboardMarkup()
        buttons.add(telebot.types.InlineKeyboardButton("🌐 Перейти на сайт", url="https://gto.by/"))
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    elif call.data == "show_faq":
        bot.send_message(
            call.message.chat.id,
            "❓ <b>Часто задаваемые вопросы</b>\n\nВыберите интересующий вас вопрос из меню ниже 👇",
            parse_mode="HTML",
            reply_markup=faq_menu
        )
    elif call.data == "show_contacts":
        text = (
            "📞 <b>Свяжитесь с БЕЛТЕХОСМОТР</b>\n\n"
            "📍 <b>Адрес:</b> г. Минск, ул. Платонова, 22а\n"
            "📱 <b>Телефон:</b> +375 (17) 311-09-80\n"
            "✉️ <b>Email:</b> info@gto.by\n"
            "🕒 <b>Режим работы:</b>\n"
            "   Пн–Чт: 8:30–17:30\n"
            "   Пт: 8:30–16:15\n"
            "   Обед: 12:15–13:00\n"
            "   Сб–Вс: выходной\n\n"
            "🌐 Посетите наш сайт или найдите нас на карте по кнопкам ниже 👇"
        )
        buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
        buttons.add(
            telebot.types.InlineKeyboardButton("🌐 Сайт", url="https://gto.by/"),
            telebot.types.InlineKeyboardButton("📍 Карта", url="https://yandex.by/maps/-/CDuX9f~Y")
        )
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    elif call.data == "show_news":
        bot.send_message(
            call.message.chat.id,
            "⏳ Загружаю новости...",
            reply_markup=main_menu
        )
        send_news(call.message.chat.id, db_handler.get_all_news(), "Свежие новости")
    elif call.data == "start_ai_mode":
        user_states[call.message.chat.id] = {'ai_mode': True}
        bot.send_message(
            call.message.chat.id,
            "🤖 <b>ИИ-помощник активирован!</b>\n\nЗадайте любой вопрос, например, «Какие документы нужны для ТО?»\n"
            "Для возврата в меню нажмите «⬅️ Назад в главное меню».",
            parse_mode="HTML",
            reply_markup=ai_mode_menu
        )

# Возврат в главное меню
@bot.message_handler(func=lambda msg: msg.text in ["⬅️ Назад в главное меню", "❌ Отмена"])
def return_to_main(msg):
    if msg.chat.id in user_states:
        user_states[msg.chat.id]['ai_mode'] = False
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(msg.chat.id, "Вы в главном меню.", reply_markup=main_menu)

# Обработчик отзыва
@bot.message_handler(func=lambda msg: msg.text == "✨ Оставить отзыв")
def start_feedback(msg):
    db_handler.add_active_user(msg.chat.id)
    sent_msg = bot.send_message(
        msg.chat.id,
        "Оцените нашу работу, выбрав звезды ⭐",
        reply_markup=feedback_menu
    )
    bot.register_next_step_handler(sent_msg, handle_feedback_rating)

def handle_feedback_rating(message):
    if message.text == "❌ Отмена":
        return_to_main(message)
        return
    rating = None if message.text == "✍️ Оставить без оценки" else message.text
    sent_msg = bot.send_message(
        message.chat.id,
        "Спасибо! Напишите ваш отзыв:",
        reply_markup=telebot.types.ForceReply(selective=True)
    )
    bot.register_next_step_handler(sent_msg, save_feedback, rating)

def save_feedback(message, rating):
    feedback = message.text.strip()
    username = message.from_user.first_name or message.from_user.username or "Аноним"
    db_handler.add_feedback(message.chat.id, feedback, rating, username)
    bot.send_message(message.chat.id, "✅ Отзыв сохранен! Спасибо за ваш отзыв!", reply_markup=main_menu)

# Обработчик раздела новостей
@bot.message_handler(func=lambda msg: msg.text == "📰 Новости")
def show_news_menu(msg):
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(msg.chat.id, "Выберите действие:", reply_markup=news_menu)

# Отправка списка новостей
def send_news(chat_id, news_list, title):
    if not news_list:
        bot.send_message(chat_id, f"📭 {title} не найдены. Попробуйте обновить новости через /update_news.", reply_markup=main_menu)
        return
    bot.send_message(chat_id, f"<b>🔎 {title}:</b>", parse_mode="HTML")
    for news in news_list[:10]:
        if news['content'] == 'Контент недоступен' or not news['content']:
            preview = "Полный текст новости доступен по ссылке."
        else:
            preview = news['content'][:200] + '...' if len(news['content']) > 200 else news['content']
        buttons = telebot.types.InlineKeyboardMarkup()
        buttons.add(telebot.types.InlineKeyboardButton("📖 Читать", callback_data=f"read_{news['id']}"))
        text = f"<b>{news['title']}</b>\n<i>📅 {news['date']}</i>\n\n{preview}"
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=buttons)

# Обработчик свежих новостей
@bot.message_handler(func=lambda msg: msg.text == "📰 Свежие новости")
def show_latest_news(msg):
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(msg.chat.id, "⏳ Загружаю новости...", reply_markup=main_menu)
    send_news(msg.chat.id, db_handler.get_all_news(), "Свежие новости")

# Обработчик полной новости
@bot.callback_query_handler(func=lambda call: call.data.startswith('read_'))
def show_full_news(call):
    db_handler.add_active_user(call.message.chat.id)
    bot.answer_callback_query(call.id, "Загружаю...")
    news_id = int(call.data.replace('read_', ''))
    news = next((n for n in db_handler.get_all_news() if n['id'] == news_id), None)
    if not news:
        bot.send_message(call.message.chat.id, "❌ Новость не найдена.", reply_markup=main_menu)
        return
    content = news['content'] if news['content'] != 'Контент недоступен' else "Полный текст новости доступен по ссылке."
    text = f"<b>{news['title']}</b>\n<i>📅 {news['date']}</i>\n\n{content}\n\n🔗 <b>Источник:</b> {news['url']}"
    if len(text) > 4096:
        for part in range(0, len(text), 4096):
            bot.send_message(call.message.chat.id, text[part:part + 4096], parse_mode="HTML", disable_web_page_preview=True)
    else:
        bot.send_message(call.message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)

# Поиск новостей по датам
@bot.message_handler(func=lambda msg: msg.text == "📅 Новости за период")
def start_period_search(msg):
    db_handler.add_active_user(msg.chat.id)
    sent_msg = bot.send_message(msg.chat.id, "Введите начальную дату (ДД.ММ.ГГГГ):", reply_markup=cancel_menu)
    bot.register_next_step_handler(sent_msg, handle_start_date)

def handle_start_date(message):
    if message.text == "❌ Отмена":
        return_to_main(message)
        return
    if not check_search_date(message.text):
        sent_msg = bot.send_message(message.chat.id, "❗ Формат даты: ДД.ММ.ГГГГ.", reply_markup=cancel_menu)
        bot.register_next_step_handler(sent_msg, handle_start_date)
        return
    sent_msg = bot.send_message(message.chat.id, "Введите конечную дату (ДД.ММ.ГГГГ):", reply_markup=cancel_menu)
    bot.register_next_step_handler(sent_msg, handle_end_date, message.text)

def handle_end_date(message, start_date):
    if message.text == "❌ Отмена":
        return_to_main(message)
        return
    end_date = message.text
    if not check_search_date(end_date):
        sent_msg = bot.send_message(message.chat.id, "❗ Формат даты: ДД.ММ.ГГГГ.", reply_markup=cancel_menu)
        bot.register_next_step_handler(sent_msg, handle_end_date, start_date)
        return
    if datetime.strptime(start_date, '%d.%m.%Y') > datetime.strptime(end_date, '%d.%m.%Y'):
        sent_msg = bot.send_message(message.chat.id, "❗ Начальная дата не может быть позже конечной.", reply_markup=cancel_menu)
        bot.register_next_step_handler(sent_msg, handle_start_date)
        return
    bot.send_message(message.chat.id, "⏳ Ищу новости...", reply_markup=main_menu)
    send_news(message.chat.id, db_handler.get_news_by_period(start_date, end_date), f"Новости с {start_date} по {end_date}")

# Поиск новостей по ключевому слову
@bot.message_handler(func=lambda msg: msg.text == "🔍 Поиск новостей")
def start_keyword_search(msg):
    db_handler.add_active_user(msg.chat.id)
    sent_msg = bot.send_message(msg.chat.id, "Введите ключевое слово:", reply_markup=cancel_menu)
    bot.register_next_step_handler(sent_msg, handle_keyword_search)

def handle_keyword_search(message):
    if message.text == "❌ Отмена":
        return_to_main(message)
        return
    keyword = message.text.strip()
    if not keyword:
        sent_msg = bot.send_message(message.chat.id, "❗ Запрос не может быть пустым.", reply_markup=cancel_menu)
        bot.register_next_step_handler(sent_msg, handle_keyword_search)
        return
    bot.send_message(message.chat.id, f"⏳ Ищу «{keyword}»...", reply_markup=main_menu)
    send_news(message.chat.id, db_handler.search_news(keyword), f"Результаты по «{keyword}»")

# Обработчик FAQ
@bot.message_handler(func=lambda msg: msg.text == "💬 FAQ")
def show_faq(msg):
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(
        msg.chat.id,
        "❓ <b>Часто задаваемые вопросы</b>\n\nВыберите интересующий вас вопрос из меню ниже 👇",
        parse_mode="HTML",
        reply_markup=faq_menu
    )

@bot.message_handler(func=lambda msg: msg.text in [
    "📄 Документы на ТО", "❓ ТО без страховки", "⚠️ Штрафы за просрочку", "💸 Стоимость ТО",
    "📆 Периодичность ТО", "🔄 Изменить запись", "🚫 Если не прошел ТО", "🧾 Онлайн-оплата"
])
def answer_faq(msg):
    answers = {
        "📄 Документы на ТО": (
            "📑 <b>Какие документы нужны для техосмотра?</b>\n\n"
            "Для прохождения техосмотра в Беларуси вам потребуются:\n"
            "✅ Паспорт или водительское удостоверение — для подтверждения личности.\n"
            "✅ Свидетельство о регистрации ТС (техпаспорт) — документ на автомобиль.\n"
            "✅ Действующий полис обязательного страхования («Автогражданка»).\n"
            "✅ Квитанция об оплате госпошлины за техосмотр.\n\n"
            "💡 <i>Совет:</i> Проверьте наличие аптечки, огнетушителя и знака аварийной остановки — их отсутствие может стать причиной отказа. "
            "Запишитесь на ТО через меню «📝 Запись на техосмотр»!"
        ),
        "❓ ТО без страховки": (
            "🛑 <b>Можно ли пройти техосмотр без страховки?</b>\n\n"
            "В Республике Беларусь техосмотр без действующего полиса обязательного страхования («Автогражданка») невозможен. "
            "Согласно законодательству, страховка является обязательным условием для допуска автомобиля к эксплуатации.\n\n"
            "📌 <b>Что делать?</b>\n"
            "1. Оформите полис «Автогражданка» в любой страховой компании.\n"
            "2. Убедитесь, что он действителен на момент прохождения ТО.\n"
            "3. Принесите полис на станцию техосмотра.\n\n"
            "💡 Подробности об оформлении страховки вы найдете в разделе «📄 О страховке»."
        ),
        "⚠️ Штрафы за просрочку": (
            "👮 <b>Какие штрафы за просроченный техосмотр?</b>\n\n"
            "Вождение автомобиля без действующего техосмотра влечет административную ответственность:\n"
            "🚨 Штраф: от 1 до 3 базовых величин (в 2025 году — до 120 BYN).\n"
            "🚨 При повторном нарушении: штраф до 5 базовых величин или лишение прав.\n"
            "🚨 Аннулирование страховки: без ТО страховка становится недействительной.\n"
            "🚨 Снятие авто с регистрации: в случае систематических нарушений.\n\n"
            "💡 <i>Совет:</i> Пройдите техосмотр вовремя, чтобы избежать проблем. "
            "Используйте «📝 Запись на техосмотр» для удобной записи!"
        ),
        "💸 Стоимость ТО": (
            "💰 <b>Сколько стоит техосмотр?</b>\n\n"
            "Стоимость техосмотра в Беларуси зависит от типа транспортного средства:\n"
            "🚗 Легковые авто: от 35 до 50 BYN.\n"
            "🚚 Грузовые авто: от 50 до 80 BYN.\n"
            "🚌 Автобусы: от 60 до 100 BYN.\n"
            "🏍 Мотоциклы: около 20–30 BYN.\n\n"
            "📌 <b>Факторы, влияющие на цену:</b>\n"
            "- Тип двигателя (дизель/бензин/электро/газ).\n"
            "- Год выпуска авто (старые авто могут требовать доп. проверок).\n"
            "- Необходимость повторного ТО (если не прошли с первого раза).\n\n"
            "💡 Для точной стоимости используйте «💼 Калькулятор ТО» в меню!"
        ),
        "📆 Периодичность ТО": (
            "📅 <b>Как часто нужно проходить техосмотр?</b>\n\n"
            "В Республике Беларусь периодичность техосмотра зависит от возраста автомобиля:\n"
            "🚗 Новые авто (до 3 лет): раз в 3 года.\n"
            "🚗 Авто от 3 до 10 лет: раз в 2 года.\n"
            "🚗 Авто старше 10 лет: ежегодно.\n"
            "🚌 Автобусы и такси: каждые 6 месяцев.\n\n"
            "📌 <b>Примечание:</b> Срок отсчитывается от даты выдачи разрешения на допуск ТС к эксплуатации. "
            "Проверьте дату последнего ТО в техпаспорте.\n\n"
            "💡 Запланируйте визит заранее через «📝 Запись на техосмотр»!"
        ),
        "🔄 Изменить запись": (
            "🔄 <b>Как изменить или отменить запись на ТО?</b>\n\n"
            "Если вам нужно изменить время или отменить запись на техосмотр:\n"
            "1. 📱 Позвоните по номеру <b>+375 (17) 311-09-80</b>.\n"
            "2. Сообщите оператору ваши данные (телефон, дату записи, авто).\n"
            "3. Укажите новое удобное время или отмените запись.\n\n"
            "💻 <b>Онлайн:</b> Измените запись через личный кабинет на сайте <a href='https://gto.by/'>gto.by</a> (если регистрировались).\n\n"
            "💡 <i>Совет:</i> Свяжитесь с нами заранее, чтобы выбрать удобное время. "
            "Посетите раздел «📞 Контакты» для связи."
        ),
        "🚫 Если не прошел ТО": (
            "🛠️ <b>Что делать, если автомобиль не прошел техосмотр?</b>\n\n"
            "Если ваш автомобиль не прошел техосмотр:\n"
            "1. 📋 Получите диагностическую карту с указанием неисправностей.\n"
            "2. 🔧 Устраните выявленные проблемы (например, замените изношенные детали, отрегулируйте фары).\n"
            "3. 🔄 Вернитесь на станцию в течение <b>20 дней</b> для повторной проверки.\n"
            "4. 💰 Повторный техосмотр обойдется дешевле (проверяются только устраненные неисправности).\n\n"
            "💡 <i>Совет:</i> Перед повторным визитом убедитесь, что все замечания устранены. "
            "Запишитесь через «📝 Запись на техосмотр»!"
        ),
        "🧾 Онлайн-оплата": (
            "✅ <b>Как оплатить техосмотр онлайн?</b>\n\n"
            "Оплату техосмотра в Беларуси можно провести через систему ЕРИП или на сайте:\n"
            "1. 💻 Зайдите на сайт <a href='https://gto.by/pay/?step=1'>gto.by</a> и выберите «Оплата».\n"
            "2. 🏦 Через ЕРИП: найдите раздел «БЕЛТЕХОСМОТР», введите номер ТС и оплатите госпошлину.\n"
            "3. 💳 Используйте банковскую карту или мобильный банкинг.\n\n"
            "📌 <b>Важно:</b> Сохраните квитанцию об оплате — она потребуется на станции ТО.\n\n"
            "💡 Рассчитайте точную стоимость в «💼 Калькулятор ТО» и оплатите сразу!"
        )
    }
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    if msg.text == "💸 Стоимость ТО":
        pass
    elif msg.text == "🔄 Изменить запись" or msg.text == "🚫 Если не прошел ТО":
        buttons.add(telebot.types.InlineKeyboardButton("📝 Записаться", callback_data="start_booking"))
    elif msg.text == "🧾 Онлайн-оплата":
        buttons.add(telebot.types.InlineKeyboardButton("💳 Оплатить", url="https://gto.by/pay/?step=1"))
    elif msg.text == "❓ ТО без страховки":
        buttons.add(telebot.types.InlineKeyboardButton("📄 О страховке", callback_data="show_insurance"))
    elif msg.text == "📄 Документы на ТО":
        buttons.add(telebot.types.InlineKeyboardButton("📝 Записаться", callback_data="start_booking"))
    bot.send_message(
        msg.chat.id,
        answers[msg.text],
        parse_mode="HTML",
        reply_markup=buttons,
        disable_web_page_preview=True
    )

# Обработчик inline-кнопок для FAQ
@bot.callback_query_handler(func=lambda call: call.data in ["start_booking", "show_insurance"])
def handle_faq_actions(call):
    bot.answer_callback_query(call.id)
    if call.data == "start_booking":
        buttons = telebot.types.InlineKeyboardMarkup()
        buttons.add(telebot.types.InlineKeyboardButton("🌐 Перейти на сайт для записи", url="https://gto.by/"))
        bot.send_message(
            call.message.chat.id,
            "🚗 Перейдите на сайт для записи на техосмотр:",
            parse_mode="HTML",
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    elif call.data == "show_insurance":
        bot.send_message(
            call.message.chat.id,
            "🚗 <b>Страхование — ваша защита на дороге</b>\n\n"
            "Страховка («Автогражданка» или КАСКО) — это не просто формальность, а важная гарантия, которая:\n\n"
            "🛡️ <b>Защищает ваш бюджет</b> — покрывает убытки при ДТП, спасая от крупных расходов.\n"
            "⚖️ <b>Обязательна по закону</b> — без полиса «Автогражданки» управлять автомобилем <u>запрещено</u>.\n"
            "🏥 <b>Помогает в критических ситуациях</b> — оплачивает лечение пострадавших в аварии.\n"
            "🔧 <b>Покрывает ремонт</b> — КАСКО компенсирует ущерб вашему авто, даже если ДТП произошло по вашей вине.\n\n"
            "💡 <i>Основные виды страхования в Беларуси:</i>\n"
            "• <b>«Автогражданка»</b> — обязательное страхование (возмещает ущерб третьим лицам).\n"
            "• <b>КАСКО</b> — добровольная страховка с полной защитой вашего автомобиля.\n\n"
            "📌 Подробнее о тарифах и условиях читайте на <a href='https://gto.by/'>нашем сайте</a>",
            parse_mode="HTML",
            reply_markup=main_menu,
            disable_web_page_preview=True
        )


# Обработчик кнопки "Запись на техосмотр"
@bot.message_handler(func=lambda msg: msg.text == "📝 Запись на техосмотр")
def start_booking(msg):
    text = (
        "🚗 <b>Запишитесь на техосмотр быстро и удобно!</b>\n\n"
        "С БЕЛТЕХОСМОТР ваш автомобиль всегда готов к дороге! "
        "Перейдите на наш официальный сайт, чтобы выбрать удобное время и станцию для прохождения техосмотра. "
        "Мы обеспечим профессиональную проверку и комфортное обслуживание.\n\n"
        "👉 <b>Записаться сейчас:</b>"
    )
    buttons = telebot.types.InlineKeyboardMarkup()
    buttons.add(telebot.types.InlineKeyboardButton("🌐 Перейти на сайт", url="https://gto.by/diagnostic-stations/"))
    bot.send_message(
        msg.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=buttons,
        disable_web_page_preview=True
    )

# Обработчик inline-кнопок для записи на техосмотр
@bot.callback_query_handler(func=lambda call: call.data == "start_booking")
def handle_command_actions(call):
    bot.answer_callback_query(call.id)
    buttons = telebot.types.InlineKeyboardMarkup()
    buttons.add(telebot.types.InlineKeyboardButton("🌐 Перейти на сайт для записи", url="https://gto.by/"))
    bot.send_message(
        call.message.chat.id,
        "🚗 Перейдите на сайт для записи на техосмотр:",
        parse_mode="HTML",
        reply_markup=buttons,
        disable_web_page_preview=True
    )


# Услуги
@bot.message_handler(func=lambda msg: msg.text == "🛠️ Услуги")
def show_services(msg):
    db_handler.add_active_user(msg.chat.id)
    text = """
🔧 <b>Услуги БелТехосмотр</b>

🚗 <b>Основные услуги:</b>
• Гостехосмотр
• Разрешение на эксплуатацию
• Сертификат ЕКМТ
• Возврат средств за неоказанные услуги

📋 <b>МСТО:</b>
• Допуск для опасных грузов
• Электронный паспорт ТС
• Изменение документов
• Диагностика для станций
• Информация о ТС

🛠️ <b>СТО:</b>
• Аренда помещений
• Обслуживание оборудования
• Техосмотр без очередей
• Хранение шин
• Заправка кондиционеров
• Диагностика, шиномонтаж
• Автомойка
• Зарядка электромобилей

⚡ <b>Дополнительно:</b>
• Обслуживание тахографов
• Консультации
• Помощь со страховкой
• Экспресс-диагностика
"""
    buttons = telebot.types.InlineKeyboardMarkup()
    buttons.add(telebot.types.InlineKeyboardButton("📝 Записаться", callback_data="service_booking"))
    buttons.add(telebot.types.InlineKeyboardButton("💰 Стоимость", callback_data="service_price"))
    bot.send_message(msg.chat.id, text, parse_mode="HTML", reply_markup=buttons)


@bot.callback_query_handler(func=lambda call: call.data in ["service_booking", "service_price"])
def handle_service_action(call):
    db_handler.add_active_user(call.message.chat.id)
    bot.answer_callback_query(call.id)
    if call.data == "service_booking":
        bot.send_message(
            call.message.chat.id,
            "📝 Выберите 'Запись на техосмотр' в меню или позвоните!",
            reply_markup=main_menu
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "💰 Используйте 'Калькулятор ТО' или уточните по телефону!",
            reply_markup=main_menu
        )


# О страховке
@bot.message_handler(func=lambda msg: msg.text == "📄 О страховке")
def show_insurance(msg):
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(
        msg.chat.id,
        "🚗 <b>Страхование — ваша защита на дороге</b>\n\n"
        "Страховка («Автогражданка» или КАСКО) — это не просто формальность, а важная гарантия, которая:\n\n"
        "🛡️ <b>Защищает ваш бюджет</b> — покрывает убытки при ДТП, спасая от крупных расходов.\n"
        "⚖️ <b>Обязательна по закону</b> — без полиса «Автогражданки» управлять автомобилем <u>запрещено</u>.\n"
        "🏥 <b>Помогает в критических ситуациях</b> — оплачивает лечение пострадавших в аварии.\n"
        "🔧 <b>Покрывает ремонт</b> — КАСКО компенсирует ущерб вашему авто, даже если ДТП произошло по вашей вине.\n\n"
        "💡 <i>Основные виды страхования в Беларуси:</i>\n"
        "• <b>«Автогражданка»</b> — обязательное страхование (возмещает ущерб третьим лицам).\n"
        "• <b>КАСКО</b> — добровольная страховка с полной защитой вашего автомобиля.\n\n"
        "📌 Подробнее о тарифах и условиях читайте на <a href='https://gto.by/'>нашем сайте</a>",
        reply_markup=main_menu,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# О компании
@bot.message_handler(func=lambda msg: msg.text == "ℹ️ О компании")
def show_company_info(msg):
    db_handler.add_active_user(msg.chat.id)
    text = (
        "🏢 <b>БЕЛТЕХОСМОТР — ваш надежный партнер на дороге!</b>\n\n"
        "Мы — лидеры в области техосмотра и страхования в Беларуси, помогая тысячам водителей сохранять свои автомобили в идеальном состоянии.\n\n"
        "🔧 <b>Наши услуги:</b>\n"
        "• <b>Техосмотр:</b> Проверяем тормоза, фары, шины, аптечку, огнетушитель и другие элементы для вашей безопасности.\n"
        "• <b>Страхование:</b> Оформляем «Автогражданку» и КАСКО быстро и удобно.\n"
        "• <b>Диагностика:</b> Используем современное оборудование для точной проверки авто.\n"
        "• <b>Дополнительно:</b> Шиномонтаж, автомойка, зарядка электромобилей и консультации.\n\n"
        "📅 <b>Правила ТО в 2025 году:</b>\n"
        "• Новые авто (до 3 лет): раз в 3 года\n"
        "• Авто 3–10 лет: раз в 2 года\n"
        "• Авто старше 10 лет: ежегодно\n"
        "• Автобусы и такси: каждые 6 месяцев\n\n"
        "🌟 <b>Почему выбирают нас?</b>\n"
        "✅ Быстрое обслуживание без очередей\n"
        "✅ Прозрачные цены и никаких скрытых платежей\n"
        "✅ Удобное расположение: г. Минск, ул. Платонова, 22а\n"
        "✅ Профессиональная команда и современные технологии\n\n"
        "👉 Готовы к техосмотру? Воспользуйтесь нашими услугами или свяжитесь с нами по кнопкам ниже!"
    )
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        telebot.types.InlineKeyboardButton("🌐 Сайт", url="https://gto.by/"),
        telebot.types.InlineKeyboardButton("📍 Карта", url="https://yandex.by/maps/-/CDuX9f~Y")
    )
    buttons.add(
        telebot.types.InlineKeyboardButton("📝 Записаться на ТО", callback_data="start_booking")
    )
    buttons.add(
        telebot.types.InlineKeyboardButton("💬 FAQ", callback_data="show_faq"),
        telebot.types.InlineKeyboardButton("📞 Контакты", callback_data="show_contacts")
    )
    bot.send_message(
        msg.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=buttons,
        disable_web_page_preview=True
    )


# Контакты
@bot.message_handler(func=lambda msg: msg.text == "📞 Контакты")
def show_contacts(msg):
    db_handler.add_active_user(msg.chat.id)
    text = (
        "📞 <b>Свяжитесь с БЕЛТЕХОСМОТР</b>\n\n"
        "📍 <b>Адрес:</b> г. Минск, ул. Платонова, 22а\n"
        "📱 <b>Телефон:</b> +375 (17) 311-09-80\n"
        "✉️ <b>Email:</b> info@gto.by\n"
        "🌐 Посетите наш сайт или найдите нас на карте по кнопкам ниже 👇"
    )
    buttons = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons.add(
        telebot.types.InlineKeyboardButton("🌐 Сайт", url="https://gto.by/"),
        telebot.types.InlineKeyboardButton("📍 Карта", url="https://yandex.by/maps/-/CDuX9f~Y")
    )
    bot.send_message(
        msg.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=buttons,
        disable_web_page_preview=True
    )


# ИИ-помощник
@bot.message_handler(func=lambda msg: msg.text == "🤖 Спросить ИИ")
def start_ai_mode(message):
    db_handler.add_active_user(message.chat.id)
    user_states[message.chat.id] = {'ai_mode': True}
    bot.send_message(
        message.chat.id,
        "Я готов ответить на ваши вопросы. Что вас интересует? "
        "Для возврата в основное меню нажмите кнопку '⬅️ Назад в главное меню'.",
        reply_markup=ai_mode_menu
    )


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('ai_mode') == True)
def handle_ai_mode_messages(message):
    db_handler.add_active_user(message.chat.id)
    chat_id = message.chat.id
    if message.text == "⬅️ Назад в главное меню":
        if chat_id in user_states:
            user_states[chat_id]['ai_mode'] = False
        return_to_main(message)
        return
    lower_text = message.text.lower()
    if any(phrase in lower_text for phrase in
           ["спасибо", "благодарю", "мерси", "thanks", "всё", "все", "до свидания", "пока"]):
        return
    bot.send_chat_action(chat_id, 'typing')
    ai_response = get_ai_response(message.text)
    if ai_response and ai_response.strip():
        bot.send_message(chat_id, ai_response, reply_markup=ai_mode_menu)


# Обработка неизвестных сообщений
@bot.message_handler(func=lambda msg: True)
def unknown_message(msg):
    db_handler.add_active_user(msg.chat.id)
    bot.send_message(msg.chat.id, "⚠️ Выберите пункт меню.", reply_markup=main_menu)


# Обработчик оплаты
@bot.callback_query_handler(func=lambda call: call.data == "pay")
def process_payment(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
                     "🔗 Вы были перенаправлены на сайт для оплаты. После оплаты вернитесь в меню.",
                     reply_markup=main_menu)


if __name__ == '__main__':
    logging.info("Бот запущен...")
    db_handler.create_tables()
    bot.polling(none_stop=True, skip_pending=True)
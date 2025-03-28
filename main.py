import requests
import logging
import time
import random
import os
from collections import deque
from pathlib import Path
from dotenv import load_dotenv
import telebot
from telebot import types

# Загрузка переменных окружения
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LEAKCHECK_API_KEY = os.getenv("LEAKCHECK_API_KEY")
API_URL = "https://leakcheck.io/api/public"

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

request_timestamps = deque(maxlen=1)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Загрузка словарей
LOCAL_DICTIONARIES = [
    "rockyou2021.txt",
    "seclists.txt",
    "probable.txt",
    "haklistgen.txt"
]

# Генератор паролей
def generate_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

# Проверка в LeakCheck API
def make_api_request(query: str) -> dict:
    current_time = time.time()
    if request_timestamps:
        elapsed = current_time - request_timestamps[0]
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
    request_timestamps.append(time.time())

    params = {
        "key": LEAKCHECK_API_KEY,
        "check": query,
        "type": "email" if "@" in query else "login"
    }
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

# Проверка в локальных словарях
def search_in_local_files(query):
    results = []
    query_lower = query.lower()
    for filename in LOCAL_DICTIONARIES:
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if query_lower in line.lower():
                        results.append((filename, i + 1, line.strip()))
                        break
        except Exception as e:
            logger.warning(f"Не удалось прочитать {filename}: {e}")
            continue
    return results

# Форматирование локальных результатов
def format_local_results(matches):
    if not matches:
        return "\n❌ В локальных базах ничего не найдено."
    response = ["\n📂 Найдено в локальных базах:"]
    for file, line_num, line in matches:
        response.append(f"\n📄 {file} (строка {line_num}):\n🔸 {line}")
    return "\n".join(response)

# Форматирование ответа LeakCheck
def format_leak_results(data: dict) -> str:
    if not data:
        return "\n❌ Ошибка: не получены данные от LeakCheck API"
    if not data.get("success", False):
        return f"\n❌ Ошибка API: {data.get('error', 'Неизвестная ошибка')}"
    found_count = data.get("found", 0)
    if found_count == 0:
        return "\n✅ В LeakCheck утечек не найдено."

    sources = data.get("sources", [])
    results = []
    for source in sources:
        name = source.get("name", "Неизвестный источник")
        date = source.get("date", "Дата неизвестна")
        lines = source.get("lines", "N/A")
        results.append(
            f"🔍 Источник: {name}\n📅 Дата: {date}\n📊 Записей: {lines}"
        )
    return f"\n⚠️ Найдено в LeakCheck: {found_count} утечек\n\n" + "\n\n".join(results)

# Главное меню с inline-кнопками
def get_inline_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 Новая проверка", callback_data="new_check"),
        types.InlineKeyboardButton("🔐 Сгенерировать пароль", callback_data="gen_pass"),
        types.InlineKeyboardButton("📤 Поделиться ботом", switch_inline_query="LeakGuard — проверь свои данные на утечки!")
    )
    return markup

# Обработка входящего запроса
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Что ты хочешь проверить? Отправь: \n\n🔹 Имя\n🔹 Почту\n🔹 Никнейм\n🔹 Пароль\n🔹 Название компании",
        reply_markup=get_inline_main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "new_check")
def callback_new_check(call):
    bot.send_message(
        call.message.chat.id,
        "Что ты хочешь проверить? Отправь: \n\n🔹 Имя\n🔹 Почту\n🔹 Никнейм\n🔹 Пароль\n🔹 Название компании",
        reply_markup=get_inline_main_menu()
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "gen_pass")
def callback_generate_password(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for length in [8, 12, 16, 20]:
        markup.add(types.InlineKeyboardButton(f"🔐 Сгенерировать {length} символов", callback_data=f"gen_pass_{length}"))
    bot.send_message(
        call.message.chat.id,
        "Выбери длину пароля:",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gen_pass_"))
def callback_generate_custom_length_password(call):
    length_str = call.data.split("_")[-1]
    try:
        length = int(length_str)
        password = generate_password(length)
        bot.send_message(
            call.message.chat.id,
            f"🔐 Вот надёжный пароль ({length} символов): `{password}`",
            parse_mode="Markdown",
            reply_markup=get_inline_main_menu()
        )
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка генерации пароля.")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_query(message):
    query = message.text.strip()
    if not query or len(query) < 3:
        bot.reply_to(message, "⚠️ Слишком короткий запрос. Попробуй ещё раз.")
        return

    status_msg = bot.send_message(message.chat.id, "🔎 Проверяю, подожди секундочку...")

    try:
        start_time = time.time()

        local_matches = search_in_local_files(query)
        response = format_local_results(local_matches)

        api_response = make_api_request(query)
        response += format_leak_results(api_response)

        if not local_matches and (not api_response or not api_response.get("found")):
            response = "✅ Утечек не найдено. Всё чисто!"

        # Дополнительная логика для паролей
        if ' ' not in query and len(query) >= 6 and query.isascii():
            freq_count = sum(1 for _, _, line in local_matches if query.lower() in line.lower())
            if freq_count >= 5:
                response += f"⚠️ Пароль слишком часто встречается! Рекомендуется сменить./n🔐 Новый пароль: `{generate_password()}`"
            elif freq_count > 0:
                response += "ℹ️ Пароль найден в базе, но не слишком популярен. Лучше заменить."
            else:
                response += "✅ Этот пароль встречается редко."

        elapsed = time.time() - start_time
        if elapsed > 15:
            response = "⚠️ Проверка заняла слишком много времени. Попробуй ещё раз позже."

    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        response = "❌ Произошла ошибка при проверке. Попробуй снова."

    bot.send_message(chat_id=message.chat.id, text=response, reply_markup=get_inline_main_menu())

# Запуск бота
if __name__ == '__main__':
    logger.info("Бот запущен...")
    bot.polling(none_stop=True)

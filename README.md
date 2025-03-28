# SafePass AI (Pet Project)

SafePass AI — это Telegram-бот, который помогает пользователям:
- Проверить логины, email, пароли и ники на утечки в утилите LeakCheck
- Выполнять локальный поиск по известным словарям утёкших паролей
- Генерировать безопасные пароли

## 🔧 Возможности:
- Проверка по API LeakCheck
- Поиск в локальных словарях (rockyou2021, seclists и др.)
- Генерация надёжных паролей по выбору длины
- Удобное Telegram-интерфейс с inline-кнопками

## 🚀 Запуск

### 1. Установите зависимости:
```bash
pip install -r requirements.txt
```

### 2. Создайте `.env` файл:
Скопируйте `.env.example` и добавьте свои ключи:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
LEAKCHECK_API_KEY=your_api_key
```

### 3. Запустите бота:
```bash
python main.py
```

## 📁 Структура
- `main.py` — основной код Telegram-бота
- `rockyou2021.txt`, `seclists.txt` — словари утёкших паролей
- `.env` — переменные окружения (НЕ загружать в GitHub)

## 🛡 Безопасность
⚠️ Никогда не загружайте `.env` с настоящими токенами в публичные репозитории.

---

Разработано с ❤️ командой Pet
# 📱 Настройка Mini App в Telegram через @BotFather

## 🎯 Что нужно сделать:

### 1. Создайте бота (если еще не создан)

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Введите название бота (например: "Hotel Bot")
4. Введите username бота (например: "your_hotel_bot")
5. **СОХРАНИТЕ ТОКЕН** - он понадобится для файла `.env`

### 2. Создайте Mini App

1. Отправьте `/newapp` боту [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота из списка
3. Введите название Mini App: `Hotel Bot`
4. Введите описание: `Система автоматизации отелей`
5. Загрузите иконку (512x512 PNG) - можно использовать любую подходящую иконку
6. **Введите URL Mini App:**
   - Для локального тестирования: `http://localhost:8000`
   - Для продакшена: `https://your-domain.com`

### 3. Настройте бота для Mini App

1. Отправьте `/setmenubutton` боту [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота
3. Введите текст кнопки: `📱 Mini App`
4. Введите URL: тот же URL, что указали при создании Mini App

### 4. Обновите код бота

В файле `bot.py` обновите URL Mini App:

```python
[InlineKeyboardButton("📱 Mini App", web_app={'url': 'http://localhost:8000'}, callback_data='mini_app')]
```

Замените `http://localhost:8000` на ваш реальный URL.

### 5. Настройте файл .env

Создайте файл `.env` в корне проекта:

```env
# Конфигурация Hotel Bot
BOT_TOKEN=ваш_токен_от_BotFather
BNOVO_API_KEY=your_bnovo_api_key_here

# Конфигурация Mini App
MINI_APP_URL=http://localhost:8000
SECRET_KEY=your-secret-key-here
MINI_APP_DEBUG=True

# Дополнительные настройки
LOG_LEVEL=INFO
```

**Важно:** Замените `ваш_токен_от_BotFather` на реальный токен вашего бота.

## 🚀 Запуск

1. **Запустите Mini App API:**
```bash
python run_mini_app_windows.py
```

2. **Запустите бота:**
```bash
python run_bot.py
```

3. **Или запустите все вместе:**
```bash
python start_simple_windows.py
```

## 🧪 Тестирование

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Нажмите "📱 Mini App"
5. Mini App должен открыться в Telegram!

## 🌐 Развертывание в интернете

### Для локального тестирования:
- URL: `http://localhost:8000`
- Работает только на вашем компьютере

### Для продакшена:
1. Разверните Mini App на сервере (Heroku, VPS, etc.)
2. Получите HTTPS URL
3. Обновите настройки в @BotFather
4. Обновите URL в коде бота

## 🔧 Дополнительные настройки

### Настройка команд бота:
1. Отправьте `/setcommands` боту [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота
3. Введите команды:
```
start - Запустить бота
help - Помощь
settings - Настройки
```

### Настройка описания бота:
1. Отправьте `/setdescription` боту [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота
3. Введите описание: `Система автоматизации отелей с Mini App интерфейсом`

## 🚨 Устранение неполадок

### Mini App не открывается:
1. Проверьте, что URL правильный
2. Убедитесь, что сервер запущен
3. Проверьте, что URL доступен из интернета (для продакшена)

### Ошибка "WebApp not found":
1. Проверьте настройки в @BotFather
2. Убедитесь, что URL совпадает в настройках и коде

### Ошибка "Invalid URL":
1. URL должен начинаться с `https://` (для продакшена)
2. Для локального тестирования можно использовать `http://localhost:8000`

## 📱 Результат

После настройки у вас будет:
- ✅ Telegram бот с кнопкой Mini App
- ✅ Mini App открывается прямо в Telegram
- ✅ Современный веб-интерфейс для всех функций бота
- ✅ Работа на всех устройствах (мобильные, десктоп)

---

**🎉 Теперь ваш Hotel Bot имеет полноценный Mini App в Telegram!**

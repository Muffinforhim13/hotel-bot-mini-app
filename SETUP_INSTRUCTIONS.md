# 🔧 Инструкции по настройке Hotel Bot

## 📋 Что нужно сделать:

### 1. Создайте файл `.env`

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Конфигурация Hotel Bot
BOT_TOKEN=your_bot_token_here
BNOVO_API_KEY=your_bnovo_api_key_here

# Конфигурация Mini App
MINI_APP_URL=https://your-domain.com
SECRET_KEY=your-secret-key-here
MINI_APP_DEBUG=True

# Дополнительные настройки
LOG_LEVEL=INFO
```

### 2. Получите токен бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен
5. Замените `your_bot_token_here` в файле `.env` на ваш токен

### 3. Настройте Mini App URL

Замените `https://your-domain.com` в файле `.env` на ваш реальный URL:
- Для локального тестирования: `http://localhost:8000`
- Для продакшена: ваш домен (например, `https://your-bot.herokuapp.com`)

### 4. Запустите приложение

После настройки `.env` файла запустите:

```bash
python start_simple_windows.py
```

## 🎯 Результат

После правильной настройки вы получите:
- ✅ Mini App API на http://localhost:8000
- ✅ Telegram бот готов к работе
- ✅ Все сервисы работают одновременно

## 🚨 Устранение неполадок

### Ошибка: "BOT_TOKEN не найден"
**Решение:** Проверьте, что файл `.env` создан и содержит правильный токен бота.

### Ошибка: "ModuleNotFoundError"
**Решение:** Установите зависимости:
```bash
pip install -r requirements.txt
```

### Ошибка: "Файлы Mini App не найдены"
**Решение:** Убедитесь, что папка `mini_app` содержит файлы:
- `index.html`
- `styles.css`
- `script.js`

## 📱 Тестирование

1. Запустите приложение
2. Откройте Telegram
3. Найдите вашего бота
4. Отправьте `/start`
5. Нажмите "📱 Mini App"
6. Используйте веб-интерфейс!

---

**🎉 После настройки ваш Hotel Bot будет полностью готов к работе!**

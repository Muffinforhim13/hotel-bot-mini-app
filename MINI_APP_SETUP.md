# 📱 Hotel Bot Mini App - Руководство по настройке

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

1. **Создайте файл `.env`** в корне проекта:
```env
BOT_TOKEN=your_bot_token_here
MINI_APP_URL=https://your-domain.com
SECRET_KEY=your-secret-key-here
MINI_APP_DEBUG=True
```

2. **Обновите URL в боте** (`bot.py`):
```python
# Замените 'https://your-domain.com' на ваш реальный URL
[InlineKeyboardButton("📱 Mini App", web_app={'url': 'https://your-domain.com'}, callback_data='mini_app')]
```

### 3. Запуск Mini App API

```bash
python run_mini_app.py
```

Mini App будет доступен по адресу: `http://localhost:8000`

## 🌐 Развертывание в продакшене

### Вариант 1: Heroku

1. **Создайте файл `Procfile`**:
```
web: python run_mini_app.py
```

2. **Создайте файл `runtime.txt`**:
```
python-3.11.0
```

3. **Разверните на Heroku**:
```bash
heroku create your-hotel-bot-mini-app
git push heroku main
```

### Вариант 2: VPS/Сервер

1. **Установите nginx**:
```bash
sudo apt update
sudo apt install nginx
```

2. **Создайте конфигурацию nginx**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Настройте SSL с Let's Encrypt**:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Вариант 3: Docker

1. **Создайте файл `Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_mini_app.py"]
```

2. **Создайте файл `docker-compose.yml`**:
```yaml
version: '3.8'
services:
  mini-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - MINI_APP_URL=${MINI_APP_URL}
    volumes:
      - ./mini_app:/app/mini_app
      - ./recorded_actions:/app/recorded_actions
```

3. **Запустите**:
```bash
docker-compose up -d
```

## 🔧 Настройка Telegram Bot

### 1. Создание бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 2. Настройка Mini App

1. Отправьте `/newapp` боту [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота
3. Введите название Mini App: `Hotel Bot`
4. Введите описание: `Система автоматизации отелей`
5. Загрузите иконку (512x512 PNG)
6. Введите URL: `https://your-domain.com`
7. Сохраните полученные данные

### 3. Обновление бота

Обновите URL в файле `bot.py`:
```python
[InlineKeyboardButton("📱 Mini App", web_app={'url': 'https://your-domain.com'}, callback_data='mini_app')]
```

## 📱 Функции Mini App

### 🧠 Умная автоматизация
- Создание объявлений на всех платформах одновременно
- Единая форма для ввода данных
- Автоматический выбор шаблонов

### 🎬 Автоматизация объявлений
- Просмотр сохраненных шаблонов
- Воспроизведение шаблонов
- Управление шаблонами

### 🏨 Платформы
- Быстрый доступ к платформам
- Статус подключения
- Открытие в браузере

### 🔔 Уведомления
- Настройка уведомлений о бронированиях
- Уведомления об изменениях статуса
- Уведомления об ошибках

### ⚙️ Настройки
- Конфигурация API ключей
- Настройки отладки
- Управление профилем

## 🔒 Безопасность

### 1. Валидация данных Telegram

Добавьте проверку подписи в `mini_app_api.py`:

```python
import hmac
import hashlib
import urllib.parse

def validate_telegram_data(init_data: str, bot_token: str) -> bool:
    """Валидация данных от Telegram"""
    try:
        # Парсинг данных
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # Извлечение hash
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return False
        
        # Создание строки для проверки
        data_check_string = init_data.replace(f'&hash={received_hash}', '')
        
        # Создание секретного ключа
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Проверка подписи
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == received_hash
    except Exception:
        return False
```

### 2. CORS настройки

Обновите CORS в `mini_app_api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://telegram.org",
        "https://web.telegram.org"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## 🧪 Тестирование

### 1. Локальное тестирование

```bash
# Запуск API
python run_mini_app.py

# Тестирование в браузере
open http://localhost:8000
```

### 2. Тестирование в Telegram

1. Запустите бота: `python run_bot.py`
2. Отправьте `/start`
3. Нажмите "📱 Mini App"
4. Протестируйте все функции

### 3. Тестирование API

```bash
# Проверка статуса
curl http://localhost:8000/api/status

# Тестирование умной автоматизации
curl -X POST http://localhost:8000/api/smart_automation \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test","hotel_name":"Test Hotel","hotel_address":"Test Address","hotel_type":"hotel","city":"Test City","phone":"+1234567890","contact_name":"Test Contact","contact_email":"contact@example.com","platforms":{"ostrovok":true}}'
```

## 📊 Мониторинг

### 1. Логи

Логи сохраняются в папке `logs/`:
- `mini_app.log` - логи Mini App API
- `bot.log` - логи основного бота

### 2. Метрики

Добавьте мониторинг в `mini_app_api.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Метрики
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🚨 Устранение неполадок

### Проблема: Mini App не открывается

**Решение:**
1. Проверьте URL в настройках бота
2. Убедитесь, что сервер запущен
3. Проверьте SSL сертификат

### Проблема: Ошибки CORS

**Решение:**
1. Обновите настройки CORS
2. Проверьте домен в `ALLOWED_ORIGINS`
3. Убедитесь, что запросы идут с правильного домена

### Проблема: API не отвечает

**Решение:**
1. Проверьте логи сервера
2. Убедитесь, что все зависимости установлены
3. Проверьте конфигурацию

### Проблема: Данные не сохраняются

**Решение:**
1. Проверьте права доступа к папкам
2. Убедитесь, что база данных доступна
3. Проверьте настройки кэширования

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи в папке `logs/`
2. Убедитесь, что все зависимости установлены
3. Проверьте конфигурацию в `.env`
4. Создайте issue с описанием проблемы

## 🔄 Обновления

Для обновления Mini App:

1. Остановите сервер
2. Обновите код
3. Установите новые зависимости: `pip install -r requirements.txt`
4. Запустите сервер: `python run_mini_app.py`

---

**🎯 Цель**: Предоставить пользователям удобный веб-интерфейс для всех функций бота прямо в Telegram!

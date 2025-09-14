#!/bin/bash

echo "🏨 Hotel Bot - Запуск Mini App и бота"
echo "====================================="

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверка наличия файла .env
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден. Создаю шаблон..."
    cat > .env << EOF
# Конфигурация Hotel Bot
BOT_TOKEN=your_bot_token_here
BNOVO_API_KEY=your_bnovo_api_key_here

# Конфигурация Mini App
MINI_APP_URL=https://your-domain.com
SECRET_KEY=your-secret-key-here
MINI_APP_DEBUG=True

# Дополнительные настройки
LOG_LEVEL=INFO
EOF
    echo "📝 Создан файл .env. Заполните его настройками."
    exit 1
fi

# Создание необходимых папок
mkdir -p logs mini_app recorded_actions sessions

# Создание виртуального окружения (если нужно)
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install -r requirements.txt

# Запуск приложения
echo "🚀 Запуск Hotel Bot и Mini App..."
python3 run_all.py

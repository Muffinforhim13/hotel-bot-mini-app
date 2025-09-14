@echo off
echo 🏨 Hotel Bot - Запуск Mini App и бота
echo =====================================

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверка наличия файла .env
if not exist .env (
    echo ⚠️ Файл .env не найден. Создаю шаблон...
    echo BOT_TOKEN=your_bot_token_here > .env
    echo MINI_APP_URL=https://your-domain.com >> .env
    echo SECRET_KEY=your-secret-key-here >> .env
    echo MINI_APP_DEBUG=True >> .env
    echo.
    echo 📝 Создан файл .env. Заполните его настройками.
    pause
    exit /b 1
)

REM Создание необходимых папок
if not exist logs mkdir logs
if not exist mini_app mkdir mini_app
if not exist recorded_actions mkdir recorded_actions
if not exist sessions mkdir sessions

REM Установка зависимостей (если нужно)
if not exist venv (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
)

echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

echo 📦 Установка зависимостей...
pip install -r requirements.txt

echo 🚀 Запуск Hotel Bot и Mini App...
python run_all.py

pause

#!/usr/bin/env python3
"""
Простой скрипт для запуска Hotel Bot и Mini App
Без сложной настройки логирования - для быстрого старта
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def create_directories():
    """Создание необходимых директорий"""
    directories = ['logs', 'mini_app', 'recorded_actions', 'sessions']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Директория {directory} готова")

def check_requirements():
    """Проверка основных требований"""
    print("🔍 Проверка требований...")
    
    # Проверка основных файлов
    required_files = [
        'bot.py',
        'mini_app_api.py',
        'run_mini_app.py',
        'mini_app/index.html',
        'mini_app/styles.css',
        'mini_app/script.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    # Проверка .env файла
    if not os.path.exists('.env'):
        print("⚠️ Файл .env не найден. Создаю шаблон...")
        env_content = """# Конфигурация Hotel Bot
BOT_TOKEN=your_bot_token_here
BNOVO_API_KEY=your_bnovo_api_key_here

# Конфигурация Mini App
MINI_APP_URL=https://your-domain.com
SECRET_KEY=your-secret-key-here
MINI_APP_DEBUG=True

# Дополнительные настройки
LOG_LEVEL=INFO
"""
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("📝 Создан файл .env. Заполните его настройками.")
        return False
    
    print("✅ Все требования выполнены")
    return True

def start_mini_app():
    """Запуск Mini App API"""
    print("🚀 Запуск Mini App API...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, 'run_mini_app.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем запуска
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Mini App API запущен на http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Ошибка запуска Mini App API: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска Mini App API: {e}")
        return None

def start_bot():
    """Запуск Telegram бота"""
    print("🤖 Запуск Telegram бота...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, 'run_bot.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем запуска
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ Telegram бот запущен")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Ошибка запуска бота: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return None

def main():
    """Главная функция"""
    print("🏨 Hotel Bot - Простой запуск Mini App и бота")
    print("=" * 50)
    
    # Создание директорий
    create_directories()
    
    # Проверка требований
    if not check_requirements():
        print("❌ Требования не выполнены. Запуск отменен.")
        input("Нажмите Enter для выхода...")
        return
    
    processes = []
    
    try:
        # Запуск Mini App
        mini_app_process = start_mini_app()
        if mini_app_process:
            processes.append(mini_app_process)
        else:
            print("❌ Не удалось запустить Mini App API")
            return
        
        # Небольшая пауза
        time.sleep(2)
        
        # Запуск бота
        bot_process = start_bot()
        if bot_process:
            processes.append(bot_process)
        else:
            print("❌ Не удалось запустить Telegram бота")
            return
        
        print("\n🎉 Все сервисы запущены успешно!")
        print("📱 Mini App доступен на: http://localhost:8000")
        print("🤖 Telegram бот готов к работе")
        print("⏹️ Для остановки нажмите Ctrl+C")
        
        # Основной цикл
        while True:
            # Проверяем состояние процессов
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"❌ Процесс {i} завершился неожиданно")
                    return
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n📡 Получен сигнал прерывания")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        # Остановка процессов
        print("⏹️ Остановка всех сервисов...")
        for process in processes:
            if process.poll() is None:
                print(f"🛑 Остановка процесса {process.pid}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        print("✅ Все сервисы остановлены")

if __name__ == "__main__":
    main()

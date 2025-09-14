#!/usr/bin/env python3
"""
Запуск Mini App API сервера для Hotel Bot
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_requirements():
    """Проверка наличия необходимых зависимостей"""
    required_packages = ['fastapi', 'uvicorn', 'pydantic']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Отсутствуют необходимые пакеты: {', '.join(missing_packages)}")
        logger.info("Установите их командой: pip install fastapi uvicorn pydantic")
        return False
    
    return True

def check_mini_app_files():
    """Проверка наличия файлов Mini App"""
    required_files = [
        'mini_app/index.html',
        'mini_app/styles.css',
        'mini_app/script.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Отсутствуют файлы Mini App: {', '.join(missing_files)}")
        return False
    
    return True

def setup_environment():
    """Настройка окружения"""
    # Создание папки для логов
    os.makedirs('logs', exist_ok=True)
    
    # Создание папки для статических файлов
    os.makedirs('mini_app', exist_ok=True)
    
    logger.info("Окружение настроено")

def main():
    """Главная функция запуска"""
    print("Запуск Hotel Bot Mini App API...")
    
    # Проверки
    if not check_requirements():
        sys.exit(1)
    
    if not check_mini_app_files():
        sys.exit(1)
    
    # Настройка окружения
    setup_environment()
    
    try:
        # Запуск API сервера
        logger.info("Запуск API сервера на http://localhost:8000")
        logger.info("Mini App будет доступен по адресу: http://localhost:8000")
        logger.info("Для остановки нажмите Ctrl+C")
        
        # Импорт и запуск приложения
        from mini_app_api import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True  # Автоперезагрузка при изменении файлов
        )
        
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

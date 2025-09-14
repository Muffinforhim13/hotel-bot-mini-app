#!/usr/bin/env python3
"""
Асинхронный единый скрипт для запуска Hotel Bot и Mini App одновременно
"""

import asyncio
import os
import sys
import signal
import logging
from pathlib import Path
from typing import Optional

# Создание папки logs перед настройкой логирования
os.makedirs('logs', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/run_all_async.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AsyncHotelBotManager:
    """Асинхронный менеджер для запуска Hotel Bot и Mini App"""
    
    def __init__(self):
        self.tasks = []
        self.running = False
        self.setup_directories()
    
    def setup_directories(self):
        """Создание необходимых директорий"""
        directories = ['logs', 'mini_app', 'recorded_actions', 'sessions']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✅ Директория {directory} готова")
    
    async def check_requirements(self) -> bool:
        """Проверка наличия необходимых файлов и зависимостей"""
        logger.info("🔍 Проверка требований...")
        
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
            logger.error(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
            return False
        
        # Проверка зависимостей
        try:
            import fastapi
            import uvicorn
            import telegram
            logger.info("✅ Все зависимости установлены")
        except ImportError as e:
            logger.error(f"❌ Отсутствуют зависимости: {e}")
            logger.info("Установите их командой: pip install -r requirements.txt")
            return False
        
        # Проверка конфигурации
        if not os.path.exists('.env'):
            logger.warning("⚠️ Файл .env не найден. Создайте его с настройками:")
            logger.info("BOT_TOKEN=your_bot_token_here")
            logger.info("MINI_APP_URL=https://your-domain.com")
            return False
        
        logger.info("✅ Все требования выполнены")
        return True
    
    async def start_mini_app(self):
        """Запуск Mini App API"""
        logger.info("🚀 Запуск Mini App API...")
        
        try:
            # Импорт и запуск Mini App API
            from mini_app_api import app
            import uvicorn
            
            # Запуск сервера
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            logger.info("✅ Mini App API запущен на http://localhost:8000")
            await server.serve()
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Mini App API: {e}")
            raise
    
    async def start_bot(self):
        """Запуск Telegram бота"""
        logger.info("🤖 Запуск Telegram бота...")
        
        try:
            # Импорт и запуск бота
            from bot import HotelBot
            from config import BOT_TOKEN
            
            if not BOT_TOKEN:
                raise ValueError("BOT_TOKEN не найден в конфигурации")
            
            # Создание и запуск бота
            bot = HotelBot(BOT_TOKEN)
            await bot.application.initialize()
            await bot.application.start()
            
            logger.info("✅ Telegram бот запущен")
            
            # Ожидание завершения
            await bot.application.updater.start_polling()
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            raise
    
    async def start_all(self):
        """Запуск всех сервисов"""
        logger.info("🚀 Запуск Hotel Bot и Mini App...")
        
        if not await self.check_requirements():
            logger.error("❌ Требования не выполнены. Запуск отменен.")
            return False
        
        self.running = True
        
        try:
            # Создание задач для запуска сервисов
            mini_app_task = asyncio.create_task(self.start_mini_app())
            bot_task = asyncio.create_task(self.start_bot())
            
            self.tasks = [mini_app_task, bot_task]
            
            logger.info("🎉 Все сервисы запущены успешно!")
            logger.info("📱 Mini App доступен на: http://localhost:8000")
            logger.info("🤖 Telegram бот готов к работе")
            logger.info("⏹️ Для остановки нажмите Ctrl+C")
            
            # Ожидание завершения задач
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска сервисов: {e}")
            return False
        
        return True
    
    async def stop_all(self):
        """Остановка всех сервисов"""
        logger.info("⏹️ Остановка всех сервисов...")
        self.running = False
        
        # Отмена всех задач
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Ожидание завершения задач
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("✅ Все сервисы остановлены")
    
    async def run(self):
        """Основной цикл работы"""
        try:
            if await self.start_all():
                # Основной цикл
                while self.running:
                    await asyncio.sleep(1)
            else:
                logger.error("❌ Не удалось запустить сервисы")
                return
                
        except KeyboardInterrupt:
            logger.info("📡 Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            await self.stop_all()

def create_env_template():
    """Создание шаблона .env файла"""
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
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("📝 Создан файл .env. Заполните его настройками.")
        return False
    return True

async def main():
    """Главная функция"""
    print("🏨 Hotel Bot - Асинхронный запуск Mini App и бота")
    print("=" * 50)
    
    # Создание шаблона .env если его нет
    if not create_env_template():
        print("❌ Сначала настройте файл .env")
        return
    
    # Создание менеджера и запуск
    manager = AsyncHotelBotManager()
    await manager.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Завершение работы...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

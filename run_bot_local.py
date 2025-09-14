#!/usr/bin/env python3
"""
Локальный запуск бота (для разработки)
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from bot import HotelBot
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция"""
    print("Запуск Hotel Bot локально...")
    
    if not BOT_TOKEN:
        print("ОШИБКА: BOT_TOKEN не найден в конфигурации")
        return
    
    try:
        # Создаем и запускаем бота
        bot = HotelBot(BOT_TOKEN)
        await bot.application.initialize()
        await bot.application.start()
        await bot.application.updater.start_polling()
        
        print("OK: Telegram бот запущен и работает")
        print("Mini App доступен на: https://hotel-bot-mini-app.vercel.app")
        print("Для остановки нажмите Ctrl+C")
        
        # Ожидание завершения
        await bot.application.updater.idle()
        
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"\nОШИБКА запуска бота: {e}")
    finally:
        try:
            await bot.application.stop()
            await bot.application.shutdown()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())

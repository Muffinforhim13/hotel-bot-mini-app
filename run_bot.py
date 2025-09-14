#!/usr/bin/env python3
"""
Быстрый запуск бота для автоматизации платформ
"""

import asyncio
import logging
from bot import HotelBot
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """
    Быстрый запуск бота
    """
    print("Запуск Telegram бота...")
    
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
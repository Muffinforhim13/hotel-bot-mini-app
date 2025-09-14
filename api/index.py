#!/usr/bin/env python3
"""
Vercel serverless function for Hotel Bot
"""

import os
import asyncio
import logging
from bot import HotelBot
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(request):
    """Обработчик для Vercel"""
    try:
        if not BOT_TOKEN:
            return {
                'statusCode': 500,
                'body': 'BOT_TOKEN not found'
            }
        
        # Создаем и запускаем бота
        bot = HotelBot(BOT_TOKEN)
        
        # Запускаем бота в фоне
        asyncio.create_task(start_bot(bot))
        
        return {
            'statusCode': 200,
            'body': 'Bot started successfully'
        }
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

async def start_bot(bot):
    """Запуск бота"""
    try:
        await bot.application.initialize()
        await bot.application.start()
        await bot.application.updater.start_polling()
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Error in bot: {e}")

# Для Vercel
def main(request):
    return handler(request)

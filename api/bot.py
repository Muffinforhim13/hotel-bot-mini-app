#!/usr/bin/env python3
"""
Simple bot handler for Vercel
"""

import os
import asyncio
import logging
from telegram import Bot
from telegram.ext import Application

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения приложения
app = None

async def start_bot():
    """Запуск бота"""
    global app
    
    try:
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN not found")
            return
        
        # Создаем приложение
        app = Application.builder().token(bot_token).build()
        
        # Добавляем обработчики
        from bot import HotelBot
        bot_instance = HotelBot(bot_token)
        
        # Копируем обработчики
        for handler in bot_instance.application.handlers[0]:
            app.add_handler(handler)
        
        # Запускаем бота
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        logger.info("Bot started successfully on Vercel")
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

def handler(request):
    """Обработчик для Vercel"""
    try:
        # Запускаем бота если он еще не запущен
        if app is None:
            asyncio.create_task(start_bot())
        
        return {
            'statusCode': 200,
            'body': 'Bot is running'
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

# Для Vercel
def main(request):
    return handler(request)

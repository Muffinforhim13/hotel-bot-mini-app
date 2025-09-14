#!/usr/bin/env python3
"""
Vercel serverless function for Hotel Bot
"""

import os
import json
import asyncio
import logging
from telegram import Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения приложения
app = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("📱 Mini App", web_app={'url': 'https://hotel-bot-mini-app.vercel.app'}, callback_data='mini_app')],
        [InlineKeyboardButton("🏨 Платформы", callback_data='platforms')],
        [InlineKeyboardButton("🧠 Умная автоматизация", callback_data='smart_menu')],
        [InlineKeyboardButton("🎬 Автоматизация объявлений", callback_data='recording_menu')],
        [InlineKeyboardButton("🔔 Уведомления", callback_data='notifications_settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = "Добро пожаловать в бота управления отелями! 🏨\n\n"
    welcome_text += "📱 **Mini App доступен!** - используйте удобный веб-интерфейс для всех функций!\n\n"
    welcome_text += "🧠 **Умная автоматизация** - введите данные один раз, получите объявления на всех платформах!\n\n"
    welcome_text += "🎬 **Автоматизация объявлений** - создавайте объявления на всех платформах!\n\n"
    welcome_text += "Выберите действие:"

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'mini_app':
        await query.edit_message_text("📱 Mini App открыт! Используйте веб-интерфейс для всех функций.")
    elif query.data == 'platforms':
        await query.edit_message_text("🏨 Платформы:\n\n• Ostrovok\n• Bronevik\n• 101 Hotels")
    elif query.data == 'smart_menu':
        await query.edit_message_text("🧠 Умная автоматизация:\n\nВведите данные один раз, получите объявления на всех платформах!")
    elif query.data == 'recording_menu':
        await query.edit_message_text("🎬 Автоматизация объявлений:\n\nСоздавайте объявления на всех платформах!")
    elif query.data == 'notifications_settings':
        await query.edit_message_text("🔔 Настройки уведомлений:\n\n• Новые бронирования\n• Изменения статуса\n• Ошибки")

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
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CallbackQueryHandler(button_callback))
        
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
            'body': json.dumps({
                'message': 'Bot is running',
                'status': 'success'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'status': 'error'
            })
        }

# Для Vercel
def main(request):
    return handler(request)
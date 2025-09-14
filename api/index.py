#!/usr/bin/env python3
"""
Simple webhook handler for Vercel
"""

import os
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(request):
    """Простой обработчик для Vercel"""
    try:
        # Проверяем переменные окружения
        bot_token = os.getenv('BOT_TOKEN')
        mini_app_url = os.getenv('MINI_APP_URL', 'https://hotel-bot-mini-app.vercel.app')
        
        if not bot_token:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'BOT_TOKEN not found',
                    'status': 'error'
                })
            }
        
        # Возвращаем информацию о боте
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Hotel Bot is running',
                'status': 'success',
                'bot_token': bot_token[:10] + '...' if bot_token else 'not_set',
                'mini_app_url': mini_app_url,
                'version': '1.0.0'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'error'
            })
        }

# Для Vercel
def main(request):
    return handler(request)
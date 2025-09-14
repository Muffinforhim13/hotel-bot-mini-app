import json
import os

def handler(request):
    """Простой обработчик для Vercel"""
    try:
        # Проверяем переменные окружения
        bot_token = os.getenv('BOT_TOKEN')
        mini_app_url = os.getenv('MINI_APP_URL', 'https://hotel-bot-mini-app.vercel.app')
        
        response = {
            'message': 'Hotel Bot is running',
            'status': 'success',
            'bot_token': bot_token[:10] + '...' if bot_token else 'not_set',
            'mini_app_url': mini_app_url,
            'version': '1.0.0'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
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

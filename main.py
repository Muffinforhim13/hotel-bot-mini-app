from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
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
        
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_POST(self):
        self.do_GET()

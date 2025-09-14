import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Bnovo PMS API Key
BNOVO_API_KEY = os.getenv('BNOVO_API_KEY')

# Другие настройки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

# Bnovo API не обязателен, но рекомендуется
if not BNOVO_API_KEY:
    print("⚠️ BNOVO_API_KEY не найден. Функции Bnovo PMS будут недоступны.") 
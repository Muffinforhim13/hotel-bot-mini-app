#!/usr/bin/env python3
"""
Конфигурация для Mini App Hotel Bot
"""

import os
from typing import Dict, Any

class MiniAppConfig:
    """Конфигурация Mini App"""
    
    def __init__(self):
        # Основные настройки
        self.APP_NAME = "Hotel Bot Mini App"
        self.APP_VERSION = "1.0.0"
        self.APP_DESCRIPTION = "Система автоматизации отелей"
        
        # Настройки сервера
        self.HOST = os.getenv("MINI_APP_HOST", "0.0.0.0")
        self.PORT = int(os.getenv("MINI_APP_PORT", "8000"))
        self.DEBUG = os.getenv("MINI_APP_DEBUG", "False").lower() == "true"
        
        # URL для Mini App (замените на ваш домен)
        self.MINI_APP_URL = os.getenv("MINI_APP_URL", "https://your-domain.com")
        
        # Настройки Telegram
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL")
        
        # Настройки безопасности
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.ALLOWED_ORIGINS = [
            "https://your-domain.com",
            "https://telegram.org",
            "https://web.telegram.org"
        ]
        
        # Настройки базы данных
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hotel_bot.db")
        
        # Настройки кэширования
        self.CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 час
        
        # Настройки логирования
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/mini_app.log")
        
        # Настройки платформ
        self.PLATFORM_URLS = {
            'ostrovok': 'https://extranet.ostrovok.ru',
            'bronevik': 'https://extranet.bronevik.com',
            '101hotels': 'https://extranet.101hotels.com'
        }
        
        # Настройки уведомлений
        self.NOTIFICATION_SETTINGS = {
            'booking_notifications': True,
            'status_notifications': True,
            'error_notifications': True
        }
        
        # Настройки лимитов
        self.RATE_LIMITS = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'max_file_size': 10 * 1024 * 1024  # 10MB
        }
        
        # Настройки шаблонов
        self.TEMPLATE_SETTINGS = {
            'max_templates_per_user': 50,
            'max_actions_per_template': 1000,
            'template_timeout': 300  # 5 минут
        }
    
    def get_platform_url(self, platform: str) -> str:
        """Получение URL платформы"""
        return self.PLATFORM_URLS.get(platform, "")
    
    def is_platform_supported(self, platform: str) -> bool:
        """Проверка поддержки платформы"""
        return platform in self.PLATFORM_URLS
    
    def get_supported_platforms(self) -> list:
        """Получение списка поддерживаемых платформ"""
        return list(self.PLATFORM_URLS.keys())
    
    def validate_config(self) -> bool:
        """Валидация конфигурации"""
        if not self.BOT_TOKEN:
            print("❌ BOT_TOKEN не установлен")
            return False
        
        if not self.MINI_APP_URL or self.MINI_APP_URL == "https://your-domain.com":
            print("⚠️ MINI_APP_URL не настроен. Установите правильный URL для Mini App")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование конфигурации в словарь"""
        return {
            'app_name': self.APP_NAME,
            'app_version': self.APP_VERSION,
            'app_description': self.APP_DESCRIPTION,
            'host': self.HOST,
            'port': self.PORT,
            'debug': self.DEBUG,
            'mini_app_url': self.MINI_APP_URL,
            'supported_platforms': self.get_supported_platforms(),
            'notification_settings': self.NOTIFICATION_SETTINGS,
            'rate_limits': self.RATE_LIMITS,
            'template_settings': self.TEMPLATE_SETTINGS
        }

# Глобальный экземпляр конфигурации
config = MiniAppConfig()

def get_config() -> MiniAppConfig:
    """Получение экземпляра конфигурации"""
    return config

def validate_environment():
    """Валидация окружения"""
    print("🔍 Проверка конфигурации Mini App...")
    
    if not config.validate_config():
        print("❌ Конфигурация невалидна")
        return False
    
    print("✅ Конфигурация валидна")
    print(f"📱 Mini App URL: {config.MINI_APP_URL}")
    print(f"🌐 Сервер: {config.HOST}:{config.PORT}")
    print(f"🏨 Поддерживаемые платформы: {', '.join(config.get_supported_platforms())}")
    
    return True

if __name__ == "__main__":
    validate_environment()

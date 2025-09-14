#!/usr/bin/env python3
"""
API сервер для Mini App Hotel Bot
Обрабатывает запросы от веб-интерфейса и интегрируется с основным ботом
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Импорты из основного бота
from smart_bot_integration import SmartBotIntegration
from action_recorder import RecordingManager
from config import BOT_TOKEN, BNOVO_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Модели данных
class SmartAutomationRequest(BaseModel):
    email: str
    password: str
    hotel_name: str
    hotel_address: str
    hotel_type: str
    city: str
    phone: str
    website: Optional[str] = None
    contact_name: str
    contact_email: str
    description: Optional[str] = None
    amenities: Optional[str] = None
    platforms: Dict[str, bool]

class PlatformRequest(BaseModel):
    platform: str

class TemplateRequest(BaseModel):
    template_id: str

class SettingsRequest(BaseModel):
    bnovo_api_key: Optional[str] = None
    debug_mode: Optional[bool] = None

class NotificationSettingsRequest(BaseModel):
    booking_notifications: bool
    status_notifications: bool
    error_notifications: bool

# Создание FastAPI приложения
app = FastAPI(title="Hotel Bot Mini App API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="mini_app"), name="static")

# Глобальные объекты
smart_integration = SmartBotIntegration()
recording_manager = RecordingManager()

# Кэш для хранения данных пользователей
user_cache = {}

def get_user_id(request: Request) -> str:
    """Получение ID пользователя из заголовков или параметров"""
    # В реальном приложении здесь будет проверка подписи Telegram
    user_id = request.headers.get("X-User-ID", "demo_user")
    return user_id

@app.get("/", response_class=HTMLResponse)
async def serve_mini_app():
    """Обслуживание главной страницы Mini App"""
    try:
        with open("mini_app/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Mini App не найден")

@app.post("/api/smart_automation")
async def handle_smart_automation(request: SmartAutomationRequest, user_id: str = Depends(get_user_id)):
    """Обработка запроса умной автоматизации"""
    try:
        logger.info(f"Запрос умной автоматизации от пользователя {user_id}")
        
        # Валидация данных
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="Email и пароль обязательны")
        
        if not any(request.platforms.values()):
            raise HTTPException(status_code=400, detail="Выберите хотя бы одну платформу")
        
        # Подготовка данных для умной системы
        user_data = {
            'email': request.email,
            'password': request.password,
            'hotel_name': request.hotel_name,
            'hotel_address': request.hotel_address,
            'hotel_type': request.hotel_type,
            'city': request.city,
            'phone': request.phone,
            'website': request.website or '',
            'contact_name': request.contact_name,
            'contact_email': request.contact_email,
            'description': request.description or '',
            'amenities': request.amenities or ''
        }
        
        # Выбор платформ
        selected_platforms = [platform for platform, selected in request.platforms.items() if selected]
        
        # Запуск умной автоматизации
        results = await smart_integration.process_universal_creation(
            user_data, selected_platforms, user_id
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "Объявления успешно созданы",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Ошибка умной автоматизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/open_platform")
async def handle_open_platform(request: PlatformRequest, user_id: str = Depends(get_user_id)):
    """Открытие платформы в браузере"""
    try:
        logger.info(f"Запрос открытия платформы {request.platform} от пользователя {user_id}")
        
        platform_urls = {
            'ostrovok': 'https://extranet.ostrovok.ru',
            'bronevik': 'https://extranet.bronevik.com',
            '101hotels': 'https://extranet.101hotels.com'
        }
        
        if request.platform not in platform_urls:
            raise HTTPException(status_code=400, detail="Неизвестная платформа")
        
        # В реальном приложении здесь будет открытие браузера
        # Для демонстрации просто возвращаем URL
        return JSONResponse(content={
            "success": True,
            "message": f"Платформа {request.platform} открыта",
            "url": platform_urls[request.platform]
        })
        
    except Exception as e:
        logger.error(f"Ошибка открытия платформы: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates")
async def get_templates(user_id: str = Depends(get_user_id)):
    """Получение списка шаблонов пользователя"""
    try:
        logger.info(f"Запрос шаблонов от пользователя {user_id}")
        
        # Получение шаблонов из recording_manager
        templates = recording_manager.get_user_templates(user_id)
        
        return JSONResponse(content={
            "success": True,
            "templates": templates
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения шаблонов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/play_template")
async def play_template(request: TemplateRequest, user_id: str = Depends(get_user_id)):
    """Воспроизведение шаблона"""
    try:
        logger.info(f"Запрос воспроизведения шаблона {request.template_id} от пользователя {user_id}")
        
        # Воспроизведение шаблона
        result = await recording_manager.play_template(request.template_id, user_id)
        
        if result['success']:
            return JSONResponse(content={
                "success": True,
                "message": "Шаблон успешно воспроизведен"
            })
        else:
            raise HTTPException(status_code=400, detail=result['error'])
        
    except Exception as e:
        logger.error(f"Ошибка воспроизведения шаблона: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/template/{template_id}")
async def delete_template(template_id: str, user_id: str = Depends(get_user_id)):
    """Удаление шаблона"""
    try:
        logger.info(f"Запрос удаления шаблона {template_id} от пользователя {user_id}")
        
        # Удаление шаблона
        result = recording_manager.delete_template(template_id, user_id)
        
        if result['success']:
            return JSONResponse(content={
                "success": True,
                "message": "Шаблон удален"
            })
        else:
            raise HTTPException(status_code=400, detail=result['error'])
        
    except Exception as e:
        logger.error(f"Ошибка удаления шаблона: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings(user_id: str = Depends(get_user_id)):
    """Получение настроек пользователя"""
    try:
        logger.info(f"Запрос настроек от пользователя {user_id}")
        
        # Получение настроек из кэша или базы данных
        settings = user_cache.get(user_id, {}).get('settings', {
            'bnovo_api_key': BNOVO_API_KEY or '',
            'debug_mode': False
        })
        
        return JSONResponse(content={
            "success": True,
            "settings": settings
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def save_settings(request: SettingsRequest, user_id: str = Depends(get_user_id)):
    """Сохранение настроек пользователя"""
    try:
        logger.info(f"Запрос сохранения настроек от пользователя {user_id}")
        
        # Инициализация кэша пользователя
        if user_id not in user_cache:
            user_cache[user_id] = {}
        if 'settings' not in user_cache[user_id]:
            user_cache[user_id]['settings'] = {}
        
        # Обновление настроек
        if request.bnovo_api_key is not None:
            user_cache[user_id]['settings']['bnovo_api_key'] = request.bnovo_api_key
        if request.debug_mode is not None:
            user_cache[user_id]['settings']['debug_mode'] = request.debug_mode
        
        return JSONResponse(content={
            "success": True,
            "message": "Настройки сохранены"
        })
        
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notification_settings")
async def save_notification_settings(request: NotificationSettingsRequest, user_id: str = Depends(get_user_id)):
    """Сохранение настроек уведомлений"""
    try:
        logger.info(f"Запрос сохранения настроек уведомлений от пользователя {user_id}")
        
        # Инициализация кэша пользователя
        if user_id not in user_cache:
            user_cache[user_id] = {}
        if 'notification_settings' not in user_cache[user_id]:
            user_cache[user_id]['notification_settings'] = {}
        
        # Обновление настроек уведомлений
        user_cache[user_id]['notification_settings'] = {
            'booking_notifications': request.booking_notifications,
            'status_notifications': request.status_notifications,
            'error_notifications': request.error_notifications
        }
        
        return JSONResponse(content={
            "success": True,
            "message": "Настройки уведомлений сохранены"
        })
        
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек уведомлений: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Получение статуса API"""
    return JSONResponse(content={
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Расширение SmartBotIntegration для работы с API
class SmartBotIntegration:
    """Расширенная версия SmartBotIntegration для API"""
    
    def __init__(self):
        self.recording_manager = RecordingManager()
        self.user_data = {}
        self.platform_templates = {
            'ostrovok': {
                'name': 'Ostrovok',
                'url': 'https://extranet.ostrovok.ru',
                'description': 'Платформа бронирования отелей'
            },
            'bronevik': {
                'name': 'Bronevik', 
                'url': 'https://extranet.bronevik.com',
                'description': 'Система управления бронированиями'
            },
            '101hotels': {
                'name': '101 Hotels',
                'url': 'https://extranet.101hotels.com', 
                'description': 'Платформа управления объектами'
            }
        }
    
    async def process_universal_creation(self, user_data: Dict[str, Any], platforms: list, user_id: str) -> Dict[str, Any]:
        """Обработка универсального создания объявлений"""
        results = {}
        
        for platform in platforms:
            try:
                logger.info(f"Создание объявления на платформе {platform} для пользователя {user_id}")
                
                # Получение шаблона для платформы
                template = self.recording_manager.get_platform_template(platform, user_id)
                
                if not template:
                    results[platform] = {
                        'success': False,
                        'error': f'Шаблон для платформы {platform} не найден'
                    }
                    continue
                
                # Воспроизведение шаблона с данными пользователя
                result = await self.recording_manager.play_template_with_data(template['id'], user_data, user_id)
                
                results[platform] = result
                
            except Exception as e:
                logger.error(f"Ошибка создания объявления на {platform}: {e}")
                results[platform] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results

# Расширение RecordingManager для работы с API
class RecordingManager:
    """Расширенная версия RecordingManager для API"""
    
    def __init__(self):
        self.recordings_dir = "recorded_actions"
        self.templates_cache = {}
    
    def get_user_templates(self, user_id: str) -> list:
        """Получение шаблонов пользователя"""
        templates = []
        
        try:
            import os
            import json
            
            if not os.path.exists(self.recordings_dir):
                return templates
            
            for filename in os.listdir(self.recordings_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(self.recordings_dir, filename), 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                        
                        # Фильтрация по пользователю (в реальном приложении)
                        templates.append({
                            'id': filename.replace('.json', ''),
                            'name': template_data.get('name', 'Без названия'),
                            'platform': template_data.get('platform', 'unknown'),
                            'actions_count': len(template_data.get('actions', [])),
                            'created_at': template_data.get('created_at', datetime.now().isoformat())
                        })
                    except Exception as e:
                        logger.error(f"Ошибка чтения шаблона {filename}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Ошибка получения шаблонов: {e}")
        
        return templates
    
    def get_platform_template(self, platform: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Получение шаблона для конкретной платформы"""
        templates = self.get_user_templates(user_id)
        
        for template in templates:
            if template['platform'] == platform:
                return template
        
        return None
    
    async def play_template(self, template_id: str, user_id: str) -> Dict[str, Any]:
        """Воспроизведение шаблона"""
        try:
            # В реальном приложении здесь будет воспроизведение шаблона
            logger.info(f"Воспроизведение шаблона {template_id} для пользователя {user_id}")
            
            return {
                'success': True,
                'message': 'Шаблон успешно воспроизведен'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def play_template_with_data(self, template_id: str, user_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Воспроизведение шаблона с данными пользователя"""
        try:
            # В реальном приложении здесь будет воспроизведение с подстановкой данных
            logger.info(f"Воспроизведение шаблона {template_id} с данными для пользователя {user_id}")
            
            return {
                'success': True,
                'message': 'Объявление успешно создано'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_template(self, template_id: str, user_id: str) -> Dict[str, Any]:
        """Удаление шаблона"""
        try:
            import os
            
            template_path = os.path.join(self.recordings_dir, f"{template_id}.json")
            
            if os.path.exists(template_path):
                os.remove(template_path)
                return {
                    'success': True,
                    'message': 'Шаблон удален'
                }
            else:
                return {
                    'success': False,
                    'error': 'Шаблон не найден'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """Запуск API сервера"""
    print("🚀 Запуск Hotel Bot Mini App API...")
    
    # Проверка наличия необходимых файлов
    import os
    if not os.path.exists("mini_app/index.html"):
        print("❌ Файлы Mini App не найдены. Убедитесь, что папка mini_app существует.")
        return
    
    # Запуск сервера
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()

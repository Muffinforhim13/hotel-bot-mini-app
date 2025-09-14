import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from action_recorder import RecordingManager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_UNIVERSAL_DATA = 2000
WAITING_PLATFORM_SELECTION = 2001

class SmartBotIntegration:
    """Умная интеграция для работы с несколькими платформами одновременно"""
    
    def __init__(self):
        self.recording_manager = RecordingManager()
        self.user_data = {}  # Хранение данных пользователей
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
    
    async def show_smart_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать умное меню для работы с несколькими платформами"""
        keyboard = [
            [InlineKeyboardButton("🚀 Создать объявления на всех платформах", callback_data='smart_create_all')],
            [InlineKeyboardButton("🎯 Выбрать конкретные платформы", callback_data='smart_select_platforms')],
            [InlineKeyboardButton("📊 Статус объявлений", callback_data='smart_status')],
            [InlineKeyboardButton("📋 Мои шаблоны", callback_data='smart_templates')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🧠 **Умная система автоматизации**\n\n"
        text += "Эта система позволяет:\n"
        text += "• Ввести данные ОДИН РАЗ\n"
        text += "• Автоматически создать объявления на ВСЕХ платформах\n"
        text += "• Выбрать конкретные платформы\n"
        text += "• Отслеживать статус публикации\n\n"
        text += "Выберите действие:"
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def start_universal_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать создание объявлений на всех платформах"""
        query = update.callback_query
        await query.answer()
        
        # Показываем форму для ввода данных
        await query.edit_message_text(
            "📝 **Введите данные для всех платформ**\n\n"
            "Эти данные будут использованы для создания объявлений на всех платформах:\n\n"
            "```\n"
            "email: ваш_email@example.com\n"
            "password: ваш_пароль\n"
            "hotel_name: Название отеля\n"
            "hotel_address: Адрес отеля\n"
            "hotel_type: Тип отеля\n"
            "city: Город\n"
            "phone: Телефон\n"
            "website: Сайт (необязательно)\n"
            "contact_name: Контактное лицо\n"
            "contact_email: Контактный email\n"
            "description: Описание отеля\n"
            "amenities: Удобства (через запятую)\n"
            "```\n\n"
            "Или отправьте 'отмена' для отмены.",
            parse_mode='Markdown'
        )
        
        return WAITING_UNIVERSAL_DATA
    
    async def select_platforms_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню выбора платформ"""
        query = update.callback_query
        await query.answer()
        
        keyboard = []
        for platform_id, platform_info in self.platform_templates.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"🏨 {platform_info['name']}", 
                    callback_data=f'platform_{platform_id}'
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("✅ Все платформы", callback_data='platform_all')],
            [InlineKeyboardButton("🔙 Назад", callback_data='smart_menu')]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Выберите платформы для создания объявлений**\n\n"
            "Выберите одну или несколько платформ:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WAITING_PLATFORM_SELECTION
    
    async def handle_platform_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора платформ"""
        query = update.callback_query
        await query.answer()
        
        platform = query.data.replace('platform_', '')
        context.user_data['selected_platforms'] = [platform] if platform != 'all' else list(self.platform_templates.keys())
        
        # Показываем форму для ввода данных
        platforms_text = ", ".join([self.platform_templates[p]['name'] for p in context.user_data['selected_platforms']])
        
        await query.edit_message_text(
            f"📝 **Введите данные для: {platforms_text}**\n\n"
            "Эти данные будут использованы для создания объявлений:\n\n"
            "```\n"
            "email: ваш_email@example.com\n"
            "password: ваш_пароль\n"
            "hotel_name: Название отеля\n"
            "hotel_address: Адрес отеля\n"
            "hotel_type: Тип отеля\n"
            "city: Город\n"
            "phone: Телефон\n"
            "website: Сайт (необязательно)\n"
            "contact_name: Контактное лицо\n"
            "contact_email: Контактный email\n"
            "description: Описание отеля\n"
            "amenities: Удобства (через запятую)\n"
            "```\n\n"
            "Или отправьте 'отмена' для отмены.",
            parse_mode='Markdown'
        )
        
        return WAITING_UNIVERSAL_DATA
    
    async def handle_universal_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка универсальных данных"""
        text = update.message.text.strip()
        
        if text.lower() in ['отмена', 'cancel', 'отменить']:
            keyboard = [
                [InlineKeyboardButton("🔙 В меню", callback_data='smart_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Создание объявлений отменено.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        # Парсим данные
        user_data = {}
        lines = text.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                user_data[key] = value
        
        if not user_data:
            await update.message.reply_text(
                "❌ Неверный формат данных.\n"
                "Попробуйте еще раз или отправьте 'отмена'."
            )
            return WAITING_UNIVERSAL_DATA
        
        # Получаем выбранные платформы
        selected_platforms = context.user_data.get('selected_platforms', list(self.platform_templates.keys()))
        
        # Начинаем создание объявлений
        await update.message.reply_text(
            f"🚀 **Начинаем создание объявлений на {len(selected_platforms)} платформах...**\n\n"
            f"Платформы: {', '.join([self.platform_templates[p]['name'] for p in selected_platforms])}\n\n"
            "Браузеры откроются автоматически и выполнят все действия.\n"
            "Не закрывайте браузеры во время выполнения!"
        )
        
        # Запускаем создание объявлений на всех платформах
        asyncio.create_task(self.create_advertisements_on_all_platforms(
            selected_platforms, user_data, update.message.chat_id
        ))
        
        return ConversationHandler.END
    
    async def create_advertisements_on_all_platforms(self, platforms, user_data, chat_id):
        """Создание объявлений на всех выбранных платформах"""
        results = {}
        
        for platform in platforms:
            try:
                await self.send_message_to_chat(
                    chat_id,
                    f"🔄 Создаю объявление на {self.platform_templates[platform]['name']}..."
                )
                
                # Получаем рекордер для платформы
                recorder = self.recording_manager.get_recorder(platform)
                
                # Ищем доступные шаблоны
                available_recordings = recorder.get_available_recordings()
                
                if available_recordings:
                    # Берем последний созданный шаблон
                    latest_recording = available_recordings[-1]
                    
                    # Загружаем и воспроизводим
                    success = recorder.load_recording(latest_recording)
                    if success:
                        result = recorder.replay_actions(user_data, delay=1.5)
                        results[platform] = {
                            'success': result,
                            'template': latest_recording
                        }
                        
                        status = "✅ Успешно" if result else "⚠️ С ошибками"
                        await self.send_message_to_chat(
                            chat_id,
                            f"{status} {self.platform_templates[platform]['name']} - {latest_recording}"
                        )
                    else:
                        results[platform] = {'success': False, 'error': 'Не удалось загрузить шаблон'}
                        await self.send_message_to_chat(
                            chat_id,
                            f"❌ {self.platform_templates[platform]['name']} - ошибка загрузки шаблона"
                        )
                else:
                    results[platform] = {'success': False, 'error': 'Нет доступных шаблонов'}
                    await self.send_message_to_chat(
                        chat_id,
                        f"❌ {self.platform_templates[platform]['name']} - нет шаблонов. Создайте шаблон через record_actions.py"
                    )
                    
            except Exception as e:
                results[platform] = {'success': False, 'error': str(e)}
                await self.send_message_to_chat(
                    chat_id,
                    f"❌ {self.platform_templates[platform]['name']} - ошибка: {str(e)}"
                )
        
        # Отправляем итоговый отчет
        await self.send_final_report(chat_id, results)
    
    async def send_final_report(self, chat_id, results):
        """Отправить итоговый отчет"""
        success_count = sum(1 for r in results.values() if r.get('success', False))
        total_count = len(results)
        
        report = f"📊 **Итоговый отчет**\n\n"
        report += f"✅ Успешно: {success_count}/{total_count}\n\n"
        
        for platform, result in results.items():
            platform_name = self.platform_templates[platform]['name']
            if result.get('success', False):
                report += f"✅ {platform_name}: Успешно\n"
            else:
                error = result.get('error', 'Неизвестная ошибка')
                report += f"❌ {platform_name}: {error}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data='smart_create_all')],
            [InlineKeyboardButton("🔙 В меню", callback_data='smart_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.send_message_to_chat(chat_id, report, reply_markup)
    
    async def show_templates_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статус шаблонов"""
        query = update.callback_query
        await query.answer()
        
        status_text = "📋 **Статус шаблонов**\n\n"
        
        for platform_id, platform_info in self.platform_templates.items():
            recorder = self.recording_manager.get_recorder(platform_id)
            recordings = recorder.get_available_recordings()
            
            if recordings:
                status_text += f"✅ {platform_info['name']}: {len(recordings)} шаблонов\n"
                for recording in recordings[-3:]:  # Показываем последние 3
                    status_text += f"   • {recording}\n"
            else:
                status_text += f"❌ {platform_info['name']}: нет шаблонов\n"
        
        status_text += "\n💡 Для создания шаблонов используйте: `python record_actions.py`"
        
        keyboard = [
            [InlineKeyboardButton("🔙 В меню", callback_data='smart_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_message_to_chat(self, chat_id, text, reply_markup=None):
        """Отправить сообщение в чат (заглушка)"""
        # Здесь должна быть интеграция с основным ботом
        print(f"Сообщение для {chat_id}: {text}")
    
    def get_handlers(self):
        """Получить обработчики для интеграции с ботом"""
        smart_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_universal_creation, pattern='^smart_create_all$'),
                CallbackQueryHandler(self.select_platforms_menu, pattern='^smart_select_platforms$'),
                CallbackQueryHandler(self.handle_platform_selection, pattern='^platform_')
            ],
            states={
                WAITING_UNIVERSAL_DATA: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_universal_data)
                ],
                WAITING_PLATFORM_SELECTION: [
                    CallbackQueryHandler(self.handle_platform_selection, pattern='^platform_')
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.show_smart_menu, pattern='^smart_menu$')
            ],
            per_chat=True
        )
        
        return [
            smart_conv_handler,
            CallbackQueryHandler(self.show_smart_menu, pattern='^smart_menu$'),
            CallbackQueryHandler(self.show_templates_status, pattern='^smart_templates$'),
        ] 
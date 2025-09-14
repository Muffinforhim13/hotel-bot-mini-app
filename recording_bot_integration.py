import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from action_recorder import RecordingManager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_REPLAY_DATA = 1002
WAITING_RECORDING_FILENAME = 1003

class RecordingBotIntegration:
    """Интеграция системы воспроизведения действий с Telegram ботом"""
    
    def __init__(self):
        self.recording_manager = RecordingManager()
        self.user_recordings = {}  # Хранение записей пользователей
    
    async def show_recording_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню воспроизведения действий"""
        keyboard = [
            [InlineKeyboardButton("📋 Мои записи", callback_data='recording_list')],
            [InlineKeyboardButton("▶️ Воспроизвести", callback_data='recording_replay')],
            [InlineKeyboardButton("🏨 Создать объявление", callback_data='create_advertisement')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🎬 **Система автоматизации объявлений**\n\n"
        text += "Эта система позволяет:\n"
        text += "• Использовать записанные шаблоны\n"
        text += "• Автоматически создавать объявления\n"
        text += "• Работать с несколькими платформами\n"
        text += "• Экономить время на рутинных задачах\n\n"
        text += "Выберите действие:"
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_recordings_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список записей пользователя"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_recordings = self.user_recordings.get(user_id, [])
        
        if not user_recordings:
            keyboard = [
                [InlineKeyboardButton("📝 Создать объявление", callback_data='create_advertisement')],
                [InlineKeyboardButton("🔙 Назад", callback_data='recording_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📋 **Мои записи**\n\n"
                "У вас пока нет сохраненных записей.\n"
                "Используйте функцию создания объявления!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Создаем кнопки для каждой записи
        keyboard = []
        for i, recording in enumerate(user_recordings[:10]):  # Показываем первые 10
            filename = recording['filename']
            platform = recording['platform']
            created_at = recording['created_at'][:10]  # Только дата
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 {platform.title()} ({created_at})",
                    callback_data=f'recording_view_{filename}'
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("📝 Создать объявление", callback_data='create_advertisement')],
            [InlineKeyboardButton("🔙 Назад", callback_data='recording_menu')]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📋 **Мои записи** ({len(user_recordings)})\n\n"
            f"Выберите запись для просмотра или воспроизведения:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def view_recording(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотреть запись"""
        query = update.callback_query
        await query.answer()
        
        filename = query.data.replace('recording_view_', '')
        
        # Получаем предварительный просмотр записи
        recorder = self.recording_manager.get_recorder('ostrovok')  # Временное решение
        preview = recorder.preview_recording(filename)
        
        keyboard = [
            [InlineKeyboardButton("▶️ Воспроизвести", callback_data=f'recording_replay_{filename}')],
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f'recording_delete_{filename}')],
            [InlineKeyboardButton("🔙 К списку", callback_data='recording_list')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            preview,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_replay_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс воспроизведения"""
        query = update.callback_query
        await query.answer()
        
        # Определяем, какая запись выбрана
        if 'recording_replay_' in query.data:
            filename = query.data.replace('recording_replay_', '')
            context.user_data['replay_filename'] = filename
        else:
            # Показываем список записей для выбора
            return await self.show_recordings_list(update, context)
        
        keyboard = [
            [InlineKeyboardButton("📝 Ввести данные", callback_data='replay_enter_data')],
            [InlineKeyboardButton("🔙 Назад", callback_data='recording_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"▶️ **Воспроизведение записи**\n\n"
            f"📁 Файл: {filename}\n\n"
            f"Для воспроизведения нужно ввести данные:\n"
            f"• Email и пароль\n"
            f"• Название отеля\n"
            f"• Адрес и другие данные\n\n"
            f"Нажмите 'Ввести данные' для продолжения.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WAITING_REPLAY_DATA
    
    async def enter_replay_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ввод данных для воспроизведения"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "📝 **Введите данные для воспроизведения**\n\n"
            "Отправьте данные в следующем формате:\n\n"
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
            "```\n\n"
            "Или отправьте 'отмена' для отмены.",
            parse_mode='Markdown'
        )
        
        return WAITING_REPLAY_DATA
    
    async def handle_replay_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка введенных данных для воспроизведения"""
        text = update.message.text.strip()
        
        if text.lower() in ['отмена', 'cancel', 'отменить']:
            keyboard = [
                [InlineKeyboardButton("🔙 В меню", callback_data='recording_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ Воспроизведение отменено.",
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
            return WAITING_REPLAY_DATA
        
        # Получаем имя файла
        filename = context.user_data.get('replay_filename')
        if not filename:
            await update.message.reply_text("❌ Ошибка: файл записи не найден.")
            return ConversationHandler.END
        
        # Начинаем воспроизведение
        keyboard = [
            [InlineKeyboardButton("⏹ Остановить", callback_data='replay_stop')],
            [InlineKeyboardButton("🔙 В меню", callback_data='recording_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "▶️ **Начинаем воспроизведение...**\n\n"
            f"📁 Файл: {filename}\n"
            f"🏷️ Платформа: {user_data.get('platform', 'unknown')}\n\n"
            "Браузер откроется автоматически и выполнит все действия.\n"
            "Не закрывайте браузер во время выполнения!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Запускаем воспроизведение в отдельном потоке
        asyncio.create_task(self.run_replay(filename, user_data, update.message.chat_id))
        
        return ConversationHandler.END
    
    async def create_advertisement_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс создания объявления"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🏨 Ostrovok", callback_data='create_ad_ostrovok')],
            [InlineKeyboardButton("🏨 Bronevik", callback_data='create_ad_bronevik')],
            [InlineKeyboardButton("🏨 101 Hotels", callback_data='create_ad_101hotels')],
            [InlineKeyboardButton("🔙 Назад", callback_data='recording_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏨 **Создание объявления**\n\n"
            "Выберите платформу для создания объявления:\n\n"
            "Система автоматически:\n"
            "• Войдет в аккаунт\n"
            "• Заполнит форму объявления\n"
            "• Опубликует объявление\n"
            "• Сохранит результат",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_platform_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора платформы для создания объявления"""
        query = update.callback_query
        await query.answer()
        
        platform = query.data.replace('create_ad_', '')
        context.user_data['selected_platform'] = platform
        
        # Показываем форму для ввода данных
        await query.edit_message_text(
            f"📝 **Создание объявления на {platform.title()}**\n\n"
            "Введите данные для объявления:\n\n"
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
        
        return WAITING_REPLAY_DATA
    
    async def run_replay(self, filename, user_data, chat_id):
        """Запуск воспроизведения в отдельном потоке"""
        try:
            # Определяем платформу из имени файла
            platform = 'ostrovok'  # По умолчанию
            if 'bronevik' in filename:
                platform = 'bronevik'
            elif '101hotels' in filename:
                platform = '101hotels'
            
            recorder = self.recording_manager.get_recorder(platform)
            success = recorder.load_recording(filename)
            
            if success:
                # Воспроизводим действия
                result = recorder.replay_actions(user_data, delay=1.5)
                
                if result:
                    await self.send_message_to_chat(
                        chat_id,
                        "✅ **Воспроизведение завершено успешно!**\n\n"
                        "Все действия выполнены автоматически.\n"
                        "Проверьте результат в браузере."
                    )
                else:
                    await self.send_message_to_chat(
                        chat_id,
                        "⚠️ **Воспроизведение завершено с ошибками**\n\n"
                        "Некоторые действия могли не выполниться.\n"
                        "Проверьте результат в браузере."
                    )
            else:
                await self.send_message_to_chat(
                    chat_id,
                    "❌ **Ошибка при загрузке записи**\n\n"
                    "Не удалось загрузить файл записи."
                )
                
        except Exception as e:
            await self.send_message_to_chat(
                chat_id,
                f"❌ **Ошибка при воспроизведении**\n\n"
                f"Произошла ошибка: {str(e)}"
            )
    
    async def send_message_to_chat(self, chat_id, text):
        """Отправить сообщение в чат (заглушка)"""
        # Здесь должна быть интеграция с основным ботом
        print(f"Сообщение для {chat_id}: {text}")
    
    def get_handlers(self):
        """Получить обработчики для интеграции с ботом"""
        recording_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_replay_flow, pattern='^recording_replay'),
                CallbackQueryHandler(self.create_advertisement_flow, pattern='^create_advertisement$'),
                CallbackQueryHandler(self.handle_platform_selection, pattern='^create_ad_')
            ],
            states={
                WAITING_REPLAY_DATA: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_replay_data),
                    CallbackQueryHandler(self.enter_replay_data, pattern='^replay_enter_data$')
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.show_recording_menu, pattern='^recording_menu$')
            ],
            per_chat=True
        )
        
        return [
            recording_conv_handler,
            CallbackQueryHandler(self.show_recording_menu, pattern='^recording_menu$'),
            CallbackQueryHandler(self.show_recordings_list, pattern='^recording_list$'),
            CallbackQueryHandler(self.view_recording, pattern='^recording_view_'),
        ]


# Импорт для интеграции с основным ботом
from datetime import datetime 
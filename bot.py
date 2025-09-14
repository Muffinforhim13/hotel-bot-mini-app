import logging
import asyncio
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from config import BOT_TOKEN, BNOVO_API_KEY
from enhanced_ostrovok_manager import EnhancedOstrovokManager as OstrovokManager
from bnovo_manager import BnovoManager
from hotels101_manager import Hotels101Manager
from bronevik_manager import BronevikManager
import os

# Пробуем импортировать упрощенную версию RPA-менеджера (без PyAutoGUI)
try:
    from rpa_manager_simple import SimpleRPAManager as RPAManager
    RPA_AVAILABLE = True
    print("✅ Используется упрощенная версия RPA-менеджера (без PyAutoGUI)")
except ImportError as e:
    print(f"Предупреждение: Не удалось импортировать упрощенную версию RPA-менеджера: {e}")
    # Пробуем импортировать полную версию RPA-менеджера
    try:
        from rpa_manager import RPAManager
        RPA_AVAILABLE = True
        print("✅ Используется полная версия RPA-менеджера (с PyAutoGUI)")
    except ImportError as e2:
        print(f"Ошибка: Не удалось импортировать полную версию RPA-менеджера: {e2}")
        RPA_AVAILABLE = False

# Импортируем AutoHotkey автоматизацию
try:
    from autohotkey_automation import AutoHotkeyAutomation
    AHK_AVAILABLE = True
    print("✅ AutoHotkey автоматизация доступна")
except ImportError as e:
    print(f"Предупреждение: AutoHotkey автоматизация недоступна: {e}")
    AHK_AVAILABLE = False

# Импортируем интегрированный менеджер
try:
    from telegram_integrated_manager import TelegramIntegratedManager
    INTEGRATED_AVAILABLE = True
    print("✅ Интегрированная автоматизация доступна")
except ImportError as e:
    print(f"Предупреждение: Интегрированная автоматизация недоступна: {e}")
    INTEGRATED_AVAILABLE = False

# Импортируем PyAutoGUI интеграцию
try:
    from pyautogui_bot_integration import PyAutoGUIBotIntegration
    PYAUTOGUI_AVAILABLE = True
    print("✅ PyAutoGUI интеграция доступна")
except ImportError as e:
    print(f"Предупреждение: PyAutoGUI интеграция недоступна: {e}")
    PYAUTOGUI_AVAILABLE = False

import sqlite3

# Состояния для ConversationHandler
WAITING_EMAIL, WAITING_PASSWORD, WAITING_2FA, WAITING_OBJECT_NAME, WAITING_OBJECT_TYPE, WAITING_OBJECT_CITY, WAITING_OBJECT_ADDRESS = range(7)

# Состояния для создания объявления Ostrovok
WAITING_AD_NAME, WAITING_AD_TYPE, WAITING_AD_REGION, WAITING_AD_ADDRESS, WAITING_AD_CHAIN = range(100, 105)

# Состояния для 101 hotels
WAITING_101HOTELS_EMAIL, WAITING_101HOTELS_PASSWORD = range(200, 202)
WAITING_101HOTELS_CONTACT_NAME, WAITING_101HOTELS_CONTACT_PHONE, WAITING_101HOTELS_CONTACT_EMAIL = range(202, 205)

# Состояния для RPA
WAITING_RPA_EMAIL, WAITING_RPA_PASSWORD = range(300, 302)
WAITING_HOTEL_NAME = 302

# Состояния для AutoHotkey автоматизации
WAITING_AHK_PLATFORM = 400
WAITING_AHK_EMAIL = 401
WAITING_AHK_PASSWORD = 402
WAITING_AHK_2FA = 403
WAITING_AHK_OBJECT_NAME = 404
WAITING_AHK_OBJECT_TYPE = 405
WAITING_AHK_OBJECT_CITY = 406
WAITING_AHK_OBJECT_ADDRESS = 407
WAITING_AHK_CONFIRMATION = 408

# Состояния для интегрированной автоматизации
WAITING_INTEGRATED_PLATFORM = 500
WAITING_INTEGRATED_EMAIL = 501
WAITING_INTEGRATED_PASSWORD = 502
WAITING_INTEGRATED_2FA = 503
WAITING_INTEGRATED_OBJECT_NAME = 504
WAITING_INTEGRATED_OBJECT_ADDRESS = 505

# Состояния для PyAutoGUI интеграции
WAITING_PYAUTOGUI_EMAIL = 600
WAITING_PYAUTOGUI_PASSWORD = 601
WAITING_PYAUTOGUI_2FA = 602
WAITING_PYAUTOGUI_OBJECT_NAME = 603
WAITING_PYAUTOGUI_HOTEL_TYPE = 604

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- SQLite DB INIT ---
# (перенесено в db.py)
# --- END SQLITE INIT ---

class HotelBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.ostrovok_manager = OstrovokManager()
        self.bnovo_manager = BnovoManager(BNOVO_API_KEY) if BNOVO_API_KEY else None
        self.hotels101_manager = Hotels101Manager()
        self.bronevik_manager = BronevikManager()
        
        # Инициализируем RPA-менеджер только если он доступен
        if RPA_AVAILABLE:
            try:
                self.rpa_manager = RPAManager()
                print("✅ RPA-менеджер успешно инициализирован")
            except Exception as e:
                print(f"❌ Ошибка при инициализации RPA-менеджера: {e}")
                self.rpa_manager = None
        else:
            self.rpa_manager = None
            print("RPA-функции недоступны из-за проблем с зависимостями")
        
        # Инициализируем AutoHotkey автоматизацию
        if AHK_AVAILABLE:
            try:
                self.ahk_automation = AutoHotkeyAutomation()
                print("✅ AutoHotkey автоматизация успешно инициализирована")
            except Exception as e:
                print(f"❌ Ошибка при инициализации AutoHotkey автоматизации: {e}")
                self.ahk_automation = None
        else:
            self.ahk_automation = None
            print("AutoHotkey автоматизация недоступна")
        
        # Инициализируем интегрированный менеджер
        if INTEGRATED_AVAILABLE:
            try:
                self.integrated_manager = TelegramIntegratedManager()
                print("✅ Интегрированный менеджер успешно инициализирован")
            except Exception as e:
                print(f"❌ Ошибка при инициализации интегрированного менеджера: {e}")
                self.integrated_manager = None
        else:
            self.integrated_manager = None
            print("Интегрированный менеджер недоступен")
        
        # Инициализируем PyAutoGUI интеграцию
        if PYAUTOGUI_AVAILABLE:
            try:
                self.pyautogui_integration = PyAutoGUIBotIntegration()
                print("✅ PyAutoGUI интеграция успешно инициализирована")
            except Exception as e:
                print(f"❌ Ошибка при инициализации PyAutoGUI интеграции: {e}")
                self.pyautogui_integration = None
        else:
            self.pyautogui_integration = None
            print("PyAutoGUI интеграция недоступна")
        
        self.user_sessions = {}  # Хранение сессий пользователей
        self.setup_handlers()
        self.setup_bnovo_notifications()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("bnovo", self.bnovo_command))
        self.application.add_handler(CommandHandler("notifications", self.notifications_command))
        self.application.add_handler(CommandHandler("pyautogui", self.pyautogui_command))
        
        # СНАЧАЛА ConversationHandler!
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("ostrovok_login", self.start_ostrovok_login),
                CallbackQueryHandler(self.start_ostrovok_login, pattern='^ostrovok_login$')
            ],
            states={
                WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_email)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_password)],
                WAITING_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_2fa_code)],
                WAITING_OBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_object_name)],
                WAITING_OBJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_object_type)],
                WAITING_OBJECT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_object_city)],
                WAITING_OBJECT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_object_address)]
            },
            fallbacks=[CallbackQueryHandler(self.cancel_login, pattern='^cancel_login$')],
            per_chat=True
        )
        self.application.add_handler(conv_handler)
        
        # ConversationHandler для AutoHotkey автоматизации
        if self.ahk_automation:
            ahk_conv_handler = ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(self.start_ahk_automation, pattern='^ahk_automation$'),
                    CallbackQueryHandler(self.start_ahk_platform_selection, pattern='^ahk_platform_')
                ],
                states={
                    WAITING_AHK_PLATFORM: [CallbackQueryHandler(self.handle_ahk_platform_selection, pattern='^ahk_platform_')],
                    WAITING_AHK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_email)],
                    WAITING_AHK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_password)],
                    WAITING_AHK_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_2fa)],
                    WAITING_AHK_OBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_object_name)],
                    WAITING_AHK_OBJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_object_type)],
                    WAITING_AHK_OBJECT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_object_city)],
                    WAITING_AHK_OBJECT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ahk_object_address)],
                    WAITING_AHK_CONFIRMATION: [CallbackQueryHandler(self.handle_ahk_confirmation, pattern='^ahk_confirm_')]
                },
                fallbacks=[CallbackQueryHandler(self.cancel_ahk_automation, pattern='^cancel_ahk$')],
                per_chat=True
            )
            self.application.add_handler(ahk_conv_handler)
        
        # ConversationHandler для создания объявления Ostrovok
        ad_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_create_ad, pattern='^ostrovok_create_ad$')],
            states={
                WAITING_AD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_ad_name)],
                WAITING_AD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_ad_type)],
                WAITING_AD_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_ad_region)],
                WAITING_AD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_ad_address)],
                WAITING_AD_CHAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_ad_chain)],
            },
            fallbacks=[],
            per_chat=True
        )
        self.application.add_handler(ad_conv_handler)

        # ConversationHandler для входа в 101 hotels
        hotels101_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_101hotels_login_conv, pattern='^101hotels_enter_credentials$')],
            states={
                WAITING_101HOTELS_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_101hotels_email)],
                WAITING_101HOTELS_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_101hotels_password)],
            },
            fallbacks=[CallbackQueryHandler(self.cancel_101hotels_login, pattern='^cancel_101hotels_login$')],
            per_chat=True
        )
        
        # ConversationHandler для ввода контактной информации 101 hotels
        hotels101_contact_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_101hotels_contact_conv, pattern='^101hotels_contact_info$')],
            states={
                WAITING_101HOTELS_CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_101hotels_contact_name)],
                WAITING_101HOTELS_CONTACT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_101hotels_contact_phone)],
                WAITING_101HOTELS_CONTACT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_101hotels_contact_email)],
            },
            fallbacks=[CallbackQueryHandler(self.cancel_101hotels_contact, pattern='^cancel_101hotels_contact$')],
            per_chat=True
        )
        self.application.add_handler(hotels101_conv_handler)
        self.application.add_handler(hotels101_contact_conv_handler)

        # ConversationHandler для RPA
        rpa_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_rpa_platform_login, pattern='^rpa_.*_login$'),
                CallbackQueryHandler(self.start_rpa_platform_add_object, pattern='^rpa_.*_add_object$')
            ],
            states={
                WAITING_RPA_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_rpa_email)],
                WAITING_RPA_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_rpa_password)],
                WAITING_OBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_hotel_name)],
            },
            fallbacks=[CallbackQueryHandler(self.cancel_rpa, pattern='^cancel_rpa$')],
            per_chat=True
        )
        self.application.add_handler(rpa_conv_handler)
        
        # ConversationHandler для интегрированной автоматизации
        if self.integrated_manager:
            integrated_conv_handler = ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(self.start_integrated_automation, pattern='^integrated_automation$'),
                    CallbackQueryHandler(self.start_integrated_platform_selection, pattern='^integrated_platform_')
                ],
                states={
                    WAITING_INTEGRATED_PLATFORM: [CallbackQueryHandler(self.handle_integrated_platform_selection, pattern='^integrated_platform_')],
                    WAITING_INTEGRATED_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_integrated_email)],
                    WAITING_INTEGRATED_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_integrated_password)],
                    WAITING_INTEGRATED_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_integrated_2fa)],
                    WAITING_INTEGRATED_OBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_integrated_object_name)],
                    WAITING_INTEGRATED_OBJECT_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_integrated_object_address)]
                },
                fallbacks=[CallbackQueryHandler(self.cancel_integrated_automation, pattern='^cancel_integrated$')],
                per_chat=True
            )
            self.application.add_handler(integrated_conv_handler)
        
        # ConversationHandler для PyAutoGUI интеграции
        if self.pyautogui_integration:
            pyautogui_conv_handler = ConversationHandler(
                entry_points=[
                    CallbackQueryHandler(self.start_pyautogui_automation, pattern='^pyautogui_automation$'),
                    CallbackQueryHandler(self.start_pyautogui_login, pattern='^pyautogui_login_start$'),
                    CallbackQueryHandler(self.start_pyautogui_add_object, pattern='^pyautogui_add_object_start$')
                ],
                states={
                    WAITING_PYAUTOGUI_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_pyautogui_email)],
                    WAITING_PYAUTOGUI_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_pyautogui_password)],
                    WAITING_PYAUTOGUI_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_pyautogui_2fa)],
                    WAITING_PYAUTOGUI_OBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_pyautogui_object_name)],
                    WAITING_PYAUTOGUI_HOTEL_TYPE: [CallbackQueryHandler(self.handle_pyautogui_hotel_type, pattern='^hotel_type_')]
                },
                fallbacks=[CallbackQueryHandler(self.cancel_pyautogui_automation, pattern='^cancel_pyautogui$')],
                per_chat=True
            )
            self.application.add_handler(pyautogui_conv_handler)
        
        # Добавляем обработчики для умной системы автоматизации
        try:
            from smart_bot_integration import SmartBotIntegration
            smart_integration = SmartBotIntegration()
            for handler in smart_integration.get_handlers():
                self.application.add_handler(handler)
            print("✅ Обработчики умной системы автоматизации добавлены")
        except ImportError as e:
            print(f"⚠️ Умная система автоматизации недоступна: {e}")
        
        # Добавляем обработчики для системы записи действий
        try:
            from recording_bot_integration import RecordingBotIntegration
            recording_integration = RecordingBotIntegration()
            for handler in recording_integration.get_handlers():
                self.application.add_handler(handler)
            print("✅ Обработчики системы записи действий добавлены")
        except ImportError as e:
            print(f"⚠️ Система записи действий недоступна: {e}")
        
        # ПОТОМ общий CallbackQueryHandler
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    def setup_bnovo_notifications(self):
        """Настройка автоматических уведомлений от Bnovo"""
        # Уведомления будут запущены после старта бота
        self.bnovo_notifications_enabled = bool(self.bnovo_manager)
    
    async def check_new_bookings_job(self, context):
        """Job для проверки новых бронирований"""
        try:
            await self.check_new_bookings()
        except Exception as e:
            logger.error(f"Ошибка в job уведомлений: {e}")
    
    async def check_new_bookings(self):
        """Проверка новых бронирований и отправка уведомлений"""
        if not self.bnovo_manager:
            return
        
        success, bookings = self.bnovo_manager.get_new_bookings(hours_back=1)
        if not success or not isinstance(bookings, list):
            return
        
        # Отправляем уведомления всем активным пользователям
        for user_id, session in self.user_sessions.items():
            if session.get('bnovo_notifications_enabled', True):
                for booking in bookings:
                    message = self.bnovo_manager.format_booking_message(booking)
                    try:
                        await self.application.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
    
    async def start_command(self, update, context):
        keyboard = [
            [InlineKeyboardButton("📱 Mini App", web_app={'url': 'http://localhost:8000'}, callback_data='mini_app')],
            [InlineKeyboardButton("🏨 Платформы", callback_data='platforms')],
            [InlineKeyboardButton("🧠 Умная автоматизация", callback_data='smart_menu')],
            [InlineKeyboardButton("🎬 Автоматизация объявлений", callback_data='recording_menu')],
            [InlineKeyboardButton("🤖 RPA-Автоматизация", callback_data='rpa_menu')] if self.rpa_manager else None,
            [InlineKeyboardButton("⚡ AutoHotkey Автоматизация", callback_data='ahk_automation')] if self.ahk_automation else None,
            [InlineKeyboardButton("🚀 Интегрированная Автоматизация", callback_data='integrated_automation')] if self.integrated_manager else None,
            [InlineKeyboardButton("🔗 Bnovo PMS", callback_data='bnovo_dashboard')] if self.bnovo_manager else None,
            [InlineKeyboardButton("🔔 Уведомления", callback_data='notifications_settings')]
        ]
        keyboard = [row for row in keyboard if row is not None]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = "Добро пожаловать в бота управления отелями! 🏨\n\n"
        welcome_text += "📱 **Mini App доступен!** - используйте удобный веб-интерфейс для всех функций!\n\n"
        
        if self.bnovo_manager:
            welcome_text += "✅ **Bnovo PMS подключен** - получайте уведомления со всех площадок!\n\n"
        else:
            welcome_text += "⚠️ **Bnovo PMS не настроен** - добавьте API ключ в config.py\n\n"
        
        welcome_text += "🧠 **Умная автоматизация** - введите данные один раз, получите объявления на всех платформах!\n\n"
        welcome_text += "🎬 **Автоматизация объявлений** - создавайте объявления на всех платформах!\n\n"
        
        if self.rpa_manager:
            welcome_text += "🤖 **RPA-автоматизация доступна** - автоматический вход и создание объектов!\n\n"
        else:
            welcome_text += "⚠️ **RPA-автоматизация недоступна** - проблемы с зависимостями\n\n"
            
        welcome_text += "Выберите действие:"

        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == 'platforms':
            await self.show_platforms_menu(query)
        elif query.data == 'smart_menu':
            # Импортируем и используем умную интеграцию
            try:
                from smart_bot_integration import SmartBotIntegration
                smart_integration = SmartBotIntegration()
                await smart_integration.show_smart_menu(update, context)
            except ImportError:
                await query.answer("❌ Модуль умной автоматизации недоступен")
        elif query.data == 'recording_menu':
            # Импортируем и используем интеграцию записи
            try:
                from recording_bot_integration import RecordingBotIntegration
                recording_integration = RecordingBotIntegration()
                await recording_integration.show_recording_menu(update, context)
            except ImportError:
                await query.answer("❌ Модуль автоматизации недоступен")
        elif query.data == 'back_to_main':
            await self.start_command(update, context)
        elif query.data == 'platform_ostrovok':
            user_id = query.from_user.id
            if user_id in self.user_sessions and self.user_sessions[user_id].get('ostrovok_logged_in'):
                await self.show_ostrovok_main_menu(query)
            else:
                keyboard = [
                    [InlineKeyboardButton("🔐 Войти в панель управления", callback_data='ostrovok_login')],
                    [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ Вы не авторизованы в панели управления\n\nВойдите, чтобы продолжить:",
                    reply_markup=reply_markup
                )
        elif query.data == 'platform_bronevik':
            user_id = query.from_user.id
            if user_id in self.user_sessions and self.user_sessions[user_id].get('bronevik_logged_in'):
                await self.show_bronevik_main_menu(query)
            else:
                keyboard = [
                    [InlineKeyboardButton("🔐 Войти в панель управления", callback_data='bronevik_login')],
                    [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ Вы не авторизованы в панели управления Bronevik\n\nВойдите, чтобы продолжить:",
                    reply_markup=reply_markup
                )
        elif query.data == 'platform_101hotels':
            user_id = query.from_user.id
            
            # Проверяем, авторизован ли пользователь
            if user_id in self.user_sessions and self.user_sessions[user_id].get('101hotels_logged_in'):
                # Если пользователь уже авторизован, показываем главное меню
                await self.show_101hotels_main_menu(query)
                return
            
            # Сразу открываем главную страницу 101hotels
            try:
                # Безопасно открываем главную страницу
                success = self.hotels101_manager.open_dashboard_safe()
                
                if success:
                    # Показываем меню с опциями
                    keyboard = [
                        [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='101hotels_login')],
                        [InlineKeyboardButton("➕ Создать новый отель", callback_data='101hotels_create_new')],
                        [InlineKeyboardButton("🔒 Закрыть браузер", callback_data='101hotels_close_browser')],
                        [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "🏨 **101 Hotels Extranet**\n\n"
                        "✅ Главная страница открыта в браузере\n\n"
                        "Выберите действие:\n"
                        "• **Войти в аккаунт** - для работы с существующими отелями\n"
                        "• **Создать новый отель** - для регистрации нового объекта",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    # Если не удалось открыть страницу, показываем стандартное меню
                    keyboard = [
                        [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='101hotels_login')],
                        [InlineKeyboardButton("➕ Создать новый отель", callback_data='101hotels_create_new')],
                        [InlineKeyboardButton("🔒 Закрыть браузер", callback_data='101hotels_close_browser')],
                        [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "🏨 **101 Hotels Extranet**\n\n"
                        "⚠️ Не удалось открыть главную страницу\n\n"
                        "Выберите действие:\n"
                        "• **Войти в аккаунт** - для работы с существующими отелями\n"
                        "• **Создать новый отель** - для регистрации нового объекта",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
            except Exception as e:
                # В случае ошибки показываем стандартное меню
                keyboard = [
                    [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='101hotels_login')],
                    [InlineKeyboardButton("➕ Создать новый отель", callback_data='101hotels_create_new')],
                    [InlineKeyboardButton("🔒 Закрыть браузер", callback_data='101hotels_close_browser')],
                    [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "🏨 **101 Hotels Extranet**\n\n"
                    f"⚠️ Ошибка при открытии страницы: {str(e)}\n\n"
                    "Выберите действие:\n"
                    "• **Войти в аккаунт** - для работы с существующими отелями\n"
                    "• **Создать новый отель** - для регистрации нового объекта",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        elif query.data == 'ostrovok_bookings':
            await self.show_ostrovok_bookings(query)
        elif query.data == 'ostrovok_statistics':
            await self.show_ostrovok_statistics(query)
        elif query.data == 'ostrovok_rooms':
            await self.show_ostrovok_rooms(query)
        elif query.data == 'ostrovok_account':
            await self.show_ostrovok_account(query)
        elif query.data == 'ostrovok_logout':
            await self.ostrovok_logout(query)
        elif query.data == 'ostrovok_add_object':
            user_id = query.from_user.id
            email = self.user_sessions.get(user_id, {}).get('ostrovok_email')
            if not email:
                await query.edit_message_text("❌ Необходимо войти в аккаунт")
                return
            ok, msg = self.ostrovok_manager.click_add_object_button()
            if ok:
                # Показываем меню выбора типа объекта
                keyboard = [
                    [InlineKeyboardButton("🏨 Объект с номерами", callback_data='ostrovok_object_with_rooms')],
                    [InlineKeyboardButton("🏠 Жильё целиком", callback_data='ostrovok_whole_apartment')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "Выберите тип объекта:",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(f"❌ {msg}")
        elif query.data == 'ostrovok_object_with_rooms':
            ok, msg = self.ostrovok_manager.click_next_on_object_with_rooms()
            if ok:
                await query.edit_message_text("✅ Выбран объект с номерами. Введите название объекта (например, Ромашка):")
                return WAITING_OBJECT_NAME
            else:
                await query.edit_message_text(f"❌ {msg}")
        elif query.data == 'ostrovok_whole_apartment':
            ok, msg = self.ostrovok_manager.select_whole_apartment_and_next()
            if ok:
                await query.edit_message_text("✅ Выбрано жильё целиком. Введите название объекта (например, Ромашка):")
                return WAITING_OBJECT_NAME
            else:
                await query.edit_message_text(f"❌ {msg}")
        elif query.data == 'ostrovok_my_objects':
            objects = self.ostrovok_manager.get_my_objects()
            if objects:
                text = 'Ваши объекты:\n\n'
                for i, obj in enumerate(objects, 1):
                    text += f"{i}. {obj['name']}\n   {obj['address']}\n   ID: {obj['id']}\n   Статус: {obj['status']}\n\n"
                keyboard = [[InlineKeyboardButton('🔙 Назад', callback_data='ostrovok_back_to_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ Не удалось получить список объектов или объекты не найдены.")
        elif query.data == 'ostrovok_new_bookings':
            objects = self.ostrovok_manager.get_my_objects()
            if objects:
                keyboard = []
                for obj in objects:
                    keyboard.append([
                        InlineKeyboardButton(f"{obj['name']} (ID: {obj['id']})", callback_data=f"ostrovok_bookings_for_{obj['id']}")
                    ])
                keyboard.append([InlineKeyboardButton('🔙 Назад', callback_data='ostrovok_back_to_menu')])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Выберите объект для просмотра новых бронирований:", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ Не удалось получить список объектов или объекты не найдены.")
        elif query.data.startswith('ostrovok_bookings_for_'):
            object_id = query.data.replace('ostrovok_bookings_for_', '')
            bookings = self.ostrovok_manager.get_new_bookings_for_object(object_id)
            if bookings:
                text = f'Новые бронирования для объекта ID {object_id}:\n\n'
                for i, booking in enumerate(bookings, 1):
                    text += f"{i}. {booking}\n"
                keyboard = [[InlineKeyboardButton('🔙 Назад', callback_data='ostrovok_new_bookings')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await query.edit_message_text(f"Нет новых бронирований для объекта ID {object_id} или не удалось получить данные.")
        elif query.data == 'ostrovok_back_to_menu':
            await self.show_ostrovok_main_menu(query)
        # Новые обработчики для Bnovo
        elif query.data == 'bnovo_dashboard':
            await self.show_bnovo_dashboard(query)
        elif query.data == 'bnovo_bookings':
            await self.show_bnovo_bookings(query)
        elif query.data == 'bnovo_statistics':
            await self.show_bnovo_statistics(query)
        elif query.data == 'bnovo_new_bookings':
            await self.show_bnovo_new_bookings(query)
        elif query.data == 'notifications_settings':
            await self.show_notifications_settings(query)
        elif query.data == 'toggle_notifications':
            await self.toggle_notifications(query)
        elif query.data == 'pyautogui_menu':
            await self.show_pyautogui_menu(query)
        elif query.data == 'pyautogui_test':
            await self.pyautogui_test_coordinates(query)
        elif query.data == 'pyautogui_login_test':
            await self.pyautogui_login_test(query)
        elif query.data == 'pyautogui_login_start':
            await self.pyautogui_login_start(query)
        elif query.data == 'pyautogui_add_object_test':
            await self.pyautogui_add_object_test(query)
        elif query.data == 'pyautogui_screen_info':
            await self.pyautogui_screen_info(query)
        elif query.data == 'pyautogui_reload':
            await self.pyautogui_reload(query)
        elif query.data == 'bnovo_back_to_dashboard':
            await self.show_bnovo_dashboard(query)
        elif query.data == 'ostrovok_create_ad':
            await query.edit_message_text("Форма создания объявления (заглушка)")
        elif query.data == 'ostrovok_my_ads':
            await query.edit_message_text("Ваши объявления (заглушка)")
        # 101 Hotels handlers
        elif query.data == '101hotels_bookings':
            await self.show_101hotels_bookings(query)
        elif query.data == '101hotels_statistics':
            await self.show_101hotels_statistics(query)
        elif query.data == '101hotels_add_object':
            await self.show_101hotels_add_object(query)
        elif query.data == '101hotels_my_objects':
            await self.show_101hotels_my_objects(query)
        elif query.data == '101hotels_logout':
            await self.show_101hotels_logout(query)
        elif query.data == '101hotels_close_browser':
            await self.close_101hotels_browser(query)
        elif query.data == '101hotels_debug_page':
            await self.show_101hotels_debug_page(query)
        elif query.data == '101hotels_select_country':
            await self.show_101hotels_country_selection(query)
        elif query.data == '101hotels_next_step':
            await self.continue_101hotels_registration(query)
        elif query.data == '101hotels_login':
            await self.start_101hotels_login(query)
        elif query.data == '101hotels_create_new':
            await self.start_101hotels_create_new(query)
        elif query.data.startswith('101hotels_country_'):
            await self.select_101hotels_country(query)
        elif query.data == '101hotels_api_basic_info':
            await self.show_101hotels_api_basic_info_form(query)
        elif query.data == '101hotels_api_progress':
            await self.show_101hotels_api_progress(query)
        elif query.data == '101hotels_api_fields':
            await self.show_101hotels_api_fields(query)
        elif query.data == '101hotels_contact_info':
            await self.start_101hotels_contact_conv(query, context)
        # RPA handlers
        elif query.data == 'rpa_menu':
            await self.show_rpa_menu(query)
        elif query.data == 'rpa_platform_101hotels':
            await self.show_rpa_platform_menu(query, '101hotels')
        elif query.data == 'rpa_platform_ostrovok':
            await self.show_rpa_platform_menu(query, 'ostrovok')
        elif query.data == 'rpa_platform_bronevik':
            await self.show_rpa_platform_menu(query, 'bronevik')
        elif query.data == 'rpa_101hotels_login':
            await self.start_rpa_platform_login(query, context, '101hotels')
        elif query.data == 'rpa_ostrovok_login':
            await self.start_rpa_platform_login(query, context, 'ostrovok')
        elif query.data == 'rpa_bronevik_login':
            await self.start_rpa_platform_login(query, context, 'bronevik')
        elif query.data == 'rpa_101hotels_add_object':
            await self.start_rpa_platform_add_object(query, context, '101hotels')
        elif query.data == 'rpa_ostrovok_add_object':
            await self.start_rpa_platform_add_object(query, context, 'ostrovok')
        elif query.data == 'rpa_bronevik_add_object':
            await self.start_rpa_platform_add_object(query, context, 'bronevik')
        elif query.data == 'rpa_autohotkey':
            await self.create_autohotkey_script(query, context)
        elif query.data == 'ahk_automation':
            await self.start_ahk_automation(query, context)
        elif query.data == 'integrated_automation':
            if self.integrated_manager:
                await self.start_integrated_automation(update, context)
            else:
                await query.answer("❌ Интегрированная автоматизация недоступна")
        elif query.data == 'integrated_test_coordinates':
            if self.integrated_manager:
                await self.test_integrated_coordinates(query)
            else:
                await query.answer("❌ Интегрированная автоматизация недоступна")
        elif query.data.startswith('test_coords_'):
            if self.integrated_manager:
                platform = query.data.replace('test_coords_', '')
                result = self.integrated_manager.test_coordinates(platform)
                await query.edit_message_text(
                    f"🧪 **Результат тестирования {platform.upper()}**\n\n{result}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад", callback_data='integrated_automation')]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                await query.answer("❌ Интегрированная автоматизация недоступна")
        # Bronevik handlers
        elif query.data == 'bronevik_bookings':
            await self.show_bronevik_bookings(query)
        elif query.data == 'bronevik_statistics':
            await self.show_bronevik_statistics(query)
        elif query.data == 'bronevik_add_object':
            await query.edit_message_text("➕ Добавление объекта на Bronevik (в разработке)")
        elif query.data == 'bronevik_my_objects':
            await query.edit_message_text("🏨 Мои объекты на Bronevik (в разработке)")
        elif query.data == 'bronevik_logout':
            await query.edit_message_text("🚪 Выход из Bronevik (в разработке)")
    
    async def show_platforms_menu(self, query):
        """Показать меню платформ"""
        keyboard = [
            [InlineKeyboardButton("🏨 Ostrovok", callback_data='platform_ostrovok')],
            [InlineKeyboardButton("🏨 Bronevik", callback_data='platform_bronevik')],
            [InlineKeyboardButton("🏨 101 hotels", callback_data='platform_101hotels')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📋 Доступные платформы:\n\n"
            "Выберите платформу для управления:",
            reply_markup=reply_markup
        )
    
    async def show_platform_info(self, query, platform_name: str):
        """Показать информацию о выбранной платформе"""
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data=f'stats_{platform_name.lower().replace(" ", "_")}')],
            [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🏨 Платформа: {platform_name}\n\n"
            f"Здесь будет отображаться информация о платформе {platform_name}.\n\n"
            f"Доступные действия:\n"
            f"• Просмотр статистики\n"
            f"• Управление бронированиями\n"
            f"• Настройки интеграции",
            reply_markup=reply_markup
        )
    
    async def start_ostrovok_login(self, update, context):
        # Открываем сайт и форму входа
        if update.message:
            await update.message.reply_text("🔄 Открываю сайт extranet.ostrovok.ru и форму входа...")
        elif update.callback_query:
            await update.callback_query.edit_message_text("🔄 Открываю сайт extranet.ostrovok.ru и форму входа...")
        try:
            self.ostrovok_manager.open_login_page()
            # После открытия формы входа спрашиваем email
            if update.message:
                await update.message.reply_text("Введите ваш email для входа на Островок:")
            elif update.callback_query:
                await update.callback_query.edit_message_text("Введите ваш email для входа на Островок:")
            return WAITING_EMAIL
        except Exception as e:
            if update.message:
                await update.message.reply_text(f"Ошибка открытия сайта: {e}")
            elif update.callback_query:
                await update.callback_query.edit_message_text(f"Ошибка открытия сайта: {e}")
            if self.ostrovok_manager.driver:
                self.ostrovok_manager.driver.quit()
            return ConversationHandler.END

    async def get_email(self, update, context):
        email = update.message.text
        context.user_data['ostrovok_email'] = email
        try:
            self.ostrovok_manager.fill_email(email)
            # После ввода email спрашиваем пароль
            await update.message.reply_text("Введите ваш пароль:")
            return WAITING_PASSWORD
        except Exception as e:
            await update.message.reply_text(f"Ошибка ввода email: {e}")
            if self.ostrovok_manager.driver:
                self.ostrovok_manager.driver.quit()
            return ConversationHandler.END

    async def get_password(self, update, context):
        password = update.message.text
        context.user_data['ostrovok_password'] = password
        try:
            self.ostrovok_manager.fill_password(password)
            self.ostrovok_manager.submit_login()
            # Проверяем, требуется ли 2FA
            try:
                self.ostrovok_manager.wait_2fa_form()
                await update.message.reply_text("Введите 4-значный код из письма/email (2FA):")
                return WAITING_2FA
            except Exception:
                # 2FA не требуется, сразу сохраняем cookies
                email = context.user_data['ostrovok_email']
                success = self.ostrovok_manager.check_login_success(email)
                if success:
                    await update.message.reply_text("Вход выполнен, cookies сохранены!")
                    await self.show_ostrovok_ad_menu(update.message)
                else:
                    await update.message.reply_text("Ошибка входа: не удалось войти или сохранить cookies.")
                if self.ostrovok_manager.driver:
                    self.ostrovok_manager.driver.quit()
                return ConversationHandler.END
        except Exception as e:
            await update.message.reply_text(f"Ошибка входа: {e}")
            if self.ostrovok_manager.driver:
                self.ostrovok_manager.driver.quit()
            return ConversationHandler.END

    async def get_2fa_code(self, update, context):
        code = update.message.text.strip()
        email = context.user_data['ostrovok_email']
        try:
            self.ostrovok_manager.fill_2fa_code(code)
            success = self.ostrovok_manager.check_login_success(email)
            if success:
                await update.message.reply_text("Вход выполнен, cookies сохранены!")
                await self.show_ostrovok_ad_menu(update.message)
            else:
                await update.message.reply_text("Ошибка входа: не удалось войти или сохранить cookies.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка 2FA: {e}")
        if self.ostrovok_manager.driver:
            self.ostrovok_manager.driver.quit()
        return ConversationHandler.END

    async def get_object_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = update.message.text.strip()
        ok, msg = self.ostrovok_manager.fill_object_name(name)
        if ok:
            await update.message.reply_text(f"✅ Название '{name}' успешно введено!\nТеперь введите тип объекта (например, Отель, Хостел, Апарт-отель и т.д.):")
            context.user_data['object_name'] = name
            return WAITING_OBJECT_TYPE
        else:
            await update.message.reply_text(f"❌ {msg}\nПопробуйте ввести название ещё раз:")
            return WAITING_OBJECT_NAME

    async def get_object_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        object_type = update.message.text.strip()
        ok, msg = self.ostrovok_manager.select_object_type(object_type)
        if ok:
            await update.message.reply_text(f"✅ Тип '{object_type}' успешно выбран!\nТеперь введите город (например, Санкт-Петербург):")
            context.user_data['object_type'] = object_type
            return WAITING_OBJECT_CITY
        else:
            await update.message.reply_text(f"❌ {msg}\nПопробуйте ввести тип ещё раз:")
            return WAITING_OBJECT_TYPE

    async def get_object_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        city = update.message.text.strip()
        ok, msg = self.ostrovok_manager.select_object_city(city)
        if ok:
            await update.message.reply_text(f"✅ Город '{city}' успешно выбран!\nТеперь введите улицу и дом (например, Невский проспект 1):")
            context.user_data['object_city'] = city
            return WAITING_OBJECT_ADDRESS
        else:
            await update.message.reply_text(f"❌ {msg}\nПопробуйте ввести город ещё раз:")
            return WAITING_OBJECT_CITY

    async def get_object_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        address = update.message.text.strip()
        ok, msg = self.ostrovok_manager.select_object_address(address)
        if ok:
            # Сохраняем все данные формы
            context.user_data['object_address'] = address
            summary = (
                f"Проверьте введённые данные:\n"
                f"Название: {context.user_data.get('object_name', '-') }\n"
                f"Тип: {context.user_data.get('object_type', '-') }\n"
                f"Город: {context.user_data.get('object_city', '-') }\n"
                f"Адрес: {context.user_data.get('object_address', '-') }"
            )
            await update.message.reply_text(summary)
            # Далее — регистрация объекта
            ok_submit, msg_submit = self.ostrovok_manager.submit_object_form()
            if ok_submit:
                await update.message.reply_text(f"✅ Адрес '{address}' успешно выбран!\nОбъект зарегистрирован!")
            else:
                await update.message.reply_text(f"✅ Адрес '{address}' успешно выбран!\n❌ Не удалось зарегистрировать объект: {msg_submit}")
            return ConversationHandler.END
        else:
            await update.message.reply_text(f"❌ {msg}\nПопробуйте ввести адрес ещё раз:")
            return WAITING_OBJECT_ADDRESS

    async def cancel_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await self.show_ostrovok_main_menu(query)
        return ConversationHandler.END
    
    async def show_ostrovok_bookings(self, query):
        """Показать бронирования отеля"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('ostrovok_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем бронирования отеля...")
        
        # Получаем бронирования
        success, result = self.ostrovok_manager.get_bookings()
        
        if success:
            bookings = result
            if bookings:
                text = "📊 Бронирования вашего отеля:\n\n"
                for i, booking in enumerate(bookings, 1):
                    text += f"{i}. 👤 Гость: {booking['guest_name']}\n"
                    text += f"   🏠 Номер: {booking['room_type']}\n"
                    text += f"   📅 Заезд: {booking['check_in']}\n"
                    text += f"   📅 Выезд: {booking['check_out']}\n"
                    text += f"   💰 Сумма: {booking['total_price']}\n"
                    text += f"   📋 Статус: {booking['status']}\n\n"
            else:
                text = "📊 В вашем отеле пока нет бронирований"
        else:
            text = f"❌ Ошибка при получении бронирований: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='ostrovok_bookings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_ostrovok')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def show_ostrovok_account(self, query):
        """Показать информацию об отеле"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('ostrovok_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем информацию об отеле...")
        
        # Получаем информацию об аккаунте
        success, result = self.ostrovok_manager.get_account_info()
        
        if success:
            account_info = result
            text = "🏨 Информация об отеле:\n\n"
            text += f"🏨 Название отеля: {account_info['hotel_name']}\n"
            text += f"👤 Владелец: {account_info['name']}\n"
            text += f"📧 Email: {account_info['email']}\n"
            text += f"📱 Телефон: {account_info['phone']}\n"
        else:
            text = f"❌ Ошибка при получении информации: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_ostrovok')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def show_ostrovok_statistics(self, query):
        """Показать статистику отеля"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('ostrovok_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем статистику отеля...")
        
        # Получаем статистику
        success, result = self.ostrovok_manager.get_hotel_statistics()
        
        if success:
            stats = result
            text = "📈 Статистика вашего отеля:\n\n"
            text += f"💰 Общая выручка: {stats['total_revenue']}\n"
            text += f"📊 Количество бронирований: {stats['total_bookings']}\n"
            text += f"📈 Средняя загрузка: {stats['occupancy_rate']}\n"
            text += f"💳 Средний чек: {stats['average_check']}\n"
        else:
            text = f"❌ Ошибка при получении статистики: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='ostrovok_statistics')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_ostrovok')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def show_ostrovok_rooms(self, query):
        """Показать управление номерами"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('ostrovok_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем информацию о номерах...")
        
        # Получаем информацию о номерах
        success, result = self.ostrovok_manager.get_room_management()
        
        if success:
            rooms = result
            if rooms:
                text = "🏠 Управление номерами:\n\n"
                for i, room in enumerate(rooms, 1):
                    text += f"{i}. 🏠 {room['room_type']}\n"
                    text += f"   💰 Цена: {room['price']}\n"
                    text += f"   📅 Доступность: {room['availability']}\n"
                    text += f"   📋 Статус: {room['status']}\n\n"
            else:
                text = "🏠 Информация о номерах недоступна"
        else:
            text = f"❌ Ошибка при получении информации о номерах: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='ostrovok_rooms')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_ostrovok')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def ostrovok_logout(self, query):
        """Выйти из аккаунта Ostrovok"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('ostrovok_logged_in'):
            await query.answer("❌ Вы не авторизованы")
            return
        
        await query.answer("🔄 Выполняется выход из аккаунта...")
        
        # Выполняем выход
        success, message = self.ostrovok_manager.logout()
        
        if success:
            # Очищаем информацию о сессии
            if user_id in self.user_sessions:
                self.user_sessions[user_id]['ostrovok_logged_in'] = False
                self.user_sessions[user_id].pop('ostrovok_email', None)
            
            keyboard = [
                [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='ostrovok_login')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ {message}\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='platform_ostrovok')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ {message}\n\n"
                "Попробуйте позже:",
                reply_markup=reply_markup
            )
    
    async def show_ostrovok_main_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("➕ Добавить объект", callback_data='ostrovok_add_object')],
            [InlineKeyboardButton("🏨 Мои объекты", callback_data='ostrovok_my_objects')],
            [InlineKeyboardButton("🆕 Новые брони", callback_data='ostrovok_new_bookings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    
    async def show_ostrovok_ad_menu(self, message_or_query):
        keyboard = [
            [InlineKeyboardButton("➕ Создать объявление", callback_data='ostrovok_create_ad')],
            [InlineKeyboardButton("Мои объявления", callback_data='ostrovok_my_ads')],
            [InlineKeyboardButton("Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "🏨 Меню выкладки объявлений Ostrovok\n\nВыберите действие:"
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup)

    # Пример справочников (можно расширить)
    OSTROVOK_TYPE_MAP = {
        'мини-отель': 8,
        'гостиница': 1,
        'апартаменты': 2,
        'отель': 8,
        'hostel': 3
    }
    OSTROVOK_REGION_MAP = {
        'санкт-петербург': 2042,
        'москва': 213,
        'сочи': 2397
    }

    async def start_create_ad(self, update, context):
        await update.callback_query.edit_message_text("Введите название объекта:")
        return WAITING_AD_NAME

    async def get_ad_name(self, update, context):
        context.user_data['ad_name'] = update.message.text
        # Предложить выбор типа
        type_list = ', '.join(self.OSTROVOK_TYPE_MAP.keys())
        await update.message.reply_text(f"Введите тип объекта (например: {type_list}):")
        return WAITING_AD_TYPE

    async def get_ad_type(self, update, context):
        type_name = update.message.text.strip().lower()
        context.user_data['ad_type_name'] = type_name
        await update.message.reply_text("Введите город:")
        return WAITING_AD_REGION

    async def get_ad_region(self, update, context):
        city = update.message.text.strip().lower()
        context.user_data['ad_city'] = city
        await update.message.reply_text("Введите адрес:")
        return WAITING_AD_ADDRESS

    async def get_ad_address(self, update, context):
        context.user_data['ad_address'] = update.message.text
        await update.message.reply_text("Введите название сети (или 'нет', если не состоит в сети):")
        return WAITING_AD_CHAIN

    async def get_ad_chain(self, update, context):
        chain = update.message.text.strip()
        context.user_data['ad_chain'] = chain
        # Теперь собираем все данные и преобразуем
        name = context.user_data['ad_name']
        type_name = context.user_data['ad_type_name']
        city = context.user_data['ad_city']
        address = context.user_data['ad_address']
        chain = context.user_data['ad_chain']
        # type_id
        type_id = self.OSTROVOK_TYPE_MAP.get(type_name, 8)
        # region_id
        region_id = self.OSTROVOK_REGION_MAP.get(city, 2042)
        # chain_id
        chain_id = 0 if chain.lower() == 'нет' else 13
        # Геокодинг через Яндекс.Карты (так как Ostrovok использует Яндекс.Карты)
        coords = await self.geocode_address(f"{city}, {address}")
        if coords is None:
            await update.message.reply_text("❌ Не удалось определить координаты по адресу. Проверьте правильность города и адреса.")
            return ConversationHandler.END
        lat, lon = coords
        
        # Подготавливаем данные в правильном формате для API Ostrovok
        hotel_data = self.ostrovok_manager.prepare_hotel_data(
            name=name,
            address=address,
            city=city,
            region_id=region_id,
            type_id=type_id,
            latitude=lat,
            longitude=lon
        )
        status, result = self.ostrovok_manager.create_hotel(hotel_data)
        if status == 200:
            await update.message.reply_text(f"✅ Объявление создано!\nID: {result.get('id', 'неизвестно')}")
        else:
            await update.message.reply_text(f"❌ Ошибка создания объявления: {result}")
        await self.show_ostrovok_ad_menu(update.message)
        return ConversationHandler.END

    async def geocode_address(self, address):
        """
        Геокодинг адреса через API Ostrovok
        """
        try:
            # Используем метод из OstrovokManager
            coords = self.ostrovok_manager.geocode_address_ostrovok(address)
            if coords:
                lat, lon = coords
                logger.info(f"Координаты получены через Ostrovok API: {lat}, {lon}")
                return lat, lon
            else:
                logger.warning(f"Не удалось получить координаты через Ostrovok API для адреса: {address}")
                # Fallback на Яндекс.Карты если Ostrovok не сработал
                return await self.geocode_address_yandex(address)
        except Exception as e:
            logger.error(f"Ошибка геокодинга через Ostrovok: {e}")
            # Fallback на Яндекс.Карты
            return await self.geocode_address_yandex(address)
    
    async def geocode_address_yandex(self, address):
        """
        Fallback геокодинг через Яндекс.Карты
        """
        import requests
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'geocode': address,
            'format': 'json',
            'results': 1
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            pos = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            lon, lat = map(float, pos.split())
            logger.info(f"Координаты получены через Яндекс.Карты: {lat}, {lon}")
            return lat, lon
        except Exception as e:
            logger.error(f"Ошибка геокодинга через Яндекс.Карты: {e}")
            return None

    # ===== BNOVO PMS МЕТОДЫ =====
    
    async def bnovo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для быстрого доступа к Bnovo"""
        if not self.bnovo_manager:
            await update.message.reply_text("❌ Bnovo PMS не настроен. Добавьте API ключ в config.py")
            return
        
        await self.show_bnovo_dashboard(update.message)
    
    async def notifications_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление уведомлениями"""
        user_id = update.effective_user.id
        enabled = self.user_sessions.get(user_id, {}).get('bnovo_notifications_enabled', True)
        
        keyboard = [
            [InlineKeyboardButton("🔕 Отключить" if enabled else "🔔 Включить", 
                                callback_data='toggle_notifications')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status = "✅ Включены" if enabled else "❌ Отключены"
        await update.message.reply_text(
            f"🔔 **Настройки уведомлений**\n\n"
            f"Статус: {status}\n\n"
            f"Уведомления о новых бронированиях будут приходить автоматически.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_bnovo_dashboard(self, message_or_query):
        """Показать главную панель Bnovo"""
        if not self.bnovo_manager:
            text = "❌ Bnovo PMS не настроен"
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
        else:
            text = "🔗 **Bnovo PMS Dashboard**\n\n"
            text += "Централизованное управление всеми площадками:\n"
            text += "• 📊 Статистика по всем платформам\n"
            text += "• 🆕 Новые бронирования\n"
            text += "• 📋 Все бронирования\n"
            text += "• 🔔 Автоматические уведомления\n\n"
            text += "Выберите действие:"
            
            keyboard = [
                [InlineKeyboardButton("📊 Статистика", callback_data='bnovo_statistics')],
                [InlineKeyboardButton("🆕 Новые брони", callback_data='bnovo_new_bookings')],
                [InlineKeyboardButton("📋 Все брони", callback_data='bnovo_bookings')],
                [InlineKeyboardButton("🔔 Уведомления", callback_data='notifications_settings')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_bnovo_bookings(self, query):
        """Показать все бронирования из Bnovo"""
        if not self.bnovo_manager:
            await query.edit_message_text("❌ Bnovo PMS не настроен")
            return
        
        await query.answer("🔄 Загружаем бронирования...")
        
        success, result = self.bnovo_manager.get_bookings()
        if success and isinstance(result, list):
            if result:
                text = f"📋 **Все бронирования** (последние 30 дней)\n\n"
                for i, booking in enumerate(result[:10], 1):  # Показываем первые 10
                    message = self.bnovo_manager.format_booking_message(booking)
                    text += f"**{i}.** {message}\n"
                
                if len(result) > 10:
                    text += f"\n... и ещё {len(result) - 10} бронирований"
            else:
                text = "📋 Бронирования не найдены"
        else:
            text = f"❌ Ошибка: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='bnovo_bookings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='bnovo_dashboard')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_bnovo_new_bookings(self, query):
        """Показать новые бронирования из Bnovo"""
        if not self.bnovo_manager:
            await query.edit_message_text("❌ Bnovo PMS не настроен")
            return
        
        await query.answer("🔄 Загружаем новые бронирования...")
        
        success, result = self.bnovo_manager.get_new_bookings(hours_back=24)
        if success and isinstance(result, list):
            if result:
                text = f"🆕 **Новые бронирования** (за последние 24 часа)\n\n"
                for i, booking in enumerate(result, 1):
                    message = self.bnovo_manager.format_booking_message(booking)
                    text += f"**{i}.** {message}\n"
            else:
                text = "🆕 Новых бронирований за последние 24 часа нет"
        else:
            text = f"❌ Ошибка: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='bnovo_new_bookings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='bnovo_dashboard')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_bnovo_statistics(self, query):
        """Показать статистику из Bnovo"""
        if not self.bnovo_manager:
            await query.edit_message_text("❌ Bnovo PMS не настроен")
            return
        
        await query.answer("📊 Загружаем статистику...")
        
        success, result = self.bnovo_manager.get_statistics()
        if success:
            text = self.bnovo_manager.format_statistics_message(result)
        else:
            text = f"❌ Ошибка: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='bnovo_statistics')],
            [InlineKeyboardButton("🔙 Назад", callback_data='bnovo_dashboard')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_notifications_settings(self, query):
        """Показать настройки уведомлений"""
        user_id = query.from_user.id
        enabled = self.user_sessions.get(user_id, {}).get('bnovo_notifications_enabled', True)
        
        keyboard = [
            [InlineKeyboardButton("🔕 Отключить" if enabled else "🔔 Включить", 
                                callback_data='toggle_notifications')],
            [InlineKeyboardButton("🔙 Назад", callback_data='bnovo_dashboard')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status = "✅ Включены" if enabled else "❌ Отключены"
        await query.edit_message_text(
            f"🔔 **Настройки уведомлений**\n\n"
            f"Статус: {status}\n\n"
            f"Уведомления о новых бронированиях будут приходить автоматически каждые 5 минут.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def toggle_notifications(self, query):
        """Переключить уведомления"""
        user_id = query.from_user.id
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        current_status = self.user_sessions[user_id].get('bnovo_notifications_enabled', True)
        self.user_sessions[user_id]['bnovo_notifications_enabled'] = not current_status
        
        await self.show_notifications_settings(query)

    # ===== 101 HOTELS МЕТОДЫ =====
    
    async def show_101hotels_main_menu(self, query):
        """Показать главное меню 101 hotels"""
        keyboard = [
            [InlineKeyboardButton("📊 Бронирования", callback_data='101hotels_bookings')],
            [InlineKeyboardButton("📈 Статистика", callback_data='101hotels_statistics')],
            [InlineKeyboardButton("➕ Добавить объект", callback_data='101hotels_add_object')],
            [InlineKeyboardButton("🏨 Мои объекты", callback_data='101hotels_my_objects')],
            [InlineKeyboardButton("🔒 Закрыть браузер", callback_data='101hotels_close_browser')],
            [InlineKeyboardButton("🚪 Выйти", callback_data='101hotels_logout')],
            [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
            [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏨 **101 Hotels Extranet**\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_101hotels_bookings(self, query):
        """Показать бронирования 101 hotels"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('101hotels_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем бронирования...")
        
        success, result = self.hotels101_manager.get_bookings()
        
        if success:
            bookings = result
            if bookings:
                text = "📊 **Бронирования 101 hotels:**\n\n"
                for i, booking in enumerate(bookings[:10], 1):
                    text += f"**{i}.** Гость: {booking.get('guest_name', 'N/A')}\n"
                    text += f"    Номер: {booking.get('room_type', 'N/A')}\n"
                    text += f"    Заезд: {booking.get('check_in', 'N/A')}\n"
                    text += f"    Выезд: {booking.get('check_out', 'N/A')}\n"
                    text += f"    Сумма: {booking.get('total_price', 'N/A')}\n\n"
            else:
                text = "📊 В вашем отеле пока нет бронирований"
        else:
            text = f"❌ Ошибка при получении бронирований: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='101hotels_bookings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_101hotels_statistics(self, query):
        """Показать статистику 101 hotels"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('101hotels_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("📊 Загружаем статистику...")
        
        success, result = self.hotels101_manager.get_statistics()
        
        if success:
            stats = result
            text = "📈 **Статистика 101 hotels:**\n\n"
            text += f"💰 Общая выручка: {stats.get('total_revenue', 'N/A')}\n"
            text += f"📊 Количество бронирований: {stats.get('total_bookings', 'N/A')}\n"
            text += f"📈 Средняя загрузка: {stats.get('occupancy_rate', 'N/A')}\n"
            text += f"💳 Средний чек: {stats.get('average_check', 'N/A')}\n"
        else:
            text = f"❌ Ошибка при получении статистики: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='101hotels_statistics')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_101hotels_add_object(self, query):
        """Показать форму добавления объекта на 101 hotels"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('101hotels_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Открываем форму добавления отеля...")
        
        # Открываем страницу отелей
        success = self.hotels101_manager.open_hotels_page()
        if not success:
            await query.edit_message_text("❌ Не удалось открыть страницу отелей")
            return
        
        # Нажимаем кнопку "Добавить отель"
        success, msg = self.hotels101_manager.click_add_hotel_button()
        if not success:
            await query.edit_message_text(f"❌ Не удалось найти кнопку добавления отеля: {msg}")
            return
        
        # Анализируем структуру страницы для отладки
        success, debug_info = self.hotels101_manager.debug_page_structure()
        if success:
            debug_text = f"📊 Отладочная информация:\nURL: {debug_info['url']}\nФорм: {debug_info['forms']}\nПолей ввода: {debug_info['inputs']}\nКнопок: {debug_info['buttons']}"
        else:
            debug_text = "❌ Не удалось получить отладочную информацию"
        
        text = f"✅ **Форма добавления отеля открыта!**\n\n{debug_text}\n\nТеперь вы можете заполнить данные отеля."
        
        keyboard = [
            [InlineKeyboardButton("🔍 Анализ страницы", callback_data='101hotels_debug_page')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_101hotels_my_objects(self, query):
        """Показать мои объекты на 101 hotels"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('101hotels_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем список отелей...")
        
        # Сначала попробуем получить через API
        success, result = self.hotels101_manager.get_my_hotels()
        
        if not success:
            # Если API не работает, попробуем через Selenium
            success = self.hotels101_manager.open_hotels_page()
            if success:
                success, result = self.hotels101_manager.get_my_hotels_from_page()
        
        if success and result:
            hotels = result
            text = "🏨 **Мои отели на 101 hotels:**\n\n"
            for i, hotel in enumerate(hotels[:10], 1):  # Показываем первые 10
                text += f"**{i}.** {hotel.get('name', 'N/A')}\n"
                text += f"    📍 {hotel.get('address', 'N/A')}\n"
                text += f"    🆔 ID: {hotel.get('id', 'N/A')}\n\n"
        else:
            text = f"❌ Не удалось получить список отелей: {result if not success else 'Отели не найдены'}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='101hotels_my_objects')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_101hotels_logout(self, query):
        """Выйти из аккаунта 101 hotels"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('101hotels_logged_in'):
            await query.answer("❌ Вы не авторизованы")
            return
        
        await query.answer("🔄 Выполняется выход из аккаунта...")
        
        # Очищаем информацию о сессии
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['101hotels_logged_in'] = False
            self.user_sessions[user_id].pop('101hotels_email', None)
        
        # Закрываем браузер
        self.hotels101_manager.close_browser()
        
        keyboard = [
            [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='101hotels_login')],
            [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ **Выход из 101 hotels выполнен успешно!**\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def close_101hotels_browser(self, query):
        """Закрыть браузер 101 hotels"""
        await query.answer("🔄 Закрываем браузер...")
        
        # Закрываем браузер
        success = self.hotels101_manager.close_browser()
        
        if success:
            keyboard = [
                [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='101hotels_login')],
                [InlineKeyboardButton("➕ Создать новый отель", callback_data='101hotels_create_new')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ **Браузер закрыт успешно!**\n\n"
                "Выберите действие:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **Ошибка при закрытии браузера**\n\n"
                "Попробуйте позже:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def show_101hotels_debug_page(self, query):
        """Показать отладочную информацию о странице 101 hotels"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('101hotels_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔍 Анализируем структуру страницы...")
        
        success, debug_info = self.hotels101_manager.debug_page_structure()
        
        if success:
            text = "🔍 **Отладочная информация страницы 101 hotels:**\n\n"
            text += f"🌐 **URL:** {debug_info['url']}\n"
            text += f"📄 **Заголовок:** {debug_info['title']}\n"
            text += f"📏 **Размер HTML:** {debug_info['page_source_length']} символов\n\n"
            text += f"📋 **Элементы на странице:**\n"
            text += f"• Форм: {debug_info['forms']}\n"
            text += f"• Полей ввода: {debug_info['inputs']}\n"
            text += f"• Кнопок: {debug_info['buttons']}\n"
            text += f"• Селектов: {debug_info['selects']}\n\n"
            text += "💡 **Совет:** Используйте эту информацию для настройки селекторов."
        else:
            text = f"❌ **Ошибка анализа страницы:** {debug_info}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить анализ", callback_data='101hotels_debug_page')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_101hotels_country_selection(self, query):
        """Показать выбор страны для регистрации"""
        user_id = query.from_user.id
        
        await query.answer("🌍 Загружаем список стран...")
        
        try:
            # Сначала получим отладочную информацию
            debug_success, debug_info = self.hotels101_manager.debug_page_structure()
            
            # Получаем список доступных стран
            success, countries = self.hotels101_manager.get_available_countries()
            
            if success and countries:
                keyboard = []
                for country in countries:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🇷🇺 {country['name']}", 
                            callback_data=f'101hotels_country_{country["id"]}'
                        )
                    ])
                
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "🌍 **Выберите страну**\n\n"
                    "В какой стране находится ваш объект?\n\n"
                    "Выберите страну из списка ниже:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                # Показываем подробную информацию об ошибке
                error_text = "❌ **Не удалось загрузить список стран**\n\n"
                
                if debug_success:
                    error_text += f"📊 **Информация о странице:**\n"
                    error_text += f"• URL: {debug_info['url']}\n"
                    error_text += f"• Заголовок: {debug_info['title']}\n"
                    error_text += f"• Форм: {debug_info['forms']}\n"
                    error_text += f"• Полей ввода: {debug_info['inputs']}\n"
                    error_text += f"• Кнопок: {debug_info['buttons']}\n"
                    error_text += f"• Labels: {debug_info['labels']}\n\n"
                    
                    if debug_info['country_elements']:
                        error_text += "🔍 **Найденные элементы стран:**\n"
                        for elem_info in debug_info['country_elements']:
                            error_text += f"• {elem_info['selector']}: {elem_info['count']} элементов\n"
                    else:
                        error_text += "🔍 **Элементы стран не найдены**\n"
                    
                    if debug_info['country_texts']:
                        error_text += "\n📝 **Найденные тексты стран:**\n"
                        for text_info in debug_info['country_texts']:
                            error_text += f"• {text_info['country']}: {text_info['count']} элементов\n"
                    else:
                        error_text += "\n📝 **Тексты стран не найдены**\n"
                else:
                    error_text += f"🔍 **Ошибка анализа страницы:** {debug_info}\n\n"
                
                error_text += f"💡 **Возможные причины:**\n"
                error_text += "• Страница еще не загрузилась полностью\n"
                error_text += "• Изменилась структура страницы\n"
                error_text += "• Проблемы с подключением к сайту\n\n"
                error_text += "🔄 **Попробуйте:**\n"
                error_text += "• Обновить страницу в браузере\n"
                error_text += "• Проверить подключение к интернету\n"
                error_text += "• Попробовать позже"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_select_country')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    error_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка при показе выбора страны: {e}")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_select_country')],
                [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ **Ошибка при загрузке списка стран**\n\n"
                f"🔍 **Детали ошибки:** {str(e)}\n\n"
                f"💡 **Попробуйте:**\n"
                f"• Обновить страницу в браузере\n"
                f"• Проверить подключение к интернету\n"
                f"• Попробовать позже",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def continue_101hotels_registration(self, query):
        """Продолжить регистрацию - перейти к следующему шагу"""
        user_id = query.from_user.id
        
        await query.answer("🔄 Переходим к следующему шагу...")
        
        try:
            # Нажимаем кнопку "Далее" через Selenium
            success, message = self.hotels101_manager.click_next_step()
            
            if success:
                # После успешного нажатия "Продолжить" переключаемся на API
                await query.edit_message_text(
                    "✅ **Переход к API**\n\n"
                    "Кнопка 'Продолжить' успешно нажата.\n"
                    "Теперь переключаемся на работу через API...",
                    parse_mode='Markdown'
                )
                
                # Получаем информацию о текущем шаге через API
                step_success, step_info = self.hotels101_manager.get_registration_step_info()
                
                if step_success:
                    keyboard = [
                        [InlineKeyboardButton("📝 Заполнить основную информацию", callback_data='101hotels_api_basic_info')],
                        [InlineKeyboardButton("📊 Прогресс регистрации", callback_data='101hotels_api_progress')],
                        [InlineKeyboardButton("🔍 Поля формы", callback_data='101hotels_api_fields')],
                        [InlineKeyboardButton("👤 Ввести контактное лицо", callback_data='101hotels_contact_info')],
                        [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"✅ **API подключен**\n\n"
                        f"**Текущий шаг:** {step_info.get('step_name', 'Неизвестно')}\n"
                        f"**Статус:** {step_info.get('status', 'Активен')}\n\n"
                        f"Выберите действие для продолжения регистрации:",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_next_step')],
                        [InlineKeyboardButton("🔍 Анализировать страницу", callback_data='101hotels_debug_page')],
                        [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_select_country')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"⚠️ **API недоступен**\n\n"
                        f"Не удалось получить информацию через API:\n`{step_info}`\n\n"
                        f"Продолжаем работу через Selenium.",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_next_step')],
                    [InlineKeyboardButton("🔍 Анализировать страницу", callback_data='101hotels_debug_page')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_select_country')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"❌ **Ошибка**\n\nНе удалось перейти к следующему шагу:\n`{message}`\n\n"
                    f"**Возможные причины:**\n"
                    f"• Кнопка 'Продолжить' заблокирована\n"
                    f"• Страна не выбрана\n"
                    f"• Форма не загружена полностью\n\n"
                    f"Попробуйте снова или проанализируйте страницу.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при продолжении регистрации: {e}")
            await query.edit_message_text(
                f"❌ **Ошибка**\n\nНе удалось продолжить регистрацию:\n`{str(e)}`",
                parse_mode='Markdown'
            )

    async def select_101hotels_country(self, query):
        """Выбрать страну для регистрации отеля"""
        user_id = query.from_user.id
        
        # Извлекаем ID страны из callback_data
        country_id = query.data.replace('101hotels_country_', '')
        
        await query.answer(f"🌍 Выбираем страну...")
        
        try:
            # Карта ID стран к названиям для отображения
            country_names = {
                "171": "Россия",
                "21": "Казахстан", 
                "1": "Киргизия",
                "4": "Беларусь",
                "14": "Узбекистан",
                "60": "Таджикистан",
                "83": "Туркменистан",
                "90": "Азербайджан",
                "216": "Армения"
            }
            
            country_name = country_names.get(country_id, f"Страна {country_id}")
            
            # Выбираем страну в форме
            success, message = self.hotels101_manager.select_country(country_name)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("➡️ Далее", callback_data='101hotels_next_step')],
                    [InlineKeyboardButton("🔍 Анализировать страницу", callback_data='101hotels_debug_page')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_select_country')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ **Страна выбрана**\n\n"
                    f"**Выбрана:** {country_name}\n\n"
                    f"Страна успешно выбрана в форме регистрации.\n"
                    f"**Следующий шаг:** Нажмите 'Далее' для перехода к следующему этапу регистрации.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_select_country')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"❌ **Ошибка выбора страны**\n\n"
                    f"Не удалось выбрать страну '{country_name}':\n"
                    f"`{message}`\n\n"
                    f"Попробуйте выбрать другую страну или повторить попытку.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при выборе страны: {e}")
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_select_country')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ **Ошибка**\n\n"
                f"Произошла ошибка при выборе страны:\n"
                f"`{str(e)}`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def start_101hotels_login(self, query):
        """Начать процесс входа в 101 hotels"""
        user_id = query.from_user.id
        
        await query.answer("🔄 Открываем страницу входа...")
        
        try:
            # Открываем страницу входа
            self.hotels101_manager.open_login_page()
            
            keyboard = [
                [InlineKeyboardButton("🔐 Ввести данные", callback_data='101hotels_enter_credentials')],
                [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔐 **Вход в 101 Hotels Extranet**\n\n"
                "Страница входа открыта в браузере.\n"
                "Нажмите 'Ввести данные' для продолжения.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка при открытии страницы входа: {str(e)}\n\n"
                "Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
                ])
            )

    async def start_101hotels_create_new(self, query):
        """Начать процесс создания нового отеля в 101 hotels"""
        user_id = query.from_user.id
        
        await query.answer("🔄 Открываем форму регистрации...")
        
        try:
            # Открываем главную страницу extranet
            dashboard_success = self.hotels101_manager.open_dashboard()
            if not dashboard_success:
                raise Exception("Не удалось открыть главную страницу")
            
            # Нажимаем кнопку "Зарегистрировать свой объект"
            register_success, register_message = self.hotels101_manager.click_register_new_object()
            
            if register_success:
                keyboard = [
                    [InlineKeyboardButton("🌍 Выбрать страну", callback_data='101hotels_select_country')],
                    [InlineKeyboardButton("🔍 Анализировать страницу", callback_data='101hotels_debug_page')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "✅ **Регистрация нового объекта**\n\n"
                    "Кнопка 'Зарегистрировать свой объект' успешно нажата!\n"
                    "Форма регистрации открылась в браузере.\n\n"
                    "**Следующий шаг:** Выберите страну, в которой находится ваш объект.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔍 Анализировать страницу", callback_data='101hotels_debug_page')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"⚠️ **Проблема с регистрацией**\n\n"
                    f"Главная страница открыта, но не удалось найти кнопку регистрации:\n"
                    f"`{register_message}`\n\n"
                    f"Используйте 'Анализировать страницу' для отладки.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при создании нового отеля: {e}")
            await query.edit_message_text(
                f"❌ **Ошибка**\n\nНе удалось начать регистрацию:\n`{str(e)}`",
                parse_mode='Markdown'
            )

    async def start_101hotels_login_conv(self, update, context):
        """Начать процесс входа в 101 hotels (для ConversationHandler)"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🔐 **Вход в 101 Hotels Extranet**\n\n"
            "Введите ваш email для входа:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data='cancel_101hotels_login')]
            ]),
            parse_mode='Markdown'
        )
        return WAITING_101HOTELS_EMAIL

    async def get_101hotels_email(self, update, context):
        """Получить email для входа в 101 hotels"""
        email = update.message.text.strip()
        context.user_data['101hotels_email'] = email
        
        try:
            # Вводим email в форму
            self.hotels101_manager.fill_email(email)
            
            await update.message.reply_text(
                "✅ Email введен!\n\n"
                "Теперь введите ваш пароль:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='cancel_101hotels_login')]
                ])
            )
            return WAITING_101HOTELS_PASSWORD
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка при вводе email: {str(e)}\n\n"
                "Попробуйте еще раз или отмените операцию.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='cancel_101hotels_login')]
                ])
            )
            return WAITING_101HOTELS_EMAIL

    async def get_101hotels_password(self, update, context):
        """Получить пароль для входа в 101 hotels"""
        password = update.message.text
        email = context.user_data.get('101hotels_email')
        
        try:
            # Вводим пароль и выполняем вход
            self.hotels101_manager.fill_password(password)
            self.hotels101_manager.submit_login()
            
            # Проверяем успешность входа
            success = self.hotels101_manager.check_login_success(email)
            
            if success:
                # Сохраняем информацию о сессии
                user_id = update.effective_user.id
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = {}
                
                self.user_sessions[user_id]['101hotels_logged_in'] = True
                self.user_sessions[user_id]['101hotels_email'] = email
                
                keyboard = [
                    [InlineKeyboardButton("🏨 Главное меню", callback_data='platform_101hotels')],
                    [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ **Вход в 101 Hotels выполнен успешно!**\n\n"
                    "Cookies сохранены. Теперь вы можете управлять своими отелями.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Ошибка входа**\n\n"
                    "Не удалось войти в аккаунт. Проверьте правильность email и пароля.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_login')],
                        [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
                    ]),
                    parse_mode='Markdown'
                )
            
            # Закрываем браузер
            if self.hotels101_manager.driver:
                self.hotels101_manager.driver.quit()
                self.hotels101_manager.driver = None
            
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Ошибка входа:** {str(e)}\n\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
                ]),
                parse_mode='Markdown'
            )
            
            # Закрываем браузер
            if self.hotels101_manager.driver:
                self.hotels101_manager.driver.quit()
                self.hotels101_manager.driver = None
            
            return ConversationHandler.END

    async def cancel_101hotels_login(self, update, context):
        """Отменить вход в 101 hotels"""
        query = update.callback_query
        await query.answer()
        
        # Закрываем браузер
        if self.hotels101_manager.driver:
            self.hotels101_manager.driver.quit()
            self.hotels101_manager.driver = None
        
        keyboard = [
            [InlineKeyboardButton("🔐 Войти в аккаунт", callback_data='101hotels_login')],
            [InlineKeyboardButton("➕ Создать новый отель", callback_data='101hotels_create_new')],
            [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ **Вход отменен**\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    # ===== BRONEVIK МЕТОДЫ =====
    
    async def show_bronevik_main_menu(self, query):
        """Показать главное меню Bronevik"""
        keyboard = [
            [InlineKeyboardButton("➕ Добавить объект", callback_data='bronevik_add_object')],
            [InlineKeyboardButton("🏨 Мои объекты", callback_data='bronevik_my_objects')],
            [InlineKeyboardButton("📊 Статистика", callback_data='bronevik_statistics')],
            [InlineKeyboardButton("📋 Бронирования", callback_data='bronevik_bookings')],
            [InlineKeyboardButton("🚪 Выйти", callback_data='bronevik_logout')],
            [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🏨 **Bronevik - Панель управления**\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_bronevik_bookings(self, query):
        """Показать бронирования Bronevik"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('bronevik_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("🔄 Загружаем бронирования...")
        
        success, result = self.bronevik_manager.get_bookings()
        
        if success:
            bookings = result
            if bookings:
                text = "📊 **Бронирования Bronevik:**\n\n"
                for i, booking in enumerate(bookings[:10], 1):
                    text += f"**{i}.** Гость: {booking.get('guest_name', 'N/A')}\n"
                    text += f"    Номер: {booking.get('room_type', 'N/A')}\n"
                    text += f"    Заезд: {booking.get('check_in', 'N/A')}\n"
                    text += f"    Выезд: {booking.get('check_out', 'N/A')}\n"
                    text += f"    Сумма: {booking.get('total_price', 'N/A')}\n\n"
            else:
                text = "📊 В вашем отеле пока нет бронирований"
        else:
            text = f"❌ Ошибка при получении бронирований: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='bronevik_bookings')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_bronevik')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_bronevik_statistics(self, query):
        """Показать статистику Bronevik"""
        user_id = query.from_user.id
        
        if user_id not in self.user_sessions or not self.user_sessions[user_id].get('bronevik_logged_in'):
            await query.answer("❌ Необходимо войти в аккаунт")
            return
        
        await query.answer("📊 Загружаем статистику...")
        
        success, result = self.bronevik_manager.get_statistics()
        
        if success:
            stats = result
            text = "📈 **Статистика Bronevik:**\n\n"
            text += f"💰 Общая выручка: {stats.get('total_revenue', 'N/A')}\n"
            text += f"📊 Количество бронирований: {stats.get('total_bookings', 'N/A')}\n"
            text += f"📈 Средняя загрузка: {stats.get('occupancy_rate', 'N/A')}\n"
            text += f"💳 Средний чек: {stats.get('average_check', 'N/A')}\n"
        else:
            text = f"❌ Ошибка при получении статистики: {result}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='bronevik_statistics')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_bronevik')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- API методы для 101 hotels ---
    
    async def show_101hotels_api_basic_info_form(self, query):
        """Показать форму для заполнения основной информации об отеле через API"""
        user_id = query.from_user.id
        
        await query.answer("📝 Открываем форму основной информации...")
        
        try:
            # Получаем поля формы для основной информации
            fields_success, fields_data = self.hotels101_manager.get_registration_form_fields("basic_info")
            
            if fields_success:
                keyboard = [
                    [InlineKeyboardButton("🏨 Название отеля", callback_data='101hotels_api_hotel_name')],
                    [InlineKeyboardButton("📍 Адрес", callback_data='101hotels_api_hotel_address')],
                    [InlineKeyboardButton("🏙️ Город", callback_data='101hotels_api_hotel_city')],
                    [InlineKeyboardButton("🏢 Тип отеля", callback_data='101hotels_api_hotel_type')],
                    [InlineKeyboardButton("📞 Телефон", callback_data='101hotels_api_hotel_phone')],
                    [InlineKeyboardButton("📧 Email", callback_data='101hotels_api_hotel_email')],
                    [InlineKeyboardButton("🌐 Сайт", callback_data='101hotels_api_hotel_website')],
                    [InlineKeyboardButton("✅ Отправить данные", callback_data='101hotels_api_submit_basic')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_next_step')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📝 **Основная информация об отеле**\n\n"
                    "Заполните основные данные отеля:\n\n"
                    "**Доступные поля:**\n"
                    "• Название отеля\n"
                    "• Адрес\n"
                    "• Город\n"
                    "• Тип отеля\n"
                    "• Контактная информация\n\n"
                    "Выберите поле для заполнения:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_api_basic_info')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_next_step')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"❌ **Ошибка**\n\n"
                    f"Не удалось получить поля формы:\n`{fields_data}`\n\n"
                    f"Попробуйте снова или вернитесь назад.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при открытии формы основной информации: {e}")
            await query.edit_message_text(
                f"❌ **Ошибка**\n\n"
                f"Не удалось открыть форму:\n`{str(e)}`",
                parse_mode='Markdown'
            )

    async def show_101hotels_api_progress(self, query):
        """Показать прогресс регистрации через API"""
        user_id = query.from_user.id
        
        await query.answer("📊 Получаем прогресс регистрации...")
        
        try:
            # Получаем прогресс регистрации
            progress_success, progress_data = self.hotels101_manager.get_registration_progress()
            
            if progress_success:
                keyboard = [
                    [InlineKeyboardButton("🔄 Обновить", callback_data='101hotels_api_progress')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_next_step')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                progress_text = "📊 **Прогресс регистрации**\n\n"
                
                if isinstance(progress_data, dict):
                    current_step = progress_data.get('current_step', 'Неизвестно')
                    total_steps = progress_data.get('total_steps', 'Неизвестно')
                    completion_percentage = progress_data.get('completion_percentage', 0)
                    status = progress_data.get('status', 'В процессе')
                    
                    progress_text += f"**Текущий шаг:** {current_step}\n"
                    progress_text += f"**Всего шагов:** {total_steps}\n"
                    progress_text += f"**Завершено:** {completion_percentage}%\n"
                    progress_text += f"**Статус:** {status}\n\n"
                    
                    # Добавляем информацию о выполненных шагах
                    completed_steps = progress_data.get('completed_steps', [])
                    if completed_steps:
                        progress_text += "**Выполненные шаги:**\n"
                        for step in completed_steps:
                            progress_text += f"✅ {step}\n"
                else:
                    progress_text += f"**Данные:** {progress_data}\n"
                
                await query.edit_message_text(
                    progress_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_api_progress')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_next_step')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"❌ **Ошибка**\n\n"
                    f"Не удалось получить прогресс регистрации:\n`{progress_data}`\n\n"
                    f"Попробуйте снова или вернитесь назад.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при получении прогресса регистрации: {e}")
            await query.edit_message_text(
                f"❌ **Ошибка**\n\n"
                f"Не удалось получить прогресс:\n`{str(e)}`",
                parse_mode='Markdown'
            )

    async def show_101hotels_api_fields(self, query):
        """Показать поля формы регистрации через API"""
        user_id = query.from_user.id
        
        await query.answer("🔍 Получаем поля формы...")
        
        try:
            # Получаем поля формы
            fields_success, fields_data = self.hotels101_manager.get_registration_form_fields()
            
            if fields_success:
                keyboard = [
                    [InlineKeyboardButton("🔄 Обновить", callback_data='101hotels_api_fields')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_next_step')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                fields_text = "🔍 **Поля формы регистрации**\n\n"
                
                if isinstance(fields_data, dict):
                    fields = fields_data.get('fields', [])
                    if fields:
                        fields_text += "**Доступные поля:**\n"
                        for field in fields:
                            field_name = field.get('name', 'Неизвестно')
                            field_type = field.get('type', 'text')
                            field_required = field.get('required', False)
                            field_label = field.get('label', field_name)
                            
                            required_mark = "🔴" if field_required else "⚪"
                            fields_text += f"{required_mark} **{field_label}** ({field_type})\n"
                    else:
                        fields_text += "Поля не найдены\n"
                else:
                    fields_text += f"**Данные:** {fields_data}\n"
                
                await query.edit_message_text(
                    fields_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_api_fields')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_next_step')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"❌ **Ошибка**\n\n"
                    f"Не удалось получить поля формы:\n`{fields_data}`\n\n"
                    f"Попробуйте снова или вернитесь назад.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при получении полей формы: {e}")
            await query.edit_message_text(
                f"❌ **Ошибка**\n\n"
                f"Не удалось получить поля формы:\n`{str(e)}`",
                parse_mode='Markdown'
            )
    
    # Методы для работы с контактной информацией 101 hotels
    async def start_101hotels_contact_conv(self, query, context):
        """Начать процесс ввода контактной информации"""
        await query.answer("👤 Начинаем ввод контактной информации...")
        
        keyboard = [
            [InlineKeyboardButton("❌ Отменить", callback_data='cancel_101hotels_contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👤 **Ввод контактной информации**\n\n"
            "Для продолжения регистрации отеля необходимо указать контактное лицо.\n\n"
            "Введите **имя и фамилию** контактного лица:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WAITING_101HOTELS_CONTACT_NAME
    
    async def get_101hotels_contact_name(self, update, context):
        """Получить имя контактного лица"""
        contact_name = update.message.text.strip()
        
        if len(contact_name) < 2:
            await update.message.reply_text(
                "❌ **Ошибка**\n\n"
                "Имя должно содержать минимум 2 символа.\n"
                "Попробуйте ещё раз:",
                parse_mode='Markdown'
            )
            return WAITING_101HOTELS_CONTACT_NAME
        
        # Сохраняем имя в контексте
        context.user_data['101hotels_contact_name'] = contact_name
        
        await update.message.reply_text(
            f"✅ **Имя сохранено:** {contact_name}\n\n"
            "Теперь введите **номер телефона** контактного лица\n"
            "(например: +7 999 123-45-67):",
            parse_mode='Markdown'
        )
        
        return WAITING_101HOTELS_CONTACT_PHONE
    
    async def get_101hotels_contact_phone(self, update, context):
        """Получить телефон контактного лица"""
        contact_phone = update.message.text.strip()
        
        # Простая валидация телефона
        phone_clean = ''.join(filter(str.isdigit, contact_phone))
        if len(phone_clean) < 10:
            await update.message.reply_text(
                "❌ **Ошибка**\n\n"
                "Номер телефона должен содержать минимум 10 цифр.\n"
                "Попробуйте ещё раз:",
                parse_mode='Markdown'
            )
            return WAITING_101HOTELS_CONTACT_PHONE
        
        # Сохраняем телефон в контексте
        context.user_data['101hotels_contact_phone'] = contact_phone
        
        await update.message.reply_text(
            f"✅ **Телефон сохранён:** {contact_phone}\n\n"
            "Теперь введите **email** контактного лица:",
            parse_mode='Markdown'
        )
        
        return WAITING_101HOTELS_CONTACT_EMAIL
    
    async def get_101hotels_contact_email(self, update, context):
        """Получить email контактного лица и отправить данные"""
        contact_email = update.message.text.strip()
        
        # Простая валидация email
        if '@' not in contact_email or '.' not in contact_email:
            await update.message.reply_text(
                "❌ **Ошибка**\n\n"
                "Введите корректный email адрес.\n"
                "Попробуйте ещё раз:",
                parse_mode='Markdown'
            )
            return WAITING_101HOTELS_CONTACT_EMAIL
        
        # Сохраняем email в контексте
        context.user_data['101hotels_contact_email'] = contact_email
        
        # Собираем все данные контактного лица
        contact_data = {
            'name': context.user_data.get('101hotels_contact_name'),
            'phone': context.user_data.get('101hotels_contact_phone'),
            'email': contact_email
        }
        
        await update.message.reply_text(
            "🔄 **Отправляем контактную информацию...**\n\n"
            f"**Имя:** {contact_data['name']}\n"
            f"**Телефон:** {contact_data['phone']}\n"
            f"**Email:** {contact_data['email']}",
            parse_mode='Markdown'
        )
        
        try:
            # Отправляем данные через Selenium
            success, message = self.hotels101_manager.submit_hotel_contact_info(contact_data)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("✅ Продолжить регистрацию", callback_data='101hotels_next_step')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ **Контактная информация успешно отправлена!**\n\n"
                    f"**Результат:** {message}\n\n"
                    "Теперь можно продолжить регистрацию отеля.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_contact_info')],
                    [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ **Ошибка отправки**\n\n"
                    f"**Причина:** {message}\n\n"
                    "Попробуйте отправить данные снова.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке контактной информации: {e}")
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data='101hotels_contact_info')],
                [InlineKeyboardButton("🔙 Назад", callback_data='101hotels_create_new')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ **Ошибка**\n\n"
                f"Не удалось отправить контактную информацию:\n`{str(e)}`\n\n"
                "Попробуйте снова или вернитесь назад.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END
    
    async def cancel_101hotels_contact(self, update, context):
        """Отменить ввод контактной информации 101 hotels"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Ввод контактной информации отменен",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # --- RPA Methods ---
    
    async def show_rpa_menu(self, query):
        """Показать меню RPA-автоматизации"""
        print(f"🔍 DEBUG: self.rpa_manager = {self.rpa_manager}")
        print(f"🔍 DEBUG: type(self.rpa_manager) = {type(self.rpa_manager)}")
        
        if not self.rpa_manager:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **RPA-функции недоступны**\n\n"
                "Проблема с зависимостями. Установите зависимости:\n"
                "```bash\n"
                "pip install numpy==1.24.3 opencv-python==4.9.0.80 pyautogui==0.9.54\n"
                "```\n\n"
                "Или запустите: `install_dependencies.bat`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("🏨 101hotels", callback_data='rpa_platform_101hotels')],
            [InlineKeyboardButton("🏨 Ostrovok", callback_data='rpa_platform_ostrovok')],
            [InlineKeyboardButton("🏨 Bronevik", callback_data='rpa_platform_bronevik')],
            [InlineKeyboardButton("📜 Создать AutoHotkey скрипт", callback_data='rpa_autohotkey')],
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🤖 **RPA-Автоматизация**\n\n"
            "Выберите платформу для автоматизации:\n\n"
            "• **101hotels** - вход и создание отелей\n"
            "• **Ostrovok** - вход и добавление объектов\n"
            "• **Bronevik** - вход и добавление объектов\n"
            "• **AutoHotkey** - создание скриптов автоматизации",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_rpa_platform_menu(self, query, platform: str):
        """Показать меню RPA для конкретной платформы"""
        platform_names = {
            '101hotels': '101hotels',
            'ostrovok': 'Ostrovok',
            'bronevik': 'Bronevik'
        }
        
        platform_name = platform_names.get(platform, platform)
        
        keyboard = [
            [InlineKeyboardButton(f"🔐 RPA Вход в {platform_name}", callback_data=f'rpa_{platform}_login')],
            [InlineKeyboardButton(f"➕ RPA Добавить объект", callback_data=f'rpa_{platform}_add_object')],
            [InlineKeyboardButton("🔙 Назад", callback_data='rpa_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🤖 **RPA-Автоматизация {platform_name}**\n\n"
            f"Выберите действие для автоматизации:\n\n"
            f"• **RPA Вход** - автоматический вход через AutoHotkey\n"
            f"• **RPA Добавить объект** - автоматическое добавление объявления",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_rpa_platform_login(self, query, context, platform: str):
        """Начать RPA-вход на платформу"""
        platform_names = {
            '101hotels': '101hotels',
            'ostrovok': 'Ostrovok',
            'bronevik': 'Bronevik'
        }
        
        platform_name = platform_names.get(platform, platform)
        
        await query.answer(f"🤖 Запускаем RPA-вход в {platform_name}...")
        
        # Сохраняем состояние для получения данных
        context.user_data['rpa_action'] = f'login_{platform}'
        context.user_data['rpa_platform'] = platform
        
        keyboard = [
            [InlineKeyboardButton("🔙 Отмена", callback_data=f'rpa_platform_{platform}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🤖 **RPA-Вход в {platform_name}**\n\n"
            "Введите email для входа:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Устанавливаем состояние для получения email
        context.user_data['waiting_for'] = 'rpa_email'
        return WAITING_RPA_EMAIL
    
    async def start_rpa_platform_add_object(self, query, context, platform: str):
        """Начать RPA-добавление объекта на платформу"""
        platform_names = {
            '101hotels': '101hotels',
            'ostrovok': 'Ostrovok',
            'bronevik': 'Bronevik'
        }
        
        platform_name = platform_names.get(platform, platform)
        
        await query.answer(f"➕ Запускаем RPA-добавление объекта в {platform_name}...")
        
        # Сохраняем состояние для получения данных
        context.user_data['rpa_action'] = f'add_object_{platform}'
        context.user_data['rpa_platform'] = platform
        
        keyboard = [
            [InlineKeyboardButton("🔙 Отмена", callback_data=f'rpa_platform_{platform}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"➕ **RPA-Добавление объекта в {platform_name}**\n\n"
            "Введите название объекта:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Устанавливаем состояние для получения названия объекта
        context.user_data['waiting_for'] = 'object_name'
        return WAITING_OBJECT_NAME
    
    async def handle_rpa_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать email для RPA-входа"""
        email = update.message.text.strip()
        context.user_data['rpa_email'] = email
        
        keyboard = [
            [InlineKeyboardButton("🔙 Отмена", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Введите пароль:",
            reply_markup=reply_markup
        )
        
        context.user_data['waiting_for'] = 'rpa_password'
        return WAITING_RPA_PASSWORD
    
    async def handle_rpa_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать пароль для RPA-входа"""
        if not self.rpa_manager:
            keyboard = [
                [InlineKeyboardButton("❌ Ошибка", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ **RPA-функции недоступны**\n\n"
                "Проблема с зависимостями.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        password = update.message.text.strip()
        email = context.user_data.get('rpa_email')
        platform = context.user_data.get('rpa_platform', '101hotels')
        
        # Выполняем RPA-вход
        success = self.rpa_manager.login_platform(platform, email, password)
        
        if success:
            keyboard = [
                [InlineKeyboardButton("✅ Успешно!", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ **RPA-вход в {platform} выполнен успешно!**\n\n"
                "Браузер автоматически вошел в аккаунт.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("❌ Ошибка", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ **Ошибка RPA-входа в {platform}**\n\n"
                "Проверьте данные и попробуйте снова.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END
    
    async def handle_hotel_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать название отеля для RPA-создания"""
        if not self.rpa_manager:
            keyboard = [
                [InlineKeyboardButton("❌ Ошибка", callback_data='platform_101hotels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ **RPA-функции недоступны**\n\n"
                "Проблема с зависимостями.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        object_name = update.message.text.strip()
        context.user_data['object_name'] = object_name
        
        # Определяем действие
        rpa_action = context.user_data.get('rpa_action', '')
        platform = context.user_data.get('rpa_platform', '101hotels')
        
        if 'add_object' in rpa_action:
            # Добавление объекта на платформу
            object_data = {
                'name': object_name,
                'type': 'Отель',
                'address': 'Москва, ул. Примерная, 1',
                'description': f'Отличный отель {object_name}',
                'price': '5000'
            }
            
            success = self.rpa_manager.add_object_to_platform(platform, object_data)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("✅ Успешно!", callback_data='platform_101hotels')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **RPA-добавление объекта в {platform} выполнено успешно!**\n\n"
                    f"Объект '{object_name}' добавлен автоматически.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("❌ Ошибка", callback_data='platform_101hotels')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"❌ **Ошибка RPA-добавления объекта в {platform}**\n\n"
                    "Попробуйте снова или используйте стандартный метод.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        else:
            # Создание отеля (для 101hotels)
            hotel_data = {
                'name': object_name,
                'country': 'Россия'
            }
            
            success = self.rpa_manager.create_hotel_101hotels(hotel_data)
            
            if success:
                keyboard = [
                    [InlineKeyboardButton("✅ Успешно!", callback_data='platform_101hotels')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **RPA-создание отеля выполнено успешно!**\n\n"
                    f"Отель '{object_name}' создан автоматически.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("❌ Ошибка", callback_data='platform_101hotels')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "❌ **Ошибка RPA-создания отеля**\n\n"
                    "Попробуйте снова или используйте стандартный метод.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        
        return ConversationHandler.END
    
    async def create_autohotkey_script(self, query, context):
        """Создать AutoHotkey скрипт"""
        if not self.rpa_manager:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='rpa_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ **RPA-функции недоступны**\n\n"
                "Проблема с зависимостями.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        await query.answer("📜 Создаем скрипт...")
        
        try:
            # Создаем скрипт для входа в 101hotels
            script_path = self.rpa_manager.create_autohotkey_script(
                '101hotels', 
                'login', 
                {'email': 'test@example.com', 'password': 'password'}
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='rpa_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📜 **AutoHotkey скрипт создан!**\n\n"
                f"Файл: `{script_path}`\n\n"
                f"Для запуска:\n"
                f"1. Установите AutoHotkey\n"
                f"2. Дважды кликните на файл\n"
                f"3. Скрипт выполнится автоматически",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data='rpa_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ **Ошибка создания скрипта**\n\n"
                f"Ошибка: {str(e)}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def cancel_rpa(self, update, context):
        """Отменить RPA-операцию"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='platform_101hotels')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ RPA-операция отменена",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # === AutoHotkey Автоматизация ===
    
    async def start_ahk_automation(self, update, context):
        """Начать AutoHotkey автоматизацию"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🏨 101 Hotels", callback_data='ahk_platform_101hotels')],
            [InlineKeyboardButton("🏨 Ostrovok", callback_data='ahk_platform_ostrovok')],
            [InlineKeyboardButton("🏨 Bronevik", callback_data='ahk_platform_bronevik')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚡ **AutoHotkey Автоматизация**\n\n"
            "Выберите платформу для автоматической выкладки объявлений:\n\n"
            "• **101 Hotels** - автоматический вход и создание отеля\n"
            "• **Ostrovok** - автоматический вход и добавление объекта\n"
            "• **Bronevik** - автоматический вход и добавление объекта\n\n"
            "🤖 AutoHotkey выполнит все действия автоматически!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_AHK_PLATFORM
    
    async def start_ahk_platform_selection(self, update, context):
        """Обработка выбора платформы для AutoHotkey"""
        query = update.callback_query
        return await self.handle_ahk_platform_selection(query, context)
    
    async def handle_ahk_platform_selection(self, update, context):
        """Обработка выбора платформы"""
        query = update.callback_query
        await query.answer()
        
        platform = query.data.replace('ahk_platform_', '')
        context.user_data['ahk_platform'] = platform
        
        platform_names = {
            '101hotels': '101 Hotels',
            'ostrovok': 'Ostrovok',
            'bronevik': 'Bronevik'
        }
        
        platform_name = platform_names.get(platform, platform)
        
        await query.edit_message_text(
            f"⚡ **AutoHotkey Автоматизация - {platform_name}**\n\n"
            f"Введите ваш email для входа в {platform_name}:",
            parse_mode='Markdown'
        )
        return WAITING_AHK_EMAIL
    
    async def handle_ahk_email(self, update, context):
        """Обработка email для AutoHotkey"""
        email = update.message.text.strip()
        context.user_data['ahk_email'] = email
        
        await update.message.reply_text(
            "Введите ваш пароль:"
        )
        return WAITING_AHK_PASSWORD
    
    async def handle_ahk_password(self, update, context):
        """Обработка пароля для AutoHotkey"""
        password = update.message.text.strip()
        context.user_data['ahk_password'] = password
        
        platform = context.user_data.get('ahk_platform')
        
        # Для всех платформ сразу переходим к вводу данных объекта
        # 2FA будет обрабатываться в самом скрипте
        await update.message.reply_text(
            "Введите название объекта (например, Отель Ромашка):"
        )
        return WAITING_AHK_OBJECT_NAME
    
    async def handle_ahk_2fa(self, update, context):
        """Обработка 2FA кода для AutoHotkey"""
        twofa_code = update.message.text.strip()
        
        if twofa_code.lower() == 'skip':
            context.user_data['ahk_2fa_code'] = ''
        else:
            context.user_data['ahk_2fa_code'] = twofa_code
        
        await update.message.reply_text(
            "Введите название объекта (например, Отель Ромашка):"
        )
        return WAITING_AHK_OBJECT_NAME
    
    async def handle_ahk_object_name(self, update, context):
        """Обработка названия объекта"""
        name = update.message.text.strip()
        context.user_data['ahk_object_name'] = name
        
        await update.message.reply_text(
            "Введите тип объекта (например, Отель, Мини-отель, Апартаменты):"
        )
        return WAITING_AHK_OBJECT_TYPE
    
    async def handle_ahk_object_type(self, update, context):
        """Обработка типа объекта"""
        object_type = update.message.text.strip()
        context.user_data['ahk_object_type'] = object_type
        
        await update.message.reply_text(
            "Введите город (например, Санкт-Петербург):"
        )
        return WAITING_AHK_OBJECT_CITY
    
    async def handle_ahk_object_city(self, update, context):
        """Обработка города"""
        city = update.message.text.strip()
        context.user_data['ahk_object_city'] = city
        
        await update.message.reply_text(
            "Введите полный адрес (например, Невский проспект 1):"
        )
        return WAITING_AHK_OBJECT_ADDRESS
    
    async def handle_ahk_object_address(self, update, context):
        """Обработка адреса и создание скрипта"""
        address = update.message.text.strip()
        context.user_data['ahk_object_address'] = address
        
        # Собираем все данные
        platform = context.user_data.get('ahk_platform')
        email = context.user_data.get('ahk_email')
        password = context.user_data.get('ahk_password')
        name = context.user_data.get('ahk_object_name')
        object_type = context.user_data.get('ahk_object_type')
        city = context.user_data.get('ahk_object_city')
        
        # Создаем данные для скрипта
        credentials = {'email': email, 'password': password}
        
        object_data = {
            'name': name,
            'type': object_type,
            'city': city,
            'address': address
        }
        
        try:
            # Создаем скрипт автоматизации
            # Для Ostrovok всегда создаем скрипт с поддержкой 2FA (с паузой)
            if platform == 'ostrovok':
                script_path = self.ahk_automation.create_full_automation_script_with_2fa(
                    platform, credentials, object_data
                )
            else:
                script_path = self.ahk_automation.create_full_automation_script(
                    platform, credentials, object_data
                )
            
            # Показываем подтверждение
            keyboard = [
                [InlineKeyboardButton("✅ Запустить автоматизацию", callback_data='ahk_confirm_run')],
                [InlineKeyboardButton("📁 Показать скрипт", callback_data='ahk_confirm_show')],
                [InlineKeyboardButton("❌ Отменить", callback_data='cancel_ahk')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            summary = f"""⚡ **AutoHotkey Автоматизация готова!**

**Платформа:** {platform}
**Email:** {email}
**Объект:** {name}
**Тип:** {object_type}
**Город:** {city}
**Адрес:** {address}

**Скрипт создан:** {os.path.basename(script_path)}"""

            # Добавляем информацию о 2FA для Ostrovok
            if platform == 'ostrovok':
                summary += """

⚠️ **Для Ostrovok:** Скрипт остановится для ввода кода 2FA после входа в систему

Выберите действие:"""
            else:
                summary += """

Выберите действие:"""
            
            await update.message.reply_text(
                summary,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            context.user_data['ahk_script_path'] = script_path
            return WAITING_AHK_CONFIRMATION
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка при создании скрипта: {str(e)}\n\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
            return ConversationHandler.END
    
    async def handle_ahk_confirmation(self, update, context):
        """Обработка подтверждения AutoHotkey автоматизации"""
        query = update.callback_query
        await query.answer()
        
        action = query.data.replace('ahk_confirm_', '')
        
        if action == 'run':
            script_path = context.user_data.get('ahk_script_path')
            if script_path and os.path.exists(script_path):
                # Запускаем скрипт
                success = self.ahk_automation.run_script(script_path)
                
                if success:
                    await query.edit_message_text(
                        "✅ **AutoHotkey автоматизация запущена!**\n\n"
                        "🤖 Скрипт выполняется в фоновом режиме.\n"
                        "📋 Следите за диалоговыми окнами на экране.\n\n"
                        "⚠️ **Важно:** Не двигайте мышь и не переключайте окна во время выполнения!",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "❌ **Ошибка запуска автоматизации!**\n\n"
                        "**Возможные причины:**\n"
                        "• AutoHotkey не установлен\n"
                        "• Нет прав на запуск\n"
                        "• Антивирус блокирует выполнение\n"
                        "• Неправильный путь к AutoHotkey\n\n"
                        "**Решение:**\n"
                        "1. Установите AutoHotkey с https://www.autohotkey.com/download/\n"
                        "2. Запустите от имени администратора\n"
                        "3. Добавьте исключение в антивирус\n"
                        "4. Перезапустите бота",
                        parse_mode='Markdown'
                    )
            else:
                await query.edit_message_text(
                    "❌ Скрипт не найден. Попробуйте создать заново."
                )
        
        elif action == 'show':
            script_path = context.user_data.get('ahk_script_path')
            if script_path and os.path.exists(script_path):
                try:
                    with open(script_path, 'r', encoding='utf-8-sig') as f:
                        script_content = f.read()
                    
                    # Показываем первые 1000 символов скрипта
                    preview = script_content[:1000] + "..." if len(script_content) > 1000 else script_content
                    
                    await query.edit_message_text(
                        f"📁 **Содержимое скрипта:**\n\n"
                        f"```\n{preview}\n```\n\n"
                        f"**Файл:** {script_path}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    await query.edit_message_text(
                        f"❌ Ошибка при чтении скрипта: {str(e)}"
                    )
            else:
                await query.edit_message_text(
                    "❌ Скрипт не найден."
                )
        
        return ConversationHandler.END
    
    async def cancel_ahk_automation(self, update, context):
        """Отменить AutoHotkey автоматизацию"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ AutoHotkey автоматизация отменена.\n\n"
            "Выберите другое действие:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ])
        )
        return ConversationHandler.END

    # Методы для интегрированной автоматизации
    async def start_integrated_automation(self, update, context):
        """Начать интегрированную автоматизацию"""
        query = update.callback_query
        await query.answer()
        
        # Показываем сводку координат
        summary = self.integrated_manager.get_coordinates_summary()
        
        keyboard = [
            [InlineKeyboardButton("🎯 Выбрать платформу", callback_data='integrated_platform_selection')],
            [InlineKeyboardButton("🧪 Тест координат", callback_data='integrated_test_coordinates')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🚀 **Интегрированная автоматизация**\n\n"
            f"{summary}\n\n"
            f"**Что умеет:**\n"
            f"• Автоматически открывает браузер\n"
            f"• Нажимает кнопку 'Войти'\n"
            f"• Запрашивает данные у пользователя\n"
            f"• Выполняет вход с 2FA\n"
            f"• Добавляет объекты\n\n"
            f"Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def start_integrated_platform_selection(self, update, context):
        """Показать выбор платформы для интегрированной автоматизации"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🏨 Ostrovok", callback_data='integrated_platform_ostrovok')],
            [InlineKeyboardButton("🏨 Bronevik", callback_data='integrated_platform_bronevik')],
            [InlineKeyboardButton("🏨 101Hotels", callback_data='integrated_platform_101hotels')],
            [InlineKeyboardButton("🔙 Назад", callback_data='integrated_automation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 **Выберите платформу для автоматизации:**\n\n"
            "Бот автоматически:\n"
            "1. Откроет браузер с выбранной платформой\n"
            "2. Нажмет кнопку 'Войти'\n"
            "3. Запросит ваши данные\n"
            "4. Выполнит вход\n\n"
            "Выберите платформу:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return WAITING_INTEGRATED_PLATFORM

    async def handle_integrated_platform_selection(self, update, context):
        """Обработать выбор платформы"""
        query = update.callback_query
        await query.answer()
        
        platform = query.data.replace('integrated_platform_', '')
        context.user_data['integrated_platform'] = platform
        
        # Открываем браузер с платформой
        success = self.integrated_manager.open_browser_with_platform(platform)
        
        if success:
            # Нажимаем кнопку входа
            login_success = self.integrated_manager.click_login_button()
            
            if login_success:
                await query.edit_message_text(
                    f"✅ **Браузер открыт для {platform.upper()}**\n\n"
                    f"🤖 Кнопка 'Войти' нажата\n"
                    f"📝 Форма входа готова\n\n"
                    f"**Введите ваш email:**",
                    parse_mode='Markdown'
                )
                return WAITING_INTEGRATED_EMAIL
            else:
                await query.edit_message_text(
                    f"⚠️ **Браузер открыт для {platform.upper()}**\n\n"
                    f"❌ Не удалось найти кнопку 'Войти'\n"
                    f"📝 Попробуйте ввести данные вручную\n\n"
                    f"**Введите ваш email:**",
                    parse_mode='Markdown'
                )
                return WAITING_INTEGRATED_EMAIL
        else:
            await query.edit_message_text(
                f"❌ **Ошибка открытия браузера**\n\n"
                f"Не удалось открыть {platform.upper()}\n\n"
                f"Попробуйте позже:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='integrated_platform_selection')]
                ]),
                parse_mode='Markdown'
            )
            return ConversationHandler.END

    async def handle_integrated_email(self, update, context):
        """Обработать email для интегрированной автоматизации"""
        email = update.message.text.strip()
        context.user_data['integrated_email'] = email
        
        await update.message.reply_text(
            "✅ **Email получен!**\n\n"
            "**Введите ваш пароль:**",
            parse_mode='Markdown'
        )
        return WAITING_INTEGRATED_PASSWORD



    async def handle_integrated_password(self, update, context):
        """Обработать пароль для интегрированной автоматизации"""
        password = update.message.text.strip()
        context.user_data['integrated_password'] = password
        
        # Выполняем первый шаг входа (email + пароль + кнопка продолжить)
        email = context.user_data['integrated_email']
        
        await update.message.reply_text(
            "🤖 **Выполняю первый шаг входа...**\n\n"
            "📝 Ввожу email и пароль...\n"
            "🔘 Нажимаю кнопку 'Продолжить'...\n\n"
            "⏳ Пожалуйста, подождите...",
            parse_mode='Markdown'
        )
        
        # Выполняем первый шаг входа
        success = self.integrated_manager.perform_login_step1(email, password)
        
        if success:
            await update.message.reply_text(
                "✅ **Первый шаг выполнен успешно!**\n\n"
                "📧 Email и пароль введены\n"
                "🔘 Кнопка 'Продолжить' нажата\n\n"
                "**Если требуется 2FA, введите код из письма/приложения:**\n"
                "**Если 2FA не нужен, напишите 'нет':**",
                parse_mode='Markdown'
            )
            return WAITING_INTEGRATED_2FA
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data='integrated_platform_selection')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ **Ошибка первого шага входа!**\n\n"
                "**Возможные причины:**\n"
                "• Неправильные данные\n"
                "• Изменились координаты\n"
                "• Проблемы с интернетом\n\n"
                "**Попробуйте снова:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationHandler.END

    async def handle_integrated_2fa(self, update, context):
        """Обработать 2FA для интегрированной автоматизации"""
        code = update.message.text.strip()
        if code.lower() == 'нет':
            # Если 2FA не нужен, вход уже завершен
            email = context.user_data['integrated_email']
            platform = context.user_data['integrated_platform']
            
            # Сохраняем информацию о сессии
            user_id = update.effective_user.id
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            
            self.user_sessions[user_id][f'{platform}_logged_in'] = True
            self.user_sessions[user_id][f'{platform}_email'] = email
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить объект", callback_data=f'integrated_add_object_{platform}')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ **Вход выполнен успешно!**\n\n"
                f"🎯 Платформа: {platform.upper()}\n"
                f"📧 Email: {email}\n"
                f"🔒 2FA: не требуется\n\n"
                f"**Выберите действие:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Если 2FA нужен, выполняем второй шаг
        context.user_data['integrated_2fa'] = code
        
        await update.message.reply_text(
            "🤖 **Выполняю второй шаг входа (2FA)...**\n\n"
            "🔢 Ввожу 2FA код...\n"
            "🔘 Подтверждаю код...\n\n"
            "⏳ Пожалуйста, подождите...",
            parse_mode='Markdown'
        )
        
        # Выполняем второй шаг входа (2FA)
        success = self.integrated_manager.perform_login_step2(code)
        
        if success:
            # Сохраняем информацию о сессии
            user_id = update.effective_user.id
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            
            platform = context.user_data['integrated_platform']
            email = context.user_data['integrated_email']
            self.user_sessions[user_id][f'{platform}_logged_in'] = True
            self.user_sessions[user_id][f'{platform}_email'] = email
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить объект", callback_data=f'integrated_add_object_{platform}')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ **Вход выполнен успешно!**\n\n"
                f"🎯 Платформа: {platform.upper()}\n"
                f"📧 Email: {email}\n"
                f"🔒 2FA: подтвержден\n\n"
                f"**Выберите действие:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data='integrated_platform_selection')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ **Ошибка 2FA!**\n\n"
                "**Возможные причины:**\n"
                "• Неправильный 2FA код\n"
                "• Изменились координаты\n"
                "• Проблемы с интернетом\n\n"
                "**Попробуйте снова:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END

    async def handle_integrated_object_name(self, update, context):
        """Обработать название объекта для интегрированной автоматизации"""
        object_name = update.message.text.strip()
        context.user_data['integrated_object_name'] = object_name
        
        await update.message.reply_text(
            "✅ **Название объекта получено!**\n\n"
            "**Введите адрес объекта:**",
            parse_mode='Markdown'
        )
        return WAITING_INTEGRATED_OBJECT_ADDRESS

    async def handle_integrated_object_address(self, update, context):
        """Обработать адрес объекта для интегрированной автоматизации"""
        object_address = update.message.text.strip()
        object_name = context.user_data['integrated_object_name']
        
        await update.message.reply_text(
            "🤖 **Добавляю объект...**\n\n"
            f"🏨 Название: {object_name}\n"
            f"📍 Адрес: {object_address}\n\n"
            "⏳ Пожалуйста, подождите...",
            parse_mode='Markdown'
        )
        
        # Добавляем объект через интегрированный менеджер
        success = self.integrated_manager.add_object(object_name, object_address)
        
        if success:
            keyboard = [
                [InlineKeyboardButton("➕ Добавить еще объект", callback_data='integrated_add_object')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')],
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ **Объект добавлен успешно!**\n\n"
                f"🏨 Название: {object_name}\n"
                f"📍 Адрес: {object_address}\n\n"
                f"**Выберите действие:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data='integrated_add_object')],
                [InlineKeyboardButton("🔙 К платформам", callback_data='platforms')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ **Ошибка добавления объекта!**\n\n"
                "**Возможные причины:**\n"
                "• Изменились координаты\n"
                "• Проблемы с интернетом\n"
                "• Неправильные данные\n\n"
                "**Попробуйте снова:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END

    async def cancel_integrated_automation(self, update, context):
        """Отменить интегрированную автоматизацию"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ Интегрированная автоматизация отменена.\n\n"
            "Выберите другое действие:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ])
        )
        return ConversationHandler.END

    async def test_integrated_coordinates(self, query):
        """Тестировать координаты интегрированной автоматизации"""
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🏨 Ostrovok", callback_data='test_coords_ostrovok')],
            [InlineKeyboardButton("🏨 Bronevik", callback_data='test_coords_bronevik')],
            [InlineKeyboardButton("🏨 101Hotels", callback_data='test_coords_101hotels')],
            [InlineKeyboardButton("🔙 Назад", callback_data='integrated_automation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🧪 **Тестирование координат**\n\n"
            "Выберите платформу для тестирования координат.\n"
            "Бот переместит мышь по всем элементам для проверки.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # PyAutoGUI методы
    async def pyautogui_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /pyautogui для тестирования координат"""
        if not self.pyautogui_integration:
            await update.message.reply_text(
                "❌ **PyAutoGUI интеграция недоступна**\n\n"
                "Убедитесь, что:\n"
                "• Установлен модуль pyautogui\n"
                "• Загружены координаты элементов\n"
                "• Система готова к работе",
                parse_mode='Markdown'
            )
            return
        
        await self.show_pyautogui_menu(update.message)

    async def show_pyautogui_menu(self, message_or_query):
        """Показать меню PyAutoGUI"""
        if not self.pyautogui_integration:
            text = "❌ **PyAutoGUI интеграция недоступна**"
            keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]]
        else:
            # Получаем информацию о координатах
            summary = self.pyautogui_integration.get_coordinates_summary()
            screen_info = self.pyautogui_integration.get_screen_info()
            
            text = f"🎯 **PyAutoGUI Координаты**\n\n"
            text += f"📺 **Экран:** {screen_info.get('screen_resolution', 'Неизвестно')}\n"
            text += f"🖱️ **Мышь:** {screen_info.get('mouse_position', 'Неизвестно')}\n"
            text += f"📍 **Координат:** {screen_info.get('coordinates_loaded', 0)}\n\n"
            text += f"{summary}\n\n"
            text += "**Выберите действие:**"
            
            keyboard = [
                [InlineKeyboardButton("🚀 Автоматизация", callback_data='pyautogui_automation')],
                [InlineKeyboardButton("🧪 Тест координат", callback_data='pyautogui_test')],
                [InlineKeyboardButton("🔐 Тест входа", callback_data='pyautogui_login_test')],
                [InlineKeyboardButton("🏨 Тест добавления объекта", callback_data='pyautogui_add_object_test')],
                [InlineKeyboardButton("📊 Информация об экране", callback_data='pyautogui_screen_info')],
                [InlineKeyboardButton("🔄 Обновить координаты", callback_data='pyautogui_reload')],
                [InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await message_or_query.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def pyautogui_test_coordinates(self, query):
        """Тестирование координат PyAutoGUI"""
        await query.answer("🧪 Тестируем координаты...")
        
        if not self.pyautogui_integration:
            await query.edit_message_text(
                "❌ **PyAutoGUI интеграция недоступна**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
                ])
            )
            return
        
        # Тестируем координаты
        test_result = self.pyautogui_integration.test_coordinates()
        
        text = f"🧪 **Тест координат PyAutoGUI**\n\n"
        text += f"{test_result['message']}\n\n"
        
        if test_result['success']:
            text += "✅ **Все координаты доступны!**\n\n"
            text += "**Доступные элементы:**\n"
            for element in test_result['available_elements']:
                text += f"• {element}\n"
        else:
            text += "⚠️ **Некоторые координаты отсутствуют**\n\n"
            text += "**Отсутствующие элементы:**\n"
            for element in test_result['missing_elements']:
                text += f"• {element}\n"
            text += "\n**Рекомендации:**\n"
            text += "• Запустите PyAutoGUI Inspector\n"
            text += "• Запишите недостающие координаты\n"
            text += "• Обновите конфигурацию"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить тест", callback_data='pyautogui_test')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def pyautogui_login_test(self, query):
        """Тестирование входа через PyAutoGUI"""
        await query.answer("🔐 Тестируем вход...")
        
        if not self.pyautogui_integration:
            await query.edit_message_text(
                "❌ **PyAutoGUI интеграция недоступна**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
                ])
            )
            return
        
        # Показываем инструкцию
        text = "🔐 **Тест входа через PyAutoGUI**\n\n"
        text += "**Внимание!** Бот будет выполнять действия на экране:\n\n"
        text += "1. 🖱️ Клик по кнопке входа\n"
        text += "2. ⌨️ Ввод тестового email\n"
        text += "3. ⌨️ Ввод тестового пароля\n"
        text += "4. 🖱️ Отправка формы\n\n"
        text += "**Убедитесь, что:**\n"
        text += "• Браузер открыт на нужной странице\n"
        text += "• Окно браузера активно\n"
        text += "• Координаты корректны\n\n"
        text += "**Нажмите кнопку для начала теста:**"
        
        keyboard = [
            [InlineKeyboardButton("🚀 Начать тест входа", callback_data='pyautogui_login_start')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def pyautogui_login_start(self, query):
        """Запуск теста входа"""
        await query.answer("🚀 Запускаем тест входа...")
        
        if not self.pyautogui_integration:
            await query.edit_message_text("❌ PyAutoGUI интеграция недоступна")
            return
        
        # Выполняем тест входа
        result = self.pyautogui_integration.perform_login_sequence(
            email="test@example.com",
            password="testpassword123"
        )
        
        text = "🔐 **Результат теста входа**\n\n"
        
        if result['success']:
            text += "✅ **Тест выполнен успешно!**\n\n"
            text += "**Выполненные шаги:**\n"
            for step in result['steps_completed']:
                text += f"• {step}\n"
        else:
            text += "❌ **Тест завершился с ошибками**\n\n"
            text += "**Ошибки:**\n"
            for error in result['errors']:
                text += f"• {error}\n"
            text += f"\n**Сообщение:** {result['message']}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить тест", callback_data='pyautogui_login_start')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def pyautogui_add_object_test(self, query):
        """Тестирование добавления объекта"""
        await query.answer("🏨 Тестируем добавление объекта...")
        
        if not self.pyautogui_integration:
            await query.edit_message_text(
                "❌ **PyAutoGUI интеграция недоступна**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
                ])
            )
            return
        
        # Выполняем тест добавления объекта
        result = self.pyautogui_integration.perform_add_object_sequence("Тестовый отель")
        
        text = "🏨 **Результат теста добавления объекта**\n\n"
        
        if result['success']:
            text += "✅ **Тест выполнен успешно!**\n\n"
            text += "**Выполненные шаги:**\n"
            for step in result['steps_completed']:
                text += f"• {step}\n"
        else:
            text += "❌ **Тест завершился с ошибками**\n\n"
            text += "**Ошибки:**\n"
            for error in result['errors']:
                text += f"• {error}\n"
            text += f"\n**Сообщение:** {result['message']}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить тест", callback_data='pyautogui_add_object_test')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def pyautogui_screen_info(self, query):
        """Показать информацию об экране"""
        await query.answer("📊 Получаем информацию об экране...")
        
        if not self.pyautogui_integration:
            await query.edit_message_text(
                "❌ **PyAutoGUI интеграция недоступна**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
                ])
            )
            return
        
        screen_info = self.pyautogui_integration.get_screen_info()
        
        text = "📊 **Информация об экране**\n\n"
        text += f"📺 **Разрешение:** {screen_info.get('screen_resolution', 'Неизвестно')}\n"
        text += f"🖱️ **Позиция мыши:** {screen_info.get('mouse_position', 'Неизвестно')}\n"
        text += f"📍 **Координат загружено:** {screen_info.get('coordinates_loaded', 0)}\n"
        text += f"🕐 **Время:** {screen_info.get('timestamp', 'Неизвестно')}\n\n"
        
        if 'error' in screen_info:
            text += f"❌ **Ошибка:** {screen_info['error']}"
        else:
            text += "✅ **Информация получена успешно**"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='pyautogui_screen_info')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def pyautogui_reload(self, query):
        """Перезагрузить координаты"""
        await query.answer("🔄 Перезагружаем координаты...")
        
        if not self.pyautogui_integration:
            await query.edit_message_text(
                "❌ **PyAutoGUI интеграция недоступна**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
                ])
            )
            return
        
        # Перезагружаем координаты
        success = self.pyautogui_integration.load_coordinates()
        
        if success:
            text = "✅ **Координаты перезагружены успешно!**\n\n"
            summary = self.pyautogui_integration.get_coordinates_summary()
            text += summary
        else:
            text = "❌ **Ошибка при перезагрузке координат**\n\n"
            text += "**Возможные причины:**\n"
            text += "• Файл конфигурации не найден\n"
            text += "• Ошибка чтения файла\n"
            text += "• Неправильный формат данных"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data='pyautogui_reload')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # Новые методы для PyAutoGUI автоматизации с выбором типа отеля
    async def start_pyautogui_automation(self, update, context):
        """Начать PyAutoGUI автоматизацию"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🔐 Вход в аккаунт", callback_data='pyautogui_login_start')],
            [InlineKeyboardButton("➕ Добавить объект", callback_data='pyautogui_add_object_start')],
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎯 PyAutoGUI Автоматизация\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def start_pyautogui_login(self, update, context):
        """Начать процесс входа через PyAutoGUI"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🔐 Вход через PyAutoGUI\n\n"
            "Введите ваш email:"
        )
        return WAITING_PYAUTOGUI_EMAIL
    
    async def handle_pyautogui_email(self, update, context):
        """Обработать ввод email для PyAutoGUI"""
        email = update.message.text.strip()
        context.user_data['pyautogui_email'] = email
        
        await update.message.reply_text(
            "Введите ваш пароль:"
        )
        return WAITING_PYAUTOGUI_PASSWORD
    
    async def handle_pyautogui_password(self, update, context):
        """Обработать ввод пароля для PyAutoGUI"""
        password = update.message.text.strip()
        email = context.user_data.get('pyautogui_email')
        
        if not self.pyautogui_integration:
            await update.message.reply_text("❌ PyAutoGUI интеграция недоступна")
            return ConversationHandler.END
        
        # Выполняем вход
        result = self.pyautogui_integration.perform_login_sequence(email, password)
        
        if result['success']:
            # Проверяем, нужен ли 2FA
            if '2fa_field' in self.pyautogui_integration.coordinates:
                await update.message.reply_text(
                    "Введите код 2FA из письма/email:"
                )
                return WAITING_PYAUTOGUI_2FA
            else:
                await update.message.reply_text(
                    f"✅ {result['message']}\n\n"
                    "Вход выполнен успешно!"
                )
                return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ {result['message']}\n\n"
                "Попробуйте еще раз или проверьте координаты."
            )
            return ConversationHandler.END
    
    async def handle_pyautogui_2fa(self, update, context):
        """Обработать ввод 2FA кода для PyAutoGUI"""
        code = update.message.text.strip()
        
        if not self.pyautogui_integration:
            await update.message.reply_text("❌ PyAutoGUI интеграция недоступна")
            return ConversationHandler.END
        
        # Кликаем по полю 2FA и вводим код
        if self.pyautogui_integration.safe_click('2fa_field'):
            time.sleep(1)
            if self.pyautogui_integration.safe_type('2fa_field', code):
                await update.message.reply_text(
                    "✅ 2FA код введен успешно!\n\n"
                    "Вход выполнен!"
                )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при вводе 2FA кода"
                )
        else:
            await update.message.reply_text(
                "❌ Не удалось найти поле для 2FA кода"
            )
        
        return ConversationHandler.END
    
    async def start_pyautogui_add_object(self, update, context):
        """Начать процесс добавления объекта через PyAutoGUI"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "➕ Добавление объекта через PyAutoGUI\n\n"
            "Введите название объекта:"
        )
        return WAITING_PYAUTOGUI_OBJECT_NAME
    
    async def handle_pyautogui_object_name(self, update, context):
        """Обработать ввод названия объекта для PyAutoGUI"""
        object_name = update.message.text.strip()
        context.user_data['pyautogui_object_name'] = object_name
        
        # Показываем меню выбора типа отеля
        available_types = self.pyautogui_integration.get_available_hotel_types()
        
        if not available_types:
            await update.message.reply_text(
                "❌ Нет доступных типов отелей. Проверьте координаты."
            )
            return ConversationHandler.END
        
        # Создаем клавиатуру с типами отелей
        keyboard = []
        for type_key, type_name in available_types.items():
            keyboard.append([InlineKeyboardButton(type_name, callback_data=f'hotel_type_{type_key}')])
        
        keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data='cancel_pyautogui')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите тип отеля:",
            reply_markup=reply_markup
        )
        return WAITING_PYAUTOGUI_HOTEL_TYPE
    
    async def handle_pyautogui_hotel_type(self, update, context):
        """Обработать выбор типа отеля для PyAutoGUI"""
        query = update.callback_query
        await query.answer()
        
        hotel_type = query.data.replace('hotel_type_', '')
        object_name = context.user_data.get('pyautogui_object_name')
        
        if not self.pyautogui_integration:
            await query.edit_message_text("❌ PyAutoGUI интеграция недоступна")
            return ConversationHandler.END
        
        # Выполняем добавление объекта
        add_result = self.pyautogui_integration.perform_add_object_sequence(object_name)
        
        if add_result['success']:
            # Выбираем тип отеля
            type_result = self.pyautogui_integration.select_hotel_type(hotel_type)
            
            if type_result['success']:
                await query.edit_message_text(
                    f"✅ Объект '{object_name}' добавлен успешно!\n"
                    f"✅ Тип отеля '{hotel_type}' выбран!\n\n"
                    "Автоматизация завершена."
                )
            else:
                await query.edit_message_text(
                    f"✅ Объект '{object_name}' добавлен успешно!\n"
                    f"❌ Ошибка выбора типа отеля: {type_result['message']}"
                )
        else:
            await query.edit_message_text(
                f"❌ Ошибка добавления объекта: {add_result['message']}"
            )
        
        return ConversationHandler.END
    
    async def cancel_pyautogui_automation(self, update, context):
        """Отменить PyAutoGUI автоматизацию"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='pyautogui_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Автоматизация отменена",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота...")
        
        # Запускаем уведомления Bnovo если они включены
        if self.bnovo_notifications_enabled:
            logger.info("Запуск уведомлений Bnovo PMS...")
            # Проверяем, доступен ли job_queue
            if hasattr(self.application, 'job_queue') and self.application.job_queue:
                # Запускаем уведомления в отдельной задаче
                self.application.job_queue.run_repeating(
                    self.check_new_bookings_job, 
                    interval=300,  # каждые 5 минут
                    first=10  # первая проверка через 10 секунд
                )
                logger.info("Уведомления Bnovo PMS запущены")
            else:
                logger.warning("JobQueue недоступен. Уведомления Bnovo PMS отключены.")
        
        self.application.run_polling()

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("Не указан токен бота! Создайте файл .env с BOT_TOKEN")
        exit(1)
    
    bot = HotelBot(BOT_TOKEN)
    bot.run() 
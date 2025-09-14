#!/usr/bin/env python3
"""
Единый скрипт для запуска Hotel Bot и Mini App одновременно
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path
from typing import List, Optional

# Создание папки logs перед настройкой логирования
os.makedirs('logs', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/run_all.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HotelBotManager:
    """Менеджер для запуска Hotel Bot и Mini App"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
        self.setup_directories()
    
    def setup_directories(self):
        """Создание необходимых директорий"""
        directories = ['logs', 'mini_app', 'recorded_actions', 'sessions']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✅ Директория {directory} готова")
    
    def check_requirements(self) -> bool:
        """Проверка наличия необходимых файлов и зависимостей"""
        logger.info("🔍 Проверка требований...")
        
        # Проверка основных файлов
        required_files = [
            'bot.py',
            'mini_app_api.py',
            'run_mini_app.py',
            'mini_app/index.html',
            'mini_app/styles.css',
            'mini_app/script.js'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
            return False
        
        # Проверка зависимостей
        try:
            import fastapi
            import uvicorn
            import telegram
            logger.info("✅ Все зависимости установлены")
        except ImportError as e:
            logger.error(f"❌ Отсутствуют зависимости: {e}")
            logger.info("Установите их командой: pip install -r requirements.txt")
            return False
        
        # Проверка конфигурации
        if not os.path.exists('.env'):
            logger.warning("⚠️ Файл .env не найден. Создайте его с настройками:")
            logger.info("BOT_TOKEN=your_bot_token_here")
            logger.info("MINI_APP_URL=https://your-domain.com")
            return False
        
        logger.info("✅ Все требования выполнены")
        return True
    
    def start_mini_app(self) -> Optional[subprocess.Popen]:
        """Запуск Mini App API"""
        logger.info("🚀 Запуск Mini App API...")
        
        try:
            # Запуск Mini App API
            process = subprocess.Popen(
                [sys.executable, 'run_mini_app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Ждем запуска сервера
            time.sleep(3)
            
            if process.poll() is None:
                logger.info("✅ Mini App API запущен на http://localhost:8000")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ Ошибка запуска Mini App API: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Mini App API: {e}")
            return None
    
    def start_bot(self) -> Optional[subprocess.Popen]:
        """Запуск Telegram бота"""
        logger.info("🤖 Запуск Telegram бота...")
        
        try:
            # Запуск бота
            process = subprocess.Popen(
                [sys.executable, 'run_bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Ждем запуска бота
            time.sleep(2)
            
            if process.poll() is None:
                logger.info("✅ Telegram бот запущен")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ Ошибка запуска бота: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return None
    
    def monitor_process(self, process: subprocess.Popen, name: str):
        """Мониторинг процесса"""
        try:
            while self.running and process.poll() is None:
                # Читаем вывод процесса
                if process.stdout and process.stdout.readable():
                    line = process.stdout.readline()
                    if line:
                        logger.info(f"[{name}] {line.strip()}")
                
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"❌ Ошибка мониторинга {name}: {e}")
    
    def start_all(self):
        """Запуск всех сервисов"""
        logger.info("🚀 Запуск Hotel Bot и Mini App...")
        
        if not self.check_requirements():
            logger.error("❌ Требования не выполнены. Запуск отменен.")
            return False
        
        self.running = True
        
        # Запуск Mini App API
        mini_app_process = self.start_mini_app()
        if mini_app_process:
            self.processes.append(mini_app_process)
            
            # Запуск мониторинга Mini App
            mini_app_thread = threading.Thread(
                target=self.monitor_process,
                args=(mini_app_process, "Mini App")
            )
            mini_app_thread.daemon = True
            mini_app_thread.start()
        else:
            logger.error("❌ Не удалось запустить Mini App API")
            self.stop_all()
            return False
        
        # Небольшая пауза перед запуском бота
        time.sleep(2)
        
        # Запуск Telegram бота
        bot_process = self.start_bot()
        if bot_process:
            self.processes.append(bot_process)
            
            # Запуск мониторинга бота
            bot_thread = threading.Thread(
                target=self.monitor_process,
                args=(bot_process, "Bot")
            )
            bot_thread.daemon = True
            bot_thread.start()
        else:
            logger.error("❌ Не удалось запустить Telegram бота")
            self.stop_all()
            return False
        
        logger.info("🎉 Все сервисы запущены успешно!")
        logger.info("📱 Mini App доступен на: http://localhost:8000")
        logger.info("🤖 Telegram бот готов к работе")
        logger.info("⏹️ Для остановки нажмите Ctrl+C")
        
        return True
    
    def stop_all(self):
        """Остановка всех сервисов"""
        logger.info("⏹️ Остановка всех сервисов...")
        self.running = False
        
        for process in self.processes:
            if process.poll() is None:
                logger.info(f"🛑 Остановка процесса {process.pid}")
                process.terminate()
                
                # Ждем завершения процесса
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ Принудительное завершение процесса")
                    process.kill()
        
        self.processes.clear()
        logger.info("✅ Все сервисы остановлены")
    
    def run(self):
        """Основной цикл работы"""
        # Обработка сигналов для корректного завершения
        def signal_handler(signum, frame):
            logger.info("📡 Получен сигнал завершения")
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            if self.start_all():
                # Основной цикл
                while self.running:
                    # Проверяем состояние процессов
                    for i, process in enumerate(self.processes):
                        if process.poll() is not None:
                            logger.error(f"❌ Процесс {i} завершился неожиданно")
                            self.stop_all()
                            return
                    
                    time.sleep(1)
            else:
                logger.error("❌ Не удалось запустить сервисы")
                return
                
        except KeyboardInterrupt:
            logger.info("📡 Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            self.stop_all()

def create_env_template():
    """Создание шаблона .env файла"""
    env_content = """# Конфигурация Hotel Bot
BOT_TOKEN=your_bot_token_here
BNOVO_API_KEY=your_bnovo_api_key_here

# Конфигурация Mini App
MINI_APP_URL=https://your-domain.com
SECRET_KEY=your-secret-key-here
MINI_APP_DEBUG=True

# Дополнительные настройки
LOG_LEVEL=INFO
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("📝 Создан файл .env. Заполните его настройками.")
        return False
    return True

def main():
    """Главная функция"""
    print("🏨 Hotel Bot - Единый запуск Mini App и бота")
    print("=" * 50)
    
    # Создание шаблона .env если его нет
    if not create_env_template():
        print("❌ Сначала настройте файл .env")
        return
    
    # Создание менеджера и запуск
    manager = HotelBotManager()
    manager.run()

if __name__ == "__main__":
    main()

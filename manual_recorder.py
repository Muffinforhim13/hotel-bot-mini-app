#!/usr/bin/env python3
"""
Ручная система записи действий
Альтернативный метод записи, который работает даже если JavaScript заблокирован
"""

import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualRecorder:
    """Ручная система записи действий"""
    
    def __init__(self, platform_name):
        self.platform_name = platform_name
        self.actions = []
        self.driver = None
        self.recording = False
        self.recordings_dir = "recorded_actions"
        
        # Создаем директорию для записей
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
    
    def setup_driver(self):
        """Настройка веб-драйвера"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def start_recording(self, url):
        """Начать запись действий"""
        try:
            self.driver = self.setup_driver()
            self.driver.get(url)
            self.recording = True
            self.actions = []
            
            # Записываем начальную навигацию
            self.actions.append({
                'type': 'navigation',
                'url': url,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Запись начата для {url}")
            logger.info("Браузер открыт. Выполните нужные действия...")
            logger.info("После каждого важного действия нажмите Enter в консоли для записи")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при начале записи: {e}")
            return False
    
    def record_current_page_state(self):
        """Записать текущее состояние страницы"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # Ищем все интерактивные элементы
            elements = []
            
            # Поля ввода
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.is_displayed():
                    elements.append({
                        'type': 'input',
                        'tagName': inp.tag_name,
                        'id': inp.get_attribute('id') or '',
                        'name': inp.get_attribute('name') or '',
                        'className': inp.get_attribute('class') or '',
                        'type_attr': inp.get_attribute('type') or '',
                        'value': inp.get_attribute('value') or '',
                        'placeholder': inp.get_attribute('placeholder') or '',
                        'xpath': self.get_xpath(inp)
                    })
            
            # Кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    elements.append({
                        'type': 'button',
                        'tagName': btn.tag_name,
                        'id': btn.get_attribute('id') or '',
                        'name': btn.get_attribute('name') or '',
                        'className': btn.get_attribute('class') or '',
                        'text': btn.text or '',
                        'xpath': self.get_xpath(btn)
                    })
            
            # Ссылки
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                if link.is_displayed():
                    elements.append({
                        'type': 'link',
                        'tagName': link.tag_name,
                        'id': link.get_attribute('id') or '',
                        'className': link.get_attribute('class') or '',
                        'text': link.text or '',
                        'href': link.get_attribute('href') or '',
                        'xpath': self.get_xpath(link)
                    })
            
            # Select элементы
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for select in selects:
                if select.is_displayed():
                    options = []
                    for option in select.find_elements(By.TAG_NAME, "option"):
                        options.append({
                            'value': option.get_attribute('value') or '',
                            'text': option.text or ''
                        })
                    
                    elements.append({
                        'type': 'select',
                        'tagName': select.tag_name,
                        'id': select.get_attribute('id') or '',
                        'name': select.get_attribute('name') or '',
                        'className': select.get_attribute('class') or '',
                        'options': options,
                        'xpath': self.get_xpath(select)
                    })
            
            # Записываем состояние страницы
            page_state = {
                'type': 'page_state',
                'url': current_url,
                'title': page_title,
                'elements': elements,
                'timestamp': datetime.now().isoformat()
            }
            
            self.actions.append(page_state)
            logger.info(f"Записано состояние страницы: {current_url}")
            logger.info(f"Найдено элементов: {len(elements)}")
            
            return page_state
            
        except Exception as e:
            logger.error(f"Ошибка при записи состояния страницы: {e}")
            return None
    
    def get_xpath(self, element):
        """Получить XPath элемента"""
        try:
            if element.get_attribute('id'):
                return f"//*[@id='{element.get_attribute('id')}']"
            
            # Простой XPath по тегу и классу
            tag = element.tag_name
            class_name = element.get_attribute('class')
            if class_name:
                return f"//{tag}[contains(@class, '{class_name.split()[0]}')]"
            
            return f"//{tag}"
        except:
            return ""
    
    def record_navigation(self):
        """Записать навигацию"""
        try:
            current_url = self.driver.current_url
            self.actions.append({
                'type': 'navigation',
                'url': current_url,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"Записана навигация: {current_url}")
        except Exception as e:
            logger.error(f"Ошибка при записи навигации: {e}")
    
    def stop_recording(self):
        """Остановить запись и сохранить действия"""
        try:
            self.recording = False
            
            if self.actions:
                # Сохраняем в файл
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{self.recordings_dir}/{self.platform_name}_manual_{timestamp}.json"
                
                recording_data = {
                    "platform": self.platform_name,
                    "recording_type": "manual",
                    "created_at": datetime.now().isoformat(),
                    "total_actions": len(self.actions),
                    "actions": self.actions
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(recording_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Запись сохранена в файл: {filename}")
                logger.info(f"Записано действий: {len(self.actions)}")
                return filename
            else:
                logger.warning("Не найдено записанных действий")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при остановке записи: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Главная функция"""
    print("🎬 Ручная система записи действий")
    print("=" * 50)
    
    platforms = {
        '1': ('ostrovok', 'Ostrovok', 'https://extranet.ostrovok.ru'),
        '2': ('bronevik', 'Bronevik', 'https://extranet.bronevik.com'),
        '3': ('101hotels', '101 Hotels', 'https://extranet.101hotels.com')
    }
    
    print("Выберите платформу:")
    for key, (platform_id, name, url) in platforms.items():
        print(f"{key}. {name} ({url})")
    
    choice = input("\nВведите номер (1-3): ").strip()
    
    if choice not in platforms:
        print("❌ Неверный выбор")
        return
    
    platform_id, platform_name, url = platforms[choice]
    
    print(f"\n🎬 Ручная запись для {platform_name}")
    print(f"🌐 URL: {url}")
    print("\n💡 ИНСТРУКЦИЯ:")
    print("1. Браузер откроется автоматически")
    print("2. Выполните нужные действия на сайте")
    print("3. После каждого важного шага нажмите Enter для записи")
    print("4. Введите 'stop' для завершения записи")
    print("5. Введите 'state' для записи текущего состояния страницы")
    print("6. Введите 'nav' для записи навигации")
    
    input("\nНажмите Enter, чтобы начать...")
    
    recorder = ManualRecorder(platform_id)
    
    if recorder.start_recording(url):
        print("\n✅ Запись начата! Выполните действия в браузере...")
        
        while True:
            command = input("\nВведите команду (state/nav/stop): ").strip().lower()
            
            if command == 'stop':
                break
            elif command == 'state':
                recorder.record_current_page_state()
            elif command == 'nav':
                recorder.record_navigation()
            else:
                print("❌ Неизвестная команда. Используйте: state, nav, stop")
        
        filename = recorder.stop_recording()
        
        if filename:
            print(f"\n✅ Запись сохранена: {filename}")
            print("Теперь вы можете использовать эту запись для автоматизации!")
        else:
            print("\n❌ Ошибка при сохранении записи")
    else:
        print("\n❌ Ошибка при запуске записи")

if __name__ == "__main__":
    main() 
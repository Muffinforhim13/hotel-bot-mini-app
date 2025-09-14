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
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionRecorder:
    """Система записи и воспроизведения действий пользователя"""
    
    def __init__(self, platform_name):
        self.platform_name = platform_name
        self.actions = []
        self.driver = None
        self.recording = False
        self.recordings_dir = "recorded_actions"
        self.recording_thread = None
        self.last_url = None
        
        # Создаем директорию для записей
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
    
    def setup_driver(self, headless=False):
        """Настройка веб-драйвера"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
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
    
    def get_element_info(self, element):
        """Получить информацию об элементе"""
        try:
            return {
                'tagName': element.tag_name,
                'id': element.get_attribute('id') or '',
                'className': element.get_attribute('class') or '',
                'name': element.get_attribute('name') or '',
                'type': element.get_attribute('type') or '',
                'value': element.get_attribute('value') or '',
                'placeholder': element.get_attribute('placeholder') or '',
                'text': element.text or '',
                'href': element.get_attribute('href') or '',
                'xpath': self.get_xpath(element)
            }
        except:
            return {}
    
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
    
    def monitor_page_changes(self):
        """Мониторинг изменений страницы"""
        while self.recording:
            try:
                current_url = self.driver.current_url
                if current_url != self.last_url:
                    self.actions.append({
                        'type': 'navigation',
                        'url': current_url,
                        'timestamp': datetime.now().isoformat()
                    })
                    self.last_url = current_url
                    logger.info(f"Записана навигация: {current_url}")
                
                time.sleep(0.5)  # Проверяем каждые 500мс
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
                break
    
    def start_recording(self, url, headless=False):
        """Начать запись действий"""
        try:
            self.driver = self.setup_driver(headless)
            self.driver.get(url)
            self.recording = True
            self.actions = []
            self.last_url = url
            
            # Запускаем мониторинг изменений страницы
            self.recording_thread = threading.Thread(target=self.monitor_page_changes)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            # Пытаемся добавить JavaScript для записи действий
            try:
                self.driver.execute_script("""
                    window.recordedActions = [];
                    window.recording = true;
                    
                    // Функция для получения XPath элемента
                    function getXPath(element) {
                        if (element.id !== '') {
                            return 'id("' + element.id + '")';
                        }
                        if (element === document.body) {
                            return element.tagName;
                        }
                        var ix = 0;
                        var siblings = element.parentNode.childNodes;
                        for (var i = 0; i < siblings.length; i++) {
                            var sibling = siblings[i];
                            if (sibling === element) {
                                return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                            }
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                                ix++;
                            }
                        }
                    }
                    
                    // Записываем клики
                    document.addEventListener('click', function(e) {
                        if (window.recording) {
                            var rect = e.target.getBoundingClientRect();
                            window.recordedActions.push({
                                type: 'click',
                                xpath: getXPath(e.target),
                                text: e.target.textContent || e.target.value || '',
                                tagName: e.target.tagName,
                                className: e.target.className,
                                id: e.target.id,
                                coordinates: {
                                    x: Math.round(rect.left + rect.width / 2),
                                    y: Math.round(rect.top + rect.height / 2)
                                },
                                timestamp: Date.now(),
                                url: window.location.href
                            });
                            console.log('Recorded click:', e.target.textContent || e.target.value);
                        }
                    }, true);
                    
                    // Записываем ввод текста
                    document.addEventListener('input', function(e) {
                        if (window.recording) {
                            window.recordedActions.push({
                                type: 'input',
                                xpath: getXPath(e.target),
                                text: e.target.textContent || e.target.value || '',
                                tagName: e.target.tagName,
                                className: e.target.className,
                                id: e.target.id,
                                value: e.target.value,
                                placeholder: e.target.placeholder || '',
                                timestamp: Date.now(),
                                url: window.location.href
                            });
                            console.log('Recorded input:', e.target.value);
                        }
                    });
                    
                    // Записываем изменения select
                    document.addEventListener('change', function(e) {
                        if (window.recording && e.target.tagName === 'SELECT') {
                            window.recordedActions.push({
                                type: 'select',
                                xpath: getXPath(e.target),
                                text: e.target.textContent || '',
                                tagName: e.target.tagName,
                                className: e.target.className,
                                id: e.target.id,
                                value: e.target.value,
                                selectedText: e.target.options[e.target.selectedIndex]?.text || '',
                                timestamp: Date.now(),
                                url: window.location.href
                            });
                            console.log('Recorded select:', e.target.value);
                        }
                    });
                    
                    // Записываем навигацию
                    var originalPushState = history.pushState;
                    history.pushState = function() {
                        if (window.recording) {
                            window.recordedActions.push({
                                type: 'navigation',
                                url: arguments[2],
                                timestamp: Date.now()
                            });
                            console.log('Recorded navigation:', arguments[2]);
                        }
                        return originalPushState.apply(this, arguments);
                    };
                """)
                logger.info("JavaScript для записи добавлен успешно")
            except Exception as js_error:
                logger.warning(f"JavaScript не удалось добавить: {js_error}")
            
            logger.info(f"Запись начата для {url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при начале записи: {e}")
            return False
    
    def stop_recording(self):
        """Остановить запись и сохранить действия"""
        try:
            self.recording = False
            
            # Ждем завершения потока мониторинга
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2)
            
            if self.driver:
                # Пытаемся получить действия из JavaScript
                try:
                    self.driver.execute_script("window.recording = false;")
                    js_actions = self.driver.execute_script("return window.recordedActions;")
                    
                    if js_actions:
                        # Объединяем JavaScript действия с навигацией
                        all_actions = js_actions + self.actions
                        # Убираем дубликаты навигации
                        seen_urls = set()
                        unique_actions = []
                        for action in all_actions:
                            if action.get('type') == 'navigation':
                                if action.get('url') not in seen_urls:
                                    unique_actions.append(action)
                                    seen_urls.add(action.get('url'))
                            else:
                                unique_actions.append(action)
                        
                        self.actions = unique_actions
                except Exception as js_error:
                    logger.warning(f"Не удалось получить JavaScript действия: {js_error}")
                    # Используем только навигационные действия
                    pass
                
                if self.actions:
                    # Сохраняем в файл
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{self.recordings_dir}/{self.platform_name}_actions_{timestamp}.json"
                    
                    recording_data = {
                        "platform": self.platform_name,
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
    
    def load_recording(self, filename):
        """Загрузить записанные действия из файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.actions = data.get('actions', [])
                logger.info(f"Загружено {len(self.actions)} действий из {filename}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке записи: {e}")
            return False
    
    def replace_placeholders(self, text, user_data):
        """Заменяет placeholder'ы на реальные данные пользователя"""
        if not text:
            return text
            
        replacements = {
            '{{email}}': user_data.get('email', ''),
            '{{password}}': user_data.get('password', ''),
            '{{hotel_name}}': user_data.get('hotel_name', ''),
            '{{hotel_address}}': user_data.get('hotel_address', ''),
            '{{hotel_type}}': user_data.get('hotel_type', ''),
            '{{city}}': user_data.get('city', ''),
            '{{phone}}': user_data.get('phone', ''),
            '{{website}}': user_data.get('website', ''),
            '{{contact_name}}': user_data.get('contact_name', ''),
            '{{contact_email}}': user_data.get('contact_email', ''),
        }
        
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, str(value))
        
        return text
    
    def find_element_smart(self, action):
        """Умный поиск элемента по нескольким критериям"""
        selectors = []
        
        # Добавляем XPath
        if action.get('xpath'):
            selectors.append(('xpath', action['xpath']))
        
        # Добавляем ID
        if action.get('id'):
            selectors.append(('id', action['id']))
        
        # Добавляем поиск по тексту
        if action.get('text'):
            text = action['text'].strip()
            if text and len(text) > 2:
                selectors.append(('xpath', f"//*[contains(text(), '{text}')]"))
                selectors.append(('xpath', f"//*[@placeholder='{text}']"))
        
        # Добавляем поиск по классу
        if action.get('className'):
            class_name = action['className'].split()[0]  # Берем первый класс
            if class_name:
                selectors.append(('class_name', class_name))
        
        # Пробуем каждый селектор
        for selector_type, selector_value in selectors:
            try:
                if selector_type == 'xpath':
                    element = self.driver.find_element(By.XPATH, selector_value)
                elif selector_type == 'id':
                    element = self.driver.find_element(By.ID, selector_value)
                elif selector_type == 'class_name':
                    element = self.driver.find_element(By.CLASS_NAME, selector_value)
                
                if element and element.is_displayed():
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    def replay_actions(self, user_data, delay=1.0):
        """Воспроизвести записанные действия"""
        if not self.actions:
            logger.error("Нет действий для воспроизведения")
            return False
        
        try:
            self.driver = self.setup_driver()
            current_url = None
            
            for i, action in enumerate(self.actions):
                try:
                    logger.info(f"Выполняем действие {i+1}/{len(self.actions)}: {action['type']}")
                    
                    # Обрабатываем навигацию
                    if action['type'] == 'navigation' and action.get('url'):
                        if current_url != action['url']:
                            self.driver.get(action['url'])
                            current_url = action['url']
                            time.sleep(delay)
                        continue
                    
                    # Находим элемент
                    element = self.find_element_smart(action)
                    
                    if not element:
                        logger.warning(f"Не удалось найти элемент для действия {i+1}")
                        continue
                    
                    # Выполняем действие
                    if action['type'] == 'click':
                        # Прокручиваем к элементу
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)
                        element.click()
                        
                    elif action['type'] == 'input':
                        # Очищаем поле и вводим текст
                        element.clear()
                        value = self.replace_placeholders(action.get('value', ''), user_data)
                        if value:
                            element.send_keys(value)
                            
                    elif action['type'] == 'select':
                        # Выбираем опцию в select
                        from selenium.webdriver.support.ui import Select
                        select = Select(element)
                        value = self.replace_placeholders(action.get('value', ''), user_data)
                        if value:
                            try:
                                select.select_by_value(value)
                            except:
                                select.select_by_visible_text(value)
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Ошибка при выполнении действия {i+1}: {e}")
                    continue
            
            logger.info("Воспроизведение завершено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при воспроизведении: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def get_available_recordings(self):
        """Получить список доступных записей"""
        recordings = []
        if os.path.exists(self.recordings_dir):
            for filename in os.listdir(self.recordings_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.recordings_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Проверяем, что запись для этой платформы
                            if data.get('platform', '').lower() == self.platform_name.lower():
                                recordings.append({
                                    'filename': filename,
                                    'filepath': filepath,
                                    'platform': data.get('platform', 'Unknown'),
                                    'created_at': data.get('created_at', ''),
                                    'total_actions': data.get('total_actions', 0)
                                })
                    except:
                        continue
        
        return sorted(recordings, key=lambda x: x['created_at'], reverse=True)
    
    def get_available_recording_files(self):
        """Получить список имен файлов записей (для совместимости)"""
        recordings = self.get_available_recordings()
        return [rec['filename'] for rec in recordings]
    
    def preview_recording(self, filename):
        """Предварительный просмотр записи"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            actions = data.get('actions', [])
            preview = f"📋 **Запись: {os.path.basename(filename)}**\n\n"
            preview += f"🏷️ Платформа: {data.get('platform', 'Unknown')}\n"
            preview += f"📅 Создана: {data.get('created_at', '')}\n"
            preview += f"🔢 Действий: {len(actions)}\n\n"
            
            preview += "**Действия:**\n"
            for i, action in enumerate(actions[:10], 1):  # Показываем первые 10
                action_type = action.get('type', 'unknown')
                text = action.get('text', '')[:50] or action.get('value', '')[:50]
                preview += f"{i}. {action_type}: {text}\n"
            
            if len(actions) > 10:
                preview += f"... и еще {len(actions) - 10} действий\n"
            
            return preview
            
        except Exception as e:
            return f"❌ Ошибка при чтении файла: {e}"


class RecordingManager:
    """Менеджер для работы с записями действий"""
    
    def __init__(self):
        self.recorders = {}
        self.current_recording = None
    
    def create_recorder(self, platform_name):
        """Создать новый рекордер для платформы"""
        recorder = ActionRecorder(platform_name)
        self.recorders[platform_name] = recorder
        return recorder
    
    def get_recorder(self, platform_name):
        """Получить рекордер для платформы"""
        if platform_name not in self.recorders:
            self.recorders[platform_name] = ActionRecorder(platform_name)
        return self.recorders[platform_name]
    
    def start_recording(self, platform_name, url):
        """Начать запись для платформы"""
        recorder = self.get_recorder(platform_name)
        success = recorder.start_recording(url)
        if success:
            self.current_recording = platform_name
        return success
    
    def stop_recording(self):
        """Остановить текущую запись"""
        if self.current_recording:
            recorder = self.recorders[self.current_recording]
            filename = recorder.stop_recording()
            self.current_recording = None
            return filename
        return None
    
    def get_all_recordings(self):
        """Получить все доступные записи"""
        recordings = []
        for platform_name in self.recorders:
            recorder = self.recorders[platform_name]
            recordings.extend(recorder.get_available_recordings())
        return recordings


# Пример использования
if __name__ == "__main__":
    # Создаем менеджер
    manager = RecordingManager()
    
    # Начинаем запись
    print("Начинаем запись действий...")
    manager.start_recording("ostrovok", "https://extranet.ostrovok.ru")
    
    input("Выполните действия на сайте и нажмите Enter для остановки записи...")
    
    # Останавливаем запись
    filename = manager.stop_recording()
    print(f"Запись сохранена: {filename}")
    
    # Воспроизводим запись
    print("Воспроизводим запись...")
    user_data = {
        'email': 'test@example.com',
        'password': 'password123',
        'hotel_name': 'Тестовый отель',
        'hotel_address': 'ул. Тестовая, 1'
    }
    
    recorder = manager.get_recorder("ostrovok")
    recorder.load_recording(filename)
    recorder.replay_actions(user_data) 
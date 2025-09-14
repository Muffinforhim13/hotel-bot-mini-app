import requests
import os
import json
import uuid
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

logger = logging.getLogger(__name__)

SESSIONS_DIR = 'sessions'
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

class BronevikManager:
    def __init__(self, email=None):
        self.session = requests.Session()
        self.email = email
        self.driver = None
        if email:
            self.load_cookies(email)

    def get_cookies_path(self, email):
        safe_email = email.replace('@', '_at_').replace('.', '_')
        return os.path.join(SESSIONS_DIR, f'{safe_email}_bronevik_cookies.json')

    def load_cookies(self, email):
        cookies_path = self.get_cookies_path(email)
        if os.path.exists(cookies_path):
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
            logger.info(f"Cookies для {email} загружены из {cookies_path}")
        else:
            logger.warning(f"Файл cookies для {email} не найден: {cookies_path}")

    def save_cookies(self, email):
        cookies_path = self.get_cookies_path(email)
        cookies = []
        for c in self.session.cookies:
            cookies.append({
                'name': c.name,
                'value': c.value,
                'domain': c.domain
            })
        with open(cookies_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"Cookies для {email} сохранены в {cookies_path}")

    # --- Selenium login methods ---
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Попробуем использовать ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Веб-драйвер успешно настроен через ChromeDriverManager")
        except Exception as e:
            logger.warning(f"Ошибка с ChromeDriverManager: {e}")
            try:
                # Попробуем запустить Chrome без service
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Веб-драйвер успешно настроен без service")
            except Exception as e2:
                logger.error(f"Ошибка запуска Chrome: {e2}")
                raise Exception(f"Не удалось запустить Chrome. Убедитесь, что Chrome установлен. Ошибка: {e2}")
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def open_login_page(self):
        if not self.driver:
            self.setup_driver()
        self.driver.get("https://bronevik.com/partner/login")
        logger.info("Открыта страница входа bronevik.com")

    def fill_email(self, email):
        wait = WebDriverWait(self.driver, 10)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.clear()
        email_input.send_keys(email)
        logger.info(f"Введён email: {email}")

    def fill_password(self, password):
        wait = WebDriverWait(self.driver, 10)
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.clear()
        password_input.send_keys(password)
        logger.info("Введён пароль")

    def submit_login(self):
        wait = WebDriverWait(self.driver, 10)
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_btn.click()
        logger.info("Кнопка Войти нажата")
        time.sleep(2)

    def check_login_success(self, email=None):
        wait = WebDriverWait(self.driver, 10)
        try:
            # Проверяем наличие элементов панели управления
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard, .partner-panel")))
            logger.info("Вход выполнен успешно")
            # Сохраняем cookies после успешного входа
            if email:
                cookies = self.driver.get_cookies()
                cookies_path = self.get_cookies_path(email)
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                logger.info(f"Cookies для {email} сохранены в {cookies_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке входа: {e}")
            return False

    def selenium_login_and_save_cookies(self, email, password):
        self.open_login_page()
        self.fill_email(email)
        self.fill_password(password)
        self.submit_login()
        success = self.check_login_success(email)
        if success:
            print("Вход выполнен, cookies сохранены.")
        else:
            print("Ошибка входа.")
        if self.driver:
            self.driver.quit()

    # --- Bronevik API Methods ---
    def search_address_on_bronevik(self, address: str):
        """
        Поиск адреса через API Bronevik
        """
        try:
            # URL для поиска адресов на Bronevik
            url = "https://bronevik.com/api/geocoding/search"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://bronevik.com",
                "Referer": "https://bronevik.com/partner/hotels/add",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
            }
            
            params = {
                "query": address,
                "limit": 5,
                "lang": "ru"
            }
            
            response = self.session.get(url, headers=headers, params=params)
            
            logger.info(f"Запрос к API Bronevik: {url} с параметрами {params}")
            logger.info(f"Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Ответ API: {data}")
                results = data.get('results', []) if isinstance(data, dict) else []
                logger.info(f"Найдено {len(results)} результатов для адреса: {address}")
                return True, results
            else:
                logger.error(f"Ошибка поиска адреса: {response.status_code} - {response.text}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при поиске адреса: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def geocode_address_bronevik(self, address: str):
        """
        Геокодинг адреса через Bronevik API
        Возвращает (lat, lng) или None
        """
        logger.info(f"Геокодинг адреса через Bronevik: {address}")
        
        # Пробуем поиск
        success, results = self.search_address_on_bronevik(address)
        
        if not success:
            logger.error(f"Не удалось выполнить поиск адреса: {results}")
            return None
        
        if not results:
            logger.warning(f"Адрес не найден: {address}")
            return None
        
        # Берем первый результат
        first_result = results[0]
        logger.info(f"Выбран результат: {first_result}")
        
        # Извлекаем координаты
        location = first_result.get('location', {})
        
        lat = location.get('lat')
        lng = location.get('lng')
        
        if lat and lng:
            logger.info(f"Успешно получены координаты: {lat}, {lng}")
            return float(lat), float(lng)
        else:
            logger.error(f"Координаты не найдены в результате")
            return None

    def create_hotel(self, hotel_data):
        """
        Создание отеля через API Bronevik
        """
        url = "https://secure.bronevik.com/ru/api/hotel/save.json.php"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Origin": "https://bronevik.com",
            "Referer": "https://bronevik.com/partner/hotels/add",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
        }
        
        # Добавляем idempotency_key если его нет
        if 'idempotency_key' not in hotel_data:
            hotel_data['idempotency_key'] = str(uuid.uuid4())
        
        # Убеждаемся что все обязательные поля присутствуют
        required_fields = ['name', 'address', 'city', 'region', 'type', 'latitude', 'longitude']
        for field in required_fields:
            if field not in hotel_data:
                logger.error(f"Отсутствует обязательное поле: {field}")
                return 400, f"Отсутствует обязательное поле: {field}"
        
        logger.info(f"Отправка запроса создания отеля: {hotel_data}")
        
        try:
            response = self.session.post(url, headers=headers, json=hotel_data)
            logger.info(f"Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Отель успешно создан: {result}")
                return response.status_code, result
            else:
                logger.error(f"Ошибка создания отеля: {response.status_code} - {response.text}")
                return response.status_code, response.text
                
        except Exception as e:
            logger.error(f"Ошибка при создании отеля: {e}")
            return 500, f"Ошибка соединения: {str(e)}"

    def prepare_hotel_data(self, name, address, city, region, hotel_type, latitude, longitude, **kwargs):
        """
        Подготовка данных для создания отеля
        """
        hotel_data = {
            "name": name,
            "address": address,
            "city": city,
            "region": region,
            "type": hotel_type,
            "latitude": latitude,
            "longitude": longitude,
            "lastAvailableStep": "category",  # Шаг регистрации
            "idempotency_key": str(uuid.uuid4())
        }
        
        # Добавляем дополнительные поля
        hotel_data.update(kwargs)
        
        logger.info(f"Подготовлены данные отеля: {hotel_data}")
        return hotel_data

    def get_bookings(self):
        """
        Получить список бронирований
        """
        try:
            url = "https://bronevik.com/api/partner/bookings"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://bronevik.com",
                "Referer": "https://bronevik.com/partner/bookings"
            }
            
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                bookings = data.get('bookings', [])
                logger.info(f"Получено {len(bookings)} бронирований")
                return True, bookings
            else:
                logger.error(f"Ошибка получения бронирований: {response.status_code}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при получении бронирований: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def get_statistics(self):
        """
        Получить статистику отеля
        """
        try:
            url = "https://bronevik.com/api/partner/statistics"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://bronevik.com",
                "Referer": "https://bronevik.com/partner/dashboard"
            }
            
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Статистика получена успешно")
                return True, data
            else:
                logger.error(f"Ошибка получения статистики: {response.status_code}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def update_hotel_step(self, hotel_id, step, step_data=None):
        """
        Обновление шага регистрации отеля
        """
        try:
            url = "https://secure.bronevik.com/ru/api/hotel/save.json.php"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://bronevik.com",
                "Referer": "https://bronevik.com/partner/hotels/add",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
            }
            
            data = {
                "id": hotel_id,
                "lastAvailableStep": step
            }
            
            # Добавляем данные шага если они есть
            if step_data:
                data.update(step_data)
            
            response = self.session.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Шаг отеля {hotel_id} обновлен на '{step}': {result}")
                return True, result
            else:
                logger.error(f"Ошибка обновления шага: {response.status_code} - {response.text}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении шага отеля: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def register_hotel_step_by_step(self, hotel_data):
        """
        Пошаговая регистрация отеля на Bronevik
        """
        logger.info("Начинаем пошаговую регистрацию отеля на Bronevik")
        
        # Шаг 1: Создание базового отеля
        success, result = self.create_hotel(hotel_data)
        if not success:
            return False, f"Ошибка создания отеля: {result}"
        
        hotel_id = result.get('hotelId') or result.get('id')
        if not hotel_id:
            return False, "Не удалось получить ID отеля"
        
        logger.info(f"Отель создан с ID: {hotel_id}")
        
        # Шаг 2: Установка категории отеля
        category_data = {
            "category": hotel_data.get("type", "hotel"),
            "stars": hotel_data.get("stars", 3)
        }
        success, result = self.update_hotel_step(hotel_id, "category", category_data)
        if not success:
            logger.warning(f"Ошибка установки категории: {result}")
        
        # Шаг 3: Установка названия
        name_data = {
            "name": hotel_data.get("name", ""),
            "name_en": hotel_data.get("name_en", hotel_data.get("name", ""))
        }
        success, result = self.update_hotel_step(hotel_id, "name", name_data)
        if not success:
            logger.warning(f"Ошибка установки названия: {result}")
        
        # Шаг 4: Установка адреса
        address_data = {
            "address": hotel_data.get("address", ""),
            "city": hotel_data.get("city", ""),
            "region": hotel_data.get("region", ""),
            "latitude": hotel_data.get("latitude", ""),
            "longitude": hotel_data.get("longitude", "")
        }
        success, result = self.update_hotel_step(hotel_id, "address", address_data)
        if not success:
            logger.warning(f"Ошибка установки адреса: {result}")
        
        return True, {"hotel_id": hotel_id, "message": "Регистрация отеля завершена"}

    def get_registration_steps(self):
        """
        Получение списка шагов регистрации
        """
        return [
            "category",      # Выбор категории отеля
            "name",          # Название отеля
            "address",       # Адрес
            "contacts",      # Контактная информация
            "rooms",         # Информация о номерах
            "photos",        # Фотографии
            "pricing",       # Ценообразование
            "settings"       # Настройки
        ]

    def get_hotel_info(self, hotel_id):
        """
        Получение информации об отеле по ID
        """
        try:
            url = "https://secure.bronevik.com/ru/api/hotel/save.json.php"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://bronevik.com",
                "Referer": "https://bronevik.com/partner/hotels/add",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
            }
            
            data = {
                "hotelId": hotel_id
            }
            
            response = self.session.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Информация об отеле {hotel_id} получена: {result}")
                return True, result
            else:
                logger.error(f"Ошибка получения информации об отеле: {response.status_code} - {response.text}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при получении информации об отеле: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def get_hotel_registration_status(self, hotel_id):
        """
        Получение статуса регистрации отеля
        """
        try:
            success, hotel_info = self.get_hotel_info(hotel_id)
            if not success:
                return False, f"Не удалось получить информацию об отеле: {hotel_info}"
            
            # Извлекаем информацию о прогрессе регистрации
            last_step = hotel_info.get('lastAvailableStep', 'unknown')
            steps = self.get_registration_steps()
            
            try:
                current_step_index = steps.index(last_step)
                progress_percent = int((current_step_index + 1) / len(steps) * 100)
            except ValueError:
                current_step_index = -1
                progress_percent = 0
            
            status_info = {
                "hotel_id": hotel_id,
                "current_step": last_step,
                "current_step_index": current_step_index,
                "total_steps": len(steps),
                "progress_percent": progress_percent,
                "next_step": steps[current_step_index + 1] if current_step_index < len(steps) - 1 else None,
                "is_completed": current_step_index == len(steps) - 1
            }
            
            logger.info(f"Статус регистрации отеля {hotel_id}: {status_info}")
            return True, status_info
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса регистрации: {e}")
            return False, f"Ошибка: {str(e)}"

    def complete_hotel_registration(self, hotel_id):
        """
        Завершение регистрации отеля (переход к последнему шагу)
        """
        try:
            steps = self.get_registration_steps()
            last_step = steps[-1]  # "settings"
            
            success, result = self.update_hotel_step(hotel_id, last_step)
            if success:
                logger.info(f"Регистрация отеля {hotel_id} завершена")
                return True, "Регистрация отеля успешно завершена"
            else:
                return False, f"Ошибка завершения регистрации: {result}"
                
        except Exception as e:
            logger.error(f"Ошибка при завершении регистрации: {e}")
            return False, f"Ошибка: {str(e)}"
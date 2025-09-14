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
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time

logger = logging.getLogger(__name__)

SESSIONS_DIR = 'sessions'
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

class Hotels101Manager:
    def __init__(self, email=None):
        self.session = requests.Session()
        self.email = email
        self.driver = None
        if email:
            self.load_cookies(email)

    def get_cookies_path(self, email):
        safe_email = email.replace('@', '_at_').replace('.', '_')
        return os.path.join(SESSIONS_DIR, f'{safe_email}_101hotels_cookies.json')

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
        self.driver.get("https://extranet.101hotels.com/login")
        wait = WebDriverWait(self.driver, 10)
        # Ждем загрузки страницы
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logger.info("Открыта страница входа extranet.101hotels.com")

    def fill_email(self, email):
        wait = WebDriverWait(self.driver, 10)
        # Используем правильный селектор для поля логина
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "_username")))
        email_input.clear()
        email_input.send_keys(email)
        logger.info(f"Введён email: {email}")

    def fill_password(self, password):
        wait = WebDriverWait(self.driver, 10)
        # Используем правильный селектор для поля пароля
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "_password")))
        password_input.clear()
        password_input.send_keys(password)
        logger.info("Введён пароль")

    def submit_login(self):
        wait = WebDriverWait(self.driver, 10)
        # Попробуем несколько селекторов для кнопки "ВОЙТИ"
        possible_selectors = [
            "button[type='submit'].Button__primary.Button__green",
            "button.Button__primary.Button__green",
            "button[type='submit']",
            "button:contains('ВОЙТИ')",
            "button:contains('Войти')"
        ]
        
        for selector in possible_selectors:
            try:
                if "contains" in selector:
                    # Для селекторов с contains используем XPath
                    xpath = f"//button[contains(text(), 'ВОЙТИ') or contains(text(), 'Войти')]"
                    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                else:
                    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                submit_btn.click()
                logger.info(f"Кнопка ВОЙТИ нажата (селектор: {selector})")
                time.sleep(2)
                return True
            except Exception as e:
                logger.warning(f"Селектор {selector} не найден: {e}")
                continue
        
        logger.error("Не удалось найти кнопку ВОЙТИ")
        return False

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
        submit_success = self.submit_login()
        if not submit_success:
            print("Ошибка при нажатии кнопки ВОЙТИ")
            if self.driver:
                self.driver.quit()
            return False
        
        success = self.check_login_success(email)
        if success:
            print("Вход выполнен, cookies сохранены.")
        else:
            print("Ошибка входа.")
        if self.driver:
            self.driver.quit()
        return success

    # --- 101 Hotels API Methods ---
    def search_address_on_101hotels(self, address: str):
        """
        Поиск адреса через API 101 hotels
        """
        try:
            # Попробуем несколько возможных URL для поиска адресов
            possible_urls = [
                "https://101hotels.com/api/geocoding/search",
                "https://101hotels.com/api/places/search",
                "https://101hotels.com/api/location/search",
                "https://101hotels.com/api/autocomplete/address"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": "https://101hotels.com/partner/hotels/add",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
            }
            
            params = {
                "query": address,
                "limit": 5,
                "lang": "ru"
            }
            
            # Пробуем каждый URL
            for url in possible_urls:
                try:
                    response = self.session.get(url, headers=headers, params=params)
                    logger.info(f"Пробуем URL: {url}")
                    logger.info(f"Статус ответа: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Ответ API: {data}")
                        results = data.get('results', []) if isinstance(data, dict) else []
                        logger.info(f"Найдено {len(results)} результатов для адреса: {address}")
                        return True, results
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка поиска адреса: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для поиска адресов"
                
        except Exception as e:
            logger.error(f"Ошибка при поиске адреса: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def geocode_address_101hotels(self, address: str):
        """
        Геокодинг адреса через 101 hotels API
        Возвращает (lat, lng) или None
        """
        logger.info(f"Геокодинг адреса через 101 hotels: {address}")
        
        # Пробуем поиск
        success, results = self.search_address_on_101hotels(address)
        
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
        Создание отеля через API 101 hotels
        """
        # Попробуем несколько возможных URL для создания отеля
        possible_urls = [
            "https://101hotels.com/api/partner/hotels/create",
            "https://101hotels.com/api/hotels/create",
            "https://101hotels.com/api/partner/properties/create",
            "https://101hotels.com/api/properties/create"
        ]
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Origin": "https://101hotels.com",
            "Referer": "https://101hotels.com/partner/hotels/add",
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
        
        # Пробуем каждый URL
        for url in possible_urls:
            try:
                response = self.session.post(url, headers=headers, json=hotel_data)
                logger.info(f"Пробуем URL: {url}")
                logger.info(f"Статус ответа: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Отель успешно создан: {result}")
                    return response.status_code, result
                elif response.status_code == 404:
                    logger.warning(f"URL {url} не найден, пробуем следующий")
                    continue
                else:
                    logger.error(f"Ошибка создания отеля: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.warning(f"Ошибка при запросе к {url}: {e}")
                continue
        
        return 500, "Не удалось найти рабочий API эндпоинт для создания отеля"

    def prepare_hotel_data(self, name, address, city, region, hotel_type, latitude, longitude):
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
            "idempotency_key": str(uuid.uuid4())
        }
        
        logger.info(f"Подготовлены данные отеля: {hotel_data}")
        return hotel_data

    def get_bookings(self):
        """
        Получить список бронирований
        """
        try:
            url = "https://101hotels.com/api/partner/bookings"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": "https://101hotels.com/partner/bookings"
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
            url = "https://101hotels.com/api/partner/statistics"
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": "https://101hotels.com/partner/dashboard"
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

    def get_my_hotels(self):
        """
        Получить список моих отелей
        """
        try:
            possible_urls = [
                "https://101hotels.com/api/partner/hotels",
                "https://101hotels.com/api/hotels",
                "https://101hotels.com/api/partner/properties",
                "https://101hotels.com/api/properties"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": "https://101hotels.com/partner/hotels"
            }
            
            for url in possible_urls:
                try:
                    response = self.session.get(url, headers=headers)
                    logger.info(f"Пробуем получить отели с URL: {url}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        hotels = data.get('hotels', []) or data.get('properties', []) or data.get('data', [])
                        logger.info(f"Получено {len(hotels)} отелей")
                        return True, hotels
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка получения отелей: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для получения отелей"
                
        except Exception as e:
            logger.error(f"Ошибка при получении отелей: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def get_hotel_details(self, hotel_id):
        """
        Получить детальную информацию об отеле
        """
        try:
            possible_urls = [
                f"https://101hotels.com/api/partner/hotels/{hotel_id}",
                f"https://101hotels.com/api/hotels/{hotel_id}",
                f"https://101hotels.com/api/partner/properties/{hotel_id}",
                f"https://101hotels.com/api/properties/{hotel_id}"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": f"https://101hotels.com/partner/hotels/{hotel_id}"
            }
            
            for url in possible_urls:
                try:
                    response = self.session.get(url, headers=headers)
                    logger.info(f"Пробуем получить детали отеля с URL: {url}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Детали отеля {hotel_id} получены")
                        return True, data
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка получения деталей отеля: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для получения деталей отеля"
                
        except Exception as e:
            logger.error(f"Ошибка при получении деталей отеля: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def update_hotel(self, hotel_id, hotel_data):
        """
        Обновить информацию об отеле
        """
        try:
            possible_urls = [
                f"https://101hotels.com/api/partner/hotels/{hotel_id}",
                f"https://101hotels.com/api/hotels/{hotel_id}",
                f"https://101hotels.com/api/partner/properties/{hotel_id}",
                f"https://101hotels.com/api/properties/{hotel_id}"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": f"https://101hotels.com/partner/hotels/{hotel_id}"
            }
            
            for url in possible_urls:
                try:
                    response = self.session.put(url, headers=headers, json=hotel_data)
                    logger.info(f"Пробуем обновить отель с URL: {url}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Отель {hotel_id} успешно обновлен")
                        return True, data
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка обновления отеля: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для обновления отеля"
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении отеля: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def delete_hotel(self, hotel_id):
        """
        Удалить отель
        """
        try:
            possible_urls = [
                f"https://101hotels.com/api/partner/hotels/{hotel_id}",
                f"https://101hotels.com/api/hotels/{hotel_id}",
                f"https://101hotels.com/api/partner/properties/{hotel_id}",
                f"https://101hotels.com/api/properties/{hotel_id}"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com",
                "Referer": f"https://101hotels.com/partner/hotels/{hotel_id}"
            }
            
            for url in possible_urls:
                try:
                    response = self.session.delete(url, headers=headers)
                    logger.info(f"Пробуем удалить отель с URL: {url}")
                    
                    if response.status_code == 200 or response.status_code == 204:
                        logger.info(f"Отель {hotel_id} успешно удален")
                        return True, "Отель успешно удален"
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка удаления отеля: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для удаления отеля"
                
        except Exception as e:
            logger.error(f"Ошибка при удалении отеля: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def test_api_connection(self):
        """
        Тестирование подключения к API 101 hotels
        """
        try:
            test_urls = [
                "https://101hotels.com/api/partner/hotels",
                "https://101hotels.com/api/hotels",
                "https://101hotels.com/api/partner/properties",
                "https://101hotels.com/api/properties"
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://101hotels.com"
            }
            
            working_urls = []
            
            for url in test_urls:
                try:
                    response = self.session.get(url, headers=headers)
                    if response.status_code in [200, 401, 403]:  # 401/403 означает что API существует, но нужна авторизация
                        working_urls.append(url)
                        logger.info(f"Рабочий URL найден: {url}")
                except Exception as e:
                    logger.warning(f"URL {url} недоступен: {e}")
            
            if working_urls:
                return True, f"Найдено {len(working_urls)} рабочих API эндпоинтов: {working_urls}"
            else:
                return False, "Не найдено рабочих API эндпоинтов"
                
        except Exception as e:
            logger.error(f"Ошибка при тестировании API: {e}")
            return False, f"Ошибка: {str(e)}"

    # --- Selenium methods for hotel management ---
    def open_hotels_page(self):
        """
        Открыть страницу управления отелями
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False
        
        try:
            self.driver.get("https://extranet.101hotels.com/hotels")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("Открыта страница управления отелями")
            return True
        except Exception as e:
            logger.error(f"Ошибка при открытии страницы отелей: {e}")
            return False

    def open_dashboard(self):
        """
        Открыть главную страницу extranet
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False
        
        try:
            self.driver.get("https://extranet.101hotels.com/dashboard")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info("Открыта главная страница extranet")
            return True
        except Exception as e:
            logger.error(f"Ошибка при открытии главной страницы: {e}")
            return False

    def open_dashboard_safe(self):
        """
        Безопасное открытие главной страницы с автоматической инициализацией драйвера
        """
        try:
            # Проверяем, инициализирован ли драйвер
            if not self.driver:
                logger.info("Инициализируем драйвер для открытия главной страницы")
                self.setup_driver()
            
            # Открываем главную страницу
            return self.open_dashboard()
            
        except Exception as e:
            logger.error(f"Ошибка при безопасном открытии главной страницы: {e}")
            return False

    def close_browser(self):
        """
        Закрыть браузер
        """
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Браузер закрыт")
                return True
            else:
                logger.info("Браузер не был открыт")
                return True
        except Exception as e:
            logger.error(f"Ошибка при закрытии браузера: {e}")
            return False

    def click_register_new_object(self):
        """
        Нажать кнопку "Зарегистрировать свой объект"
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти кнопку по разным селекторам
            possible_selectors = [
                "span:contains('Зарегистрировать свой объект')",
                "button:contains('Зарегистрировать свой объект')",
                "a:contains('Зарегистрировать свой объект')",
                "[data-v-a9906cda]:contains('Зарегистрировать свой объект')",
                ".register-object-btn",
                "#register-object-btn"
            ]
            
            for selector in possible_selectors:
                try:
                    if "contains" in selector:
                        # Для селекторов с contains используем XPath
                        xpath = f"//*[contains(text(), 'Зарегистрировать свой объект')]"
                        register_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        register_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", register_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", register_btn)
                    logger.info(f"Кнопка 'Зарегистрировать свой объект' нажата (селектор: {selector})")
                    return True, "Кнопка успешно нажата"
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти кнопку 'Зарегистрировать свой объект'"
            
        except Exception as e:
            logger.error(f"Ошибка при нажатии кнопки 'Зарегистрировать свой объект': {e}")
            return False, f"Ошибка: {str(e)}"

    def click_add_hotel_button(self):
        """
        Нажать кнопку "Добавить отель"
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти кнопку по разным селекторам
            possible_selectors = [
                "button[data-test-id='add-hotel']",
                "button.add-hotel",
                "a[href*='add']",
                "button:contains('Добавить')",
                "button:contains('Add')",
                ".add-hotel-btn",
                "#add-hotel-btn"
            ]
            
            for selector in possible_selectors:
                try:
                    if "contains" in selector:
                        # Для селекторов с contains используем XPath
                        xpath = f"//button[contains(text(), 'Добавить') or contains(text(), 'Add')]"
                        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", add_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", add_btn)
                    logger.info(f"Кнопка 'Добавить отель' нажата (селектор: {selector})")
                    return True, "Кнопка успешно нажата"
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти кнопку 'Добавить отель'"
            
        except Exception as e:
            logger.error(f"Ошибка при нажатии кнопки 'Добавить отель': {e}")
            return False, f"Ошибка: {str(e)}"

    def fill_hotel_name(self, name):
        """
        Заполнить название отеля
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти поле по разным селекторам
            possible_selectors = [
                "input[name='name']",
                "input[data-test-id='hotel-name']",
                "input[placeholder*='название']",
                "input[placeholder*='name']",
                "#hotel-name",
                ".hotel-name-input"
            ]
            
            for selector in possible_selectors:
                try:
                    name_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    name_input.clear()
                    name_input.send_keys(name)
                    logger.info(f"Название отеля '{name}' введено (селектор: {selector})")
                    return True, "Название успешно введено"
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти поле для названия отеля"
            
        except Exception as e:
            logger.error(f"Ошибка при вводе названия отеля: {e}")
            return False, f"Ошибка: {str(e)}"

    def fill_hotel_address(self, address):
        """
        Заполнить адрес отеля
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти поле по разным селекторам
            possible_selectors = [
                "input[name='address']",
                "input[data-test-id='hotel-address']",
                "input[placeholder*='адрес']",
                "input[placeholder*='address']",
                "#hotel-address",
                ".hotel-address-input"
            ]
            
            for selector in possible_selectors:
                try:
                    address_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    address_input.clear()
                    address_input.send_keys(address)
                    logger.info(f"Адрес отеля '{address}' введен (селектор: {selector})")
                    return True, "Адрес успешно введен"
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти поле для адреса отеля"
            
        except Exception as e:
            logger.error(f"Ошибка при вводе адреса отеля: {e}")
            return False, f"Ошибка: {str(e)}"

    def select_hotel_type(self, hotel_type):
        """
        Выбрать тип отеля
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти селект по разным селекторам
            possible_selectors = [
                "select[name='type']",
                "select[data-test-id='hotel-type']",
                "#hotel-type",
                ".hotel-type-select"
            ]
            
            for selector in possible_selectors:
                try:
                    type_select = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    # Попробуем найти опцию по тексту
                    from selenium.webdriver.support.ui import Select
                    select = Select(type_select)
                    
                    # Попробуем разные варианты текста
                    possible_texts = [hotel_type, hotel_type.lower(), hotel_type.title()]
                    for text in possible_texts:
                        try:
                            select.select_by_visible_text(text)
                            logger.info(f"Тип отеля '{text}' выбран (селектор: {selector})")
                            return True, "Тип отеля успешно выбран"
                        except Exception:
                            continue
                    
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти селект для типа отеля"
            
        except Exception as e:
            logger.error(f"Ошибка при выборе типа отеля: {e}")
            return False, f"Ошибка: {str(e)}"

    def click_next_button(self):
        """
        Нажать кнопку "Далее" или "Next"
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти кнопку по разным селекторам
            possible_selectors = [
                "button[type='submit']",
                "button:contains('Далее')",
                "button:contains('Next')",
                "button.next-btn",
                ".next-button",
                "#next-btn"
            ]
            
            for selector in possible_selectors:
                try:
                    if "contains" in selector:
                        # Для селекторов с contains используем XPath
                        xpath = f"//button[contains(text(), 'Далее') or contains(text(), 'Next')]"
                        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", next_btn)
                    logger.info(f"Кнопка 'Далее' нажата (селектор: {selector})")
                    return True, "Кнопка успешно нажата"
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти кнопку 'Далее'"
            
        except Exception as e:
            logger.error(f"Ошибка при нажатии кнопки 'Далее': {e}")
            return False, f"Ошибка: {str(e)}"

    def get_my_hotels_from_page(self):
        """
        Получить список отелей со страницы
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            # Попробуем найти элементы отелей по разным селекторам
            possible_selectors = [
                ".hotel-item",
                ".hotel-card",
                "[data-test-id='hotel-item']",
                ".property-item",
                ".property-card"
            ]
            
            hotels = []
            for selector in possible_selectors:
                try:
                    hotel_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if hotel_elements:
                        for element in hotel_elements:
                            try:
                                name = element.find_element(By.CSS_SELECTOR, ".hotel-name, .property-name").text
                                address = element.find_element(By.CSS_SELECTOR, ".hotel-address, .property-address").text
                                hotel_id = element.get_attribute("data-id") or element.get_attribute("id")
                                
                                hotels.append({
                                    "name": name,
                                    "address": address,
                                    "id": hotel_id
                                })
                            except Exception as e:
                                logger.warning(f"Ошибка при извлечении данных отеля: {e}")
                                continue
                        
                        if hotels:
                            logger.info(f"Найдено {len(hotels)} отелей (селектор: {selector})")
                            return True, hotels
                    
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден: {e}")
                    continue
            
            return False, "Не удалось найти отели на странице"
            
        except Exception as e:
            logger.error(f"Ошибка при получении отелей со страницы: {e}")
            return False, f"Ошибка: {str(e)}"

    def debug_page_structure(self):
        """
        Отладочный метод для анализа структуры страницы
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            # Получим HTML страницы
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            title = self.driver.title
            
            debug_info = {
                "url": current_url,
                "title": title,
                "page_source_length": len(page_source),
                "forms": len(self.driver.find_elements(By.TAG_NAME, "form")),
                "inputs": len(self.driver.find_elements(By.TAG_NAME, "input")),
                "buttons": len(self.driver.find_elements(By.TAG_NAME, "button")),
                "selects": len(self.driver.find_elements(By.TAG_NAME, "select")),
                "labels": len(self.driver.find_elements(By.TAG_NAME, "label")),
                "country_elements": []
            }
            
            # Анализируем элементы стран с точным селектором
            country_selector = "input[type='radio'][name='country_id']"
            
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, country_selector)
                if elements:
                    debug_info["country_elements"].append({
                        "selector": country_selector,
                        "count": len(elements),
                        "elements": []
                    })
                    
                    for i, element in enumerate(elements):
                        element_info = {
                            "index": i,
                            "tag_name": element.tag_name,
                            "type": element.get_attribute("type"),
                            "name": element.get_attribute("name"),
                            "value": element.get_attribute("value"),
                            "id": element.get_attribute("id"),
                            "class": element.get_attribute("class")
                        }
                        debug_info["country_elements"][-1]["elements"].append(element_info)
                        
                        # Пробуем найти соответствующий label
                        try:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{element.get_attribute('id')}']")
                            element_info["label_text"] = label.text.strip()
                        except:
                            element_info["label_text"] = "Не найден"
                            
            except Exception as e:
                logger.warning(f"Ошибка при анализе элементов стран: {e}")
            
            # Ищем альтернативные селекторы
            alternative_selectors = [
                "input[name='country_id']",
                ".new-cool-checkbox",
                "input[class*='checkbox']"
            ]
            
            for selector in alternative_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        debug_info["country_elements"].append({
                            "selector": selector,
                            "count": len(elements),
                            "elements": []
                        })
                        
                        for i, element in enumerate(elements[:3]):  # Только первые 3 элемента
                            element_info = {
                                "index": i,
                                "tag_name": element.tag_name,
                                "type": element.get_attribute("type"),
                                "name": element.get_attribute("name"),
                                "value": element.get_attribute("value"),
                                "id": element.get_attribute("id"),
                                "class": element.get_attribute("class")
                            }
                            debug_info["country_elements"][-1]["elements"].append(element_info)
                except Exception as e:
                    logger.warning(f"Ошибка при анализе селектора {selector}: {e}")
            
            # Ищем текст стран
            country_texts = [
                "Россия", "Беларусь", "Абхазия", "Азербайджан", "Армения", 
                "Грузия", "Казахстан", "Киргизия", "Узбекистан", "Таджикистан"
            ]
            
            debug_info["country_texts"] = []
            for country_text in country_texts:
                try:
                    xpath = f"//*[contains(text(), '{country_text}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        debug_info["country_texts"].append({
                            "country": country_text,
                            "count": len(elements),
                            "elements": []
                        })
                        
                        for i, element in enumerate(elements[:2]):  # Только первые 2 элемента
                            element_info = {
                                "index": i,
                                "tag_name": element.tag_name,
                                "text": element.text.strip(),
                                "class": element.get_attribute("class"),
                                "id": element.get_attribute("id")
                            }
                            debug_info["country_texts"][-1]["elements"].append(element_info)
                except Exception as e:
                    logger.warning(f"Ошибка при поиске текста {country_text}: {e}")
            
            logger.info(f"Отладочная информация страницы: {debug_info}")
            return True, debug_info
            
        except Exception as e:
            logger.error(f"Ошибка при анализе структуры страницы: {e}")
            return False, f"Ошибка: {str(e)}"

    # --- Методы для работы с формой регистрации отеля ---
    def select_country(self, country_name):
        """
        Выбрать страну в форме регистрации
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # Карта стран и их ID (обновленная на основе HTML)
            country_map = {
                "россия": "171",
                "russia": "171",
                "russian federation": "171",
                "беларусь": "4",
                "belarus": "4",
                "абхазия": "2",
                "abkhazia": "2",
                "азербайджан": "90",
                "azerbaijan": "90",
                "армения": "216",
                "armenia": "216",
                "грузия": "60",
                "georgia": "60",
                "казахстан": "21", 
                "kazakhstan": "21",
                "киргизия": "1",
                "kyrgyzstan": "1",
                "kyrgyz republic": "1",
                "узбекистан": "14",
                "uzbekistan": "14",
                "таджикистан": "83",
                "tajikistan": "83",
                "туркменистан": "3",
                "turkmenistan": "3"
            }
            
            # Нормализуем название страны
            country_lower = country_name.lower().strip()
            
            if country_lower not in country_map:
                available_countries = ", ".join(country_map.keys())
                return False, f"Страна '{country_name}' не найдена. Доступные страны: {available_countries}"
            
            country_id = country_map[country_lower]
            logger.info(f"Выбираем страну: {country_name} (ID: {country_id})")
            
            # Метод 1: Поиск по точному селектору
            try:
                logger.info("Метод 1: Поиск по точному селектору")
                radio_selector = f"input[type='radio'][name='country_id'][value='{country_id}']"
                radio_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, radio_selector)))
                
                # Проверяем, что элемент видим и кликабелен
                if radio_button.is_displayed() and radio_button.is_enabled():
                    # Кликаем по радио-кнопке
                    self.driver.execute_script("arguments[0].click();", radio_button)
                    logger.info(f"Страна '{country_name}' (ID: {country_id}) выбрана по радио-кнопке")
                    return True, f"Страна '{country_name}' успешно выбрана"
                else:
                    logger.warning(f"Элемент найден, но не видим или не кликабелен")
                    raise Exception("Элемент не кликабелен")
                
            except Exception as e:
                logger.warning(f"Метод 1 не сработал: {e}")
                
                # Метод 2: Поиск по ID элемента
                try:
                    logger.info("Метод 2: Поиск по ID элемента")
                    id_selector = f"#country_{country_id}"
                    radio_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, id_selector)))
                    
                    if radio_button.is_displayed() and radio_button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", radio_button)
                        logger.info(f"Страна '{country_name}' (ID: {country_id}) выбрана по ID")
                        return True, f"Страна '{country_name}' успешно выбрана"
                    else:
                        raise Exception("Элемент не кликабелен")
                        
                except Exception as e2:
                    logger.warning(f"Метод 2 не сработал: {e2}")
                    
                    # Метод 3: Поиск по label
                    try:
                        logger.info("Метод 3: Поиск по label")
                        label_selector = f"label[for='country_{country_id}']"
                        label = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, label_selector)))
                        
                        if label.is_displayed() and label.is_enabled():
                            self.driver.execute_script("arguments[0].click();", label)
                            logger.info(f"Страна '{country_name}' (ID: {country_id}) выбрана по label")
                            return True, f"Страна '{country_name}' успешно выбрана"
                        else:
                            raise Exception("Label не кликабелен")
                            
                    except Exception as e3:
                        logger.warning(f"Метод 3 не сработал: {e3}")
                        
                        # Метод 4: Поиск по любому элементу с нужным значением
                        try:
                            logger.info("Метод 4: Поиск по значению")
                            value_selector = f"input[value='{country_id}']"
                            input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, value_selector)))
                            
                            if input_element.is_displayed() and input_element.is_enabled():
                                self.driver.execute_script("arguments[0].click();", input_element)
                                logger.info(f"Страна '{country_name}' (ID: {country_id}) выбрана по значению")
                                return True, f"Страна '{country_name}' успешно выбрана"
                            else:
                                raise Exception("Элемент не кликабелен")
                                
                        except Exception as e4:
                            logger.warning(f"Метод 4 не сработал: {e4}")
                            
                            # Метод 5: Поиск по тексту страны
                            try:
                                logger.info("Метод 5: Поиск по тексту страны")
                                xpath = f"//*[contains(text(), '{country_name}')]"
                                elements = self.driver.find_elements(By.XPATH, xpath)
                                
                                for element in elements:
                                    try:
                                        # Ищем ближайший input элемент
                                        input_element = element.find_element(By.XPATH, ".//input | ../input | ../../input")
                                        if input_element.get_attribute("value") == country_id:
                                            self.driver.execute_script("arguments[0].click();", input_element)
                                            logger.info(f"Страна '{country_name}' (ID: {country_id}) выбрана по тексту")
                                            return True, f"Страна '{country_name}' успешно выбрана"
                                    except:
                                        continue
                                
                                raise Exception("Элемент с текстом не найден")
                                
                            except Exception as e5:
                                logger.error(f"Метод 5 не сработал: {e5}")
                                return False, f"Не удалось выбрать страну '{country_name}' ни одним методом"
            
        except Exception as e:
            logger.error(f"Ошибка при выборе страны '{country_name}': {e}")
            return False, f"Ошибка: {str(e)}"

    def _select_country_by_radio(self, country_id):
        """Выбрать страну по радио-кнопке"""
        wait = WebDriverWait(self.driver, 5)
        radio_selector = f"input[name='country_id'][value='{country_id}']"
        radio_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, radio_selector)))
        self.driver.execute_script("arguments[0].click();", radio_button)
        return True, "Выбрано по радио-кнопке"

    def _select_country_by_text(self, country_name):
        """Выбрать страну по тексту"""
        wait = WebDriverWait(self.driver, 5)
        xpath = f"//*[contains(text(), '{country_name}')]"
        elements = self.driver.find_elements(By.XPATH, xpath)
        
        for element in elements:
            try:
                # Ищем ближайший input элемент
                input_element = element.find_element(By.XPATH, ".//input | ../input | ../../input")
                self.driver.execute_script("arguments[0].click();", input_element)
                return True, "Выбрано по тексту"
            except:
                continue
        
        return False, "Не найдено по тексту"

    def _select_country_by_value(self, country_id):
        """Выбрать страну по значению"""
        wait = WebDriverWait(self.driver, 5)
        value_selector = f"input[value='{country_id}']"
        input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, value_selector)))
        self.driver.execute_script("arguments[0].click();", input_element)
        return True, "Выбрано по значению"

    def _select_country_by_label(self, country_id, country_name):
        """Выбрать страну по label"""
        wait = WebDriverWait(self.driver, 5)
        
        # Пробуем найти label по for атрибуту
        label_selectors = [
            f"label[for='country_{country_id}']",
            f"label[for='{country_id}']",
            f"label:contains('{country_name}')"
        ]
        
        for selector in label_selectors:
            try:
                if "contains" in selector:
                    xpath = f"//label[contains(text(), '{country_name}')]"
                    label = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                else:
                    label = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                self.driver.execute_script("arguments[0].click();", label)
                return True, "Выбрано по label"
            except:
                continue
        
        return False, "Не найдено по label"

    def click_next_step(self):
        """
        Нажать кнопку "Продолжить" для перехода к следующему шагу
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Попробуем найти кнопку "Продолжить" по разным селекторам
            possible_selectors = [
                "button[type='submit'].custom-button.custom-button_primary.custom-button_medium.next-step-js",
                "button.custom-button.custom-button_primary.next-step-js",
                "button.next-step-js",
                "button:contains('Продолжить')",
                "button:contains('Далее')",
                "button:contains('Next')",
                "button:contains('Continue')",
                "button[type='submit']",
                ".next-step-btn",
                ".continue-btn"
            ]
            
            for selector in possible_selectors:
                try:
                    if "contains" in selector:
                        # Для селекторов с contains используем XPath
                        xpath = f"//button[contains(text(), 'Продолжить') or contains(text(), 'Далее') or contains(text(), 'Next') or contains(text(), 'Continue')]"
                        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    # Проверяем, не заблокирована ли кнопка
                    if next_btn.get_attribute("disabled"):
                        logger.warning(f"Кнопка заблокирована (селектор: {selector})")
                        continue
                    
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", next_btn)
                    logger.info(f"Кнопка 'Продолжить' нажата (селектор: {selector})")
                    return True, "Переход к следующему шагу выполнен"
                except Exception as e:
                    logger.warning(f"Селектор {selector} не найден или не кликабелен: {e}")
                    continue
            
            return False, "Не удалось найти активную кнопку 'Продолжить'"
            
        except Exception as e:
            logger.error(f"Ошибка при переходе к следующему шагу: {e}")
            return False, f"Ошибка: {str(e)}"

    def get_current_step_info(self):
        """
        Получить информацию о текущем шаге регистрации
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            # Получаем информацию о текущем шаге
            step_info = {}
            
            # Проверяем атрибуты формы
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                form = forms[0]
                step_info["current_step"] = form.get_attribute("data-step")
                step_info["next_step"] = form.get_attribute("data-next_step")
                step_info["prev_step"] = form.get_attribute("data-prev_step")
            
            # Получаем заголовок шага
            try:
                step_header = self.driver.find_element(By.CSS_SELECTOR, ".step-header")
                step_info["step_title"] = step_header.text
            except:
                step_info["step_title"] = "Заголовок не найден"
            
            # Получаем URL
            step_info["url"] = self.driver.current_url
            
            logger.info(f"Информация о текущем шаге: {step_info}")
            return True, step_info
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о шаге: {e}")
            return False, f"Ошибка: {str(e)}"

    def get_available_countries(self):
        """
        Получить список доступных стран
        """
        if not self.driver:
            logger.error("Драйвер не инициализирован")
            return False, "Драйвер не инициализирован"
        
        try:
            countries = []
            
            # Ждем загрузки страницы
            wait = WebDriverWait(self.driver, 15)
            
            # Сначала проверим, что мы на правильной странице
            try:
                # Ждем появления заголовка или формы
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1, .join-form, form")))
                logger.info("Страница загружена, ищем элементы стран")
            except Exception as e:
                logger.warning(f"Страница не загрузилась полностью: {e}")
            
            # Основной селектор для элементов стран
            country_selector = "input[type='radio'][name='country_id']"
            
            try:
                # Ждем появления элементов стран с увеличенным таймаутом
                logger.info("Ожидаем появления элементов стран...")
                country_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, country_selector)))
                logger.info(f"Найдено {len(country_elements)} элементов стран")
                
                # Карта ID стран к названиям
                country_names = {
                    "171": "Россия",
                    "4": "Беларусь", 
                    "2": "Абхазия",
                    "90": "Азербайджан",
                    "216": "Армения",
                    "60": "Грузия",
                    "21": "Казахстан",
                    "1": "Киргизия",
                    "14": "Узбекистан",
                    "83": "Таджикистан",
                    "3": "Туркменистан",
                    "5": "Молдова",
                    "6": "Украина",
                    "7": "Латвия",
                    "8": "Литва",
                    "9": "Эстония"
                }
                
                # Обрабатываем каждый элемент
                for element in country_elements:
                    try:
                        country_id = element.get_attribute("value")
                        element_id = element.get_attribute("id")
                        
                        logger.info(f"Обрабатываем элемент: ID={element_id}, value={country_id}")
                        
                        if country_id and country_id in country_names:
                            country_name = country_names[country_id]
                        else:
                            # Если ID нет в карте, попробуем получить название из label
                            try:
                                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{element_id}']")
                                country_name = label.text.strip()
                                if not country_name:
                                    country_name = f"Страна {country_id}"
                            except:
                                country_name = f"Страна {country_id}"
                        
                        countries.append({
                            "id": country_id,
                            "name": country_name,
                            "label_id": element_id
                        })
                        
                        logger.info(f"Добавлена страна: {country_name} (ID: {country_id})")
                        
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке элемента страны: {e}")
                        continue
                
            except Exception as e:
                logger.warning(f"Не удалось найти элементы стран с основным селектором: {e}")
                
                # Попробуем альтернативные селекторы
                alternative_selectors = [
                    "input[name='country_id']",
                    "input[type='radio'][name*='country']",
                    ".new-cool-checkbox",
                    "input[class*='checkbox']",
                    "input[value]"
                ]
                
                for selector in alternative_selectors:
                    try:
                        logger.info(f"Пробуем селектор: {selector}")
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            logger.info(f"Найдены элементы с селектором {selector}: {len(elements)}")
                            # Обрабатываем элементы так же, как выше
                            for element in elements:
                                try:
                                    country_id = element.get_attribute("value")
                                    element_id = element.get_attribute("id")
                                    
                                    if country_id and country_id.isdigit():
                                        country_name = f"Страна {country_id}"
                                        countries.append({
                                            "id": country_id,
                                            "name": country_name,
                                            "label_id": element_id or f"country_{country_id}"
                                        })
                                        logger.info(f"Добавлена страна: {country_name} (ID: {country_id})")
                                except Exception as e:
                                    logger.warning(f"Ошибка при обработке элемента: {e}")
                                    continue
                            break
                    except Exception as e:
                        logger.warning(f"Ошибка с селектором {selector}: {e}")
                        continue
            
            # Если все еще нет стран, создаем базовый список
            if not countries:
                logger.warning("Не удалось найти страны на странице, создаем базовый список")
                basic_countries = [
                    {"id": "171", "name": "Россия", "label_id": "country_171"},
                    {"id": "4", "name": "Беларусь", "label_id": "country_4"},
                    {"id": "21", "name": "Казахстан", "label_id": "country_21"},
                    {"id": "1", "name": "Киргизия", "label_id": "country_1"},
                    {"id": "14", "name": "Узбекистан", "label_id": "country_14"},
                    {"id": "83", "name": "Таджикистан", "label_id": "country_83"},
                    {"id": "90", "name": "Азербайджан", "label_id": "country_90"},
                    {"id": "216", "name": "Армения", "label_id": "country_216"},
                    {"id": "2", "name": "Абхазия", "label_id": "country_2"},
                    {"id": "60", "name": "Грузия", "label_id": "country_60"}
                ]
                countries = basic_countries
            
            logger.info(f"Итого найдено {len(countries)} доступных стран")
            return True, countries
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка стран: {e}")
            return False, f"Ошибка: {str(e)}"

    # --- API методы для регистрации отеля после выбора страны ---
    
    def get_registration_step_info(self):
        """
        Получить информацию о текущем шаге регистрации через обратный API
        Анализируем сетевые запросы веб-интерфейса
        """
        try:
            # Анализируем текущую страницу через Selenium для получения данных
            if not self.driver:
                return False, "Драйвер не инициализирован"
            
            # Получаем информацию о текущем шаге из DOM
            step_info = {}
            
            try:
                # Ищем элементы, которые содержат информацию о шаге
                step_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-step], .step-info, .registration-step")
                
                for element in step_elements:
                    step_info["current_step"] = element.get_attribute("data-step") or element.text
                    step_info["step_title"] = element.get_attribute("title") or element.text
                    break
                
                # Ищем форму регистрации
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    form = forms[0]
                    step_info["form_action"] = form.get_attribute("action")
                    step_info["form_method"] = form.get_attribute("method")
                    
                    # Получаем все поля формы
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    fields = []
                    for inp in inputs:
                        field_info = {
                            "name": inp.get_attribute("name"),
                            "type": inp.get_attribute("type"),
                            "required": inp.get_attribute("required") is not None,
                            "placeholder": inp.get_attribute("placeholder"),
                            "value": inp.get_attribute("value")
                        }
                        fields.append(field_info)
                    step_info["fields"] = fields
                
                # Получаем URL текущей страницы
                step_info["url"] = self.driver.current_url
                
                # Анализируем заголовок страницы
                step_info["page_title"] = self.driver.title
                
                logger.info(f"Информация о текущем шаге получена: {step_info}")
                return True, step_info
                
            except Exception as e:
                logger.warning(f"Ошибка при анализе DOM: {e}")
                # Возвращаем базовую информацию
                step_info["url"] = self.driver.current_url
                step_info["page_title"] = self.driver.title
                return True, step_info
                
        except Exception as e:
            logger.error(f"Ошибка при получении информации о шаге: {e}")
            return False, f"Ошибка: {str(e)}"

    def submit_registration_step(self, step_data):
        """
        Отправить данные текущего шага регистрации через обратный API
        Заполняем форму и отправляем данные через Selenium
        """
        try:
            if not self.driver:
                return False, "Драйвер не инициализирован"
            
            # Заполняем поля формы данными
            for field_name, field_value in step_data.items():
                try:
                    # Ищем поле по имени
                    field = self.driver.find_element(By.CSS_SELECTOR, f"input[name='{field_name}'], textarea[name='{field_name}'], select[name='{field_name}']")
                    
                    # Очищаем поле и вводим значение
                    field.clear()
                    field.send_keys(str(field_value))
                    logger.info(f"Заполнено поле {field_name}: {field_value}")
                    
                except Exception as e:
                    logger.warning(f"Не удалось заполнить поле {field_name}: {e}")
                    continue
            
            # Ищем кнопку отправки формы
            submit_buttons = [
                "button[type='submit']",
                "input[type='submit']",
                ".submit-btn",
                ".next-step-btn",
                "button:contains('Продолжить')",
                "button:contains('Далее')",
                "button:contains('Next')"
            ]
            
            for button_selector in submit_buttons:
                try:
                    if "contains" in button_selector:
                        # Для селекторов с contains используем XPath
                        xpath = f"//button[contains(text(), 'Продолжить') or contains(text(), 'Далее') or contains(text(), 'Next')]"
                        submit_btn = self.driver.find_element(By.XPATH, xpath)
                    else:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, button_selector)
                    
                    # Проверяем, не заблокирована ли кнопка
                    if submit_btn.get_attribute("disabled"):
                        logger.warning(f"Кнопка заблокирована: {button_selector}")
                        continue
                    
                    # Нажимаем кнопку
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    
                    logger.info(f"Форма отправлена успешно (кнопка: {button_selector})")
                    
                    # Ждем загрузки следующей страницы
                    time.sleep(2)
                    
                    # Получаем информацию о результате
                    result_info = {
                        "success": True,
                        "new_url": self.driver.current_url,
                        "new_title": self.driver.title
                    }
                    
                    return True, result_info
                    
                except Exception as e:
                    logger.warning(f"Не удалось найти или нажать кнопку {button_selector}: {e}")
                    continue
            
            return False, "Не удалось найти активную кнопку отправки формы"
                
        except Exception as e:
            logger.error(f"Ошибка при отправке данных шага: {e}")
            return False, f"Ошибка: {str(e)}"

    def get_registration_form_fields(self, step_name=None):
        """
        Получить поля формы для текущего шага регистрации через обратный API
        Анализируем DOM страницы для извлечения полей формы
        """
        try:
            if not self.driver:
                return False, "Драйвер не инициализирован"
            
            # Получаем все поля формы с текущей страницы
            fields_data = {
                "fields": [],
                "form_info": {},
                "current_step": step_name or "current"
            }
            
            try:
                # Ищем форму регистрации
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                if forms:
                    form = forms[0]
                    fields_data["form_info"] = {
                        "action": form.get_attribute("action"),
                        "method": form.get_attribute("method"),
                        "id": form.get_attribute("id"),
                        "class": form.get_attribute("class")
                    }
                    
                    # Получаем все поля ввода
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    textareas = form.find_elements(By.TAG_NAME, "textarea")
                    selects = form.find_elements(By.TAG_NAME, "select")
                    
                    # Обрабатываем input поля
                    for inp in inputs:
                        field_info = {
                            "name": inp.get_attribute("name"),
                            "type": inp.get_attribute("type"),
                            "id": inp.get_attribute("id"),
                            "required": inp.get_attribute("required") is not None,
                            "placeholder": inp.get_attribute("placeholder"),
                            "value": inp.get_attribute("value"),
                            "label": self._get_field_label(inp),
                            "element_type": "input"
                        }
                        if field_info["name"]:  # Только поля с именем
                            fields_data["fields"].append(field_info)
                    
                    # Обрабатываем textarea поля
                    for textarea in textareas:
                        field_info = {
                            "name": textarea.get_attribute("name"),
                            "type": "textarea",
                            "id": textarea.get_attribute("id"),
                            "required": textarea.get_attribute("required") is not None,
                            "placeholder": textarea.get_attribute("placeholder"),
                            "value": textarea.text,
                            "label": self._get_field_label(textarea),
                            "element_type": "textarea"
                        }
                        if field_info["name"]:
                            fields_data["fields"].append(field_info)
                    
                    # Обрабатываем select поля
                    for select in selects:
                        field_info = {
                            "name": select.get_attribute("name"),
                            "type": "select",
                            "id": select.get_attribute("id"),
                            "required": select.get_attribute("required") is not None,
                            "label": self._get_field_label(select),
                            "element_type": "select",
                            "options": self._get_select_options(select)
                        }
                        if field_info["name"]:
                            fields_data["fields"].append(field_info)
                
                # Если форма не найдена, ищем поля по всей странице
                if not fields_data["fields"]:
                    all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name], textarea[name], select[name]")
                    for element in all_inputs:
                        field_info = {
                            "name": element.get_attribute("name"),
                            "type": element.get_attribute("type") or element.tag_name,
                            "id": element.get_attribute("id"),
                            "required": element.get_attribute("required") is not None,
                            "placeholder": element.get_attribute("placeholder"),
                            "value": element.get_attribute("value") or element.text,
                            "label": self._get_field_label(element),
                            "element_type": element.tag_name
                        }
                        if field_info["name"]:
                            fields_data["fields"].append(field_info)
                
                logger.info(f"Найдено {len(fields_data['fields'])} полей формы")
                return True, fields_data
                
            except Exception as e:
                logger.warning(f"Ошибка при анализе полей формы: {e}")
                return False, f"Ошибка анализа DOM: {str(e)}"
                
        except Exception as e:
            logger.error(f"Ошибка при получении полей формы: {e}")
            return False, f"Ошибка: {str(e)}"

    def _get_field_label(self, element):
        """Получить label для поля формы"""
        try:
            # Ищем label по for атрибуту
            field_id = element.get_attribute("id")
            if field_id:
                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                return label.text.strip()
            
            # Ищем ближайший label
            parent = element.find_element(By.XPATH, "..")
            label = parent.find_element(By.TAG_NAME, "label")
            return label.text.strip()
        except:
            return ""

    def _get_select_options(self, select_element):
        """Получить опции для select элемента"""
        try:
            options = []
            option_elements = select_element.find_elements(By.TAG_NAME, "option")
            for option in option_elements:
                options.append({
                    "value": option.get_attribute("value"),
                    "text": option.text.strip(),
                    "selected": option.get_attribute("selected") is not None
                })
            return options
        except:
            return []

    def submit_hotel_basic_info(self, hotel_data):
        """
        Отправить основную информацию об отеле через обратный API
        Заполняем поля формы основной информацией
        """
        try:
            if not self.driver:
                return False, "Драйвер не инициализирован"
            
            # Маппинг полей формы к данным отеля
            field_mapping = {
                "name": ["hotel_name", "name", "property_name", "title"],
                "address": ["address", "street_address", "location"],
                "city": ["city", "town", "locality"],
                "type": ["hotel_type", "property_type", "type"],
                "phone": ["phone", "telephone", "contact_phone"],
                "email": ["email", "contact_email", "manager_email"],
                "website": ["website", "url", "site"]
            }
            
            filled_fields = []
            
            # Заполняем поля формы
            for data_key, field_names in field_mapping.items():
                if data_key in hotel_data:
                    value = hotel_data[data_key]
                    
                    # Пробуем найти поле по разным именам
                    field_found = False
                    for field_name in field_names:
                        try:
                            field = self.driver.find_element(By.CSS_SELECTOR, f"input[name='{field_name}'], textarea[name='{field_name}'], select[name='{field_name}']")
                            
                            # Очищаем поле и вводим значение
                            field.clear()
                            field.send_keys(str(value))
                            filled_fields.append(f"{field_name}: {value}")
                            field_found = True
                            break
                            
                        except Exception as e:
                            logger.warning(f"Поле {field_name} не найдено: {e}")
                            continue
                    
                    if not field_found:
                        logger.warning(f"Не удалось найти поле для {data_key}: {value}")
            
            logger.info(f"Заполнено полей: {len(filled_fields)}")
            logger.info(f"Заполненные поля: {filled_fields}")
            
            # Пытаемся отправить форму
            return self.submit_registration_step({})
            
        except Exception as e:
            logger.error(f"Ошибка при отправке основной информации об отеле: {e}")
            return False, f"Ошибка: {str(e)}"

    def submit_hotel_contact_info(self, contact_data):
        """
        Отправить контактную информацию отеля через Selenium
        """
        try:
            if not self.driver:
                logger.error("WebDriver не инициализирован")
                return False, "WebDriver не инициализирован"
            
            logger.info(f"Отправляем контактную информацию через Selenium: {contact_data}")
            
            # Ищем поля для контактной информации на странице
            contact_name = contact_data.get('name', '')
            contact_phone = contact_data.get('phone', '')
            contact_email = contact_data.get('email', '')
            
            # Заполняем поле имени контактного лица
            name_selectors = [
                'input[name*="contact_name"]',
                'input[name*="contact_person"]',
                'input[name*="contact_full_name"]',
                'input[name*="name"][placeholder*="контакт"]',
                'input[name*="name"][placeholder*="contact"]',
                'input[id*="contact_name"]',
                'input[id*="contact_person"]'
            ]
            
            name_field = None
            for selector in name_selectors:
                try:
                    name_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Найдено поле имени: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if name_field:
                name_field.clear()
                name_field.send_keys(contact_name)
                logger.info(f"Заполнено поле имени: {contact_name}")
            else:
                logger.warning("Поле имени контактного лица не найдено")
            
            # Заполняем поле телефона
            phone_selectors = [
                'input[name*="contact_phone"]',
                'input[name*="contact_tel"]',
                'input[name*="phone"][placeholder*="телефон"]',
                'input[name*="phone"][placeholder*="phone"]',
                'input[type="tel"]',
                'input[id*="contact_phone"]',
                'input[id*="contact_tel"]'
            ]
            
            phone_field = None
            for selector in phone_selectors:
                try:
                    phone_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Найдено поле телефона: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if phone_field:
                phone_field.clear()
                phone_field.send_keys(contact_phone)
                logger.info(f"Заполнено поле телефона: {contact_phone}")
            else:
                logger.warning("Поле телефона контактного лица не найдено")
            
            # Заполняем поле email
            email_selectors = [
                'input[name*="contact_email"]',
                'input[name*="email"][placeholder*="email"]',
                'input[type="email"]',
                'input[id*="contact_email"]',
                'input[name*="email"]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Найдено поле email: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if email_field:
                email_field.clear()
                email_field.send_keys(contact_email)
                logger.info(f"Заполнено поле email: {contact_email}")
            else:
                logger.warning("Поле email контактного лица не найдено")
            
            # Ищем кнопку "Далее" или "Продолжить"
            next_button_selectors = [
                'button[type="submit"]',
                'button.next-step-js',
                'button[class*="next"]',
                'button[class*="continue"]',
                'button:contains("Далее")',
                'button:contains("Продолжить")',
                'button:contains("Next")',
                'button:contains("Continue")',
                'input[type="submit"]'
            ]
            
            next_button = None
            for selector in next_button_selectors:
                try:
                    if ':contains(' in selector:
                        # Для селекторов с текстом используем XPath
                        text = selector.split('"')[1]
                        xpath = f"//button[contains(text(), '{text}')]"
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                    else:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    logger.info(f"Найдена кнопка продолжения: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if next_button:
                # Проверяем, не заблокирована ли кнопка
                if not next_button.get_attribute('disabled'):
                    next_button.click()
                    logger.info("Кнопка продолжения нажата")
                    
                    # Ждем немного для обработки формы
                    time.sleep(2)
                    
                    return True, "Контактная информация успешно отправлена"
                else:
                    logger.warning("Кнопка продолжения заблокирована")
                    return False, "Кнопка продолжения заблокирована. Проверьте заполнение всех обязательных полей."
            else:
                logger.warning("Кнопка продолжения не найдена")
                return False, "Кнопка продолжения не найдена на странице"
                
        except Exception as e:
            logger.error(f"Ошибка при отправке контактной информации через Selenium: {e}")
            return False, f"Ошибка: {str(e)}"

    def submit_hotel_amenities(self, amenities_data):
        """
        Отправить информацию об удобствах отеля
        """
        try:
            possible_urls = [
                "https://extranet.101hotels.com/api/hotel/amenities",
                "https://extranet.101hotels.com/api/partner/hotel/amenities",
                "https://extranet.101hotels.com/api/registration/amenities",
                "https://extranet.101hotels.com/api/hotel/facilities"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://extranet.101hotels.com",
                "Referer": "https://extranet.101hotels.com/partner/hotels/add",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
            }
            
            for url in possible_urls:
                try:
                    response = self.session.post(url, headers=headers, json=amenities_data)
                    logger.info(f"Пробуем отправить информацию об удобствах с URL: {url}")
                    logger.info(f"Отправляемые данные: {amenities_data}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Информация об удобствах успешно отправлена: {data}")
                        return True, data
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка отправки информации об удобствах: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для отправки информации об удобствах"
                
        except Exception as e:
            logger.error(f"Ошибка при отправке информации об удобствах: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def finalize_hotel_registration(self, final_data=None):
        """
        Завершить регистрацию отеля
        """
        try:
            possible_urls = [
                "https://extranet.101hotels.com/api/hotel/registration/finalize",
                "https://extranet.101hotels.com/api/partner/hotel/registration/finalize",
                "https://extranet.101hotels.com/api/registration/complete",
                "https://extranet.101hotels.com/api/hotel/complete"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Origin": "https://extranet.101hotels.com",
                "Referer": "https://extranet.101hotels.com/partner/hotels/add",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
            }
            
            data = final_data or {}
            
            for url in possible_urls:
                try:
                    response = self.session.post(url, headers=headers, json=data)
                    logger.info(f"Пробуем завершить регистрацию отеля с URL: {url}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Регистрация отеля успешно завершена: {data}")
                        return True, data
                    elif response.status_code == 404:
                        logger.warning(f"URL {url} не найден, пробуем следующий")
                        continue
                    else:
                        logger.error(f"Ошибка завершения регистрации отеля: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка при запросе к {url}: {e}")
                    continue
            
            return False, "Не удалось найти рабочий API эндпоинт для завершения регистрации отеля"
                
        except Exception as e:
            logger.error(f"Ошибка при завершении регистрации отеля: {e}")
            return False, f"Ошибка соединения: {str(e)}"

    def get_registration_progress(self):
        """
        Получить прогресс регистрации отеля через обратный API
        Анализируем DOM для определения прогресса
        """
        try:
            if not self.driver:
                return False, "Драйвер не инициализирован"
            
            progress_data = {
                "current_step": "unknown",
                "total_steps": 0,
                "completion_percentage": 0,
                "status": "В процессе",
                "completed_steps": [],
                "current_url": self.driver.current_url
            }
            
            try:
                # Ищем индикаторы прогресса
                progress_indicators = self.driver.find_elements(By.CSS_SELECTOR, ".progress-bar, .step-indicator, .registration-progress")
                
                if progress_indicators:
                    for indicator in progress_indicators:
                        # Анализируем прогресс-бар
                        try:
                            progress_text = indicator.text
                            if "%" in progress_text:
                                # Извлекаем процент из текста
                                import re
                                percentage_match = re.search(r'(\d+)%', progress_text)
                                if percentage_match:
                                    progress_data["completion_percentage"] = int(percentage_match.group(1))
                        except:
                            pass
                
                # Ищем номера шагов
                step_numbers = self.driver.find_elements(By.CSS_SELECTOR, "[data-step], .step-number, .current-step")
                
                if step_numbers:
                    for step in step_numbers:
                        try:
                            step_num = step.get_attribute("data-step") or step.text
                            if step_num and step_num.isdigit():
                                progress_data["current_step"] = f"Шаг {step_num}"
                                break
                        except:
                            pass
                
                # Ищем общее количество шагов
                total_steps_elements = self.driver.find_elements(By.CSS_SELECTOR, ".total-steps, .steps-count")
                
                if total_steps_elements:
                    for element in total_steps_elements:
                        try:
                            total_text = element.text
                            if "из" in total_text:
                                # Извлекаем общее количество из текста "X из Y"
                                import re
                                total_match = re.search(r'из\s*(\d+)', total_text)
                                if total_match:
                                    progress_data["total_steps"] = int(total_match.group(1))
                                    break
                        except:
                            pass
                
                # Анализируем URL для определения шага
                current_url = self.driver.current_url
                if "step" in current_url:
                    import re
                    step_match = re.search(r'step[=/](\d+)', current_url)
                    if step_match:
                        progress_data["current_step"] = f"Шаг {step_match.group(1)}"
                
                # Ищем выполненные шаги
                completed_steps = self.driver.find_elements(By.CSS_SELECTOR, ".completed-step, .step-done, .step-success")
                
                for step in completed_steps:
                    try:
                        step_text = step.text.strip()
                        if step_text:
                            progress_data["completed_steps"].append(step_text)
                    except:
                        pass
                
                # Если не удалось определить прогресс, используем базовую информацию
                if progress_data["current_step"] == "unknown":
                    progress_data["current_step"] = "Текущий шаг"
                
                if progress_data["total_steps"] == 0:
                    progress_data["total_steps"] = 5  # Предполагаемое количество шагов
                
                # Рассчитываем процент завершения на основе URL или других индикаторов
                if progress_data["completion_percentage"] == 0:
                    if "country" in current_url:
                        progress_data["completion_percentage"] = 20
                    elif "basic" in current_url or "info" in current_url:
                        progress_data["completion_percentage"] = 40
                    elif "contact" in current_url:
                        progress_data["completion_percentage"] = 60
                    elif "amenities" in current_url or "facilities" in current_url:
                        progress_data["completion_percentage"] = 80
                    elif "complete" in current_url or "finish" in current_url:
                        progress_data["completion_percentage"] = 100
                
                logger.info(f"Прогресс регистрации: {progress_data}")
                return True, progress_data
                
            except Exception as e:
                logger.warning(f"Ошибка при анализе прогресса: {e}")
                # Возвращаем базовую информацию
                return True, progress_data
                
        except Exception as e:
            logger.error(f"Ошибка при получении прогресса регистрации: {e}")
            return False, f"Ошибка: {str(e)}"

    def register_hotel_step_by_step(self, hotel_info):
        """
        Пошаговая регистрация отеля через обратный API
        Используем Selenium для эмуляции пользовательских действий
        """
        try:
            logger.info("Начинаем пошаговую регистрацию отеля через обратный API")
            
            if not self.driver:
                return False, "Драйвер не инициализирован"
            
            # Шаг 1: Получаем информацию о текущем шаге
            step_success, step_info = self.get_registration_step_info()
            if not step_success:
                return False, f"Не удалось получить информацию о шаге: {step_info}"
            
            logger.info(f"Текущий шаг: {step_info}")
            
            # Шаг 2: Заполняем основную информацию об отеле
            basic_info = {
                "name": hotel_info.get("name"),
                "address": hotel_info.get("address"),
                "city": hotel_info.get("city"),
                "country_id": hotel_info.get("country_id"),
                "type": hotel_info.get("type"),
                "phone": hotel_info.get("phone"),
                "email": hotel_info.get("email"),
                "website": hotel_info.get("website")
            }
            
            # Заполняем поля формы
            filled_count = 0
            for field_name, value in basic_info.items():
                if value:
                    try:
                        # Ищем поле по различным именам
                        field_selectors = [
                            f"input[name='{field_name}']",
                            f"input[name='hotel_{field_name}']",
                            f"input[name='property_{field_name}']",
                            f"textarea[name='{field_name}']",
                            f"select[name='{field_name}']"
                        ]
                        
                        field_found = False
                        for selector in field_selectors:
                            try:
                                field = self.driver.find_element(By.CSS_SELECTOR, selector)
                                field.clear()
                                field.send_keys(str(value))
                                logger.info(f"Заполнено поле {field_name}: {value}")
                                filled_count += 1
                                field_found = True
                                break
                            except:
                                continue
                        
                        if not field_found:
                            logger.warning(f"Не удалось найти поле для {field_name}")
                            
                    except Exception as e:
                        logger.warning(f"Ошибка при заполнении поля {field_name}: {e}")
                        continue
            
            logger.info(f"Заполнено {filled_count} полей из {len(basic_info)}")
            
            # Шаг 3: Нажимаем кнопку "Продолжить" или "Далее"
            next_button_selectors = [
                "button[type='submit']",
                "button.next-step-btn",
                "button:contains('Продолжить')",
                "button:contains('Далее')",
                "button:contains('Next')",
                ".continue-btn",
                ".submit-btn"
            ]
            
            button_clicked = False
            for selector in next_button_selectors:
                try:
                    if "contains" in selector:
                        # Используем XPath для поиска по тексту
                        xpath = f"//button[contains(text(), 'Продолжить') or contains(text(), 'Далее') or contains(text(), 'Next')]"
                        button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Проверяем, не заблокирована ли кнопка
                    if button.get_attribute("disabled"):
                        logger.warning(f"Кнопка заблокирована: {selector}")
                        continue
                    
                    # Нажимаем кнопку
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", button)
                    
                    logger.info(f"Нажата кнопка: {selector}")
                    button_clicked = True
                    break
                    
                except Exception as e:
                    logger.warning(f"Не удалось найти или нажать кнопку {selector}: {e}")
                    continue
            
            if not button_clicked:
                return False, "Не удалось найти активную кнопку для продолжения"
            
            # Ждем загрузки следующей страницы
            time.sleep(3)
            
            # Шаг 4: Получаем информацию о результате
            result_info = {
                "success": True,
                "filled_fields": filled_count,
                "new_url": self.driver.current_url,
                "new_title": self.driver.title,
                "message": "Регистрация отеля выполнена успешно"
            }
            
            logger.info("Пошаговая регистрация отеля завершена")
            return True, result_info
            
        except Exception as e:
            logger.error(f"Ошибка при пошаговой регистрации отеля: {e}")
            return False, f"Ошибка: {str(e)}"
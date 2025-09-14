import requests
import os
import json
import uuid
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pyautogui

logger = logging.getLogger(__name__)

SESSIONS_DIR = 'sessions'
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

class Hotels101Manager:
    def __init__(self, email=None):
        self.session = requests.Session()
        self.email = email
        self.driver = None
        self.coordinates = self.load_coordinates()
        if email:
            self.load_cookies(email)

    def load_coordinates(self):
        """Загрузить координаты элементов интерфейса (устарело)"""
        logger.warning("Метод load_coordinates устарел. Используйте новую систему записи действий.")
        return {}

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

    # --- Selenium методы ---
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
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Веб-драйвер успешно настроен")
        except Exception as e:
            logger.error(f"Ошибка запуска Chrome: {e}")
            raise Exception(f"Не удалось запустить Chrome. Ошибка: {e}")
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def open_login_page(self):
        """Открыть страницу входа 101 отеля"""
        if not self.driver:
            self.setup_driver()
        self.driver.get("https://extranet.101hotels.com/login")
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        logger.info("Открыта страница входа extranet.101hotels.com")

    def fill_email(self, email):
        """Заполнить поле email"""
        wait = WebDriverWait(self.driver, 10)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "_username")))
        email_input.clear()
        email_input.send_keys(email)
        logger.info(f"Введён email: {email}")

    def fill_password(self, password):
        """Заполнить поле пароля"""
        wait = WebDriverWait(self.driver, 10)
        password_input = wait.until(EC.presence_of_element_located((By.NAME, "_password")))
        password_input.clear()
        password_input.send_keys(password)
        logger.info("Введён пароль")

    def submit_login(self):
        """Нажать кнопку входа"""
        wait = WebDriverWait(self.driver, 10)
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_btn.click()
        logger.info("Кнопка ВОЙТИ нажата")
        time.sleep(2)
        return True

    def check_login_success(self, email=None):
        """Проверить успешность входа"""
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard, .partner-panel")))
            logger.info("Вход выполнен успешно")
            if email:
                cookies = self.driver.get_cookies()
                cookies_path = self.get_cookies_path(email)
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                logger.info(f"Cookies для {email} сохранены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке входа: {e}")
            return False

    # --- Основные методы для работы с ботом ---
    def login_to_account(self, email, password):
        """Войти в существующий аккаунт"""
        logger.info(f"Выполняется вход в существующий аккаунт: {email}")
        
        # Открываем страницу входа
        self.open_login_page()
        time.sleep(2)
        
        # Заполняем форму входа
        self.fill_email(email)
        self.fill_password(password)
        
        # Нажимаем кнопку входа
        success = self.submit_login()
        if not success:
            return False, "Ошибка при нажатии кнопки входа"
        
        # Проверяем успешность входа
        login_success = self.check_login_success(email)
        if login_success:
            return True, "Вход в существующий аккаунт выполнен успешно"
        else:
            return False, "Ошибка входа. Проверьте логин и пароль"

    def register_new_object(self, object_data):
        """Зарегистрировать новый объект (новый пользователь)"""
        logger.info("Начинаем регистрацию нового объекта")
        
        # Открываем страницу входа
        self.open_login_page()
        time.sleep(2)
        
        # Кликаем по ссылке "ЗАРЕГИСТРИРОВАТЬ СВОЙ ОБЪЕКТ"
        self.click_register_object_link()
        time.sleep(3)
        
        # Заполняем форму регистрации объекта (Шаг 1 из 6)
        success = self.fill_object_registration_form(object_data)
        if not success:
            return False, "Ошибка при заполнении формы регистрации"
        
        # Нажимаем кнопку "ПРОДОЛЖИТЬ"
        continue_success = self.click_continue_button()
        if not continue_success:
            return False, "Ошибка при переходе к следующему шагу"
        
        return True, "Форма регистрации объекта заполнена успешно"

    def fill_object_registration_form(self, object_data):
        """Заполнить форму регистрации объекта (Шаг 1)"""
        logger.info("Заполняем форму регистрации объекта")
        
        try:
            # Заполняем контактное лицо
            if 'contact_name' in object_data:
                self.fill_contact_person_field(object_data['contact_name'])
            
            # Заполняем телефон для подтверждения
            if 'confirmation_phone' in object_data:
                self.fill_confirmation_phone_field(object_data['confirmation_phone'])
            
            # Заполняем email
            if 'email' in object_data:
                self.fill_email_field(object_data['email'])
            
            # Заполняем контактный телефон
            if 'contact_phone' in object_data:
                self.fill_contact_phone_field(object_data['contact_phone'])
            
            # Заполняем номер классификации (если есть)
            if 'classification_number' in object_data:
                self.fill_classification_number_field(object_data['classification_number'])
            else:
                # Если номера нет, ставим галочку "не нужно классификация"
                self.check_no_classification_checkbox()
            
            # Выбираем правовую форму
            legal_form = object_data.get('legal_form', 'legal_entity')
            self.select_legal_form(legal_form)
            
            # Ставим галочку согласия на обработку персональных данных
            self.check_personal_data_consent()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при заполнении формы: {e}")
            return False

    def create_new_object(self, object_data):
        """Создать новый объект (для совместимости)"""
        return self.register_new_object(object_data)

    # --- PyAutoGUI методы для автоматизации ---
    def click_register_object_link(self):
        """Клик по ссылке регистрации объекта"""
        coords = self.coordinates.get('coordinates', {}).get('registration_options', {}).get('register_object_link', {})
        x, y = coords.get('x', 1166), coords.get('y', 950)
        pyautogui.click(x, y)
        logger.info(f"Клик по ссылке регистрации объекта: ({x}, {y})")
        time.sleep(2)

    def fill_contact_person_field(self, name):
        """Заполнить поле контактного лица"""
        coords = self.coordinates.get('coordinates', {}).get('object_registration_form', {}).get('contact_person_field', {})
        x, y = coords.get('x', 1000), coords.get('y', 300)
        pyautogui.click(x, y)
        pyautogui.write(name)
        logger.info(f"Заполнено контактное лицо: {name}")
        time.sleep(1)

    def fill_confirmation_phone_field(self, phone):
        """Заполнить поле телефона для подтверждения"""
        coords = self.coordinates.get('coordinates', {}).get('object_registration_form', {}).get('confirmation_phone_field', {})
        x, y = coords.get('x', 1000), coords.get('y', 350)
        pyautogui.click(x, y)
        pyautogui.write(phone)
        logger.info(f"Заполнен телефон для подтверждения: {phone}")
        time.sleep(1)

    def fill_email_field(self, email):
        """Заполнить поле email"""
        coords = self.coordinates.get('coordinates', {}).get('object_registration_form', {}).get('email_field', {})
        x, y = coords.get('x', 1000), coords.get('y', 400)
        pyautogui.click(x, y)
        pyautogui.write(email)
        logger.info(f"Заполнен email: {email}")
        time.sleep(1)

    def fill_contact_phone_field(self, phone):
        """Заполнить поле контактного телефона"""
        coords = self.coordinates.get('coordinates', {}).get('object_registration_form', {}).get('contact_phone_field', {})
        x, y = coords.get('x', 1000), coords.get('y', 450)
        pyautogui.click(x, y)
        pyautogui.write(phone)
        logger.info(f"Заполнен контактный телефон: {phone}")
        time.sleep(1)

    def fill_classification_number_field(self, number):
        """Заполнить поле номера классификации"""
        coords = self.coordinates.get('coordinates', {}).get('object_registration_form', {}).get('classification_number_field', {})
        x, y = coords.get('x', 1000), coords.get('y', 500)
        pyautogui.click(x, y)
        pyautogui.write(number)
        logger.info(f"Заполнен номер классификации: {number}")
        time.sleep(1)

    def check_no_classification_checkbox(self):
        """Поставить галочку 'не нужно классификация'"""
        coords = self.coordinates.get('coordinates', {}).get('object_registration_form', {}).get('no_classification_checkbox', {})
        x, y = coords.get('x', 1000), coords.get('y', 550)
        pyautogui.click(x, y)
        logger.info("Поставлена галочка 'не нужно классификация'")
        time.sleep(1)

    def select_legal_form(self, legal_form):
        """Выбрать правовую форму"""
        legal_form_map = {
            "legal_entity": "legal_entity_radio",
            "individual_entrepreneur": "individual_entrepreneur_radio", 
            "self_employed": "self_employed_radio"
        }
        
        form_key = legal_form_map.get(legal_form, "legal_entity_radio")
        coords = self.coordinates.get('coordinates', {}).get('legal_form_selection', {}).get(form_key, {})
        x, y = coords.get('x', 1000), coords.get('y', 650)
        pyautogui.click(x, y)
        logger.info(f"Выбрана правовая форма: {legal_form}")
        time.sleep(1)

    def check_personal_data_consent(self):
        """Поставить галочку согласия на обработку персональных данных"""
        coords = self.coordinates.get('coordinates', {}).get('form_footer', {}).get('personal_data_checkbox', {})
        x, y = coords.get('x', 1000), coords.get('y', 950)
        pyautogui.click(x, y)
        logger.info("Поставлена галочка согласия на обработку персональных данных")
        time.sleep(1)

    def click_continue_button(self):
        """Нажать кнопку 'ПРОДОЛЖИТЬ'"""
        coords = self.coordinates.get('coordinates', {}).get('form_footer', {}).get('continue_button', {})
        x, y = coords.get('x', 1200), coords.get('y', 1000)
        pyautogui.click(x, y)
        logger.info("Нажата кнопка 'ПРОДОЛЖИТЬ'")
        time.sleep(2)
        return True

    def get_available_options(self):
        """Получить доступные опции для 101 отеля"""
        return {
            "platform": "101hotels",
            "platform_name": "101 отель",
            "description": "Платформа управления объектами размещения",
            "workflow_options": [
                {
                    "id": "existing_account_login",
                    "name": "Войти в существующий аккаунт",
                    "description": "Для пользователей с уже существующим аккаунтом"
                },
                {
                    "id": "register_new_object",
                    "name": "Зарегистрировать новый объект",
                    "description": "Для новых пользователей - регистрация объекта (6 шагов)"
                }
            ],
            "supported_countries": [
                "Россия", "Беларусь", "Казахстан", "Киргизия", 
                "Узбекистан", "Таджикистан", "Азербайджан", 
                "Армения", "Абхазия", "Грузия"
            ],
            "supported_legal_forms": [
                "Юридическое лицо",
                "Индивидуальный предприниматель", 
                "Самозанятый"
            ],
            "registration_steps": [
                "Шаг 1: Контактная информация и правовая форма",
                "Шаг 2-6: Дополнительная информация об объекте"
            ]
        }

    def process_request(self, action, data=None):
        """Обработать запрос пользователя"""
        if action == "existing_account_login":
            email = data.get('email')
            password = data.get('password')
            if not email or not password:
                return False, "Необходимо указать email и пароль"
            return self.login_to_account(email, password)
        
        elif action == "register_new_object":
            if not data:
                return False, "Необходимо указать данные объекта"
            return self.register_new_object(data)
        
        elif action == "get_options":
            return True, self.get_available_options()
        
        else:
            return False, f"Неизвестное действие: {action}"

    def close_browser(self):
        """Закрыть браузер"""
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

# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создание менеджера
    manager = Hotels101Manager()
    
    # Получение доступных опций
    success, options = manager.process_request("get_options")
    if success:
        print("Доступные опции для 101 отеля:")
        print(json.dumps(options, ensure_ascii=False, indent=2))
    
    # Пример входа в существующий аккаунт
    # success, message = manager.process_request("existing_account_login", {
    #     "email": "test@example.com",
    #     "password": "password123"
    # })
    # print(f"Результат входа: {message}")
    
    # Пример регистрации нового объекта
    # success, message = manager.process_request("register_new_object", {
    #     "contact_name": "Иван Иванов",
    #     "confirmation_phone": "+7 999 123-45-67",
    #     "email": "ivan@example.com",
    #     "contact_phone": "+7 999 123-45-67",
    #     "legal_form": "legal_entity"
    # })
    # print(f"Результат регистрации объекта: {message}") 
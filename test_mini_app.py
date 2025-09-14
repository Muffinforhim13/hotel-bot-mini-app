#!/usr/bin/env python3
"""
Тестирование Mini App Hotel Bot
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

class MiniAppTester:
    """Тестер для Mini App API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_user_id = "test_user_123"
    
    def test_status(self) -> bool:
        """Тест статуса API"""
        print("🔍 Тестирование статуса API...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API работает: {data['status']}")
                return True
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
    
    def test_mini_app_page(self) -> bool:
        """Тест главной страницы Mini App"""
        print("🔍 Тестирование главной страницы...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                content = response.text
                if "Hotel Bot" in content and "Mini App" in content:
                    print("✅ Главная страница загружается корректно")
                    return True
                else:
                    print("❌ Неверное содержимое страницы")
                    return False
            else:
                print(f"❌ Ошибка загрузки страницы: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
    
    def test_smart_automation(self) -> bool:
        """Тест умной автоматизации"""
        print("🔍 Тестирование умной автоматизации...")
        
        test_data = {
            "email": "test@example.com",
            "password": "test_password",
            "hotel_name": "Test Hotel",
            "hotel_address": "Test Address 123",
            "hotel_type": "hotel",
            "city": "Test City",
            "phone": "+1234567890",
            "contact_name": "Test Contact",
            "contact_email": "contact@example.com",
            "description": "Test hotel description",
            "amenities": "Wi-Fi, Parking, Breakfast",
            "platforms": {
                "ostrovok": True,
                "bronevik": False,
                "101hotels": True
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/smart_automation",
                json=test_data,
                headers={"X-User-ID": self.test_user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Умная автоматизация работает")
                    return True
                else:
                    print(f"❌ Ошибка умной автоматизации: {data.get('message')}")
                    return False
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
    
    def test_platforms(self) -> bool:
        """Тест платформ"""
        print("🔍 Тестирование платформ...")
        
        platforms = ["ostrovok", "bronevik", "101hotels"]
        success_count = 0
        
        for platform in platforms:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/open_platform",
                    json={"platform": platform},
                    headers={"X-User-ID": self.test_user_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print(f"✅ Платформа {platform} доступна")
                        success_count += 1
                    else:
                        print(f"❌ Ошибка платформы {platform}: {data.get('message')}")
                else:
                    print(f"❌ Ошибка API для {platform}: {response.status_code}")
            except Exception as e:
                print(f"❌ Ошибка соединения для {platform}: {e}")
        
        return success_count == len(platforms)
    
    def test_templates(self) -> bool:
        """Тест шаблонов"""
        print("🔍 Тестирование шаблонов...")
        
        try:
            # Получение шаблонов
            response = self.session.get(
                f"{self.base_url}/api/templates",
                headers={"X-User-ID": self.test_user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    templates = data.get("templates", [])
                    print(f"✅ Получено шаблонов: {len(templates)}")
                    return True
                else:
                    print(f"❌ Ошибка получения шаблонов: {data.get('message')}")
                    return False
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
    
    def test_settings(self) -> bool:
        """Тест настроек"""
        print("🔍 Тестирование настроек...")
        
        try:
            # Получение настроек
            response = self.session.get(
                f"{self.base_url}/api/settings",
                headers={"X-User-ID": self.test_user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    settings = data.get("settings", {})
                    print(f"✅ Настройки получены: {list(settings.keys())}")
                    
                    # Тест сохранения настроек
                    test_settings = {
                        "bnovo_api_key": "test_api_key",
                        "debug_mode": True
                    }
                    
                    save_response = self.session.post(
                        f"{self.base_url}/api/settings",
                        json=test_settings,
                        headers={"X-User-ID": self.test_user_id}
                    )
                    
                    if save_response.status_code == 200:
                        save_data = save_response.json()
                        if save_data.get("success"):
                            print("✅ Настройки сохранены")
                            return True
                        else:
                            print(f"❌ Ошибка сохранения настроек: {save_data.get('message')}")
                            return False
                    else:
                        print(f"❌ Ошибка API при сохранении: {save_response.status_code}")
                        return False
                else:
                    print(f"❌ Ошибка получения настроек: {data.get('message')}")
                    return False
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
    
    def test_notification_settings(self) -> bool:
        """Тест настроек уведомлений"""
        print("🔍 Тестирование настроек уведомлений...")
        
        test_settings = {
            "booking_notifications": True,
            "status_notifications": False,
            "error_notifications": True
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/notification_settings",
                json=test_settings,
                headers={"X-User-ID": self.test_user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Настройки уведомлений сохранены")
                    return True
                else:
                    print(f"❌ Ошибка сохранения настроек уведомлений: {data.get('message')}")
                    return False
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Запуск всех тестов"""
        print("🚀 Запуск тестирования Mini App...")
        print("=" * 50)
        
        tests = {
            "API Status": self.test_status,
            "Mini App Page": self.test_mini_app_page,
            "Smart Automation": self.test_smart_automation,
            "Platforms": self.test_platforms,
            "Templates": self.test_templates,
            "Settings": self.test_settings,
            "Notification Settings": self.test_notification_settings
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
                results[test_name] = False
            
            print("-" * 30)
            time.sleep(1)  # Пауза между тестами
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Вывод сводки тестов"""
        print("\n" + "=" * 50)
        print("📊 СВОДКА ТЕСТИРОВАНИЯ")
        print("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"{test_name}: {status}")
        
        print("-" * 50)
        print(f"Всего тестов: {total}")
        print(f"Пройдено: {passed}")
        print(f"Провалено: {total - passed}")
        print(f"Процент успеха: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 Все тесты пройдены! Mini App готов к использованию!")
        else:
            print(f"\n⚠️ {total - passed} тестов провалено. Проверьте настройки.")

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование Hotel Bot Mini App")
    print("Убедитесь, что Mini App API запущен на http://localhost:8000")
    print()
    
    # Проверка доступности сервера
    tester = MiniAppTester()
    
    try:
        response = requests.get("http://localhost:8000/api/status", timeout=5)
        if response.status_code != 200:
            print("❌ Mini App API недоступен. Запустите сервер командой: python run_mini_app.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Mini App API недоступен. Запустите сервер командой: python run_mini_app.py")
        return
    
    # Запуск тестов
    results = tester.run_all_tests()
    tester.print_summary(results)

if __name__ == "__main__":
    main()

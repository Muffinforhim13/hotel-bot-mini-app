#!/usr/bin/env python3
"""
Тестовый скрипт для умной системы автоматизации
Проверяет работу с несколькими платформами одновременно
"""

import time
import json
from action_recorder import RecordingManager

def test_smart_system():
    """Тест умной системы"""
    print("🧠 Тест умной системы автоматизации")
    print("=" * 50)
    
    # Создаем менеджер
    manager = RecordingManager()
    
    # Тестовые данные
    test_data = {
        'email': 'test@example.com',
        'password': 'testpassword',
        'hotel_name': 'Тестовый отель',
        'hotel_address': 'ул. Тестовая, 1',
        'hotel_type': 'Отель',
        'city': 'Москва',
        'phone': '+7 999 123-45-67',
        'website': 'https://test-hotel.com',
        'contact_name': 'Иван Иванов',
        'contact_email': 'ivan@test-hotel.com',
        'description': 'Отличный отель в центре города',
        'amenities': 'Wi-Fi, Парковка, Ресторан'
    }
    
    platforms = ['ostrovok', 'bronevik', '101hotels']
    
    print(f"📋 Тестовые данные: {test_data}")
    print(f"🎯 Платформы: {', '.join(platforms)}")
    
    results = {}
    
    for platform in platforms:
        print(f"\n🔄 Тестируем {platform.title()}...")
        
        try:
            # Получаем рекордер
            recorder = manager.get_recorder(platform)
            
            # Проверяем доступные шаблоны
            recordings = recorder.get_available_recordings()
            
            if recordings:
                latest_recording = recordings[0]  # Берем самый новый
                print(f"   📁 Найден шаблон: {latest_recording['filename']}")
                
                # Загружаем шаблон
                success = recorder.load_recording(latest_recording['filepath'])
                
                if success:
                    print(f"   ✅ Шаблон загружен успешно")
                    
                    # Проверяем, что данные корректно заменяются
                    preview = recorder.preview_recording(latest_recording['filepath'])
                    print(f"   📋 Предварительный просмотр: {preview[:100]}...")
                    
                    results[platform] = {
                        'status': 'ready',
                        'template': latest_recording,
                        'message': 'Готов к использованию'
                    }
                else:
                    print(f"   ❌ Ошибка загрузки шаблона")
                    results[platform] = {
                        'status': 'error',
                        'message': 'Не удалось загрузить шаблон'
                    }
            else:
                print(f"   ❌ Нет доступных шаблонов")
                results[platform] = {
                    'status': 'no_templates',
                    'message': 'Создайте шаблон через record_actions.py'
                }
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results[platform] = {
                'status': 'error',
                'message': str(e)
            }
    
    # Выводим итоговый отчет
    print(f"\n📊 Итоговый отчет:")
    print("=" * 30)
    
    ready_count = sum(1 for r in results.values() if r['status'] == 'ready')
    total_count = len(results)
    
    print(f"✅ Готово к работе: {ready_count}/{total_count}")
    
    for platform, result in results.items():
        status_icon = "✅" if result['status'] == 'ready' else "❌"
        print(f"{status_icon} {platform.title()}: {result['message']}")
    
    if ready_count > 0:
        print(f"\n🎉 Система готова к работе!")
        print(f"💡 Для создания объявлений используйте Telegram бота")
    else:
        print(f"\n⚠️ Сначала создайте шаблоны:")
        print(f"   python record_actions.py")

def show_platform_info():
    """Показать информацию о платформах"""
    print("\n📋 Информация о платформах:")
    print("=" * 30)
    
    platforms = {
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
    
    for platform_id, info in platforms.items():
        print(f"🏨 {info['name']}")
        print(f"   🌐 {info['url']}")
        print(f"   📝 {info['description']}")
        print()

def main():
    """Главная функция"""
    print("🧠 Умная система автоматизации - Тест")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. 🧪 Тест умной системы")
        print("2. 📋 Информация о платформах")
        print("3. ❌ Выход")
        
        choice = input("\nВведите номер (1-3): ").strip()
        
        if choice == '1':
            test_smart_system()
        elif choice == '2':
            show_platform_info()
        elif choice == '3':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main() 
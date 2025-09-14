#!/usr/bin/env python3
"""
Тестовый скрипт для системы записи действий
"""

import time
import json
from action_recorder import RecordingManager

def test_recording():
    """Тест записи действий"""
    print("🎬 Тестирование системы записи действий")
    print("=" * 50)
    
    # Создаем менеджер
    manager = RecordingManager()
    
    # Тестируем запись для Ostrovok
    print("\n1. Начинаем запись для Ostrovok...")
    success = manager.start_recording("ostrovok", "https://extranet.ostrovok.ru")
    
    if success:
        print("✅ Запись начата успешно!")
        print("🌐 Браузер открыт: https://extranet.ostrovok.ru")
        print("\n💡 Выполните следующие действия:")
        print("   • Введите email в поле входа")
        print("   • Введите пароль")
        print("   • Нажмите кнопку входа")
        print("   • Перейдите к созданию объекта")
        print("   • Заполните форму с placeholder'ами:")
        print("     - {{email}} для email")
        print("     - {{password}} для пароля")
        print("     - {{hotel_name}} для названия отеля")
        print("     - {{hotel_address}} для адреса")
        
        input("\n⏸️ Нажмите Enter когда закончите выполнять действия...")
        
        # Останавливаем запись
        print("\n2. Останавливаем запись...")
        filename = manager.stop_recording()
        
        if filename:
            print(f"✅ Запись сохранена: {filename}")
            
            # Показываем статистику
            recorder = manager.get_recorder("ostrovok")
            recordings = recorder.get_available_recordings()
            
            print(f"\n📊 Статистика записей:")
            for recording in recordings:
                print(f"   • {recording['filename']}: {recording['total_actions']} действий")
            
            # Тестируем воспроизведение
            print("\n3. Тестируем воспроизведение...")
            test_data = {
                'email': 'test@example.com',
                'password': 'testpassword123',
                'hotel_name': 'Тестовый отель',
                'hotel_address': 'ул. Тестовая, 1',
                'hotel_type': 'Отель',
                'city': 'Москва',
                'phone': '+7 (999) 123-45-67',
                'website': 'https://test-hotel.ru',
                'contact_name': 'Иван Иванов',
                'contact_email': 'ivan@test-hotel.ru'
            }
            
            print("📝 Тестовые данные:")
            for key, value in test_data.items():
                print(f"   • {key}: {value}")
            
            confirm = input("\n▶️ Нажмите Enter для начала воспроизведения...")
            
            if confirm == '':
                success = recorder.load_recording(filename)
                if success:
                    print("🔄 Воспроизводим действия...")
                    result = recorder.replay_actions(test_data, delay=2.0)
                    
                    if result:
                        print("✅ Воспроизведение завершено успешно!")
                    else:
                        print("❌ Воспроизведение завершено с ошибками")
                else:
                    print("❌ Не удалось загрузить запись")
        else:
            print("❌ Не удалось сохранить запись")
    else:
        print("❌ Не удалось начать запись")

def test_platforms():
    """Тест для разных платформ"""
    print("\n🏨 Тестирование разных платформ")
    print("=" * 50)
    
    manager = RecordingManager()
    
    platforms = {
        'ostrovok': 'https://extranet.ostrovok.ru',
        'bronevik': 'https://extranet.bronevik.com',
        '101hotels': 'https://extranet.101hotels.com'
    }
    
    for platform, url in platforms.items():
        print(f"\n📋 Тестируем {platform.title()}...")
        
        # Создаем рекордер
        recorder = manager.create_recorder(platform)
        
        # Проверяем доступные записи
        recordings = recorder.get_available_recordings()
        print(f"   📁 Найдено записей: {len(recordings)}")
        
        for recording in recordings[:3]:  # Показываем первые 3
            print(f"   • {recording['filename']}: {recording['total_actions']} действий")

def show_help():
    """Показать справку"""
    print("🎬 Система записи действий - Справка")
    print("=" * 50)
    print("\n📋 Доступные команды:")
    print("   test_recording() - Тест записи действий")
    print("   test_platforms() - Тест разных платформ")
    print("   show_help() - Показать эту справку")
    
    print("\n💡 Как использовать:")
    print("   1. Запустите test_recording()")
    print("   2. Выполните действия в браузере")
    print("   3. Используйте placeholder'ы: {{email}}, {{password}}, etc.")
    print("   4. Остановите запись")
    print("   5. Воспроизведите с новыми данными")
    
    print("\n🔧 Placeholder'ы:")
    print("   {{email}} - Email пользователя")
    print("   {{password}} - Пароль")
    print("   {{hotel_name}} - Название отеля")
    print("   {{hotel_address}} - Адрес отеля")
    print("   {{hotel_type}} - Тип отеля")
    print("   {{city}} - Город")
    print("   {{phone}} - Телефон")
    print("   {{website}} - Сайт")
    print("   {{contact_name}} - Контактное лицо")
    print("   {{contact_email}} - Контактный email")

if __name__ == "__main__":
    print("🎬 Система записи действий")
    print("=" * 50)
    
    while True:
        print("\n📋 Выберите действие:")
        print("1. Тест записи действий")
        print("2. Тест платформ")
        print("3. Справка")
        print("4. Выход")
        
        choice = input("\nВведите номер (1-4): ").strip()
        
        if choice == '1':
            test_recording()
        elif choice == '2':
            test_platforms()
        elif choice == '3':
            show_help()
        elif choice == '4':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.") 
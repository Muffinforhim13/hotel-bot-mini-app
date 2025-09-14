#!/usr/bin/env python3
"""
Скрипт для записи действий на платформах бронирования
Запускайте этот скрипт для создания шаблонов, которые потом будет использовать бот
"""

import time
import json
import os
from datetime import datetime
from action_recorder import RecordingManager

def main():
    print("🎬 Система записи действий для Hotel Bot")
    print("=" * 50)
    
    # Создаем менеджер записей
    manager = RecordingManager()
    
    while True:
        print("\nВыберите действие:")
        print("1. 🎬 Записать действия на Ostrovok")
        print("2. 🎬 Записать действия на Bronevik") 
        print("3. 🎬 Записать действия на 101 Hotels")
        print("4. 📋 Показать мои записи")
        print("5. ▶️ Воспроизвести запись")
        print("6. ❌ Выход")
        
        choice = input("\nВведите номер (1-6): ").strip()
        
        if choice == '1':
            record_platform_actions(manager, 'ostrovok', 'https://extranet.ostrovok.ru')
        elif choice == '2':
            record_platform_actions(manager, 'bronevik', 'https://extranet.bronevik.com')
        elif choice == '3':
            record_platform_actions(manager, '101hotels', 'https://extranet.101hotels.com')
        elif choice == '4':
            show_recordings(manager)
        elif choice == '5':
            replay_recording(manager)
        elif choice == '6':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

def record_platform_actions(manager, platform, url):
    """Записать действия для конкретной платформы"""
    print(f"\n🎬 Запись действий для {platform.title()}")
    print(f"🌐 URL: {url}")
    
    print("\n💡 ВЫБЕРИТЕ МЕТОД ЗАПИСИ:")
    print("1. 🚀 Автоматическая запись (JavaScript)")
    print("2. 🖱️ Ручная запись (более надежно)")
    
    method_choice = input("\nВведите номер (1-2): ").strip()
    
    if method_choice == "2":
        # Используем ручную запись
        print("\n🖱️ Ручная запись")
        print("💡 СОВЕТЫ:")
        print("• После каждого важного шага введите 'state' для записи")
        print("• Используйте 'nav' для записи навигации")
        print("• Введите 'stop' для завершения")
        
        input("\nНажмите Enter, чтобы начать...")
        
        try:
            from manual_recorder import ManualRecorder
            recorder = ManualRecorder(platform)
            
            if recorder.start_recording(url):
                print("✅ Запись начата! Выполните действия в браузере...")
                
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
                    print(f"✅ Запись сохранена: {filename}")
                    print("Теперь вы можете использовать эту запись для автоматизации!")
                else:
                    print("❌ Ошибка при сохранении записи")
            else:
                print("❌ Ошибка при запуске записи")
                
        except ImportError:
            print("❌ Модуль ручной записи недоступен")
            print("Используйте автоматическую запись")
            method_choice = "1"
    
    if method_choice == "1":
        # Используем автоматическую запись
        print("\n🚀 Автоматическая запись")
        print("💡 СОВЕТЫ:")
        print("• Используйте placeholder'ы: {{email}}, {{password}}, {{hotel_name}}")
        print("• Заполните все нужные поля")
        print("• Кликайте по всем важным элементам")
        print("• Дойдите до финального шага создания объявления")
        
        input("\nНажмите Enter, чтобы начать запись...")
        
        try:
            # Начинаем запись
            success = manager.start_recording(platform, url)
            
            if success:
                print(f"✅ Запись начата! Браузер открыт: {url}")
                print("Выполните нужные действия в браузере...")
                print("Не закрывайте браузер!")
                
                input("\nНажмите Enter, когда закончите действия...")
                
                # Останавливаем запись
                filename = manager.stop_recording()
                
                if filename:
                    print(f"✅ Запись сохранена: {filename}")
                    
                    # Показываем предварительный просмотр
                    recorder = manager.get_recorder(platform)
                    preview = recorder.preview_recording(filename)
                    print(f"\n📋 Предварительный просмотр:\n{preview}")
                    
                    # Спрашиваем, хочет ли пользователь воспроизвести
                    replay = input("\nХотите воспроизвести запись? (y/n): ").strip().lower()
                    if replay == 'y':
                        test_replay(manager, filename, platform)
                else:
                    print("❌ Ошибка при сохранении записи")
                    print("💡 Попробуйте ручную запись (метод 2)")
            else:
                print("❌ Ошибка при начале записи")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def show_recordings(manager):
    """Показать список записей"""
    print("\n📋 Ваши записи:")
    
    for platform in ['ostrovok', 'bronevik', '101hotels']:
        recorder = manager.get_recorder(platform)
        recordings = recorder.get_available_recordings()
        
        if recordings:
            print(f"\n🏨 {platform.title()}:")
            for i, filename in enumerate(recordings, 1):
                preview = recorder.preview_recording(filename)
                print(f"  {i}. {filename}")
                print(f"     {preview[:100]}...")
        else:
            print(f"\n🏨 {platform.title()}: нет записей")

def replay_recording(manager):
    """Воспроизвести запись"""
    print("\n▶️ Воспроизведение записи")
    
    # Показываем доступные записи
    all_recordings = []
    for platform in ['ostrovok', 'bronevik', '101hotels']:
        recorder = manager.get_recorder(platform)
        recordings = recorder.get_available_recordings()
        for filename in recordings:
            all_recordings.append((platform, filename))
    
    if not all_recordings:
        print("❌ Нет доступных записей")
        return
    
    print("Доступные записи:")
    for i, (platform, filename) in enumerate(all_recordings, 1):
        print(f"{i}. {platform.title()} - {filename}")
    
    try:
        choice = int(input("\nВыберите номер записи: ")) - 1
        if 0 <= choice < len(all_recordings):
            platform, filename = all_recordings[choice]
            test_replay(manager, filename, platform)
        else:
            print("❌ Неверный номер")
    except ValueError:
        print("❌ Введите число")

def test_replay(manager, filename, platform):
    """Тестовое воспроизведение записи"""
    print(f"\n▶️ Воспроизведение: {filename}")
    
    # Запрашиваем тестовые данные
    print("\nВведите тестовые данные:")
    user_data = {}
    
    fields = [
        'email', 'password', 'hotel_name', 'hotel_address', 
        'hotel_type', 'city', 'phone', 'website', 
        'contact_name', 'contact_email'
    ]
    
    for field in fields:
        value = input(f"{field}: ").strip()
        if value:
            user_data[field] = value
    
    if not user_data:
        print("❌ Не введены данные для воспроизведения")
        return
    
    print(f"\nВоспроизводим с данными: {user_data}")
    input("Нажмите Enter для начала воспроизведения...")
    
    try:
        recorder = manager.get_recorder(platform)
        success = recorder.load_recording(filename)
        
        if success:
            result = recorder.replay_actions(user_data, delay=1.5)
            if result:
                print("✅ Воспроизведение завершено успешно!")
            else:
                print("⚠️ Воспроизведение завершено с ошибками")
        else:
            print("❌ Ошибка при загрузке записи")
            
    except Exception as e:
        print(f"❌ Ошибка при воспроизведении: {e}")

if __name__ == "__main__":
    main() 
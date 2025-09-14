#!/usr/bin/env python3
"""
Быстрый тест системы записи действий
"""

from action_recorder import RecordingManager
import time

def quick_test():
    """Быстрый тест записи и воспроизведения"""
    print("🚀 Быстрый тест системы записи действий")
    print("=" * 50)
    
    # Создаем менеджер
    manager = RecordingManager()
    
    print("\n1️⃣ Начинаем запись для Ostrovok...")
    success = manager.start_recording("ostrovok", "https://extranet.ostrovok.ru")
    
    if not success:
        print("❌ Не удалось начать запись")
        return
    
    print("✅ Запись начата!")
    print("🌐 Браузер открыт: https://extranet.ostrovok.ru")
    print("\n💡 Выполните простые действия:")
    print("   • Кликните на поле ввода email")
    print("   • Введите: {{email}}")
    print("   • Кликните на поле ввода пароля")
    print("   • Введите: {{password}}")
    print("   • Кликните на кнопку входа")
    
    input("\n⏸️ Нажмите Enter когда закончите...")
    
    print("\n2️⃣ Останавливаем запись...")
    filename = manager.stop_recording()
    
    if not filename:
        print("❌ Не удалось сохранить запись")
        return
    
    print(f"✅ Запись сохранена: {filename}")
    
    # Тестовые данные
    test_data = {
        'email': 'test@example.com',
        'password': 'test123'
    }
    
    print(f"\n3️⃣ Воспроизводим с данными: {test_data}")
    
    recorder = manager.get_recorder("ostrovok")
    success = recorder.load_recording(filename)
    
    if not success:
        print("❌ Не удалось загрузить запись")
        return
    
    print("🔄 Воспроизводим действия...")
    result = recorder.replay_actions(test_data, delay=2.0)
    
    if result:
        print("✅ Тест завершен успешно!")
        print("\n🎉 Система записи действий работает корректно!")
    else:
        print("❌ Тест завершен с ошибками")
        print("\n🔧 Проверьте логи для диагностики")

if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n\n⏹️ Тест прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("🔧 Проверьте, что Chrome установлен и доступен") 
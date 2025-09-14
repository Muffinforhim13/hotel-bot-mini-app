import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class BnovoManager:
    """Менеджер для работы с Bnovo PMS API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.pms.bnovo.ru"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_bookings(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Tuple[bool, List[Dict]]:
        """
        Получить список бронирований за период
        
        Args:
            date_from: Дата начала в формате YYYY-MM-DD
            date_to: Дата окончания в формате YYYY-MM-DD
            
        Returns:
            Tuple[bool, List[Dict]]: (успех, список бронирований)
        """
        try:
            # Если даты не указаны, берем текущий месяц
            if not date_from:
                date_from = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not date_to:
                date_to = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                date_to = date_to.strftime('%Y-%m-%d')
            
            # Убеждаемся, что date_from раньше date_to
            if date_from >= date_to:
                date_to = (datetime.strptime(date_from, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            
            params = {
                'date_from': date_from,
                'date_to': date_to,
                'limit': 20,   # Максимум 20 согласно API
                'offset': 0    # Обязательный параметр
            }
            
            response = requests.get(
                f"{self.base_url}/api/v1/bookings",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Проверяем структуру ответа
                if 'data' in response_data and 'bookings' in response_data['data']:
                    bookings = response_data['data']['bookings']
                    logger.info(f"Получено {len(bookings)} бронирований")
                    return True, bookings
                else:
                    logger.error(f"Неожиданная структура ответа: {response_data}")
                    return False, "Неожиданная структура ответа API"
            else:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при получении бронирований: {e}")
            return False, f"Ошибка соединения: {str(e)}"
    
    def get_booking_details(self, booking_id: str) -> Tuple[bool, Dict]:
        """
        Получить детальную информацию о бронировании
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Tuple[bool, Dict]: (успех, данные бронирования)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/bookings/{booking_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                booking = response.json()
                return True, booking
            else:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return False, f"Ошибка API: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ошибка при получении деталей бронирования: {e}")
            return False, f"Ошибка соединения: {str(e)}"
    
    def get_new_bookings(self, hours_back: int = 24) -> Tuple[bool, List[Dict]]:
        """
        Получить новые бронирования за последние N часов
        
        Args:
            hours_back: Количество часов назад для поиска
            
        Returns:
            Tuple[bool, List[Dict]]: (успех, список новых бронирований)
        """
        try:
            date_from = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d')
            date_to = datetime.now().strftime('%Y-%m-%d')
            
            return self.get_bookings(date_from, date_to)
            
        except Exception as e:
            logger.error(f"Ошибка при получении новых бронирований: {e}")
            return False, f"Ошибка: {str(e)}"
    
    def format_booking_message(self, booking: Dict) -> str:
        """
        Форматировать бронирование для отправки в Telegram
        
        Args:
            booking: Данные бронирования
            
        Returns:
            str: Отформатированное сообщение
        """
        try:
            # Извлекаем данные из ответа API (новая структура)
            customer = booking.get('customer', {})
            guest_name = f"{customer.get('name', '')} {customer.get('surname', '')}".strip()
            if not guest_name:
                guest_name = 'Не указано'
            
            room_name = booking.get('room_name', 'Не указано')
            dates = booking.get('dates', {})
            check_in = dates.get('arrival', 'Не указано')
            check_out = dates.get('departure', 'Не указано')
            
            # Форматируем даты
            if check_in != 'Не указано':
                try:
                    check_in = check_in.split('+')[0]  # Убираем часовой пояс
                    check_in = check_in.replace('T', ' ')
                except:
                    pass
            
            if check_out != 'Не указано':
                try:
                    check_out = check_out.split('+')[0]  # Убираем часовой пояс
                    check_out = check_out.replace('T', ' ')
                except:
                    pass
            
            amount = booking.get('amount', 'Не указано')
            if amount != 'Не указано':
                amount = f"{amount} ₽"
            
            status = booking.get('status', {})
            status_name = status.get('name', 'Не указано') if isinstance(status, dict) else str(status)
            
            source = booking.get('source', {})
            platform = source.get('name', 'Не указано') if isinstance(source, dict) else str(source)
            
            booking_id = booking.get('id', 'Не указано')
            booking_number = booking.get('number', '')
            
            message = f"🏨 **Бронирование #{booking_id}**\n"
            if booking_number:
                message += f"📋 **Номер:** {booking_number}\n"
            message += f"👤 **Гость:** {guest_name}\n"
            message += f"🏠 **Комната:** {room_name}\n"
            message += f"📅 **Заезд:** {check_in}\n"
            message += f"📅 **Выезд:** {check_out}\n"
            message += f"💰 **Сумма:** {amount}\n"
            message += f"📋 **Статус:** {status_name}\n"
            message += f"🌐 **Платформа:** {platform}\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка форматирования бронирования: {e}")
            return f"❌ Ошибка форматирования данных бронирования"
    
    def get_statistics(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Получить статистику по бронированиям
        
        Args:
            date_from: Дата начала
            date_to: Дата окончания
            
        Returns:
            Tuple[bool, Dict]: (успех, статистика)
        """
        try:
            success, bookings = self.get_bookings(date_from, date_to)
            if not success:
                return False, bookings
            
            if not isinstance(bookings, list):
                return False, "Неверный формат данных"
            
            # Подсчитываем статистику
            total_bookings = len(bookings)
            total_revenue = sum(float(booking.get('amount', 0)) for booking in bookings if booking.get('amount'))
            confirmed_bookings = len([b for b in bookings if b.get('status', {}).get('name') == 'Заселен'])
            
            # Группируем по платформам
            platforms = {}
            for booking in bookings:
                source = booking.get('source', {})
                platform = source.get('name', 'Неизвестно') if isinstance(source, dict) else str(source)
                if platform not in platforms:
                    platforms[platform] = {'count': 0, 'revenue': 0}
                platforms[platform]['count'] += 1
                platforms[platform]['revenue'] += float(booking.get('amount', 0))
            
            stats = {
                'total_bookings': total_bookings,
                'total_revenue': f"{total_revenue:.2f} ₽",
                'confirmed_bookings': confirmed_bookings,
                'platforms': platforms,
                'period': f"{date_from} - {date_to}" if date_from and date_to else "Текущий месяц"
            }
            
            return True, stats
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return False, f"Ошибка: {str(e)}"
    
    def format_statistics_message(self, stats: Dict) -> str:
        """
        Форматировать статистику для отправки в Telegram
        
        Args:
            stats: Данные статистики
            
        Returns:
            str: Отформатированное сообщение
        """
        try:
            message = f"📊 **Статистика за период:** {stats['period']}\n\n"
            message += f"📈 **Всего бронирований:** {stats['total_bookings']}\n"
            message += f"✅ **Подтверждено:** {stats['confirmed_bookings']}\n"
            message += f"💰 **Общая выручка:** {stats['total_revenue']}\n\n"
            
            if stats.get('platforms'):
                message += "🌐 **По платформам:**\n"
                for platform, data in stats['platforms'].items():
                    message += f"• {platform}: {data['count']} бронирований, {data['revenue']:.2f} ₽\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка форматирования статистики: {e}")
            return f"❌ Ошибка форматирования статистики"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Проверить подключение к API
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            # Используем правильные параметры для тестирования
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            
            response = requests.get(
                f"{self.base_url}/api/v1/bookings",
                headers=self.headers,
                params={
                    'date_from': tomorrow,
                    'date_to': day_after_tomorrow,
                    'limit': 20,
                    'offset': 0
                }
            )
            
            if response.status_code == 200:
                return True, "✅ Подключение к Bnovo PMS успешно"
            elif response.status_code == 401:
                return False, "❌ Неверный API ключ"
            else:
                return False, f"❌ Ошибка API: {response.status_code}"
                
        except Exception as e:
            return False, f"❌ Ошибка соединения: {str(e)}" 
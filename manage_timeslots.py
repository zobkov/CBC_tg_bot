#!/usr/bin/env python3
"""
Утилита для управления доступностью тайм-слотов в системе интервью.

Использование:
python3 manage_timeslots.py ДЕНЬ ВРЕМЯ_НАЧАЛА ВРЕМЯ_КОНЦА ДОСТУПНОСТЬ [--department НОМЕР]

Примеры:
python3 manage_timeslots.py 2025-10-09 09:00 12:00 0 --department 1
python3 manage_timeslots.py 2025-10-09 14:00 16:00 1
"""

import asyncio
import sys
import argparse
from datetime import datetime, date, time
from typing import List, Dict, Tuple, Optional

import asyncpg
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from app.infrastructure.database.dao.interview import InterviewDAO
from app.services.interview_google_sync import InterviewGoogleSheetsSync
from config.config import load_config


class TimeslotManager:
    """Менеджер для управления тайм-слотами"""
    
    def __init__(self, bot: Bot, db_conn: asyncpg.Connection):
        self.bot = bot
        self.db = db_conn
    
    async def find_nearest_timeslots(self, target_date: date, start_time: time, end_time: time, 
                                   department: Optional[int] = None) -> List[Dict]:
        """Найти ближайшие тайм-слоты к заданному временному отрезку"""
        
        base_query = """
        SELECT id, department_number, interview_date, start_time, is_available, reserved_by
        FROM interview_timeslots 
        WHERE interview_date = $1
        """
        params = [target_date]
        
        if department:
            base_query += " AND department_number = $2"
            params.append(department)
        
        base_query += " ORDER BY start_time"
        
        all_slots = await self.db.fetch(base_query, *params)
        
        # Фильтруем слоты в заданном временном диапазоне
        matching_slots = []
        for slot in all_slots:
            slot_time = slot['start_time']
            if start_time <= slot_time <= end_time:
                matching_slots.append({
                    'id': slot['id'],
                    'department_number': slot['department_number'],
                    'interview_date': slot['interview_date'],
                    'start_time': slot['start_time'],
                    'is_available': slot['is_available'],
                    'reserved_by': slot['reserved_by']
                })
        
        return matching_slots
    
    async def get_affected_users(self, timeslot_ids: List[int]) -> List[Dict]:
        """Получить пользователей, забронировавших указанные слоты"""
        if not timeslot_ids:
            return []
        
        query = """
        SELECT DISTINCT ts.reserved_by as user_id, a.full_name, a.telegram_username, 
               ts.id as timeslot_id, ts.interview_date, ts.start_time, ts.department_number
        FROM interview_timeslots ts
        LEFT JOIN applications a ON ts.reserved_by = a.user_id
        WHERE ts.id = ANY($1) AND ts.reserved_by IS NOT NULL
        """
        
        users = await self.db.fetch(query, timeslot_ids)
        return [dict(user) for user in users]
    
    async def update_timeslots_availability(self, timeslot_ids: List[int], is_available: bool) -> int:
        """Обновить доступность тайм-слотов"""
        if not timeslot_ids:
            return 0
        
        query = """
        UPDATE interview_timeslots 
        SET is_available = $1, updated = NOW()
        WHERE id = ANY($2)
        """
        
        result = await self.db.execute(query, is_available, timeslot_ids)
        # Extract number from result like "UPDATE 5"
        return int(result.split()[-1])
    
    async def reset_user_bookings(self, user_ids: List[int]) -> int:
        """Сбросить бронирования пользователей"""
        if not user_ids:
            return 0
        
        # Сначала получаем информацию о слотах, которые будут сброшены
        slots_query = """
        SELECT DISTINCT department_number, interview_date, start_time, reserved_by
        FROM interview_timeslots 
        WHERE reserved_by = ANY($1)
        """
        
        slots_to_sync = await self.db.fetch(slots_query, user_ids)
        
        # Теперь сбрасываем бронирования
        query = """
        UPDATE interview_timeslots 
        SET reserved_by = NULL, updated = NOW()
        WHERE reserved_by = ANY($1)
        """
        
        result = await self.db.execute(query, user_ids)
        updated_count = int(result.split()[-1])
        
        # Синхронизация с Google Sheets для каждого сброшенного слота
        if updated_count > 0 and slots_to_sync:
            try:
                dao = InterviewDAO(self.db)
                sync_service = InterviewGoogleSheetsSync(dao)
                
                for slot in slots_to_sync:
                    sync_task = asyncio.create_task(sync_service.sync_single_timeslot_change(
                        department_number=slot['department_number'],
                        slot_date=slot['interview_date'],
                        slot_time=slot['start_time'],
                        user_id=None  # None означает удаление бронирования
                    ))
                
                print(f"  🔄 Запущена синхронизация с Google Sheets для {len(slots_to_sync)} слотов")
            except Exception as e:
                print(f"  ⚠️  Ошибка синхронизации с Google Sheets: {e}")
        
        return updated_count
    
    async def send_notification_to_user(self, user_id: int) -> bool:
        """Отправить уведомление пользователю о недоступности времени"""
        try:
            message = (
                "К сожалению, время, которое ты выбрал, больше недоступно. "
                "Выбери, пожалуйста, новое время для собеседования."
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⏰ Выбрать время",
                    callback_data="reschedule_interview"
                )]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
            return False
    
    async def notify_affected_users(self, users: List[Dict]) -> Dict[str, int]:
        """Отправить уведомления всем затронутым пользователям"""
        stats = {"success": 0, "errors": 0}
        
        for user in users:
            user_id = user['user_id']
            username = user.get('telegram_username', 'no_username')
            
            print(f"📤 Отправка уведомления пользователю {user['full_name']} (@{username}, ID: {user_id})")
            
            success = await self.send_notification_to_user(user_id)
            if success:
                stats["success"] += 1
                print(f"  ✅ Уведомление отправлено")
            else:
                stats["errors"] += 1
                print(f"  ❌ Ошибка отправки")
        
        return stats


async def main():
    """Основная функция утилиты"""
    parser = argparse.ArgumentParser(
        description="Утилита для управления доступностью тайм-слотов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python3 manage_timeslots.py 2025-10-09 09:00 12:00 0 --department 1
    Отключить слоты с 09:00 до 12:00 на 9 октября для отдела 1
  
  python3 manage_timeslots.py 2025-10-10 14:00 16:00 1
    Включить слоты с 14:00 до 16:00 на 10 октября для всех отделов
        """
    )
    
    parser.add_argument("date", help="Дата в формате YYYY-MM-DD (например: 2025-10-09)")
    parser.add_argument("start_time", help="Время начала в формате HH:MM (например: 09:00)")
    parser.add_argument("end_time", help="Время окончания в формате HH:MM (например: 12:00)")
    parser.add_argument("availability", type=int, choices=[0, 1], 
                       help="Доступность: 0 = недоступно, 1 = доступно")
    parser.add_argument("--department", type=int, 
                       help="Номер отдела (1-6). Если не указан, применяется ко всем отделам")
    parser.add_argument("--dry-run", action="store_true",
                       help="Показать что будет изменено, но не применять изменения")
    
    args = parser.parse_args()
    
    # Валидация входных данных
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        start_time = datetime.strptime(args.start_time, "%H:%M").time()
        end_time = datetime.strptime(args.end_time, "%H:%M").time()
    except ValueError as e:
        print(f"❌ Ошибка формата: {e}")
        return 1
    
    if start_time >= end_time:
        print("❌ Время начала должно быть раньше времени окончания")
        return 1
    
    is_available = bool(args.availability)
    
    # Загрузка конфигурации
    config = load_config()
    bot = Bot(token=config.tg_bot.token)
    
    # Подключение к базе данных
    try:
        db_conn = await asyncpg.connect(
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password,
            database=config.db_applications.database,
        )
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return 1
    
    try:
        manager = TimeslotManager(bot, db_conn)
        
        print(f"🔍 Поиск тайм-слотов...")
        print(f"  Дата: {target_date}")
        print(f"  Время: {start_time} - {end_time}")
        print(f"  Отдел: {args.department if args.department else 'все отделы'}")
        print(f"  Новое состояние: {'доступно' if is_available else 'недоступно'}")
        
        # Найти подходящие тайм-слоты
        matching_slots = await manager.find_nearest_timeslots(
            target_date, start_time, end_time, args.department
        )
        
        if not matching_slots:
            print("❌ Не найдено подходящих тайм-слотов")
            return 1
        
        print(f"\n📋 Найдено {len(matching_slots)} подходящих тайм-слотов:")
        
        timeslot_ids = []
        reserved_slots = []
        
        for slot in matching_slots:
            slot_id = slot['id']
            dept = slot['department_number']
            slot_time = slot['start_time']
            available = slot['is_available']
            reserved = slot['reserved_by']
            
            status_emoji = "🟢" if available else "🔴"
            reserved_emoji = "🔒" if reserved else "🔓"
            
            print(f"  {status_emoji} {reserved_emoji} ID:{slot_id} | Отдел {dept} | {slot_time} | "
                  f"{'Доступен' if available else 'Недоступен'} | "
                  f"{'Забронирован' if reserved else 'Свободен'}")
            
            timeslot_ids.append(slot_id)
            if reserved:
                reserved_slots.append(slot_id)
        
        # Проверить затронутых пользователей
        affected_users = []
        if reserved_slots:
            affected_users = await manager.get_affected_users(reserved_slots)
            
            if affected_users:
                print(f"\n⚠️  ВНИМАНИЕ: {len(affected_users)} пользователей забронировали эти слоты:")
                for user in affected_users:
                    username = user.get('telegram_username', 'no_username')
                    print(f"  👤 {user['full_name']} (@{username}, ID: {user['user_id']}) | "
                          f"Слот {user['start_time']} в отделе {user['department_number']}")
                
                if not is_available:  # Если делаем слоты недоступными
                    if args.dry_run:
                        print("\n[DRY RUN] Этим пользователям будут отправлены уведомления")
                    else:
                        confirm = input(f"\n❓ Отправить уведомления {len(affected_users)} пользователям "
                                      f"и сбросить их бронирования? (да/yes/y): ").lower().strip()
                        
                        if confirm not in ['да', 'yes', 'y']:
                            print("❌ Операция отменена пользователем")
                            return 0
        
        # Применить изменения
        if args.dry_run:
            print(f"\n[DRY RUN] Было бы обновлено {len(timeslot_ids)} тайм-слотов")
            if affected_users and not is_available:
                print(f"[DRY RUN] Было бы сброшено {len(affected_users)} бронирований")
                print(f"[DRY RUN] Было бы отправлено {len(affected_users)} уведомлений")
        else:
            print(f"\n🔄 Обновление тайм-слотов...")
            
            # Обновить доступность
            updated_count = await manager.update_timeslots_availability(timeslot_ids, is_available)
            print(f"  ✅ Обновлено {updated_count} тайм-слотов")
            
            # Сбросить бронирования и уведомить пользователей
            if affected_users and not is_available:
                print(f"\n📤 Сброс бронирований и отправка уведомлений...")
                
                # Сбросить бронирования
                user_ids = [user['user_id'] for user in affected_users]
                reset_count = await manager.reset_user_bookings(user_ids)
                print(f"  ✅ Сброшено {reset_count} бронирований")
                
                # Отправить уведомления
                notification_stats = await manager.notify_affected_users(affected_users)
                print(f"  ✅ Уведомления: {notification_stats['success']} успешно, "
                      f"{notification_stats['errors']} ошибок")
        
        print(f"\n✅ Операция завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        await db_conn.close()
        await bot.session.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
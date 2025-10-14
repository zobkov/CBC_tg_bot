#!/usr/bin/env python3
"""
Анализ потерянных записей на интервью и экспорт в CSV
"""
import asyncio
import csv
import logging
from datetime import datetime, date, time
from typing import List, Dict, Any
import sys

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.infrastructure.database.dao.interview import InterviewDAO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Найденные потерянные записи из логов
LOST_BOOKINGS = [
    {
        "datetime": "2025-10-07 09:45:09",
        "user_id": 1795429556,
        "username": "aksinyaTS",
        "slot": "2025-10-13 09:20:00"
    },
    {
        "datetime": "2025-10-07 13:30:01",
        "user_id": 1792625920,
        "username": "Marriiammm",
        "slot": "2025-10-10 09:00:00"
    },
    {
        "datetime": "2025-10-07 15:35:52",
        "user_id": 1208741476,
        "username": "vmarikim",
        "slot": "2025-10-10 08:40:00"
    },
    {
        "datetime": "2025-10-07 15:53:03",
        "user_id": 1018109907,
        "username": "furleun",
        "slot": "2025-10-10 08:20:00"
    },
    {
        "datetime": "2025-10-08 15:44:37",
        "user_id": "unknown",  # Нужно найти в логах
        "username": "unknown",
        "slot": "2025-10-09 08:00:00"
    },
    {
        "datetime": "2025-10-08 20:51:42",
        "user_id": 1857783886,
        "username": "lubochkacat",
        "slot": "2025-10-11 09:00:00"
    }
]


class InterviewAnalysisService:
    """Service for analyzing interview bookings and Google Sheets sync issues"""
    
    def __init__(self, dao: InterviewDAO):
        self.dao = dao
        
    async def check_database_bookings(self) -> List[Dict[str, Any]]:
        """Get all current bookings from database"""
        async with self.dao.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT its.id, its.department_number, its.interview_date, its.start_time, 
                           its.reserved_by, a.full_name, a.telegram_username
                    FROM interview_timeslots its
                    LEFT JOIN applications a ON its.reserved_by = a.user_id
                    WHERE its.reserved_by IS NOT NULL
                    ORDER BY its.interview_date, its.start_time
                """)
                
                results = await cursor.fetchall()
                bookings = []
                
                for row in results:
                    bookings.append({
                        'timeslot_id': row[0],
                        'department_number': row[1],
                        'interview_date': row[2],
                        'start_time': row[3],
                        'user_id': row[4],
                        'full_name': row[5] or 'Unknown',
                        'telegram_username': row[6] or 'no_username'
                    })
                
                return bookings
    
    async def check_lost_bookings_in_db(self) -> Dict[str, Any]:
        """Check if lost bookings from logs are actually in the database"""
        results = {
            "found_in_db": [],
            "missing_from_db": [],
            "analysis": []
        }
        
        for lost_booking in LOST_BOOKINGS:
            if lost_booking["user_id"] == "unknown":
                continue
                
            # Check if this user has any booking
            current_booking = await self.dao.get_user_current_booking(lost_booking["user_id"])
            
            analysis_item = {
                "log_entry": lost_booking,
                "current_booking": current_booking,
                "status": "found" if current_booking else "missing"
            }
            
            if current_booking:
                results["found_in_db"].append(analysis_item)
                # Check if it matches the failed slot
                log_slot_date = lost_booking["slot"].split()[0]
                log_slot_time = lost_booking["slot"].split()[1]
                
                current_date = str(current_booking["interview_date"])
                current_time = str(current_booking["start_time"])
                
                if log_slot_date == current_date and log_slot_time == current_time:
                    analysis_item["match"] = "exact_match"
                else:
                    analysis_item["match"] = "different_slot"
                    analysis_item["note"] = f"Expected: {lost_booking['slot']}, Found: {current_date} {current_time}"
            else:
                results["missing_from_db"].append(analysis_item)
            
            results["analysis"].append(analysis_item)
        
        return results
    
    async def export_bookings_to_csv(self, filename: str = "interview_bookings.csv"):
        """Export all bookings to CSV in Google Sheets format"""
        bookings = await self.check_database_bookings()
        
        # Group by department
        departments = {}
        for booking in bookings:
            dept = booking['department_number']
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(booking)
        
        # Department mapping
        dept_names = {
            1: "Prog_exhib",
            2: "Art", 
            3: "Partners",
            4: "SMMPR",
            5: "Design",
            6: "Logistics"
        }
        
        # Create CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'Department', 'Department_Name', 'Date', 'Time', 
                'User_ID', 'Full_Name', 'Username', 'Timeslot_ID'
            ])
            
            # Data
            for dept_num, dept_bookings in departments.items():
                dept_name = dept_names.get(dept_num, f"Unknown_{dept_num}")
                
                for booking in dept_bookings:
                    writer.writerow([
                        dept_num,
                        dept_name,
                        booking['interview_date'],
                        booking['start_time'],
                        booking['user_id'],
                        booking['full_name'],
                        booking['telegram_username'],
                        booking['timeslot_id']
                    ])
        
        logger.info(f"✅ Exported {len(bookings)} bookings to {filename}")
        return filename
    
    async def diagnose_sync_issue(self):
        """Diagnose the root cause of Google Sheets sync issues"""
        
        # Check Google Sheets configuration
        from app.services.interview_google_sync import InterviewGoogleSheetsSync
        
        sync_service = InterviewGoogleSheetsSync(self.dao)
        
        print("🔍 Диагностика проблем синхронизации Google Sheets")
        print("=" * 60)
        
        # Check time slots configuration
        print("📅 Конфигурация временных слотов:")
        print(f"Поддерживаемые даты: {sync_service.DATES}")
        print(f"Поддерживаемые времена: {sync_service.TIME_SLOTS[:5]}...{sync_service.TIME_SLOTS[-5:]}")
        
        # Analyze failed slots
        print("\n❌ Анализ проваленных слотов:")
        for lost_booking in LOST_BOOKINGS:
            slot_datetime = lost_booking["slot"]
            try:
                # Parse the slot datetime
                dt = datetime.strptime(slot_datetime, "%Y-%m-%d %H:%M:%S")
                slot_date = dt.date()
                slot_time = dt.time()
                
                # Check if date is supported
                date_supported = slot_date in sync_service.DATES
                
                # Check if time is supported
                time_str = slot_time.strftime("%H:%M")
                time_supported = time_str in sync_service.TIME_SLOTS
                
                print(f"  • {slot_datetime}:")
                print(f"    - Дата поддерживается: {date_supported}")
                print(f"    - Время поддерживается: {time_supported}")
                if not date_supported:
                    print(f"    - ❌ Дата {slot_date} не в списке поддерживаемых!")
                if not time_supported:
                    print(f"    - ❌ Время {time_str} не в списке поддерживаемых!")
                
            except Exception as e:
                print(f"  • {slot_datetime}: ❌ Ошибка парсинга - {e}")


async def main():
    """Main function"""
    
    # Parse command line arguments
    export_csv = "--csv" in sys.argv
    analyze_lost = "--analyze" in sys.argv
    diagnose = "--diagnose" in sys.argv
    
    if not any([export_csv, analyze_lost, diagnose]):
        print("📊 Анализ записей на интервью")
        print("=" * 40)
        print("Доступные команды:")
        print("  --csv      Экспорт в CSV")
        print("  --analyze  Анализ потерянных записей")
        print("  --diagnose Диагностика проблем синхронизации")
        print("  --all      Выполнить все операции")
        return
    
    if "--all" in sys.argv:
        export_csv = analyze_lost = diagnose = True
    
    # Load config and setup connections
    config = load_config()
    
    # Setup database connection
    db_pool = await get_pg_pool(
        db_name=config.db_applications.database,
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password
    )
    
    dao = InterviewDAO(db_pool)
    analysis_service = InterviewAnalysisService(dao)
    
    try:
        if export_csv:
            print("\n📄 Экспорт записей в CSV...")
            filename = await analysis_service.export_bookings_to_csv()
            print(f"✅ Данные экспортированы в {filename}")
        
        if analyze_lost:
            print("\n🔍 Анализ потерянных записей...")
            results = await analysis_service.check_lost_bookings_in_db()
            
            print(f"\n📊 Результаты анализа:")
            print(f"Найдено в БД: {len(results['found_in_db'])}")
            print(f"Отсутствует в БД: {len(results['missing_from_db'])}")
            
            if results["found_in_db"]:
                print(f"\n✅ Записи, найденные в БД:")
                for item in results["found_in_db"]:
                    log_entry = item["log_entry"]
                    current = item["current_booking"]
                    print(f"  • {log_entry['username']} (ID: {log_entry['user_id']})")
                    print(f"    Ожидалось: {log_entry['slot']}")
                    print(f"    Найдено: {current['interview_date']} {current['start_time']}")
                    print(f"    Статус: {item.get('match', 'unknown')}")
            
            if results["missing_from_db"]:
                print(f"\n❌ Записи, отсутствующие в БД:")
                for item in results["missing_from_db"]:
                    log_entry = item["log_entry"]
                    print(f"  • {log_entry['username']} (ID: {log_entry['user_id']})")
                    print(f"    Слот: {log_entry['slot']}")
                    print(f"    Время лога: {log_entry['datetime']}")
        
        if diagnose:
            print("\n🔧 Диагностика проблем синхронизации...")
            await analysis_service.diagnose_sync_issue()
        
    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
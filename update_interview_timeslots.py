#!/usr/bin/env python3
"""
Script to clear old interview timeslots and populate new ones.
New structure: 5 days starting from October 9, 2025, with 20-minute intervals.
"""

import asyncio
import csv
from datetime import datetime, time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config import load_config
import psycopg_pool


async def clear_old_timeslots(pool):
    """Clear all existing timeslots from the database."""
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM interview_timeslots")
                await conn.commit()
                print("✅ Все старые тайм-слоты удалены")
    except Exception as e:
        print(f"❌ Ошибка при удалении старых тайм-слотов: {e}")
        raise


async def populate_timeslots_from_csv(pool, csv_file_path, department_id):
    """
    Populate timeslots from CSV file.
    
    Args:
        pool: Database connection pool
        csv_file_path: Path to CSV file
        department_id: Department ID for timeslots
    """
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                with open(csv_file_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    
                    # Parse dates from headers (skip first column "Время")
                    date_columns = list(reader.fieldnames)[1:]  # Skip "Время" column
                    
                    # Map dates to actual dates
                    dates = []
                    for date_str in date_columns:
                        # Parse "9 октября" -> 2025-10-09
                        day = int(date_str.split()[0])
                        month = 10  # октября = October
                        year = 2025
                        dates.append(f"{year}-{month:02d}-{day:02d}")
                    
                    print(f"📅 Обрабатываем даты: {dates}")
                    
                    timeslots_added = 0
                    
                    for row in reader:
                        time_str = row['Время']
                        
                        # Parse time (e.g., "10:00" -> time(10, 0))
                        hour, minute = map(int, time_str.split(':'))
                        slot_time = time(hour, minute)
                        
                        # Process each date column
                        for i, date_str in enumerate(dates):
                            availability = row[date_columns[i]]
                            is_available = availability.lower() == 'да'
                            
                            if is_available:
                                # Insert available timeslot
                                await cursor.execute("""
                                    INSERT INTO interview_timeslots 
                                    (interview_date, start_time, department_number, is_available, reserved_by) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (date_str, slot_time, department_id, True, None))
                                timeslots_added += 1
                    
                    await conn.commit()
                    print(f"✅ Добавлено {timeslots_added} доступных тайм-слотов для отдела {department_id}")
                    
    except Exception as e:
        print(f"❌ Ошибка при загрузке тайм-слотов из CSV: {e}")
        raise


async def create_timeslots_for_all_departments(pool, reference_csv_path):
    """
    Create the same timeslot pattern for all departments based on reference CSV.
    """
    # Department IDs mapping
    departments = {
        1: "Отдел программы",
        2: "Творческий отдел", 
        3: "Отдел партнёров",
        4: "Отдел SMM&PR",
        5: "Отдел дизайна",
        6: "Отдел логистики и ИТ",
        7: "Выставочный отдел"
    }
    
    for dept_id, dept_name in departments.items():
        print(f"\n📝 Создаем тайм-слоты для {dept_name} (ID: {dept_id})")
        await populate_timeslots_from_csv(pool, reference_csv_path, dept_id)


async def verify_timeslots(pool):
    """Verify the timeslots were created correctly."""
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:
                # Count total timeslots
                await cursor.execute("SELECT COUNT(*) FROM interview_timeslots")
                total_count = (await cursor.fetchone())[0]
                
                # Count by department
                await cursor.execute("""
                    SELECT department_number, COUNT(*) 
                    FROM interview_timeslots 
                    GROUP BY department_number 
                    ORDER BY department_number
                """)
                dept_counts = await cursor.fetchall()
                
                print(f"\n📊 Статистика тайм-слотов:")
                print(f"Всего слотов: {total_count}")
                print("По отделам:")
                for dept_id, count in dept_counts:
                    print(f"  Отдел {dept_id}: {count} слотов")
                    
    except Exception as e:
        print(f"❌ Ошибка при проверке тайм-слотов: {e}")


async def main():
    config = load_config()
    
    # Create connection pool
    connection_string = f"postgresql://{config.db_applications.user}:{config.db_applications.password}@{config.db_applications.host}:{config.db_applications.port}/{config.db_applications.database}"
    
    pool = psycopg_pool.AsyncConnectionPool(
        connection_string,
        min_size=1,
        max_size=3,
        open=False
    )
    
    await pool.open()
    
    try:
        print("🔄 Начинаем обновление тайм-слотов...")
        
        # Step 1: Clear old timeslots
        print("\n1️⃣ Удаляем старые тайм-слоты...")
        await clear_old_timeslots(pool)
        
        # Step 2: Create new timeslots for all departments
        print("\n2️⃣ Создаем новые тайм-слоты...")
        csv_path = "Запись тайм-слотов КБК26 - Артем З.csv"
        await create_timeslots_for_all_departments(pool, csv_path)
        
        # Step 3: Verify results
        print("\n3️⃣ Проверяем результаты...")
        await verify_timeslots(pool)
        
        print("\n✅ Обновление тайм-слотов завершено успешно!")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1
    finally:
        await pool.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
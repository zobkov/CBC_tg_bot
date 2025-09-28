#!/usr/bin/env python3
"""
Script to populate interview_timeslots table from logistics_timeslots.csv
"""
import asyncio
import csv
import os
from datetime import datetime, time, date
from typing import List, Tuple

import asyncpg
from config.config import load_config


async def load_timeslots_from_csv(csv_path: str, department_number: int = 6) -> List[Tuple[int, date, time, bool]]:
    """Load timeslots data from CSV file for specific department"""
    timeslots = []
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header: "Время,4 октября,5 октября,6 октября"
        
        # Extract dates from header
        dates = []
        for date_str in header[1:]:  # Skip "Время" column
            # Parse dates like "4 октября", "5 октября", "6 октября"
            day = int(date_str.split()[0])
            # Assuming October 2025 based on context
            dates.append(date(2025, 10, day))
        
        for row in reader:
            time_str = row[0]  # e.g., "8:00", "8:30"
            availability = row[1:]  # ["Нет", "Да", "Нет"]
            
            # Parse time
            hour, minute = map(int, time_str.split(':'))
            slot_time = time(hour, minute)
            
            # Create slots for specified department
            for i, available_str in enumerate(availability):
                is_available = available_str.strip().lower() == 'да'
                timeslots.append((department_number, dates[i], slot_time, is_available))
    
    return timeslots


async def populate_timeslots_table(csv_path: str = "logistics_timeslots.csv", department_number: int = 6, clear_existing: bool = True):
    """Populate interview_timeslots table with data from CSV"""
    config = load_config()
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return
    
    # Connect to database
    conn = await asyncpg.connect(
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password,
        database=config.db_applications.database,
    )
    
    try:
        # Load data from CSV
        print(f"Loading timeslots from {csv_path} for department {department_number}...")
        timeslots = await load_timeslots_from_csv(csv_path, department_number)
        print(f"Loaded {len(timeslots)} timeslots")
        
        # Clear existing data if requested
        if clear_existing:
            await conn.execute("DELETE FROM interview_timeslots WHERE department_number = $1", department_number)
            print(f"Cleared existing timeslots for department {department_number}")
        
        # Insert new data
        insert_query = """
        INSERT INTO interview_timeslots (department_number, interview_date, start_time, is_available)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (department_number, interview_date, start_time)
        DO UPDATE SET is_available = EXCLUDED.is_available
        """
        
        await conn.executemany(insert_query, timeslots)
        print(f"Successfully inserted/updated {len(timeslots)} timeslots")
        
        # Show summary
        summary_query = """
        SELECT department_number, interview_date, 
               COUNT(*) as total_slots,
               COUNT(*) FILTER (WHERE is_available) as available_slots
        FROM interview_timeslots 
        GROUP BY department_number, interview_date 
        ORDER BY department_number, interview_date
        """
        
        results = await conn.fetch(summary_query)
        print("\nSummary:")
        for row in results:
            print(f"Dept {row['department_number']}, {row['interview_date']}: "
                  f"{row['available_slots']}/{row['total_slots']} available slots")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    
    # Default values
    csv_path = "logistics_timeslots.csv"
    department_number = 6  # Логистика и ИТ
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            department_number = int(sys.argv[2])
        except ValueError:
            print(f"Invalid department number: {sys.argv[2]}")
            sys.exit(1)
    
    print(f"Using CSV: {csv_path}")
    print(f"Department: {department_number}")
    
    asyncio.run(populate_timeslots_table(csv_path, department_number))
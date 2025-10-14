#!/usr/bin/env python3
"""
Script to populate interview_timeslots table from CSV files in timeslots/ folder
This script updates the availability status of existing timeslots without deleting them.
"""
import asyncio
import csv
import os
import glob
from datetime import datetime, time, date
from typing import List, Tuple, Dict

import asyncpg
from config.config import load_config


# Mapping of CSV file prefixes to department numbers
DEPARTMENT_MAPPING = {
    "Art": 2,           # Творческий отдел
    "Design": 5,        # Отдел дизайна  
    "Logistics": 6,     # Отдел логистики и ИТ
    "Partners": 3,      # Отдел партнёров
    "Prog_exhib": 1,    # Отдел программы (+ Выставочный отдел объединены в dept 1)
    "SMMPR": 4          # Отдел SMM&PR
}


async def load_timeslots_from_csv(csv_path: str, department_number: int) -> List[Tuple[int, date, time, bool]]:
    """Load timeslots data from CSV file for specific department"""
    timeslots = []
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header: "Время,9 октября,10 октября,..."
        
        # Extract dates from header
        dates = []
        for date_str in header[1:]:  # Skip "Время" column
            # Parse dates like "9 октября", "10 октября", etc.
            day = int(date_str.split()[0])
            # Assuming October 2025 based on context
            dates.append(date(2025, 10, day))
        
        print(f"  Found dates: {[d.strftime('%Y-%m-%d') for d in dates]}")
        
        for row in reader:
            if not row or not row[0].strip():  # Skip empty rows
                continue
                
            time_str = row[0].strip()  # e.g., "8:00", "8:20"
            availability = row[1:]     # ["Нет", "Да", "Нет", ...]
            
            # Parse time
            try:
                hour, minute = map(int, time_str.split(':'))
                slot_time = time(hour, minute)
            except ValueError:
                print(f"  Warning: Invalid time format '{time_str}', skipping")
                continue
            
            # Create slots for specified department
            for i, available_str in enumerate(availability):
                if i >= len(dates):  # Skip if more columns than dates
                    break
                    
                is_available = available_str.strip().lower() == 'да'
                timeslots.append((department_number, dates[i], slot_time, is_available))
    
    return timeslots


async def ensure_all_timeslots_exist(conn: asyncpg.Connection, timeslots_from_csv: List[Tuple[int, date, time, bool]]):
    """Ensure all timeslots from CSV exist in database, create missing ones"""
    
    if not timeslots_from_csv:
        return
    
    department_number = timeslots_from_csv[0][0]  # Get department from first slot
    
    print(f"  Ensuring all {len(timeslots_from_csv)} timeslots exist for department {department_number}")
    
    # Insert all slots from CSV, ignore conflicts for existing ones
    insert_query = """
    INSERT INTO interview_timeslots (department_number, interview_date, start_time, is_available)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (department_number, interview_date, start_time) 
    DO UPDATE SET is_available = EXCLUDED.is_available, updated = NOW()
    """
    
    # Execute batch insert
    await conn.executemany(insert_query, timeslots_from_csv)
    
    # Check how many we have now
    total_count = await conn.fetchval(
        "SELECT COUNT(*) FROM interview_timeslots WHERE department_number = $1",
        department_number
    )
    
    print(f"  Department {department_number} now has {total_count} total timeslots")


async def update_timeslots_availability(csv_path: str, department_number: int, conn: asyncpg.Connection):
    """Update timeslot availability from CSV, creating missing slots as needed"""
    
    print(f"\nProcessing {csv_path} for department {department_number}...")
    
    # Load availability data from CSV
    timeslots = await load_timeslots_from_csv(csv_path, department_number)
    print(f"  Loaded {len(timeslots)} timeslots from CSV")
    
    if not timeslots:
        print(f"  No timeslots found in CSV, skipping")
        return
    
    # Ensure all timeslots from CSV exist in database
    await ensure_all_timeslots_exist(conn, timeslots)
    
    # Count how many slots are available
    available_count = sum(1 for _, _, _, is_available in timeslots if is_available)
    print(f"  CSV contains {available_count} available slots out of {len(timeslots)} total")
    
    # Show availability summary for this department
    summary_query = """
    SELECT interview_date, 
           COUNT(*) as total_slots,
           COUNT(*) FILTER (WHERE is_available) as available_slots
    FROM interview_timeslots 
    WHERE department_number = $1
    GROUP BY interview_date 
    ORDER BY interview_date
    """
    
    results = await conn.fetch(summary_query, department_number)
    print(f"  Final availability summary for department {department_number}:")
    total_available = 0
    total_slots = 0
    for row in results:
        available = row['available_slots']
        total = row['total_slots']
        total_available += available
        total_slots += total
        print(f"    {row['interview_date']}: {available}/{total} available slots")
    
    print(f"  Total for department {department_number}: {total_available}/{total_slots} available slots")


async def populate_all_timeslots(timeslots_dir: str = "timeslots"):
    """Populate all interview timeslots from CSV files in the specified directory"""
    config = load_config()
    
    if not os.path.exists(timeslots_dir):
        print(f"Error: Directory {timeslots_dir} not found")
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
        print(f"=== Updating interview timeslots from {timeslots_dir}/ ===\n")
        
        # Find all CSV files in timeslots directory
        csv_pattern = os.path.join(timeslots_dir, "*.csv")
        csv_files = glob.glob(csv_pattern)
        
        if not csv_files:
            print(f"No CSV files found in {timeslots_dir}/")
            return
        
        processed_departments = set()
        
        for csv_file in csv_files:
            filename = os.path.basename(csv_file)
            print(f"Found CSV file: {filename}")
            
            # Extract department identifier from filename
            department_number = None
            for prefix, dept_num in DEPARTMENT_MAPPING.items():
                if prefix in filename:
                    department_number = dept_num
                    break
            
            if department_number is None:
                print(f"  Warning: Could not determine department for {filename}, skipping")
                continue
            
            if department_number in processed_departments:
                print(f"  Warning: Department {department_number} already processed, skipping {filename}")
                continue
            
            try:
                await update_timeslots_availability(csv_file, department_number, conn)
                processed_departments.add(department_number)
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
        
        print(f"\n=== Summary ===")
        print(f"Processed {len(processed_departments)} departments: {sorted(processed_departments)}")
        
        # Show overall summary
        overall_summary_query = """
        SELECT department_number,
               COUNT(*) as total_slots,
               COUNT(*) FILTER (WHERE is_available) as available_slots,
               COUNT(*) FILTER (WHERE reserved_by IS NOT NULL) as reserved_slots
        FROM interview_timeslots 
        GROUP BY department_number 
        ORDER BY department_number
        """
        
        results = await conn.fetch(overall_summary_query)
        print(f"\nOverall timeslots summary:")
        for row in results:
            print(f"  Dept {row['department_number']}: "
                  f"{row['available_slots']} available, "
                  f"{row['reserved_slots']} reserved, "
                  f"{row['total_slots']} total")
    
    except Exception as e:
        print(f"Error: {e}")
        raise
    
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    
    # Default directory for timeslots CSV files
    timeslots_dir = "timeslots"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        timeslots_dir = sys.argv[1]
    
    print(f"Using timeslots directory: {timeslots_dir}")
    
    asyncio.run(populate_all_timeslots(timeslots_dir))
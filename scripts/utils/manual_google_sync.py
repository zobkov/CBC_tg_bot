#!/usr/bin/env python3
"""
Скрипт для ручной синхронизации всех записей с Google Sheets
"""
import asyncio
import logging
from typing import List, Dict, Any
import sys

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.infrastructure.database.dao.interview import InterviewDAO
from app.services.interview_google_sync import InterviewGoogleSheetsSync

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def manual_sync_all_bookings():
    """Manually sync all bookings to Google Sheets"""
    
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
    sync_service = InterviewGoogleSheetsSync(dao)
    
    try:
        # Get all current bookings
        async with db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT id, department_number, interview_date, start_time, reserved_by
                    FROM interview_timeslots 
                    WHERE reserved_by IS NOT NULL
                    ORDER BY interview_date, start_time
                """)
                
                bookings = await cursor.fetchall()
        
        logger.info(f"Found {len(bookings)} bookings to sync")
        
        success_count = 0
        error_count = 0
        
        for booking in bookings:
            timeslot_id, dept_num, interview_date, start_time, user_id = booking
            
            try:
                success = await sync_service.sync_single_timeslot_change(
                    department_number=dept_num,
                    slot_date=interview_date,
                    slot_time=start_time,
                    user_id=user_id
                )
                
                if success:
                    success_count += 1
                    logger.info(f"✅ Synced: {interview_date} {start_time} (dept {dept_num}, user {user_id})")
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to sync: {interview_date} {start_time} (dept {dept_num}, user {user_id})")
                
                # Longer delay to respect Google API quota (60 requests/minute)
                # With 1.5s delay, we make ~40 requests/minute, staying well under limit
                await asyncio.sleep(1.5)
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error syncing {interview_date} {start_time}: {e}")
        
        print(f"\n📊 Sync Results:")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Errors: {error_count}")
        print(f"📝 Total: {len(bookings)}")
        
    finally:
        await db_pool.close()


async def main():
    """Main function"""
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("🔄 Manual Google Sheets Sync Tool")
        print("=" * 40)
        print("This script syncs all current interview bookings to Google Sheets")
        print("Usage: python3 manual_google_sync.py [--dry-run]")
        print("")
        print("Options:")
        print("  --dry-run    Show what would be synced without actually syncing")
        print("  --help, -h   Show this help message")
        return
    
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🟡 DRY RUN MODE - No actual syncing will be performed")
        print("=" * 50)
        
        # Just show what would be synced
        config = load_config()
        db_pool = await get_pg_pool(
            db_name=config.db_applications.database,
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password
        )
        
        try:
            async with db_pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT its.id, its.department_number, its.interview_date, its.start_time, 
                               its.reserved_by, a.full_name, a.telegram_username
                        FROM interview_timeslots its
                        LEFT JOIN applications a ON its.reserved_by = a.user_id
                        WHERE its.reserved_by IS NOT NULL
                        ORDER BY its.interview_date, its.start_time
                    """)
                    
                    bookings = await cursor.fetchall()
                    
                    print(f"📊 Found {len(bookings)} bookings that would be synced:")
                    print()
                    
                    for booking in bookings:
                        timeslot_id, dept_num, interview_date, start_time, user_id, full_name, username = booking
                        print(f"  • {interview_date} {start_time} - Dept {dept_num}")
                        print(f"    {full_name} (@{username or 'no_username'}) [ID: {user_id}]")
                    
                    print(f"\n🔄 To perform actual sync, run without --dry-run")
        finally:
            await db_pool.close()
    else:
        print("🔄 Starting manual Google Sheets sync...")
        print("=" * 50)
        
        confirm = input("⚠️  This will sync ALL bookings to Google Sheets. Continue? (y/yes): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Sync cancelled")
            return
        
        await manual_sync_all_bookings()


if __name__ == "__main__":
    asyncio.run(main())
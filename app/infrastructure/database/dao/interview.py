"""
Data Access Object for interview timeslots management
"""
from datetime import date, time, datetime
from typing import List, Dict, Any, Optional

import psycopg_pool
from psycopg import AsyncConnection


class InterviewDAO:
    """DAO for managing interview timeslots and bookings"""
    
    def __init__(self, db_pool: psycopg_pool.AsyncConnectionPool):
        self.db_pool = db_pool
    
    async def get_user_approved_department(self, user_id: int) -> int:
        """Get the department number for which user was approved, 0 if not approved"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                # Get which position (1, 2, or 3) user was approved for
                await cursor.execute(
                    "SELECT approved FROM users WHERE user_id = %s",
                    (user_id,)
                )
                result = await cursor.fetchone()
                approved_position = result[0] if result else 0
                
                if not approved_position:
                    return 0
                    
                # Get the department for the approved position
                department_field = f"department_{approved_position}"
                
                await cursor.execute(f"""
                    SELECT {department_field} FROM applications WHERE user_id = %s
                """, (user_id,))
                result = await cursor.fetchone()
                department_name = result[0] if result else None
                
                if not department_name:
                    return 0
                    
                # Map department name to number
                # Note: Отдел программы (1) and Выставочный отдел (7) are merged into department 1
                dept_mapping = {
                    "Отдел программы": 1,
                    "Творческий отдел": 2, 
                    "Отдел партнёров": 3,
                    "Отдел SMM&PR": 4,
                    "Отдел дизайна": 5,
                    "Отдел логистики и ИТ": 6,
                    "Выставочный отдел": 1  # Merged with Отдел программы
                }
                
                return dept_mapping.get(department_name, 0)
    
    async def get_available_dates_for_department(self, department_number: int) -> List[date]:
        """Get list of dates that have available timeslots for given department"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT DISTINCT interview_date 
                    FROM interview_timeslots 
                    WHERE department_number = %s AND is_available = true
                    ORDER BY interview_date
                """, (department_number,))
                results = await cursor.fetchall()
                
                return [row[0] for row in results]
    
    async def get_available_timeslots_for_date(
        self, 
        department_number: int, 
        interview_date: date
    ) -> List[Dict[str, Any]]:
        """Get available timeslots for specific department and date"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT id, start_time, interview_date
                    FROM interview_timeslots 
                    WHERE department_number = %s 
                      AND interview_date = %s 
                      AND is_available = true
                      AND reserved_by IS NULL
                    ORDER BY start_time
                """, (department_number, interview_date))
                results = await cursor.fetchall()
                
                return [
                    {"id": row[0], "start_time": row[1], "interview_date": row[2]}
                    for row in results
                ]
    
    async def get_user_current_booking(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's current interview booking if any"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT id, interview_date, start_time, department_number
                    FROM interview_timeslots 
                    WHERE reserved_by = %s
                """, (user_id,))
                result = await cursor.fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "interview_date": result[1],
                        "start_time": result[2], 
                        "department_number": result[3]
                    }
                return None
    
    async def get_timeslot_by_id(self, timeslot_id: int) -> Optional[Dict[str, Any]]:
        """Get timeslot information by ID"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT id, department_number, interview_date, start_time, 
                           is_available, reserved_by
                    FROM interview_timeslots 
                    WHERE id = %s
                """, (timeslot_id,))
                result = await cursor.fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "department_number": result[1],
                        "interview_date": result[2],
                        "start_time": result[3],
                        "is_available": result[4],
                        "reserved_by": result[5]
                    }
                return None
    
    async def book_timeslot(self, user_id: int, timeslot_id: int) -> bool:
        """
        Book a timeslot for user. Returns True if successful, False if slot already taken.
        Also cancels any existing booking for this user.
        """
        async with self.db_pool.connection() as conn:
            async with conn.transaction():
                # First, cancel any existing booking for this user
                await self._cancel_user_booking_internal(conn, user_id)
                
                # Try to book the new slot
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        UPDATE interview_timeslots 
                        SET reserved_by = %s, 
                            is_available = false,
                            updated = NOW()
                        WHERE id = %s 
                          AND is_available = true 
                          AND reserved_by IS NULL
                    """, (user_id, timeslot_id))
                    
                    # Check if the update affected any rows
                    return cursor.rowcount > 0
    
    async def cancel_user_booking(self, user_id: int) -> bool:
        """Cancel user's current booking if any"""
        async with self.db_pool.connection() as conn:
            return await self._cancel_user_booking_internal(conn, user_id)
    
    async def _cancel_user_booking_internal(self, conn: AsyncConnection, user_id: int) -> bool:
        """Internal method to cancel user booking within existing connection/transaction"""
        async with conn.cursor() as cursor:
            await cursor.execute("""
                UPDATE interview_timeslots 
                SET reserved_by = NULL,
                    is_available = true,
                    updated = NOW()
                WHERE reserved_by = %s
            """, (user_id,))
            
            return cursor.rowcount > 0
    
    async def get_user_info_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's full name and username by user_id"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT first_name, last_name, username 
                    FROM users 
                    WHERE user_id = %s
                """, (user_id,))
                result = await cursor.fetchone()
                
                if result:
                    first_name = result[0] or ""
                    last_name = result[1] or ""
                    username = result[2] or ""
                    
                    # Build full name
                    full_name = f"{first_name} {last_name}".strip()
                    if not full_name:
                        full_name = f"User {user_id}"
                    
                    return {
                        "full_name": full_name,
                        "username": username or f"user{user_id}"
                    }
                return None

    async def get_department_timeslots_summary(
        self, 
        department_number: int
    ) -> List[Dict[str, Any]]:
        """Get summary of all timeslots for a department (for admin purposes)"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT interview_date, start_time, is_available, reserved_by
                    FROM interview_timeslots 
                    WHERE department_number = %s
                    ORDER BY interview_date, start_time
                """, (department_number,))
                results = await cursor.fetchall()
                
                return [
                    {
                        "interview_date": row[0],
                        "start_time": row[1],
                        "is_available": row[2],
                        "reserved_by": row[3]
                    }
                    for row in results
                ]
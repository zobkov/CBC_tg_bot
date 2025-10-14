"""
DAO for feedback operations
"""
from typing import List, Dict, Any, Optional
import psycopg_pool
from psycopg import AsyncConnection

from config.config import load_config


class FeedbackDAO:
    """Data Access Object for feedback operations"""
    
    def __init__(self, db_pool: psycopg_pool.AsyncConnectionPool):
        self.db_pool = db_pool
        self.config = load_config()
    
    async def get_user_feedback_positions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get positions with available feedback for user"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT 
                        a.department_1, a.subdepartment_1, a.position_1,
                        a.department_2, a.subdepartment_2, a.position_2,
                        a.department_3, a.subdepartment_3, a.position_3,
                        u.task_1_feedback, u.task_2_feedback, u.task_3_feedback,
                        u.approved
                    FROM applications a
                    LEFT JOIN evaluated_applications ea ON a.user_id = ea.user_id
                    LEFT JOIN users u ON a.user_id = u.user_id
                    WHERE a.user_id = %s
                      AND u.approved = 0
                """, (user_id,))
                result = await cursor.fetchone()
                
                if not result:
                    return []
                
                positions = []
                departments = self.config.selection.departments
                
                # Check each priority position for feedback
                for priority in [1, 2, 3]:
                    dept_idx = priority - 1  # 0-based index for result tuple
                    department_num = result[dept_idx * 3]     # department_X
                    subdepartment_num = result[dept_idx * 3 + 1]  # subdepartment_X  
                    position_num = result[dept_idx * 3 + 2]       # position_X
                    feedback_text = result[9 + priority - 1]      # task_X_feedback
                    
                    if department_num and feedback_text:
                        # Get department info
                        dept_info = departments.get(str(department_num), {})
                        dept_name = dept_info.get("name", f"{department_num}")
                        
                        # Get subdepartment info
                        subdept_name = ""
                        if subdepartment_num and subdepartment_num != 0:
                            subdepts = dept_info.get("subdepartments", {})
                            subdept_info = subdepts.get(str(subdepartment_num), {})
                            subdept_name = subdept_info.get("name", f"{subdepartment_num}")
                        
                        # Get position info
                        positions_list = dept_info.get("positions", [])
                        position_name = position_num if position_num else "Неизвестная позиция"
                        
                        # Build full position title
                        full_position = dept_name
                        if subdept_name:
                            full_position += f" - {subdept_name}"
                        full_position += f" - {position_name}"
                        
                        positions.append({
                            "priority": priority,
                            "department": department_num,
                            "subdepartment": subdepartment_num,
                            "position": position_num,
                            "full_title": full_position,
                            "has_feedback": True
                        })
                
                return positions
    
    async def get_feedback_for_position(self, user_id: int, priority: int) -> Dict[str, Any]:
        """Get feedback text for specific position priority"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                feedback_column = f"task_{priority}_feedback"
                
                await cursor.execute(f"""
                    SELECT {feedback_column}
                    FROM users 
                    WHERE user_id = %s
                """, (user_id,))
                result = await cursor.fetchone()
                
                if result and result[0]:
                    return {"feedback": result[0]}
                
                return {"feedback": None}
    
    async def get_users_with_submitted_tasks(self) -> List[Dict[str, Any]]:
        """Get all users who submitted at least one task"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT DISTINCT a.user_id, a.full_name, a.telegram_username,
                           COALESCE(u.approved, 0) as approved
                    FROM applications a
                    LEFT JOIN users u ON a.user_id = u.user_id
                    WHERE (u.task_1_submitted = true OR 
                           u.task_2_submitted = true OR 
                           u.task_3_submitted = true)
                """)
                results = await cursor.fetchall()
                
                users = []
                for result in results:
                    users.append({
                        "user_id": result[0],
                        "full_name": result[1],
                        "telegram_username": result[2],
                        "approved": result[3]
                    })
                
                return users
    
    async def get_single_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get single user data if they submitted tasks"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT a.user_id, a.full_name, a.telegram_username,
                           COALESCE(u.approved, 0) as approved
                    FROM applications a
                    LEFT JOIN users u ON a.user_id = u.user_id
                    WHERE a.user_id = %s 
                      AND (u.task_1_submitted = true OR 
                           u.task_2_submitted = true OR 
                           u.task_3_submitted = true)
                """, (user_id,))
                result = await cursor.fetchone()
                
                if result:
                    return {
                        "user_id": result[0],
                        "full_name": result[1],
                        "telegram_username": result[2],
                        "approved": result[3]
                    }
                
                return None
    
    async def get_approved_user_position(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get approved position info for user"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT 
                        a.department_1, a.subdepartment_1, a.position_1,
                        a.department_2, a.subdepartment_2, a.position_2,
                        a.department_3, a.subdepartment_3, a.position_3,
                        u.approved
                    FROM applications a
                    LEFT JOIN users u ON a.user_id = u.user_id
                    WHERE a.user_id = %s AND CAST(u.approved AS INTEGER) > 0
                """, (user_id,))
                result = await cursor.fetchone()
                
                if not result:
                    return None
                
                approved_priority = int(result[9]) if result[9] else 0  # approved column
                if approved_priority and 1 <= approved_priority <= 3:
                    dept_idx = (approved_priority - 1) * 3
                    department_num = result[dept_idx]
                    subdepartment_num = result[dept_idx + 1]
                    position_num = result[dept_idx + 2]
                    
                    departments = self.config.selection.departments
                    dept_info = departments.get(str(department_num), {})
                    dept_name = dept_info.get("name", f"{department_num}")
                    
                    # Get subdepartment info
                    subdept_name = ""
                    if subdepartment_num and subdepartment_num != 0:
                        subdepts = dept_info.get("subdepartments", {})
                        subdept_info = subdepts.get(str(subdepartment_num), {})
                        subdept_name = subdept_info.get("name", f"{subdepartment_num}")
                    
                    # Get position info
                    position_name = position_num if position_num else "Неизвестная позиция"
                    
                    # Build full position title
                    full_position = dept_name
                    if subdept_name:
                        full_position += f" - {subdept_name}"
                    full_position += f" - {position_name}"
                    
                    return {
                        "department": department_num,
                        "subdepartment": subdepartment_num,
                        "position": position_num,
                        "full_title": full_position,
                        "priority": approved_priority
                    }
                
                return None
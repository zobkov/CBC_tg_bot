#!/usr/bin/env python3
"""
Script to update users approved status based on CSV file with approved candidates
"""
import asyncio
import csv
import logging
import os
import json
from typing import Dict, Optional

import asyncpg
from config.config import load_config


def get_department_number_by_name(dept_name: str, subdept_name: str = "") -> int:
    """Get department number by department and subdepartment names"""
    
    # Mapping from department names to numbers
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
    
    dept_number = dept_mapping.get(dept_name, 0)
    
    # For departments with subdepartments, we need to distinguish them
    # But since approved column stores which priority position (1-3) was approved,
    # we'll return the base department number for now
    # The actual position matching should be done through applications table
    
    return dept_number


async def get_user_approved_position_number(
    conn: asyncpg.Connection, 
    user_id: int, 
    target_dept_name: str, 
    target_subdept_name: str,
    target_position: str
) -> int:
    """
    Get which position number (1, 2, or 3) corresponds to the approved department/position
    by looking at the user's application priorities
    """
    
    # Get user's application with all 3 priority choices
    app = await conn.fetchrow("""
        SELECT department_1, subdepartment_1, position_1,
               department_2, subdepartment_2, position_2, 
               department_3, subdepartment_3, position_3
        FROM applications 
        WHERE user_id = $1
    """, user_id)
    
    if not app:
        print(f"Warning: No application found for user {user_id}")
        return 0
    
    # Check each priority position to see which one matches the approved position
    for i in range(1, 4):
        app_dept = app[f"department_{i}"]
        app_subdept = app[f"subdepartment_{i}"] or ""
        app_position = app[f"position_{i}"]
        
        # Compare with target (approved) position
        if (app_dept == target_dept_name and 
            app_subdept == target_subdept_name and 
            app_position == target_position):
            return i
    
    # If no exact match found, try to match by department only (for flexibility)
    for i in range(1, 4):
        app_dept = app[f"department_{i}"]
        if app_dept == target_dept_name:
            print(f"Warning: Partial match for user {user_id} - dept matches but position differs")
            return i
    
    print(f"Warning: No matching position found for user {user_id}")
    return 0


async def load_approved_from_csv(csv_path: str) -> tuple[list, list]:
    """Load approved candidates and rejected candidates with feedback from CSV file"""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return [], []
    
    approved_candidates = []
    rejected_candidates = []
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                user_id = int(row["ID"])
                username = row.get("Username", "")
                department = row.get("Отдел", "")
                subdepartment = row.get("Подотдел", "")
                position = row.get("Вакансия", "")
                approved = row.get("Одобрен", "").strip()
                feedback = row.get("Обратная связь – ГОТОВО", "").strip()
                
                candidate_data = {
                    "user_id": user_id,
                    "username": username,
                    "department": department,
                    "subdepartment": subdepartment,
                    "position": position,
                    "feedback": feedback
                }
                
                # Check if approved
                if approved.lower() in ["да", "yes", "1", "true"]:
                    approved_candidates.append(candidate_data)
                else:
                    # Add to rejected list if there's feedback
                    if feedback:
                        rejected_candidates.append(candidate_data)
                
            except (ValueError, KeyError) as e:
                print(f"Error parsing row: {row}, error: {e}")
                continue
    
    return approved_candidates, rejected_candidates


async def update_task_feedback(conn, user_id: int, department: str, subdepartment: str, position: str, feedback: str):
    """Update task feedback for rejected candidate"""
    try:
        # Find which priority position (1, 2, or 3) this corresponds to
        position_number = await get_user_approved_position_number(
            conn, user_id, department, subdepartment, position
        )
        
        if position_number == 0:
            print(f"Could not match position for feedback - user {user_id}")
            return False
        
        # Update appropriate feedback column
        feedback_column = f"task_{position_number}_feedback"
        
        result = await conn.execute(f"""
            UPDATE users 
            SET {feedback_column} = $1 
            WHERE user_id = $2
        """, feedback, user_id)
        
        if result == "UPDATE 1":
            print(f"✅ Updated feedback for user {user_id}: {feedback_column} = '{feedback[:50]}...'")
            return True
        else:
            print(f"⚠️ User {user_id} not found for feedback update")
            return False
            
    except Exception as e:
        print(f"❌ Error updating feedback for user {user_id}: {e}")
        return False


async def update_approved_status_from_csv(csv_path: str = "approved_candidates.csv"):
    """Update approved status for users based on CSV file"""
    config = load_config()
    
    # Connect to database
    conn = await asyncpg.connect(
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password,
        database=config.db_applications.database,
    )
    
    try:
        # Load approved candidates and rejected with feedback from CSV
        print(f"Loading candidates from {csv_path}...")
        approved_candidates, rejected_candidates = await load_approved_from_csv(csv_path)
        
        print(f"Found {len(approved_candidates)} approved candidates")
        print(f"Found {len(rejected_candidates)} rejected candidates with feedback")
        
        # Reset all users to not approved first
        await conn.execute("UPDATE users SET approved = 0")
        print("Reset all users to not approved")
        
        # Process approved candidates
        updated_count = 0
        errors_count = 0
        
        for candidate in approved_candidates:
            try:
                user_id = candidate["user_id"]
                department = candidate["department"]
                subdepartment = candidate["subdepartment"]
                position = candidate["position"]
                
                # Find which priority position (1, 2, or 3) this corresponds to
                approved_position = await get_user_approved_position_number(
                    conn, user_id, department, subdepartment, position
                )
                
                if approved_position == 0:
                    print(f"Could not match position for user {user_id} ({candidate['username']})")
                    errors_count += 1
                    continue
                
                # Update user's approved status
                result = await conn.execute("""
                    UPDATE users 
                    SET approved = $1 
                    WHERE user_id = $2
                """, approved_position, user_id)
                
                if result == "UPDATE 1":
                    updated_count += 1
                    print(f"✅ Updated user {user_id} ({candidate['username']}): approved = {approved_position} ({department} - {position})")
                else:
                    print(f"⚠️ User {user_id} not found in users table")
                    errors_count += 1
                
            except Exception as e:
                print(f"❌ Error updating user {candidate.get('user_id', 'unknown')}: {e}")
                errors_count += 1
        
        # Process rejected candidates with feedback
        feedback_updated_count = 0
        
        print(f"\n📝 Processing feedback for rejected candidates...")
        for candidate in rejected_candidates:
            try:
                user_id = candidate["user_id"]
                department = candidate["department"]
                subdepartment = candidate["subdepartment"]
                position = candidate["position"]
                feedback = candidate["feedback"]
                
                success = await update_task_feedback(
                    conn, user_id, department, subdepartment, position, feedback
                )
                
                if success:
                    feedback_updated_count += 1
                else:
                    errors_count += 1
                
            except Exception as e:
                print(f"❌ Error updating feedback for user {candidate.get('user_id', 'unknown')}: {e}")
                errors_count += 1
        
        print(f"\n📊 Summary:")
        print(f"✅ Successfully updated approved status: {updated_count} users")
        print(f"✅ Successfully updated feedback: {feedback_updated_count} users")
        print(f"❌ Errors: {errors_count}")
        
        # Show approval statistics
        summary = await conn.fetch("""
            SELECT approved, COUNT(*) as count
            FROM users
            WHERE approved > 0
            GROUP BY approved
            ORDER BY approved
        """)
        
        print(f"\n📈 Approval statistics:")
        for row in summary:
            print(f"Position {row['approved']}: {row['count']} users approved")
        
        total_approved = await conn.fetchval("""
            SELECT COUNT(*) FROM users WHERE approved > 0
        """)
        
        # Show feedback statistics
        feedback_summary = await conn.fetch("""
            SELECT 
                COUNT(CASE WHEN task_1_feedback IS NOT NULL THEN 1 END) as task_1_feedback_count,
                COUNT(CASE WHEN task_2_feedback IS NOT NULL THEN 1 END) as task_2_feedback_count,
                COUNT(CASE WHEN task_3_feedback IS NOT NULL THEN 1 END) as task_3_feedback_count
            FROM users
        """)
        
        print(f"\n📝 Feedback statistics:")
        for row in feedback_summary:
            print(f"Task 1 feedback: {row['task_1_feedback_count']} users")
            print(f"Task 2 feedback: {row['task_2_feedback_count']} users")
            print(f"Task 3 feedback: {row['task_3_feedback_count']} users")
        
        print(f"Total approved users: {total_approved}")
    
    except Exception as e:
        print(f"Error: {e}")
        raise
    
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Allow custom CSV path as command line argument
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "approved_candidates.csv"
    
    if not os.path.exists(csv_path):
        print(f"Available CSV files:")
        for file in os.listdir("."):
            if file.endswith(".csv"):
                print(f"  - {file}")
        print(f"\nUsage: python {sys.argv[0]} [csv_file_path]")
        print(f"Default: {csv_path}")
        sys.exit(1)
    
    asyncio.run(update_approved_status_from_csv(csv_path))
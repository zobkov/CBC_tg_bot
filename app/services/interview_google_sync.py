"""
Service for syncing interview timeslots with Google Sheets
"""
import asyncio
import random
from datetime import date, time, datetime
from typing import Dict, List, Optional, Any
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

from config.config import load_config
from app.infrastructure.database.dao.interview import InterviewDAO

logger = logging.getLogger(__name__)


class InterviewGoogleSheetsSync:
    """Service for syncing interview timeslots with Google Sheets"""
    
    # Mapping from department numbers to sheet names
    DEPARTMENT_SHEET_MAPPING = {
        1: "Prog_exhib",    # Отдел программы + Выставочный отдел
        2: "Art",           # Творческий отдел
        3: "Partners",      # Отдел партнёров
        4: "SMMPR",         # Отдел SMM&PR
        5: "Design",        # Отдел дизайна
        6: "Logistics"      # Отдел логистики и ИТ
    }
    
    # Time slots corresponding to rows in Google Sheets (starting from row 2)
    TIME_SLOTS = [
        "8:00", "8:20", "8:40", "9:00", "9:20", "9:40",
        "10:00", "10:20", "10:40", "11:00", "11:20", "11:40",
        "12:00", "12:20", "12:40", "13:00", "13:20", "13:40",
        "14:00", "14:20", "14:40", "15:00", "15:20", "15:40",
        "16:00", "16:20", "16:40", "17:00", "17:20", "17:40",
        "18:00", "18:20", "18:40", "19:00", "19:20", "19:40",
        "20:00", "20:20", "20:40", "21:00", "21:20", "21:40",
        "22:00", "22:20", "22:40", "23:00", "23:20", "23:40"
    ]
    
    # Date columns (B, D, F, H, J for 9-13 October)
    DATE_COLUMNS = ['B', 'D', 'F', 'H', 'J']
    # Tag columns (C, E, G, I, K for usernames)
    TAG_COLUMNS = ['C', 'E', 'G', 'I', 'K']
    
    # Dates for October 2025
    DATES = [
        date(2025, 10, 9),   # 9 октября
        date(2025, 10, 10),  # 10 октября
        date(2025, 10, 11),  # 11 октября
        date(2025, 10, 12),  # 12 октября
        date(2025, 10, 13)   # 13 октября
    ]
    
    def __init__(self, dao: InterviewDAO):
        self.dao = dao
        self.config = load_config()
        self.spreadsheet_id = "1lEqpkUwnqtZuT2zKWFSwNTYfZflZx3qX6Cc3WQz38dU"
        self.service = None
        
    async def _get_service(self):
        """Get Google Sheets service client"""
        if self.service is None:
            try:
                credentials = Credentials.from_service_account_file(
                    self.config.google.credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=credentials)
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets service: {e}")
                raise
                
        return self.service
    
    async def _execute_with_retry(self, request_builder, max_retries: int = 3):
        """Execute Google Sheets request with exponential backoff for quota limits"""
        for attempt in range(max_retries + 1):
            try:
                return request_builder().execute()
            except HttpError as e:
                if e.resp.status == 429:  # Rate limit exceeded
                    if attempt < max_retries:
                        # Exponential backoff with jitter
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limit exceeded, waiting {delay:.2f} seconds before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} retries")
                        raise
                else:
                    # For other errors, don't retry
                    raise
        return None

    def _time_to_row(self, slot_time: time) -> int:
        """Convert time to row number (1-indexed)"""
        # Format time without leading zero for hours to match TIME_SLOTS format
        time_str = f"{slot_time.hour}:{slot_time.minute:02d}"
        if time_str in self.TIME_SLOTS:
            return self.TIME_SLOTS.index(time_str) + 2  # +2 because rows start from 2
        return -1
    
    def _date_to_column_index(self, slot_date: date) -> int:
        """Convert date to column index (0-4 for 9-13 October)"""
        if slot_date in self.DATES:
            return self.DATES.index(slot_date)
        return -1
    
    async def _get_user_info(self, user_id: int) -> Dict[str, str]:
        """Get user's full name and username from database"""
        try:
            user_info = await self.dao.get_user_info_by_id(user_id)
            if user_info:
                return user_info
            else:
                return {
                    "full_name": f"User {user_id}",
                    "username": f"user{user_id}"
                }
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
            return {
                "full_name": f"User {user_id}",
                "username": f"user{user_id}"
            }
    
    async def sync_department_timeslots(self, department_number: int) -> bool:
        """Sync all timeslots for a specific department to Google Sheets"""
        try:
            sheet_name = self.DEPARTMENT_SHEET_MAPPING.get(department_number)
            if not sheet_name:
                logger.warning(f"No sheet mapping found for department {department_number}")
                return False
                
            logger.info(f"Syncing timeslots for department {department_number} to sheet {sheet_name}")
            
            # Get all timeslots for this department
            timeslots = await self._get_department_timeslots(department_number)
            
            # Build the update data
            updates = await self._build_sheet_updates(timeslots)
            
            # Apply updates to Google Sheets
            return await self._apply_batch_update(sheet_name, updates)
            
        except Exception as e:
            logger.error(f"Error syncing department {department_number} timeslots: {e}")
            return False
    
    async def _get_department_timeslots(self, department_number: int) -> List[Dict[str, Any]]:
        """Get all timeslots for a department from database"""
        try:
            # Use the DAO to get timeslots summary
            timeslots = await self.dao.get_department_timeslots_summary(department_number)
            
            # Add user info for booked slots
            enhanced_timeslots = []
            for slot in timeslots:
                enhanced_slot = dict(slot)
                if slot["reserved_by"]:
                    user_info = await self._get_user_info(slot["reserved_by"])
                    enhanced_slot["user_full_name"] = user_info["full_name"]
                    enhanced_slot["user_username"] = user_info["username"]
                else:
                    enhanced_slot["user_full_name"] = ""
                    enhanced_slot["user_username"] = ""
                enhanced_timeslots.append(enhanced_slot)
                
            return enhanced_timeslots
            
        except Exception as e:
            logger.error(f"Error getting timeslots for department {department_number}: {e}")
            return []
    
    async def _build_sheet_updates(self, timeslots: List[Dict[str, Any]]) -> Dict[str, List[List[str]]]:
        """Build the data structure for batch update to Google Sheets"""
        # Initialize empty grid: 48 rows x 10 columns (B2:K49)
        # Columns: B(name), C(tag), D(name), E(tag), F(name), G(tag), H(name), I(tag), J(name), K(tag)
        grid = [["" for _ in range(10)] for _ in range(48)]
        
        # Fill grid with timeslot data
        for slot in timeslots:
            slot_time = slot["start_time"]
            slot_date = slot["interview_date"]
            
            row_index = self._time_to_row(slot_time) - 2  # Convert to 0-based index
            col_index = self._date_to_column_index(slot_date)
            
            if row_index >= 0 and col_index >= 0:
                # Name column (even indices: 0, 2, 4, 6, 8)
                name_col = col_index * 2
                # Tag column (odd indices: 1, 3, 5, 7, 9)
                tag_col = col_index * 2 + 1
                
                if slot["reserved_by"]:
                    grid[row_index][name_col] = slot["user_full_name"]
                    grid[row_index][tag_col] = slot["user_username"]
                else:
                    grid[row_index][name_col] = ""
                    grid[row_index][tag_col] = ""
        
        return {"B2:K49": grid}
    
    async def _apply_batch_update(self, sheet_name: str, updates: Dict[str, List[List[str]]]) -> bool:
        """Apply batch update to Google Sheets"""
        try:
            service = await self._get_service()
            
            # Prepare batch update request
            batch_update_data = []
            
            for range_name, values in updates.items():
                full_range = f"{sheet_name}!{range_name}"
                batch_update_data.append({
                    'range': full_range,
                    'values': values
                })
            
            # Execute batch update with retry mechanism
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': batch_update_data
            }
            
            result = await self._execute_with_retry(
                lambda: service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                )
            )
            
            logger.info(f"Successfully updated {len(batch_update_data)} ranges in sheet {sheet_name}")
            logger.debug(f"Update result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying batch update to sheet {sheet_name}: {e}")
            return False
    
    async def sync_all_departments(self) -> Dict[int, bool]:
        """Sync all departments to their respective sheets"""
        results = {}
        
        for dept_number in self.DEPARTMENT_SHEET_MAPPING.keys():
            success = await self.sync_department_timeslots(dept_number)
            results[dept_number] = success
            
            # Add small delay between requests to avoid rate limiting
            await asyncio.sleep(0.5)
        
        return results
    
    async def sync_single_timeslot_change(
        self, 
        department_number: int, 
        slot_date: Any, 
        slot_time: Any,
        user_id: Optional[int] = None
    ) -> bool:
        """Sync a single timeslot change (booking/cancellation)"""
        try:
            # Convert inputs to proper types
            if isinstance(slot_date, str):
                slot_date = datetime.strptime(slot_date, "%Y-%m-%d").date()
            elif hasattr(slot_date, 'date'):  # datetime object
                slot_date = slot_date.date()
            
            if isinstance(slot_time, str):
                # Handle both HH:MM and HH:MM:SS formats
                if len(slot_time) > 5:  # HH:MM:SS format
                    slot_time = datetime.strptime(slot_time, "%H:%M:%S").time()
                else:  # HH:MM format
                    slot_time = datetime.strptime(slot_time, "%H:%M").time()
            elif hasattr(slot_time, 'time'):  # datetime object
                slot_time = slot_time.time()
            
            sheet_name = self.DEPARTMENT_SHEET_MAPPING.get(department_number)
            if not sheet_name:
                logger.warning(f"No sheet mapping found for department {department_number}")
                return False
                
            row_num = self._time_to_row(slot_time)
            col_index = self._date_to_column_index(slot_date)
            
            if row_num < 0 or col_index < 0:
                logger.warning(f"Invalid time slot: {slot_date} {slot_time} (row: {row_num}, col: {col_index})")
                logger.warning(f"Available dates: {self.DATES}")
                logger.warning(f"Available times: {self.TIME_SLOTS}")
                return False
            
            # Get column letters for name and username
            name_col = self.DATE_COLUMNS[col_index]
            tag_col = self.TAG_COLUMNS[col_index]
            
            name_value = ""
            tag_value = ""
            
            if user_id:
                user_info = await self._get_user_info(user_id)
                name_value = user_info["full_name"]
                tag_value = user_info["username"]
            
            # Update both cells
            service = await self._get_service()
            
            batch_update_data = [
                {
                    'range': f"{sheet_name}!{name_col}{row_num}",
                    'values': [[name_value]]
                },
                {
                    'range': f"{sheet_name}!{tag_col}{row_num}",
                    'values': [[tag_value]]
                }
            ]
            
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': batch_update_data
            }
            
            # Use retry mechanism for API call
            result = await self._execute_with_retry(
                lambda: service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                )
            )
            
            logger.info(f"Successfully updated single timeslot in {sheet_name}: {slot_date} {slot_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing single timeslot change: {e}")
            return False
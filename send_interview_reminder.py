#!/usr/bin/env python3
"""
Рассылка напоминания о записи на интервью для одобренных пользователей без слота
"""
import asyncio
import logging
from typing import List, Dict, Any
import sys

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.infrastructure.database.dao.interview import InterviewDAO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Сообщение для рассылки
REMINDER_MESSAGE = """🔔 <b>Последний звонок!</b>

До конца регистрации на онлайн-собеседование осталось меньше 30 минут — успей выбрать удобное время!"""


class InterviewReminderService:
    """Service for sending interview reminder to approved users without timeslot"""
    
    def __init__(self, bot: Bot, dao: InterviewDAO):
        self.bot = bot
        self.dao = dao
        
    async def get_approved_users_without_timeslot(self) -> List[Dict[str, Any]]:
        """Get all approved users who haven't selected a timeslot"""
        async with self.dao.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                # Получаем одобренных пользователей без забронированного слота
                await cursor.execute("""
                    SELECT u.user_id, a.full_name, a.telegram_username, u.approved
                    FROM users u
                    LEFT JOIN applications a ON u.user_id = a.user_id
                    WHERE u.approved IS NOT NULL 
                      AND u.approved != 0
                      AND NOT EXISTS (
                          SELECT 1 FROM interview_timeslots its 
                          WHERE its.reserved_by = u.user_id
                      )
                    ORDER BY u.user_id
                """)
                
                results = await cursor.fetchall()
                users = []
                
                for row in results:
                    users.append({
                        'user_id': row[0],
                        'full_name': row[1] or 'Unknown',
                        'telegram_username': row[2] or 'no_username',
                        'approved': row[3]
                    })
                
                return users
    
    async def send_reminder_message(self, user_id: int) -> bool:
        """Send reminder message to user"""
        try:
            # Create inline keyboard with personal cabinet button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🏠 Личный кабинет",
                    callback_data="go_to_main_menu"
                )]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=REMINDER_MESSAGE,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logger.info(f"✅ Reminder sent to user {user_id}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"❌ User {user_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"❌ Bad request for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending reminder to {user_id}: {e}")
            return False
    
    async def send_reminders(self, dry_run: bool = True, test_user_ids: List[int] = None) -> Dict[str, int]:
        """Send reminders to eligible users or specific test users"""
        
        if test_user_ids:
            logger.info(f"🧪 Starting TEST reminder for users: {test_user_ids}")
            # Get specific test users and check if they are approved and have no timeslot
            users = []
            all_approved_users = await self.get_approved_users_without_timeslot()
            for user_id in test_user_ids:
                user_data = next((u for u in all_approved_users if u['user_id'] == user_id), None)
                if user_data:
                    users.append(user_data)
                else:
                    logger.warning(f"⚠️ Test user {user_id} not eligible (not approved or already has timeslot)")
        else:
            logger.info("🚀 Starting interview reminder broadcast...")
            users = await self.get_approved_users_without_timeslot()
        
        logger.info(f"📊 Found {len(users)} eligible users to process")
        
        stats = {
            "total_users": len(users),
            "messages_sent": 0,
            "errors": 0
        }
        
        for user in users:
            user_id = user["user_id"]
            
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would send reminder to user {user_id} - {user['full_name']} (@{user['telegram_username']})")
                    stats["messages_sent"] += 1
                else:
                    success = await self.send_reminder_message(user_id)
                    if success:
                        stats["messages_sent"] += 1
                    else:
                        stats["errors"] += 1
                    
                    # Small delay between messages
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                import traceback
                logger.error(f"❌ Error processing user {user_id}: {e}")
                logger.error(f"📍 Full traceback: {traceback.format_exc()}")
                logger.error(f"🔍 User data: {user}")
                stats["errors"] += 1
        
        # Log results
        mode = "DRY RUN" if dry_run else "LIVE"
        logger.info(f"📊 Interview reminder broadcast completed ({mode}):")
        logger.info(f"   Total eligible users: {stats['total_users']}")
        logger.info(f"   Messages sent: {stats['messages_sent']}")
        logger.info(f"   Errors: {stats['errors']}")
        
        return stats


async def main():
    """Main function"""
    
    # Parse command line arguments
    dry_run = True
    test_user_ids = None
    
    # Check for test mode with specific user IDs
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Default test users, but allow adding more via command line
        test_user_ids = [257026813]
        # Add any additional user IDs from command line
        if len(sys.argv) > 2:
            for arg in sys.argv[2:]:
                try:
                    test_user_ids.append(int(arg))
                except ValueError:
                    logger.warning(f"⚠️ Invalid user ID: {arg}, skipping")
        
        dry_run = False  # Send real messages in test mode
        logger.warning(f"🧪 TEST MODE - Sending REAL messages to users: {test_user_ids}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--live":
        dry_run = False
        logger.warning("🔴 LIVE MODE ACTIVATED - Real messages will be sent!")
    else:
        logger.info("🟡 DRY RUN MODE - No actual messages will be sent")
    
    # Load config and setup connections
    config = load_config()
    bot = Bot(token=config.tg_bot.token)
    
    # Setup database connection
    db_pool = await get_pg_pool(
        db_name=config.db_applications.database,
        host=config.db_applications.host,
        port=config.db_applications.port,
        user=config.db_applications.user,
        password=config.db_applications.password
    )
    
    dao = InterviewDAO(db_pool)
    reminder_service = InterviewReminderService(bot, dao)
    
    try:
        # First, get statistics without sending
        eligible_users = await reminder_service.get_approved_users_without_timeslot()
        
        # Filter users if in test mode
        if test_user_ids:
            eligible_users = [user for user in eligible_users if user['user_id'] in test_user_ids]
        
        # Show detailed statistics
        print("\n" + "="*60)
        print("📊 INTERVIEW REMINDER STATISTICS")
        print("="*60)
        
        if test_user_ids:
            print(f"🧪 MODE: TEST (specific users: {test_user_ids})")
        elif dry_run:
            print("🟡 MODE: DRY RUN (no messages will be sent)")
        else:
            print("🔴 MODE: LIVE (REAL messages will be sent)")
        
        print(f"\nEligible users (approved but no timeslot): {len(eligible_users)}")
        
        if eligible_users:
            print(f"\n📝 USERS TO RECEIVE REMINDER ({len(eligible_users)}):")
            for user in eligible_users:
                username = user.get('telegram_username', 'no_username')
                approved_dept = user.get('approved', 'unknown')
                print(f"   • {user['user_id']} - {user['full_name']} (@{username}) [approved: {approved_dept}]")
        else:
            print("\n✅ No eligible users found (all approved users already have timeslots)")
        
        print("\n📧 MESSAGE TO SEND:")
        print("-" * 40)
        print(REMINDER_MESSAGE)
        print("-" * 40)
        
        print("="*60)
        
        # Ask for confirmation if not dry run and there are users to message
        if not dry_run and eligible_users:
            print(f"\n⚠️  ВНИМАНИЕ: Будет отправлено {len(eligible_users)} сообщений!")
            if test_user_ids:
                print(f"🧪 Тестовый режим - сообщения только для: {test_user_ids}")
            else:
                print("🔴 БОЕВОЙ РЕЖИМ - сообщения всем одобренным пользователям без слота!")
            
            confirm = input("\n❓ Подтверждаете отправку? (да/yes/y для подтверждения): ").lower().strip()
            
            if confirm not in ['да', 'yes', 'y']:
                print("\n❌ Отправка отменена пользователем")
                await db_pool.close()
                await bot.session.close()
                return
            
            print(f"\n🚀 Начинаем отправку сообщений...")
        elif not dry_run and not eligible_users:
            print("\n✅ Нет пользователей для отправки - все одобренные пользователи уже выбрали слоты")
            await db_pool.close()
            await bot.session.close()
            return
        
        # Send reminders
        stats = await reminder_service.send_reminders(
            dry_run=dry_run, 
            test_user_ids=test_user_ids
        )
        
        # Show final summary
        print("\n" + "="*50)
        print("📊 FINAL SUMMARY")
        print("="*50)
        if test_user_ids:
            print(f"Mode: TEST (users: {test_user_ids})")
        else:
            print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Eligible users: {stats['total_users']}")
        print(f"Messages sent: {stats['messages_sent']}")
        print(f"Errors: {stats['errors']}")
        
        if not dry_run and stats['messages_sent'] > 0:
            print(f"\n✅ Reminder broadcast completed successfully!")
            print(f"📤 {stats['messages_sent']} messages sent")
        elif dry_run and stats['total_users'] > 0:
            print(f"\n🟡 Dry run completed - {stats['total_users']} users would receive messages")
        
        print("="*50)
        
        if dry_run and not test_user_ids:
            print("\n💡 Available modes:")
            print("   python3 send_interview_reminder.py           # Dry run (safe)")
            print("   python3 send_interview_reminder.py --test    # Test with specific users")
            print("   python3 send_interview_reminder.py --live    # Real broadcast")
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Fatal error: {e}")
        logger.error(f"📍 Full traceback: {traceback.format_exc()}")
    finally:
        await db_pool.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Рассылка для начала третьего этапа - уведомления об одобрении/отклонении
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import os
import json

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.infrastructure.database.dao.feedback import FeedbackDAO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы для видео
VIDEO_PATH = "app/bot/assets/broadcast/video/interview_instruction.mp4"
VIDEO_FILE_ID_STORAGE = "config/video_file_ids.json"
TARGET_USER_ID = 257026813  # Пользователь для генерации file_id


async def get_video_file_id(bot: Bot) -> str:
    """Получить file_id видео, отправив его пользователю если нужно"""
    
    # Проверяем, есть ли уже сохраненный file_id
    if os.path.exists(VIDEO_FILE_ID_STORAGE):
        try:
            with open(VIDEO_FILE_ID_STORAGE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "interview_instruction" in data:
                    logger.info(f"📹 Using cached video file_id: {data['interview_instruction'][:20]}...")
                    return data["interview_instruction"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"⚠️ Error reading video file_id cache: {e}")
    
    # Отправляем видео пользователю для получения file_id
    logger.info(f"📹 Generating video file_id by sending to user {TARGET_USER_ID}")
    
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"Video file not found: {VIDEO_PATH}")
    
    try:
        video_file = FSInputFile(VIDEO_PATH)
        message = await bot.send_video(
            chat_id=TARGET_USER_ID,
            video=video_file,
            caption="🎬 Генерация file_id для видео (можно удалить это сообщение)"
        )
        
        file_id = message.video.file_id
        logger.info(f"✅ Generated video file_id: {file_id[:20]}...")
        
        # Сохраняем file_id для будущего использования
        os.makedirs(os.path.dirname(VIDEO_FILE_ID_STORAGE), exist_ok=True)
        
        # Загружаем существующие данные или создаем новые
        data = {}
        if os.path.exists(VIDEO_FILE_ID_STORAGE):
            try:
                with open(VIDEO_FILE_ID_STORAGE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        data["interview_instruction"] = file_id
        
        with open(VIDEO_FILE_ID_STORAGE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Video file_id saved to {VIDEO_FILE_ID_STORAGE}")
        return file_id
        
    except Exception as e:
        logger.error(f"❌ Error generating video file_id: {e}")
        raise


class Stage3BroadcastService:
    """Service for stage 3 broadcast (approval/rejection notifications)"""
    
    def __init__(self, bot: Bot, dao: FeedbackDAO):
        self.bot = bot
        self.dao = dao
        
    async def send_approval_notification(self, user_id: int, position_info: Dict[str, Any]) -> bool:
        """Send approval notification to user"""
        try:
            # Получаем file_id видео
            video_file_id = await get_video_file_id(self.bot)
            
            # Сначала отправляем видео
            await self.bot.send_video(
                chat_id=user_id,
                video=video_file_id,
                caption="🎬 Инструкция по записи на онлайн-собеседование"
            )
            
            # Затем отправляем основное сообщение
            message = f"""你好! Отбор был непростым испытанием. Мы внимательно изучили десятки решений, и твоё оказалось одним из самых сильных. Поздравляем и добро пожаловать на заключительный этап отбора!

<b>Ты прошел на позицию: </b>
{position_info['full_title']}

Переходи в Личный кабинет, чтобы выбрать удобное время для онлайн-собеседования с руководителем направления. На этом этапе мы хотим узнать тебя получше, обсудить твои идеи, подход к работе и то, как ты видишь себя в команде КБК.

Помни, собеседование это не допрос, а твой шанс раскрыться. Покажи, что за профессиональными навыками стоит искренняя личность — с уникальным взглядом и энергией.

Если появятся вопросы — пиши в поддержку. Мы всегда рядом и готовы помочь!
"""
            
            # Create inline keyboard with personal cabinet button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🏠 Личный кабинет",
                    callback_data="go_to_main_menu"
                )]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logger.info(f"✅ Approval notification sent to user {user_id}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"❌ User {user_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"❌ Bad request for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending approval notification to {user_id}: {e}")
            return False
    
    async def send_rejection_notification(self, user_id: int) -> bool:
        """Send rejection notification with feedback button"""
        try:
            message = """大家好!
Мы внимательно изучили десятки тестовых заданий. Конкуренция была очень высокой, и на этот раз твоя работа не вошла в список финалистов. Это не поражение — это возможность сделать шаг вперёд.

Чтобы этот шаг был осознанным, мы подготовили персональную обратную связь. Руководители отделов внимательно проанализировали решения и отметили сильные стороны и точки роста.

Ты можешь запросить обратную связь прямо в личном кабинете — она поможет понять, что ты умеешь делать блестяще, а над чем еще следует поработать к следующему сезону.

Мы верим, что впереди будет ещё много возможностей, где твой потенциал проявится в полной мере! Ждем тебя на следующих отборах КБК!
"""
            
            # Create inline keyboard with feedback button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📝 Получить обратную связь",
                    callback_data="start_feedback_dialog"
                )]
            ])
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logger.info(f"✅ Rejection notification sent to user {user_id}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"❌ User {user_id} blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.warning(f"❌ Bad request for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending rejection notification to {user_id}: {e}")
            return False
    
    async def send_stage3_broadcasts(self, dry_run: bool = True, test_user_ids: List[int] = None) -> Dict[str, int]:
        """Send stage 3 notifications to all eligible users or specific test users"""
        if test_user_ids:
            logger.info(f"🧪 Starting TEST broadcast for users: {test_user_ids}")
            # Get specific test users
            users = []
            for user_id in test_user_ids:
                # Get user data from database
                user_data = await self.dao.get_single_user_data(user_id)
                if user_data:
                    users.append(user_data)
                else:
                    logger.warning(f"⚠️ Test user {user_id} not found or didn't submit tasks")
        else:
            logger.info("🚀 Starting stage 3 broadcast...")
            # Get all users who submitted at least one task
            users = await self.dao.get_users_with_submitted_tasks()
        
        logger.info(f"📊 Found {len(users)} users to process")
        
        stats = {
            "total_users": len(users),
            "approved_sent": 0,
            "rejected_sent": 0,
            "errors": 0
        }
        
        for user in users:
            user_id = user["user_id"]
            approved = int(user["approved"]) if user["approved"] else 0
            
            try:
                if dry_run:
                    if approved > 0:
                        logger.info(f"[DRY RUN] Would send approval to user {user_id}")
                        stats["approved_sent"] += 1
                    else:
                        logger.info(f"[DRY RUN] Would send rejection to user {user_id}")
                        stats["rejected_sent"] += 1
                else:
                    if approved > 0:
                        # User is approved - get position info and send approval
                        position_info = await self.dao.get_approved_user_position(user_id)
                        if position_info:
                            success = await self.send_approval_notification(user_id, position_info)
                            if success:
                                stats["approved_sent"] += 1
                            else:
                                stats["errors"] += 1
                        else:
                            logger.warning(f"⚠️ User {user_id} approved but no position info found")
                            stats["errors"] += 1
                    else:
                        # User is rejected - send rejection with feedback option
                        success = await self.send_rejection_notification(user_id)
                        if success:
                            stats["rejected_sent"] += 1
                        else:
                            stats["errors"] += 1
                
                # Small delay between messages
                if not dry_run:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                import traceback
                logger.error(f"❌ Error processing user {user_id}: {e}")
                logger.error(f"📍 Full traceback: {traceback.format_exc()}")
                logger.error(f"🔍 User data: {user}")
                stats["errors"] += 1
        
        # Log results
        mode = "DRY RUN" if dry_run else "LIVE"
        logger.info(f"📊 Stage 3 broadcast completed ({mode}):")
        logger.info(f"   Total users: {stats['total_users']}")
        logger.info(f"   Approved notifications: {stats['approved_sent']}")
        logger.info(f"   Rejected notifications: {stats['rejected_sent']}")
        logger.info(f"   Errors: {stats['errors']}")
        
        return stats


async def main():
    """Main function"""
    import sys
    
    # Parse command line arguments
    dry_run = True
    test_user_ids = None
    
    # Check for test mode with specific user IDs
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_user_ids = [257026813,1905792261,8336687438] # artem k - 1905792261,8336687438
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
    
    dao = FeedbackDAO(db_pool)
    broadcast_service = Stage3BroadcastService(bot, dao)
    
    try:
        # First, get statistics without sending
        users_data = await dao.get_users_with_submitted_tasks()
        
        # Filter users if in test mode
        if test_user_ids:
            users_data = [user for user in users_data if user['user_id'] in test_user_ids]
        
        # Calculate statistics
        approved_users = [user for user in users_data if user['approved'] and int(user['approved']) > 0]
        rejected_users = [user for user in users_data if not user['approved'] or int(user['approved']) == 0]
        
        # Show detailed statistics
        print("\n" + "="*60)
        print("📊 BROADCAST STATISTICS")
        print("="*60)
        
        if test_user_ids:
            print(f"🧪 MODE: TEST (specific users: {test_user_ids})")
        elif dry_run:
            print("🟡 MODE: DRY RUN (no messages will be sent)")
        else:
            print("🔴 MODE: LIVE (REAL messages will be sent)")
        
        print(f"\nTotal users to process: {len(users_data)}")
        print(f"📝 Users who submitted tasks: {len(users_data)}")
        print(f"✅ Approved users (will get interview invite): {len(approved_users)}")
        print(f"❌ Rejected users (will get rejection + feedback option): {len(rejected_users)}")
        
        if approved_users:
            print(f"\n✅ APPROVED USERS ({len(approved_users)}):")
            for user in approved_users:
                username = user.get('telegram_username', 'no_username')
                print(f"   • {user['user_id']} - {user['full_name']} (@{username})")
        
        if rejected_users:
            print(f"\n❌ REJECTED USERS ({len(rejected_users)}):")
            for user in rejected_users[:10]:  # Show first 10
                username = user.get('telegram_username', 'no_username')
                print(f"   • {user['user_id']} - {user['full_name']} (@{username})")
            if len(rejected_users) > 10:
                print(f"   ... and {len(rejected_users) - 10} more users")
        
        print("="*60)
        
        # Ask for confirmation if not dry run
        if not dry_run:
            print(f"\n⚠️  ВНИМАНИЕ: Будет отправлено {len(users_data)} сообщений!")
            if test_user_ids:
                print(f"🧪 Тестовый режим - сообщения только для: {test_user_ids}")
            else:
                print("🔴 БОЕВОЙ РЕЖИМ - сообщения ВСЕМ пользователям!")
            
            confirm = input("\n❓ Подтверждаете отправку? (да/yes/y для подтверждения): ").lower().strip()
            
            if confirm not in ['да', 'yes', 'y']:
                print("\n❌ Отправка отменена пользователем")
                await db_pool.close()
                await bot.session.close()
                return
            
            print(f"\n🚀 Начинаем отправку сообщений...")
        
        # Send broadcasts
        stats = await broadcast_service.send_stage3_broadcasts(
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
        print(f"Total users processed: {stats['total_users']}")
        print(f"Approved notifications: {stats['approved_sent']}")
        print(f"Rejected notifications: {stats['rejected_sent']}")
        print(f"Errors: {stats['errors']}")
        
        if not dry_run:
            print(f"\n✅ Broadcast completed successfully!")
            print(f"📤 {stats['approved_sent'] + stats['rejected_sent']} messages sent")
        
        print("="*50)
        
        if dry_run and not test_user_ids:
            print("\n💡 Available modes:")
            print("   python3 send_stage3_broadcast.py         # Dry run (safe)")
            print("   python3 send_stage3_broadcast.py --test  # Test with specific users")
            print("   python3 send_stage3_broadcast.py --live  # Real broadcast")
        
    finally:
        await db_pool.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
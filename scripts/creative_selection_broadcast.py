#!/usr/bin/env python3
"""
Mass broadcast script for creative selection (casting) announcement.

This script sends a media group with 3 images and a text message with a button
to start the creative selection process to all active users in the database.

Features:
- Image preparation phase (get file_ids by sending to admin)
- Message preview before sending
- Multiple send modes: test (admin only), dry-run (no actual send), full broadcast
- Automatic is_alive status update on delivery failures
- Detailed logging to console and file
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.input_file import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import load_config
from app.infrastructure.database.database.db import DB
from app.infrastructure.database.models.users import Users


# ============================================================================
# CONFIGURATION
# ============================================================================

ADMIN_USER_ID = 257026813

IMAGE_PATHS = [
    "app/bot/assets/broadcast/images/1.jpeg",
    "app/bot/assets/broadcast/images/2.jpeg",
    "app/bot/assets/broadcast/images/3.jpeg",
]

_BROADCAST_MESSAGE = """大家好! Давно мечтал проявить себя? Звёздный час настал! Мы объявляем <b>отбор в творческие коллективы КБК'26</b>. Твой креатив, яркость и энергия точно сделают наш форум незабываемым! 

Подробнее о направлениях читай в карточках! 

✅ А если боишься, что у тебя мало опыта – не переживай! Спешим развеять сомнения. Мастер-классы и интерактивы подобраны так, чтобы любой человек смог их провести.

Регистрируйся в боте по ссылке 👉 @CBC_forum_bot

<b>Дедлайн: 22 февраля 12:00</b>

Развивай свои творческие способности вместе с КБК‘26!
"""


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """Setup logging to console and file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"storage/broadcast_{timestamp}.log"
    
    # Ensure storage directory exists
    Path("storage").mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("broadcast")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging to file: {log_file}")
    return logger


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def prepare_images(bot: Bot, logger: logging.Logger) -> list[str]:
    """
    Send images to admin user to get file_ids for faster broadcasting.
    
    Returns:
        List of file_ids for the images.
    """
    logger.info("=" * 60)
    logger.info("PHASE 1: IMAGE PREPARATION")
    logger.info("=" * 60)
    logger.info(f"Sending {len(IMAGE_PATHS)} images to admin user {ADMIN_USER_ID} to get file_ids...")
    
    file_ids = []
    
    try:
        # Build media group
        media_group = MediaGroupBuilder()
        for img_path in IMAGE_PATHS:
            if not Path(img_path).exists():
                logger.error(f"Image not found: {img_path}")
                raise FileNotFoundError(f"Image not found: {img_path}")
            media_group.add_photo(media=FSInputFile(img_path))
        
        # Send media group to admin
        messages = await bot.send_media_group(
            chat_id=ADMIN_USER_ID,
            media=media_group.build()
        )
        
        # Extract file_ids
        for msg in messages:
            if msg.photo:
                file_id = msg.photo[-1].file_id  # Get largest photo
                file_ids.append(file_id)
                logger.debug(f"Got file_id: {file_id[:50]}...")
        
        logger.info(f"✅ Successfully obtained {len(file_ids)} file_ids")
        return file_ids
        
    except Exception as e:
        logger.error(f"❌ Failed to prepare images: {e}")
        raise


def create_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with creative selection button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎭 Начать отбор",
            callback_data="start_creative_selection"
        )]
    ])


def preview_message(logger: logging.Logger):
    """Display message preview to user."""
    logger.info("\n" + "=" * 60)
    logger.info("MESSAGE PREVIEW")
    logger.info("=" * 60)
    
    print("\n📸 Media group: 3 images from app/bot/assets/broadcast/images/")
    print("\n📝 Message text:")
    print(_BROADCAST_MESSAGE)
    print("\n🔘 Button: 🎭 Начать отбор")
    print("   └─ Callback: start_creative_selection")
    print("=" * 60 + "\n")


def select_mode(logger: logging.Logger) -> str:
    """
    Interactive mode selection.
    
    Returns:
        One of: 'test', 'dry-run', 'full'
    """
    logger.info("\nSELECT BROADCAST MODE:")
    print("\n" + "=" * 60)
    print("BROADCAST MODE SELECTION")
    print("=" * 60)
    print("1. 🧪 Test send - send only to admin (257026813)")
    print("2. 👁️  Dry run - show recipients, no actual send")
    print("3. 🚀 Full broadcast - send to all active users")
    print("=" * 60)
    
    while True:
        choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if choice == "1":
            logger.info("Selected mode: TEST")
            return "test"
        elif choice == "2":
            logger.info("Selected mode: DRY-RUN")
            return "dry-run"
        elif choice == "3":
            confirm = input("\n⚠️  Are you sure you want to send to ALL users? (yes/no): ").strip().lower()
            if confirm == "yes":
                logger.info("Selected mode: FULL BROADCAST")
                return "full"
            else:
                print("Cancelled. Please select again.")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


async def get_users(db: DB, mode: str, logger: logging.Logger) -> list[int]:
    """
    Get list of user IDs based on selected mode.
    
    Args:
        db: Database instance
        mode: 'test', 'dry-run', or 'full'
        logger: Logger instance
        
    Returns:
        List of user_ids to send to
    """
    if mode == "test":
        logger.info(f"Test mode: sending only to admin {ADMIN_USER_ID}")
        return [ADMIN_USER_ID]
    
    # Query active users
    stmt = select(Users.user_id).where(
        Users.is_alive == True,  # noqa: E712
        Users.is_blocked == False  # noqa: E712
    )
    result = await db.session.execute(stmt)
    user_ids = [row[0] for row in result.fetchall()]
    
    logger.info(f"Found {len(user_ids)} active users (is_alive=True, is_blocked=False)")
    
    if user_ids:
        logger.info(f"Sample user IDs: {user_ids[:5]}...")
    
    return user_ids


async def send_broadcast(
    bot: Bot,
    db: DB,
    file_ids: list[str],
    user_ids: list[int],
    mode: str,
    logger: logging.Logger
) -> dict:
    """
    Send broadcast messages to users.
    
    Args:
        bot: Bot instance
        db: Database instance
        file_ids: List of image file_ids
        user_ids: List of user_ids to send to
        mode: 'test', 'dry-run', or 'full'
        logger: Logger instance
        
    Returns:
        Dictionary with statistics
    """
    logger.info("\n" + "=" * 60)
    logger.info(f"PHASE 3: BROADCASTING ({mode.upper()})")
    logger.info("=" * 60)
    
    if mode == "dry-run":
        logger.info("DRY RUN MODE: No messages will be sent")
        logger.info(f"Would send to {len(user_ids)} users")
        if user_ids:
            logger.info(f"User IDs: {user_ids}")
        return {
            "total": len(user_ids),
            "sent": 0,
            "blocked": 0,
            "errors": 0,
            "dry_run": True
        }
    
    stats = {
        "total": len(user_ids),
        "sent": 0,
        "blocked": 0,
        "errors": 0,
        "dry_run": False
    }
    
    keyboard = create_keyboard()
    
    logger.info(f"Starting broadcast to {len(user_ids)} users...")
    
    for idx, user_id in enumerate(user_ids, 1):
        try:
            # Build media group with file_ids
            media_group = MediaGroupBuilder()
            for file_id in file_ids:
                media_group.add_photo(media=file_id)
            
            # Send media group
            await bot.send_media_group(
                chat_id=user_id,
                media=media_group.build()
            )
            
            # Send text message with button
            await bot.send_message(
                chat_id=user_id,
                text=_BROADCAST_MESSAGE,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            stats["sent"] += 1
            
            # Log progress every 10 users
            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{len(user_ids)} ({stats['sent']} sent, {stats['blocked']} blocked, {stats['errors']} errors)")
            
            # Delay between sends to avoid rate limits
            await asyncio.sleep(0.5)
            
        except TelegramForbiddenError:
            # User blocked the bot
            logger.warning(f"User {user_id} blocked the bot, updating is_alive=False")
            await db.users.update_alive_status(user_id=user_id, is_alive=False)
            stats["blocked"] += 1
            
        except TelegramBadRequest as e:
            # User not found or blocked
            error_msg = str(e).lower()
            logger.warning(f"Bad request for user {user_id}: {e}")
            if any(keyword in error_msg for keyword in ["chat not found", "user not found", "user is blocked", "user_is_blocked", "blocked"]):
                logger.info(f"Updating is_alive=False for user {user_id}")
                await db.users.update_alive_status(user_id=user_id, is_alive=False)
                stats["blocked"] += 1
            else:
                stats["errors"] += 1
                
        except TelegramRetryAfter as e:
            # Rate limit hit, wait and retry
            logger.warning(f"Rate limit hit, waiting {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after)
            # Retry this user
            try:
                media_group = MediaGroupBuilder()
                for file_id in file_ids:
                    media_group.add_photo(media=file_id)
                await bot.send_media_group(chat_id=user_id, media=media_group.build())
                await bot.send_message(
                    chat_id=user_id,
                    text=_BROADCAST_MESSAGE,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                stats["sent"] += 1
            except Exception as retry_error:
                logger.error(f"Retry failed for user {user_id}: {retry_error}")
                stats["errors"] += 1
                
        except Exception as e:
            logger.error(f"Unexpected error sending to user {user_id}: {e}")
            stats["errors"] += 1
    
    return stats


# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main():
    """Main broadcast script logic."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("CREATIVE SELECTION BROADCAST SCRIPT")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config()
    logger.info("✅ Configuration loaded")
    
    # Initialize bot
    bot = Bot(token=config.tg_bot.token)
    logger.info("✅ Bot initialized")
    
    # Setup database
    url = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.database}"
    engine = create_async_engine(url, echo=False, pool_size=3, max_overflow=0)
    async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("✅ Database connection established")
    
    try:
        # Phase 1: Prepare images
        file_ids = await prepare_images(bot, logger)
        
        # Phase 2: Preview and mode selection
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: PREVIEW AND MODE SELECTION")
        logger.info("=" * 60)
        preview_message(logger)
        
        mode = select_mode(logger)
        
        # Get users
        async with async_session_maker() as session:
            db = DB(session)
            user_ids = await get_users(db, mode, logger)
            
            if not user_ids:
                logger.warning("No users found to send to!")
                return
            
            # Send broadcast
            stats = await send_broadcast(bot, db, file_ids, user_ids, mode, logger)
            
            # Commit database changes (is_alive updates)
            if mode != "dry-run":
                await session.commit()
                logger.info("✅ Database changes committed")
        
        # Display final statistics
        logger.info("\n" + "=" * 60)
        logger.info("BROADCAST COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total users: {stats['total']}")
        if not stats['dry_run']:
            logger.info(f"✅ Successfully sent: {stats['sent']}")
            logger.info(f"🚫 Blocked users: {stats['blocked']}")
            logger.info(f"❌ Errors: {stats['errors']}")
            success_rate = (stats['sent'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"📊 Success rate: {success_rate:.1f}%")
        else:
            logger.info("ℹ️  Dry run - no messages sent")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("\n❌ Broadcast cancelled by user")
        
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        
    finally:
        # Cleanup
        await engine.dispose()
        await bot.session.close()
        logger.info("✅ Resources cleaned up")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBroadcast cancelled.")
        sys.exit(0)

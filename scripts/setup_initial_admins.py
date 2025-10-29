#!/usr/bin/env python3
"""
Скрипт для установки первых администраторов системы ролей
Используется после развертывания системы ролей
"""
import asyncio
import logging
import os
import sys

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import load_config
from app.infrastructure.database.connect_to_pg import get_pg_pool
from app.infrastructure.database.database.db import DB
from app.enums.roles import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_initial_admins():
    """Устанавливает первых администраторов системы"""
    logger.info("Loading config...")
    config = load_config()
    
    if not config.admin_ids:
        logger.warning("Список администраторов пуст в конфигурации (ADMIN_IDS)")
        return
    
    logger.info(f"Setting up {len(config.admin_ids)} initial admins: {config.admin_ids}")
    
    try:
        # Подключаемся к БД
        logger.info("Connecting to database...")
        db_pool = await get_pg_pool(
            db_name=config.db_applications.database,
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password,
        )
        
        async with db_pool.connection() as conn:
            db = DB(conn, conn)
            
            for admin_id in config.admin_ids:
                logger.info(f"Setting up admin {admin_id}...")
                
                # Проверяем, существует ли пользователь
                user = await db.users.get_user_record(user_id=admin_id)
                
                if not user:
                    # Создаем пользователя если не существует
                    logger.info(f"Creating new user {admin_id}...")
                    await db.users.add(
                        user_id=admin_id,
                        language="ru",
                        is_alive=True,
                        is_blocked=False
                    )
                
                # Добавляем роль admin
                try:
                    await db.users.add_user_role(
                        user_id=admin_id,
                        role=Role.ADMIN.value
                    )
                    logger.info(f"✅ Admin role granted to user {admin_id}")
                except Exception as e:
                    if "already has role" in str(e).lower():
                        logger.info(f"ℹ️  User {admin_id} already has admin role")
                    else:
                        raise
            
            await conn.commit()
            logger.info("✅ All initial admins setup completed")
            
    except Exception as e:
        logger.error(f"❌ Error setting up initial admins: {e}")
        raise
    finally:
        if 'db_pool' in locals():
            await db_pool.close()


async def show_current_admins():
    """Показывает текущих администраторов"""
    logger.info("Loading config...")
    config = load_config()
    
    try:
        logger.info("Connecting to database...")
        db_pool = await get_pg_pool(
            db_name=config.db_applications.database,
            host=config.db_applications.host,
            port=config.db_applications.port,
            user=config.db_applications.user,
            password=config.db_applications.password,
        )
        
        async with db_pool.connection() as conn:
            db = DB(conn, conn)
            
            # Получаем всех администраторов
            admin_users = await db.users.list_users_by_role(role=Role.ADMIN.value)
            
            if admin_users:
                logger.info(f"Current admins ({len(admin_users)}):")
                for admin_id in admin_users:
                    user = await db.users.get_user_record(user_id=admin_id)
                    if user:
                        logger.info(f"  - {admin_id}: roles={user.roles}")
                    else:
                        logger.info(f"  - {admin_id}: (user record not found)")
            else:
                logger.info("No administrators found in the system")
                
    except Exception as e:
        logger.error(f"❌ Error showing current admins: {e}")
        raise
    finally:
        if 'db_pool' in locals():
            await db_pool.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage initial system administrators")
    parser.add_argument(
        "action", 
        choices=["setup", "show"], 
        help="Action to perform: setup initial admins or show current admins"
    )
    
    args = parser.parse_args()
    
    if args.action == "setup":
        asyncio.run(setup_initial_admins())
    elif args.action == "show":
        asyncio.run(show_current_admins())
#!/usr/bin/env python3
"""
Extract blocked user IDs from broadcast log and update their is_alive status to False.
"""

import asyncio
import re
import sys
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import load_config
from app.infrastructure.database.models.users import Users


async def main():
    """Extract user IDs from log and update database."""
    
    # Read log file
    log_file = "boradcast logging.yaml"
    if not Path(log_file).exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    print(f"📖 Reading log file: {log_file}")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # Extract all user IDs marked for blocking
    pattern = r"Will update is_alive=False for user (\d+)"
    matches = re.findall(pattern, log_content)
    
    # Convert to integers and remove duplicates
    user_ids = sorted(set(int(uid) for uid in matches))
    
    print(f"✅ Found {len(user_ids)} unique user IDs to block")
    print(f"📝 Sample IDs: {user_ids[:10]}...")
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    confirm = input(f"⚠️  Update is_alive=False for {len(user_ids)} users? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Operation cancelled")
        return
    
    # Load configuration and connect to database
    config = load_config()
    url = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.database}"
    engine = create_async_engine(url, echo=False, pool_size=3, max_overflow=0)
    async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session_maker() as session:
            print(f"\n🔄 Updating {len(user_ids)} users in database...")
            
            # Batch update all users at once
            stmt = (
                update(Users)
                .where(Users.user_id.in_(user_ids))
                .values(is_alive=False)
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            print(f"✅ Successfully updated {result.rowcount} users")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        raise
        
    finally:
        await engine.dispose()
    
    # Save user IDs to file for reference
    output_file = "storage/blocked_users_list.txt"
    Path("storage").mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        for uid in user_ids:
            f.write(f"{uid}\n")
    
    print(f"💾 Saved user IDs to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlalchemy.orm import sessionmaker

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from app.infrastructure.database.orm.base import Base
from app.infrastructure.database.models.broadcasts import Broadcasts
from app.infrastructure.database.database.db import DB

from config.config import load_config

def create_db_url() -> str:
    config = load_config()
    URL = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.database}"
    return URL

engine = create_async_engine(
    create_db_url(),
    echo=False,
    future=True,
    pool_size=3,
    max_overflow=0,
)

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def key_validation(key: str) -> bool: 
    if key == "":
        print("Empty key. Try again")
        return False
    return True



async def main():
    """Основная функция"""

    key, title, description, channel = None, None, None, None

    try:
        while True:
            key = str(input("Enter key: "))
            if key_validation(key):
                break

        title = str(input("Enter title: "))

        description = str(input("Enter description: "))
    except Exception as e:
        print(f"ERROR {e}")
        return -2
    
    print(f"\nKey: {key}\nTitle: {title}\nDescription: {description}")

    try:
        async with AsyncSessionLocal() as session:
            database = DB(session)

            await database.broadcasts.add(
                key=key,
                title=title,
                description=description,
            )
            
            await session.commit()
        engine.dispose()

    except Exception as e:
        print(f"\n\n\n!!!!!!!!! ERROR: {e}")
        return -1

    print(f"Added broadcast: {key}")
    return 0


if __name__ == "__main__":
    print(f"============\nEXIT CODE: {asyncio.run(main())}\n============")
import asyncio
import logging
import logging.config
import os
import sys

from app.bot import main
from app.services.logger.logging_settings import logging_config

logging.config.dictConfig(logging_config)

if sys.platform.startswith("win") or os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(main())

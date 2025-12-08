
from typing import Annotated
from datetime import datetime, timezone

from sqlalchemy.orm import mapped_column
from sqlalchemy import Boolean, DateTime, BigInteger, text, ForeignKey
from sqlalchemy.sql import func

intpk = Annotated[int, mapped_column(primary_key=True)] # internal pk of other tables rather than users (where bigint used due to telegram id size)
created = Annotated[datetime, mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', NOW())"),
    )]
updated = Annotated[datetime, mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )]
from psycopg import AsyncConnection

from app.infrastructure.database.database.users import _UsersDB
from app.infrastructure.database.database.applications import _ApplicationsDB


class DB:
    def __init__(self, users_connection: AsyncConnection, applications_connection: AsyncConnection) -> None:
        self.users = _UsersDB(connection=users_connection)
        self.applications = _ApplicationsDB(connection=applications_connection)

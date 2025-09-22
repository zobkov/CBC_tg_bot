from psycopg import AsyncConnection

from app.infrastructure.database.database.users import _UsersDB
from app.infrastructure.database.database.applications import _ApplicationsDB
from app.infrastructure.database.database.evaluated_applications import _EvaluatedApplicationsDB


class DB:
    def __init__(self, users_connection: AsyncConnection, applications_connection: AsyncConnection) -> None:
        # Users are now stored in the applications database
        self.users = _UsersDB(connection=applications_connection)
        self.applications = _ApplicationsDB(connection=applications_connection)
        self.evaluated_applications = _EvaluatedApplicationsDB(connection=applications_connection)

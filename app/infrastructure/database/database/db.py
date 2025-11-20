from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database.users import _UsersDB
from app.infrastructure.database.database.evaluated_applications import _EvaluatedApplicationsDB
from app.infrastructure.database.database.task_statistics import _TaskStatisticsDB
from app.infrastructure.database.database.quiz_dod import _QuizDodDB
from app.infrastructure.database.database.quiz_dod_users_info import _QuizDodUsersInfoDB


class DB:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = _UsersDB(session=session)
        self.evaluated_applications = _EvaluatedApplicationsDB(session=session)
        self.task_statistics = _TaskStatisticsDB(session=session)
        self.quiz_dod = _QuizDodDB(session=session)
        self.quiz_dod_users_info = _QuizDodUsersInfoDB(session=session)

    @property
    def session(self) -> AsyncSession:
        return self._session

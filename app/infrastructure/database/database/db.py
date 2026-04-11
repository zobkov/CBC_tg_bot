from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database.users import _UsersDB
from app.infrastructure.database.database.feedback import _FeedbackDB
from app.infrastructure.database.database.quiz_dod import _QuizDodDB
from app.infrastructure.database.database.quiz_dod_users_info import _QuizDodUsersInfoDB
from app.infrastructure.database.database.user_info import _UsersInfoDB
from app.infrastructure.database.database.broadcasts import _BroadcastsDB
from app.infrastructure.database.database.user_subscriptions import _UserSubscriptionsDB
from app.infrastructure.database.database.creative_applications import _CreativeApplicationsDB
from app.infrastructure.database.database.online_events import _OnlineEventsDB
from app.infrastructure.database.database.online_registrations import _OnlineRegistrationsDB
from app.infrastructure.database.database.user_mentors import _UserMentorsDB
from app.infrastructure.database.database.volunteer_applications import _VolunteerApplicationsDB
from app.infrastructure.database.database.volunteer_selection_part2 import _VolSelPart2DB
from app.infrastructure.database.database.forum_registrations import _ForumRegistrationsDB
from app.infrastructure.database.database.career_fair_stats import _CareerFairStatsDB
from app.infrastructure.database.database.lectory_questions import _LectoryQuestionsDB


class DB:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = _UsersDB(session=session)
        self.feedback = _FeedbackDB(session=session)
        self.quiz_dod = _QuizDodDB(session=session)
        self.quiz_dod_users_info = _QuizDodUsersInfoDB(session=session)
        self.users_info = _UsersInfoDB(session=session)
        self.broadcasts = _BroadcastsDB(session=session)
        self.user_subscriptions = _UserSubscriptionsDB(session=session)
        self.creative_applications = _CreativeApplicationsDB(session=session)
        self.online_events = _OnlineEventsDB(session=session)
        self.online_registrations = _OnlineRegistrationsDB(session=session)
        self.user_mentors = _UserMentorsDB(session=session)
        self.volunteer_applications = _VolunteerApplicationsDB(session=session)
        self.volunteer_selection_part2 = _VolSelPart2DB(session=session)
        self.forum_registrations = _ForumRegistrationsDB(session=session)
        self.career_fair_stats = _CareerFairStatsDB(session=session)
        self.lectory_questions = _LectoryQuestionsDB(session=session)

    @property
    def session(self) -> AsyncSession:
        return self._session

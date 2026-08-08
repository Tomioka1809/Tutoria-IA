# Import all the models, so that Base has them before being
# imported by Alembic
from app.infrastructure.database.base_class import Base  # noqa
from app.infrastructure.database.models.user import User  # noqa
from app.infrastructure.database.models.service_type import ServiceType  # noqa
from app.infrastructure.database.models.tutor_assignment import TutorAssignment  # noqa
from app.infrastructure.database.models.session import Session  # noqa
from app.infrastructure.database.models.event import Event  # noqa
from app.infrastructure.database.models.streak import Streak  # noqa
from app.infrastructure.database.models.notification import Notification  # noqa
from app.infrastructure.database.models.conversation import Conversation  # noqa
from app.infrastructure.database.models.message import Message  # noqa
from app.infrastructure.database.models.corpus_chunk import CorpusChunk  # noqa
from app.infrastructure.database.models.profiles import StudentProfile, TutorProfile, AdminProfile  # noqa
from app.infrastructure.database.models.motivational_quote import MotivationalQuote  # noqa
from app.infrastructure.database.models.password_reset_token import PasswordResetToken  # noqa

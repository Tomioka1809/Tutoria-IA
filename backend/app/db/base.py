# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.service_type import ServiceType  # noqa
from app.models.tutor_assignment import TutorAssignment  # noqa
from app.models.session import Session  # noqa
from app.models.event import Event  # noqa
from app.models.streak import Streak  # noqa
from app.models.notification import Notification  # noqa
from app.models.conversation import Conversation  # noqa
from app.models.message import Message  # noqa

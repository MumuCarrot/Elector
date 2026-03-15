# Import all models so SQLAlchemy can resolve relationship() string references
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_role import UserRole
from app.models.user_role_link import UserRoleLink
from app.models.election import Election
from app.models.election_setting import ElectionSetting
from app.models.election_access import ElectionAccess
from app.models.election_results_cache import ElectionResultsCache
from app.models.candidates import Candidate
from app.models.attachment import Attachment

__all__ = [
    "User",
    "UserProfile",
    "UserRole",
    "UserRoleLink",
    "Election",
    "ElectionSetting",
    "ElectionAccess",
    "ElectionResultsCache",
    "Candidate",
    "Attachment",
]

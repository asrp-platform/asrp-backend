
from pydantic import BaseModel

from app.domains.memberships.models import MembershipTypeEnum
from app.domains.shared.schemas import FeedbackAdditionalInfoCreateSchema


class MembershipCreateSchema(BaseModel):
    primary_affiliation: str
    job_title: str
    practice_setting: str
    subspecialty: str
    is_trained_in_us: bool


class MembershipDataSchema(BaseModel):
    membership: MembershipCreateSchema
    membership_type: MembershipTypeEnum
    feedback_additional_info: FeedbackAdditionalInfoCreateSchema
    is_agrees_communications: bool

    model_config = {
        "from_attributes": True,
    }

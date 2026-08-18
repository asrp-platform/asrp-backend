from pydantic import BaseModel


class CommunicationPreferencesViewSchema(BaseModel):
    membership_account_notifications: bool
    newsletters: bool
    events_meetings: bool
    committees_leadership: bool
    volunteer_opportunities: bool

    model_config = {"from_attributes": True}


class CommunicationPreferencesUpdateSchema(BaseModel):
    newsletters: bool | None = None
    events_meetings: bool | None = None
    committees_leadership: bool | None = None
    volunteer_opportunities: bool | None = None

    model_config = {"extra": "forbid"}

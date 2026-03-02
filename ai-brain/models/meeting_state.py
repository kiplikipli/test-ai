from typing import Literal

from pydantic import BaseModel, Field

from models.attendee import Attendee
from models.date_range import DateRange


MeetingStatus = Literal[
    'collecting',
    'resolving_attendees',
    'scheduling',
    'awaiting_confirmation',
    'completed',
]


class MeetingState(BaseModel):
    session_id: str
    legal_entity_id: int
    requester_email: str

    title: str | None = None
    duration_minutes: int = 60

    attendees: list[Attendee] = Field(default_factory=list)
    date_range: DateRange | None = None

    suggested_slots: list[dict] = Field(default_factory=list)
    selected_slot: dict | None = None

    status: MeetingStatus = 'collecting'

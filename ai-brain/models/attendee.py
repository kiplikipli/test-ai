from typing import Literal

from pydantic import BaseModel


class Attendee(BaseModel):
    name: str | None = None
    email: str | None = None
    department: str | None = None
    squad: str | None = None
    priority: Literal['required', 'preferred', 'optional'] = 'required'

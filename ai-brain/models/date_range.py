from datetime import datetime

from pydantic import BaseModel


class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
    timezone: str

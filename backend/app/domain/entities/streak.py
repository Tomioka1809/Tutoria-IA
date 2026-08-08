from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class StreakBase(BaseModel):
    student_id: int
    current_streak: int = 0
    max_streak: int = 0
    last_session_date: Optional[date] = None

class StreakOut(StreakBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

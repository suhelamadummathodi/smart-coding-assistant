from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum



class SenderType(str, Enum):
    user = "user"
    ai = "ai"

# -------------------------
# Message Schemas
# -------------------------
class MessageBase(BaseModel):
    content: str
    model_used: Optional[str] = None

class MessageCreate(MessageBase):
    sender_type: SenderType
    session_id: int

class MessageOut(MessageBase):
    id: int
    sender_type: str
    created_at: datetime

    class Config:
        from_attributes = True

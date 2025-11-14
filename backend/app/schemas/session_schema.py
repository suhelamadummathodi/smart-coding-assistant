from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.message_schema import MessageOut


# -------------------------
# Project Schemas
# -------------------------
class ProjectOut(BaseModel):
    name: str
    user_id: int
    id: int

    class Config:
        from_attributes = True
    
# -------------------------
# Session Schemas
# -------------------------
class SessionInstanceBase(BaseModel):
    user_id: int
    title: Optional[str] = None
    project_id: Optional[int] = None

class SessionInstanceCreate(SessionInstanceBase):
    pass

class SessionInstanceUpdate(BaseModel):
    title: Optional[str] = None
    project_id: Optional[int] = None

class SessionInstanceOut(SessionInstanceBase):
    id: int
    user_id: int
    project: Optional[ProjectOut] = None
    messages: List[MessageOut] = []
    created_at: datetime
    title: Optional[str] = None
    
    class Config:
        from_attributes = True

class MessageSessionOut(BaseModel):
    ai_message: MessageOut
    session: SessionInstanceOut

class ProjectClone(BaseModel):
    repo_url: str
    project_name: str
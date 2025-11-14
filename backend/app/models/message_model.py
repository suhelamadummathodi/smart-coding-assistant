from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class SenderType(str, enum.Enum):
    user = "user"
    ai = "ai"

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False, default=SenderType.user)
    content = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionInstance", back_populates="messages")
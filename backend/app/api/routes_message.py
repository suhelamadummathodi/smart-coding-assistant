from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.schemas.message_schema import MessageCreate, MessageOut
from app.schemas.session_schema import MessageSessionOut
from app.services.message_services import create_message, get_messages
from app.services.session_services import get_session
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List


router = APIRouter()

@router.post("/messages", response_model=MessageSessionOut)
def add_message(message: MessageCreate, db: Session = Depends(get_db)):
    db_session = get_session(db, session_id=message.session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return create_message(db, message=message)

@router.get("/messages/{session_id}", response_model=List[MessageOut])
def get_session_messages(session_id: int, db: Session = Depends(get_db)):
    db_session = get_session(db, session_id=session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return get_messages(db, session_id=session_id)
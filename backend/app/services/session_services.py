# app/crud.py
from sqlalchemy.orm import Session
from app.models.session_model import SessionInstance 
from app.schemas.session_schema import SessionInstanceCreate, SessionInstanceUpdate
from app.services.llm_factory import LLMFactory

def create_session(db: Session, sessioninstance: SessionInstanceCreate):
    db_session = SessionInstance(user_id=sessioninstance.user_id, project_id=sessioninstance.project_id, title=sessioninstance.title)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_sessions(db: Session, user_id: int):
    return db.query(SessionInstance).filter(SessionInstance.user_id == user_id).order_by(SessionInstance.created_at.desc()).all()

def get_session(db: Session, session_id: int):
    return db.query(SessionInstance).filter(SessionInstance.id == session_id).first()

def generate_session_title(db: Session, session: SessionInstance, model: str = "ollama"):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes user prompts into short titles."},
        {"role": "user", "content": f"Summarize this chat in 4 words: {session.messages[0].content}"}
    ]
    title = LLMFactory.generate_response(messages, model=model)[:50].strip()
    session.title = title.strip('"') or "New Chat"
    db.commit()
    db.refresh(session)
    return session

def rename_session_crud(db: Session, session_id: int, session_data: SessionInstanceUpdate):
    session = get_session(db, session_id=session_id)
    if session_data.title is not None:
        session.title = session_data.title
    if session_data.project_id is not None:
        session.project_id = session_data.project_id
    db.commit()
    db.refresh(session)
    return session

def delete_session_crud(db: Session, session_id: int):
    session = get_session(db, session_id=session_id)
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}

def list_sessions_by_project(db: Session, user_id: int, project_id: int):
    return db.query(SessionInstance).filter(SessionInstance.user_id == user_id, SessionInstance.project_id == project_id).order_by(SessionInstance.created_at.desc()).all()
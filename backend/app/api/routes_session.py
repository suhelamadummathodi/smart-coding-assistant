from fastapi import APIRouter, HTTPException
from app.database import get_db
from app.schemas.session_schema import SessionInstanceCreate, SessionInstanceOut, SessionInstanceUpdate
from app.schemas.user_schema import UserResponse as User
from app.services.session_services import create_session, delete_session_crud, get_sessions, get_session, list_sessions_by_project, rename_session_crud
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Any, List
from app.core.dependencies import get_current_user



router = APIRouter()

print(">>> Checking SessionOut type:", SessionInstanceOut)
    
@router.post("/sessions", response_model=SessionInstanceOut)
def add_new_session(sessioninstance: SessionInstanceCreate, db: Session = Depends(get_db)):
    return create_session(db,  sessioninstance=sessioninstance)

@router.get("/sessions", response_model=List[SessionInstanceOut])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_sessions(db, user_id=user.id)

@router.get("/sessions/{session_id}", response_model=SessionInstanceOut)
def get_session_by_id(session_id: int, db: Session = Depends(get_db)):
    db_session = get_session(db, session_id=session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

# ✅ Rename Session
@router.put("/sessions/{session_id}")
def rename_session(session_id: int, session_data: SessionInstanceUpdate, db: Session = Depends(get_db)):
    session = get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return rename_session_crud(db, session_id, session_data)
    

# ✅ Delete Session
@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return delete_session_crud(db, session_id)
    
@router.get("/sessions/projects/{project_id}", response_model=List[SessionInstanceOut])
def list_sessions_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sessions = list_sessions_by_project(db, user_id=user.id, project_id=project_id)
    return sessions
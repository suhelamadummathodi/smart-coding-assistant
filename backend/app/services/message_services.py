# app/crud.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.message_model import Message, SenderType
from app.models.session_model import SessionInstance
from app.schemas.message_schema import MessageCreate
from app.schemas.session_schema import  MessageSessionOut
from app.services import ai_service
from app.services.search import retrieve_top_k
from app.services.session_services import generate_session_title


def create_message(db: Session, message: MessageCreate):
    # 1️⃣ Save user message
    db_msg = Message(
        session_id=message.session_id,
        sender_type=message.sender_type,
        content=message.content,
        model_used=message.model_used
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    # 2️⃣ Fetch session & project
    session_instance = db.query(SessionInstance).filter(SessionInstance.id == message.session_id).first()
    if not session_instance:
        raise HTTPException(status_code=404, detail="Session not found")
    
    #project id
    project_id = session_instance.project_id

    if project_id:

        # 3️⃣ Retrieve top-k code chunks for context
        top_chunks = retrieve_top_k(project_id, message.content, db=db, top_k=6)
        
        # 4️⃣ Construct LLM messages
        system_prompt = "You are a developer assistant. Only use the provided context files; mention file path and lines you used."
        context_text = ""
        for chunk in top_chunks:
            context_text += f"File: {chunk['file_path']} lines {chunk['start_line']}-{chunk['end_line']}\n{chunk['text']}\n\n"

        messages_for_llm = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context_text},
            {"role": "user", "content": message.content},
        ]
    
    else:
         # 2️⃣ Get session history (for context)
        history = (
            db.query(Message)
            .filter(Message.session_id == message.session_id)
            .order_by(Message.created_at)
            .all()
        )
        messages_for_llm = [
            {"role": "user" if m.sender_type == "user" else "assistant", "content": m.content}
            for m in history
        ]
        

    # 5️⃣ Generate AI response
    try:
        ai_response = ai_service.generate_code_suggestion(
            messages=messages_for_llm,
            model=message.model_used
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 6️⃣ Generate session title if missing
    if not session_instance.title:
        session_instance = generate_session_title(db, session_instance, model=message.model_used)

    # 7️⃣ Save AI message
    ai_message = Message(
        session_id=message.session_id,
        sender_type=SenderType.ai,
        content=ai_response,
        model_used=message.model_used,
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return MessageSessionOut(ai_message=ai_message, session=session_instance)


def get_messages(db: Session, session_id: int):
    return db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()

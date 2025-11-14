from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.dependencies import get_current_user
from app.database import engine, Base
from app.api.routes_ai import router as ai_router
from app.api.routes_auth import router as auth_router
from app.api.routes_session import router as session_router
from app.api.routes_message import router as message_router
from app.api.routes_project import router as project_router
from app.schemas.user_schema import UserResponse



app = FastAPI(title="Smart Coding Assistant API")

# Create database tables
Base.metadata.create_all(bind=engine)

# Add CORS
origins = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
    "https://smart-coding-assistant-1.onrender.com",
    # Add more allowed origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],          # Allow GET, POST, PUT, DELETE etc.
    allow_headers=["*"],          # Allow all headers
)


app.include_router(ai_router, prefix="/api/ai", tags=["AI"])
app.include_router(auth_router, prefix="/api", tags=["Auth"])
app.include_router(message_router, prefix="/api", tags=["Messages"])
app.include_router(session_router, prefix="/api", tags=["Sessions"])
app.include_router(project_router, prefix="/api/projects", tags=["Projects"])


@app.get("/")
def home():
    return {"message": "Smart Coding Assistant API is running"}

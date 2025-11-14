from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "ollama")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/smart_coding_assistant_db")

settings = Settings()

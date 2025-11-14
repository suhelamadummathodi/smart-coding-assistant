from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # 'zip' or 'git'
    repo_url = Column(String(1024), nullable=True)
    source_url  = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("FileStore", back_populates="project", cascade="all, delete")
    sessions = relationship("SessionInstance", back_populates="project", cascade="all, delete")

class SessionInstance(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete")
    user = relationship("User", back_populates="sessions")
    project = relationship("Project", back_populates="sessions")


class FileStore(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    path = Column(String(1024), nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="files")
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("FileStore", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False, cascade="all, delete")

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False, unique=True)
    vector_id = Column(Integer, nullable=False)  # id in FAISS index
    created_at = Column(DateTime, default=datetime.utcnow)

    chunk = relationship("Chunk", back_populates="embedding")
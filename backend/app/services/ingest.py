# app/services/ingest.py
import os
from uuid import uuid4
import zipfile
import shutil
import tempfile
from fastapi import HTTPException
from git import Repo
from pathlib import Path
from app.models.session_model import Project, FileStore, Chunk, Embedding
from sqlalchemy.orm import Session
from hashlib import sha256
from app.services.supabase_client import supabase

# file extensions to include
INCLUDE_EXT = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".go", ".rs",
               ".html", ".css", ".json", ".md", ".yml", ".yaml", ".sh", ".sql"}
IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "venv", "env", ".venv"}

from app.embeddings.indexer import FaissIndex

def is_text_file(path: Path):
    # simple extension check; could also check mime
    return path.suffix.lower() in INCLUDE_EXT

def walk_and_collect(root_dir):
    files = []
    for p in Path(root_dir).rglob("*"):
        if p.is_file():
            # skip ignored dirs in path
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            if not is_text_file(p):
                continue
            files.append(p)
    return files

def create_project_from_dir(user_id: int, name: str, src_dir: str, db: Session, source_type: str="zip", repo_url=None):
    
    try:
        # create project metadata
        print("Creating project record...")
        proj = Project(user_id=user_id, name=name, source_type=source_type, repo_url=repo_url, source_url=src_dir)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        print(f"Created project {proj.id} - {proj.name}")
        # gather files
        files_on_disk = walk_and_collect(src_dir)
        for p in files_on_disk:
            rel = os.path.relpath(str(p), src_dir)
            content = p.read_text(encoding='utf-8', errors='ignore')
            content_hash = sha256(content.encode('utf-8')).hexdigest()
            f = FileStore(project_id=proj.id, path=rel, content=content, content_hash=content_hash, size=len(content))
            db.add(f)
            db.commit()
            db.refresh(f)
        return proj.id, proj.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_zip_and_create_project(user_id:int, zip_file_path:str, project_name:str, db:Session):
    tmpdir = f"/tmp/proj_{uuid4().hex}"
    os.makedirs(tmpdir, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            z.extractall(tmpdir)
        proj_id, proj_name= create_project_from_dir(user_id, project_name, tmpdir, db=db, source_type="zip")

        upload_folder_to_supabase(tmpdir, proj_id)

        shutil.rmtree(tmpdir)
        return proj_id, proj_name
    except Exception:
        shutil.rmtree(tmpdir)
        raise

def upload_folder_to_supabase(local_path, project_id):
    bucket = "project-files"
    base_path = f"project_{project_id}/"

    for root, dirs, files in os.walk(local_path):
        for file in files:
            local_file = os.path.join(root, file)
            rel = os.path.relpath(local_file, local_path)
            supa_path = base_path + rel.replace("\\", "/")

            with open(local_file, "rb") as f:
                supabase.storage.from_(bucket).upload(
                    supa_path, f, file_options={"upsert": True}
                )

def clone_git_and_create_project(user_id:int, repo_url:str, project_name:str, db:Session):
    tmpdir = f"/tmp/proj_{uuid4().hex}"
    os.makedirs(tmpdir, exist_ok=True)
    try:
        Repo.clone_from(repo_url, tmpdir, depth=1)
        print("Cloned repo to", tmpdir)
        proj_id, proj_name = create_project_from_dir(user_id, project_name, tmpdir, db=db, source_type="git", repo_url=repo_url)

        upload_folder_to_supabase(tmpdir, proj_id)

        shutil.rmtree(tmpdir)
        return proj_id, proj_name
    except Exception:
        shutil.rmtree(tmpdir)
        raise

# chunker: simple line-based chunking with approx token limits
def chunk_file_content(content:str, max_lines=80, overlap=10):
    lines = content.splitlines()
    chunks = []
    i = 0
    n = len(lines)
    while i < n:
        start = i
        end = min(i + max_lines, n)
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()
        if chunk_text:
            chunks.append((start+1, end, chunk_text))
        i = end - overlap
        if i <= start:
            i = end
    return chunks

def index_project(project_id:int, db:Session):
    print("Indexing project", project_id)
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise RuntimeError("Project not found")

        chunk_texts = []
        chunk_db_ids = []

        files = db.query(FileStore).filter(FileStore.project_id == project_id).all()
        for f in files:
            chunks = chunk_file_content(f.content)
            for start, end, text in chunks:
                db_chunk = Chunk(file_id=f.id, start_line=start, end_line=end, text=text)
                db.add(db_chunk)
                db.commit()
                db.refresh(db_chunk)
                chunk_texts.append(text)
                chunk_db_ids.append(db_chunk.id)
            print(f"Processed file {f.path}, created {len(chunks)} chunks.")
        # create embeddings + put vectors into faiss
        index = FaissIndex(project_id)
        if chunk_texts:
            print(f"Creating embeddings and indexing in FAISS...{len(chunk_db_ids)} chunks to index.")
            vector_ids = index.add_vectors(chunk_texts, chunk_db_ids)
            # persist vector metadata in DB
            for vec_id, chunk_db_id in zip(vector_ids, chunk_db_ids):
                emb = Embedding(chunk_id=chunk_db_id, vector_id=int(vec_id))
                db.add(emb)
            db.commit()
            print(f"Indexed {len(chunk_texts)} chunks for project {project_id}.")
        return {"indexed_chunks": len(chunk_texts)}
    except Exception as e:
        raise(HTTPException(status_code=500, detail=str(e)))

def project_by_user(user_id:int, db:Session):
    try:
        projects = db.query(Project).filter(Project.user_id == user_id).all()
        project_list = [{"id": p.id, "name": p.name} for p in projects]
        return {"projects": project_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
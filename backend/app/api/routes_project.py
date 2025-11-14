# app/api/routes_projects.py
from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from fastapi import BackgroundTasks
import os
import shutil
from fastapi.params import File
from app.database import get_db
from app.schemas.session_schema import ProjectClone
from app.services.ingest import extract_zip_and_create_project, clone_git_and_create_project, index_project, project_by_user
from app.models.session_model import Chunk, FileStore, Project
from app.core.dependencies import get_current_user
from app.schemas.user_schema import UserResponse as User
from sqlalchemy.orm import Session
from app.services.supabase_client import supabase

router = APIRouter()

@router.post("/upload")
async def upload_project_zip(
    background_tasks: BackgroundTasks,
    upload: UploadFile = File(...),
    project_name: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Save uploaded file to temp, extract and create project
    tmpdir = os.path.join("tmp_uploads")
    os.makedirs(tmpdir, exist_ok=True)
    file_path = os.path.join(tmpdir, f"{upload.filename}")
    with open(file_path, "wb") as f:
        f.write(await upload.read())

    try:
        proj_id, proj_name = extract_zip_and_create_project(user.id, file_path, project_name, db=db)
        # schedule cleanup of extract_dir (optional) or index in background
        
        background_tasks.add_task(index_project, proj_id, db)
        return {"project": {"id": proj_id, "name": proj_name}}
    finally:
        os.remove(file_path)

@router.post("/clone")
def clone_repo(background_tasks: BackgroundTasks, project: ProjectClone, user:User=Depends(get_current_user), db:Session =Depends(get_db)):
    # clone and process
    try:
        proj_id, proj_name = clone_git_and_create_project(user.id, project.repo_url, project.project_name, db)
        
        background_tasks.add_task(index_project, proj_id, db)
        return {"project": {"id": proj_id, "name": proj_name}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{project_id}/index")
def index_manual(project_id: int, user:User = Depends(get_current_user), db:Session =Depends(get_db)):
    # check permission
    
    try:
        proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    result = index_project(project_id, db=db)
    return result

@router.get("/{project_id}/status")
def status(project_id:int, user:User=Depends(get_current_user), db:Session =Depends(get_db)):
    # For simplicity return count of chunks
    
    try:
        proj = db.query(Project).filter(Project.id == project_id, Project.user_id == user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        chunk_count = db.query(Chunk).join(FileStore).filter(FileStore.project_id==project_id).count()
        return {"project_id": project_id, "chunk_count": chunk_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/list")
def list_projects(user:User = Depends(get_current_user), db:Session =Depends(get_db)):
    return project_by_user(user_id=user.id, db=db)


def delete_project_files(project_id: int):
    folder = f"project_{project_id}/"

    # delete from project files bucket
    supabase.storage.from_("project-files").remove([folder])

    # delete FAISS files too
    supabase.storage.from_("faiss-indexes").remove([folder])


@router.delete("/{project_id}")
def delete_project(project_id:int, db:Session =Depends(get_db)):
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        
        delete_project_files(project_id)
        
        db.delete(proj)
        db.commit()
        return {"message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# app/services/search.py
from fastapi import HTTPException
from app.embeddings.indexer import FaissIndex
from app.models.session_model import Chunk, FileStore
from sqlalchemy.orm import Session

def retrieve_top_k(project_id:int, query:str, db: Session, top_k=5):
    index = FaissIndex(project_id)
    # query faiss, map to chunk ids
    results = index.query(query, top_k=top_k)
    
    try:
        chunks = []
        for r in results:
            print("Search result:", r)
            chunk = db.query(Chunk).filter(Chunk.id == r["chunk_id"]).first()
            print("Mapped chunk:", chunk.file.id,project_id)
            if chunk and chunk.file.project_id == project_id:
                chunks.append({"text": chunk.text, "file_path": chunk.file.path, "start_line": chunk.start_line, "end_line": chunk.end_line, "score": r["distance"]})
        print("Retrieved chunks from search:", chunks)    
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        

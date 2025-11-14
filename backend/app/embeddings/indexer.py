# app/embeddings/indexer.py
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import threading
import pickle
import tempfile
from app.services.supabase_client import supabase

BASE_DIR = os.path.join(os.getcwd(), "data")  # each project will have its own folder
os.makedirs(BASE_DIR, exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIM = 384

# Use RLock so nested calls (add_vectors -> save) are safe
_LOCK = threading.RLock()


class FaissIndex:
    """
    Handles vector storage and retrieval for one project.
    Each project has its own index files inside data/project_<id>/.
    """
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.model = SentenceTransformer(MODEL_NAME)
        self.dim = EMBED_DIM

        self.project_dir = f"project_{self.project_id}/"
        os.makedirs(self.project_dir, exist_ok=True)

        self.index_file = os.path.join(self.project_dir, "faiss_index.bin")
        self.meta_file = os.path.join(self.project_dir, "faiss_meta.pkl")

        self.index = None
        self.id_map = {}
        self._load_or_init()

    def _load_or_init(self):
        bucket = "faiss-indexes"
        base = self.project_dir

        idx_bytes = supabase.storage.from_(bucket).download(f"{base}faiss_index.bin")
        meta_bytes = supabase.storage.from_(bucket).download(f"{base}faiss_meta.pkl")

        if idx_bytes and meta_bytes:
            tmp = tempfile.TemporaryDirectory()
            idx_path = os.path.join(tmp.name, "faiss_index.bin")
            meta_path = os.path.join(tmp.name, "faiss_meta.pkl")

            open(idx_path, "wb").write(idx_bytes)
            open(meta_path, "wb").write(meta_bytes)

            self.index = faiss.read_index(idx_path)
            self.id_map = pickle.load(open(meta_path, "rb"))
            self._next_id = max(self.id_map.keys()) + 1 if self.id_map else 0
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.id_map = {}
            self._next_id = 0


    def save(self):
        with _LOCK:
            with tempfile.TemporaryDirectory() as tmp:
                idx_file = os.path.join(tmp, "faiss_index.bin")
                meta_file = os.path.join(tmp, "faiss_meta.pkl")

                faiss.write_index(self.index, idx_file)
                with open(meta_file, "wb") as f:
                    pickle.dump(self.id_map, f)

                # upload to supabase storage
                bucket = "faiss-indexes"
                supabase.storage.from_(bucket).upload(
                    f"{self.project_dir}faiss_index.bin",
                    open(idx_file, "rb"),
                    file_options={"upsert": True},
                )
                supabase.storage.from_(bucket).upload(
                    f"{self.project_dir}faiss_meta.pkl",
                    open(meta_file, "rb"),
                    file_options={"upsert": True},
                )

    def add_vectors(self, texts, chunk_ids):
        """
        texts: list[str], chunk_ids: list[int]
        returns list of vector ids assigned
        """
        with _LOCK:
            print(f"[Project {self.project_id}] Adding {len(texts)} vectors...")
            embs = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            if embs.ndim == 1:
                embs = embs.reshape(1, -1)

            n = embs.shape[0]
            self.index.add(np.asarray(embs).astype("float32"))

            base = self.index.ntotal - n
            vector_ids = []
            for i, cid in enumerate(chunk_ids):
                vec_id = base + i
                self.id_map[vec_id] = cid
                vector_ids.append(vec_id)
                print(f"[Project {self.project_id}] Mapped chunk {cid} -> vector {vec_id}")

            self.save()
            return vector_ids

    def query(self, text, top_k=5):
        print(f"[Project {self.project_id}] Querying top {top_k} results...")
        emb = self.model.encode([text], convert_to_numpy=True)
        D, I = self.index.search(np.asarray(emb).astype("float32"), top_k)

        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            chunk_id = self.id_map.get(int(idx))
            if chunk_id is not None:
                results.append({"chunk_id": chunk_id, "distance": float(dist)})
        print(f"[Project {self.project_id}] Query results: {results}")
        return results

# Vector store logic placeholder

import faiss
import numpy as np
import os
import pickle
from .loader import load_documents

def embed(text: str) -> np.ndarray:
    return np.random.rand(384).astype("float32")  # dummy embedding

def create_or_load_vector_store():
    index_path = "backend/data/faiss_index/index.faiss"
    doc_path = "backend/data/faiss_index/docs.pkl"

    if os.path.exists(index_path) and os.path.exists(doc_path):
        index = faiss.read_index(index_path)
        with open(doc_path, "rb") as f:
            docs = pickle.load(f)
    else:
        docs = load_documents()
        embeddings = np.array([embed(doc) for doc in docs])
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        os.makedirs("backend/data/faiss_index", exist_ok=True)
        faiss.write_index(index, index_path)
        with open(doc_path, "wb") as f:
            pickle.dump(docs, f)
    return {"index": index, "docs": docs}

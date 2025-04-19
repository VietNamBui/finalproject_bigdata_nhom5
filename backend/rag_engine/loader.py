# Load data logic placeholder

import os

def load_documents(path: str = "backend/data/documents") -> list[str]:
    docs = []
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        if os.path.isfile(full_path) and filename.endswith(".txt"):
            with open(full_path, "r", encoding="utf-8") as f:
                docs.append(f.read())
    return docs

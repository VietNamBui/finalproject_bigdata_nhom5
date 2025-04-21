from backend.rag_engine.vector_store import inspect_documents
files = inspect_documents("backend/data/documents_cleaned")
print(f"Found {len(files)} files: {files}")
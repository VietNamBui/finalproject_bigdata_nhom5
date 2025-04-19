# Full RAG pipeline placeholder

from .vector_store import create_or_load_vector_store
from .retriever import search_similar_docs
from .generator import generate_answer

def rag_ask(question: str) -> str:
    store = create_or_load_vector_store()
    contexts = search_similar_docs(question, store)
    return generate_answer(question, contexts)


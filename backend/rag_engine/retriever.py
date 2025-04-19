# Retriever logic placeholder

from .vector_store import embed

def search_similar_docs(question: str, store: dict, top_k: int = 3) -> list[str]:
    vec = embed(question).reshape(1, -1)
    D, I = store["index"].search(vec, top_k)
    return [store["docs"][i] for i in I[0]]


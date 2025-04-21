# backend/rag_engine/rag_pipeline.py
from .vector_store import create_or_load_vector_store, search_similar_docs
from .generator import generate_answer

def rag_ask(question: str, model, model_name="gemini-embedding", api_key=None) -> str:
    """
    Run the RAG pipeline to answer a question.
    
    Args:
        question: The user's question
        model: Initialized Gemini model
        model_name: Embedding model name
        api_key: Gemini API key
    Returns:
        Answer as a string
    """
    print(f"Processing question: {question}")
    index = create_or_load_vector_store(model_name=model_name, api_key=api_key)
    contexts = search_similar_docs(question, index, top_k=5)
    print(f"Retrieved contexts: {contexts}")
    answer = generate_answer(question, contexts, model)
    print(f"Generated answer: {answer}")
    return answer
# backend/rag_engine/generator.py
from .gemini import generate_answer as gemini_generate_answer
from typing import List

def generate_answer(question: str, contexts: List[str], model) -> str:
    return gemini_generate_answer(model, question, contexts)
# backend/rag_engine/gemini.py
import google.generativeai as genai
from typing import List, Optional

def init_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

def generate_answer(model, question: str, contexts: List[str], history: Optional[List[dict]] = None) -> str:
    try:
        # Kết hợp contexts và question thành prompt
        context_text = "\n".join(contexts)
        prompt = f"Based on the following context, answer the question in a concise and accurate manner:\n\nContext:\n{context_text}\n\nQuestion: {question}"
        
        if history:
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
        else:
            response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating answer: {e}"
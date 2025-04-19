# backend/rag_engine/gemini.py
import google.generativeai as genai

def init_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash-latest")

def generate_answer(model, question: str, history=None):
    if history:
        chat = model.start_chat(history=history)
        response = chat.send_message(question)
    else:
        response = model.generate_content(question)
    return response.text

# backend/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .rag_engine.gemini import init_gemini, generate_answer
from .rag_engine.loader import load_documents
from .rag_engine.vector_store import create_or_load_vector_store
from .rag_engine.retriever import search_similar_docs

import os

app = FastAPI()

# Khởi tạo mô hình Gemini
gemini_model = init_gemini("AIzaSyD1e4ZLVLvnhqrmE6Nda5EsUBCbihukV2o")  # ⚠️ thay bằng API key thật của bạn

# Khởi tạo vector store một lần duy nhất khi khởi chạy
docs = load_documents("backend/data/documents")
vector_store = create_or_load_vector_store()

# Cho phép frontend truy cập API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    with open("frontend/chat.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/about", response_class=HTMLResponse)
async def about_page():
    with open("frontend/about.html", "r", encoding="utf-8") as f:
        return f.read()

# API chat
conversation_history = []

@app.post("/chat")
async def chat_api(request: Request):
    body = await request.json()
    question = body.get("question", "")

    # Tìm các đoạn văn tương tự
    contexts = search_similar_docs(question, vector_store)

    # Gọi Gemini để trả lời dựa trên ngữ cảnh
    answer = generate_answer(gemini_model, question, history=[{"role": "user", "parts": c} for c in contexts])

    conversation_history.append({"user": question, "bot": answer})

    return JSONResponse({"history": conversation_history})

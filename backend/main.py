# FastAPI main file placeholder

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

    # Giả lập trả lời từ mô hình
    answer = f"Bot trả lời: {question[::-1]}"  # giả lập đảo ngược

    conversation_history.append({"user": question, "bot": answer})

    return JSONResponse({"history": conversation_history})

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .rag_engine.gemini import init_gemini
from .rag_engine.rag_pipeline import rag_ask
import os
import re
import logging

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# Cấu hình Gemini
gemini_api_key = "AIzaSyD1e4ZLVLvnhqrmE6Nda5EsUBCbihukV2o"
gemini_model = init_gemini(gemini_api_key)
model_name = "gemini-embedding"

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thư mục tĩnh
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    logger.debug("Serving index.html")
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 failed for index.html, trying windows-1252")
        try:
            with open("frontend/index.html", "r", encoding="windows-1252") as f:
                content = f.read()
            with open("frontend/index.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Converted index.html to UTF-8")
            return content
        except Exception as e:
            logger.error(f"Error reading index.html: {e}")
            return HTMLResponse("Error: index.html not found", status_code=404)
    except FileNotFoundError:
        logger.error("index.html not found")
        return HTMLResponse("Error: index.html not found", status_code=404)

@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    logger.debug("Serving chat.html")
    try:
        with open("frontend/chat.html", "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 failed for chat.html, trying windows-1252")
        try:
            with open("frontend/chat.html", "r", encoding="windows-1252") as f:
                content = f.read()
            with open("frontend/chat.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Converted chat.html to UTF-8")
            return content
        except Exception as e:
            logger.error(f"Error reading chat.html: {e}")
            return HTMLResponse("Error: chat.html not found", status_code=404)
    except FileNotFoundError:
        logger.error("chat.html not found")
        return HTMLResponse("Error: chat.html not found", status_code=404)

@app.get("/about", response_class=HTMLResponse)
async def about_page():
    logger.debug("Serving about.html")
    try:
        with open("frontend/about.html", "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        logger.warning("UTF-8 failed for about.html, trying windows-1252")
        try:
            with open("frontend/about.html", "r", encoding="windows-1252") as f:
                content = f.read()
            with open("frontend/about.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Converted about.html to UTF-8")
            return content
        except Exception as e:
            logger.error(f"Error reading about.html: {e}")
            return HTMLResponse("Error: about.html not found", status_code=404)
    except FileNotFoundError:
        logger.error("about.html not found")
        return HTMLResponse("Error: about.html not found", status_code=404)

def route_question(question: str) -> str:
    question = question.lower().strip()
    logger.debug(f"Routing question: '{question}'")
    if re.search(r"\b(giới thiệu|about)\b", question):
        logger.info("Routed to about_page")
        return "about_page"
    elif re.search(r"\b(hỏi đáp|chat)\b", question):
        logger.info("Routed to chat_page")
        return "chat_page"
    elif re.search(r"\b(xin chào|hello|hi)\b", question):
        logger.info("Routed to greeting")
        return "greeting"
    logger.info("Routed to rag_ask")
    return "rag_ask"

conversation_history = []

@app.post("/chat")
async def chat_api(request: Request):
    try:
        body = await request.json()
        question = body.get("question", "").strip()
        if not question:
            logger.warning("Empty question received")
            return JSONResponse({"error": "Question cannot be empty"}, status_code=400)
        
        logger.info(f"Received question: '{question}'")
        route = route_question(question)
        logger.info(f"Route chosen: {route}")

        if route == "about_page":
            answer = "Đây là hệ thống RAG hỗ trợ trả lời câu hỏi dựa trên tài liệu. Xem chi tiết tại trang Giới thiệu."
        elif route == "chat_page":
            answer = "Bạn đang ở chế độ trò chuyện! Hãy đặt câu hỏi để tôi trả lời."
        elif route == "greeting":
            answer = "Xin chào! Hãy đặt câu hỏi về Big Data hoặc các chủ đề liên quan để tôi hỗ trợ."
        else:
            logger.debug("Calling rag_ask...")
            answer = rag_ask(question, gemini_model, model_name=model_name, api_key=gemini_api_key)
            logger.debug(f"rag_ask returned: {answer}")

        conversation_history.append({"user": question, "bot": answer})
        logger.info(f"Returning answer: '{answer}'")
        return JSONResponse({"history": conversation_history})
    except Exception as e:
        logger.error(f"Error in chat_api: {str(e)}", exc_info=True)
        return JSONResponse({"error": f"Error processing request: {str(e)}"}, status_code=500)
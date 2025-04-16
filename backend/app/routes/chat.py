from fastapi import APIRouter, UploadFile, File

router = APIRouter()

chat_history = []

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    chat_history.append({"filename": file.filename, "content": content.decode("utf-8")})
    return {"filename": file.filename}

@router.get("/history")
def get_history():
    return chat_history
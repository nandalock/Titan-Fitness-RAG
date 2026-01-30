import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
# 因为 main.py 和 ai_module.py 在同一个文件夹，直接 import 即可
from ai_module import AIFitnessAgent

class QuestionRequest(BaseModel):
    question: str
    chat_id: str


class QuestionResponse(BaseModel):
    answer: str
    source_documents: list
    processing_time: float

rag_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_system
    print(f"🚀 正在启动服务...")
    try:
        rag_system = AIFitnessAgent()
        rag_system.initialize_system()
        print("✅ 系统就绪")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    yield
    print("🛑 服务关闭")


app = FastAPI(title="Titan Fitness API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"message": "Server is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "rag_initialized": rag_system is not None and rag_system.is_initialized}


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    if not rag_system or not rag_system.is_initialized:
        raise HTTPException(status_code=503, detail="系统正在初始化")
    try:
        result = rag_system.ask_question(request.question, request.chat_id)
        return QuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream_ask")
async def stream_ask_question(request: QuestionRequest):
    """
    流式问答接口
    返回格式：application/x-ndjson (每一行是一个 JSON 对象)
    """
    # 1. 基础检查
    if rag_system is None:
        raise HTTPException(status_code=503, detail="系统未初始化完成")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    # 2. 获取生成器 (就是刚才你在 ai_module 里写的那个 ask_stream)
    # 注意：这里不需要 await，因为我们要把生成器本身传给 FastAPI
    generator = rag_system.ask_stream(request.question, request.chat_id)

    # 3. 返回流式响应
    # media_type="application/x-ndjson" 告诉前端：我会给你发很多行 JSON，每一行都是独立的
    return StreamingResponse(generator, media_type="application/x-ndjson")
@app.get("/ui")
async def get_ui():
    # 修复：获取当前脚本所在目录，确保能找到 index.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")

    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        return {"error": f"找不到文件: {html_path}"}


if __name__ == "__main__":
    import uvicorn

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8000)
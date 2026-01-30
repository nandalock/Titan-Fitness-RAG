import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件 (如果有的话)
load_dotenv()


class Settings:
    # --- 1. 基础路径配置 ---
    # 获取当前文件 (src/core/config.py) 的绝对路径
    _current_file = os.path.abspath(__file__)
    # 回退两层找到项目根目录 (src/core -> src -> AIFitnessAgent)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))

    # 定义数据目录 mydocs
    DATA_DIR = os.path.join(PROJECT_ROOT, "mydocs")

    # 定义向量库路径
    VECTOR_DB_DIR = os.path.join(DATA_DIR, "faiss_index")

    # 定义历史记录路径
    HISTORY_DIR = os.path.join(DATA_DIR, "history_chat")

    # --- 2. 模型与 API 配置 ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL_NAME = "qwen-plus"  # 你可以改成 qwen-turbo 或其他

    # --- 3. RAG 参数配置 ---
    CHUNK_SIZE = 300
    CHUNK_OVERLAP = 50
    VECTOR_SEARCH_TOP_K: int = 3
    # 中文友好的分隔符
    SEPARATORS = ["\n\n", "\n", "。", "！", "？", "，", "、", ""]

    def __init__(self):
        # 初始化时检查必要的配置
        if not self.OPENAI_API_KEY:
            print("⚠️ 警告: 未检测到 OPENAI_API_KEY 环境变量")


# 实例化单例对象，方便其他文件直接 import settings
settings = Settings()
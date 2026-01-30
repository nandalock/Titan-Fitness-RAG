import time
from langchain_community.embeddings import DashScopeEmbeddings

# 引入新架构组件
from core.config_data import settings
from core.logger import logger
from infra.vector_store_manager import VectorStoreManager
from services.chat_service import ChatService  # 👈 引入新写的服务


class AIFitnessAgent:
    def __init__(self):
        # 1. 基础检查
        if not settings.OPENAI_API_KEY:
            raise ValueError("未找到 API Key")

        # 2. 初始化基础设施 (Infra)
        self.embedding_model = DashScopeEmbeddings(
            model="text-embedding-v1",
            dashscope_api_key=settings.OPENAI_API_KEY
        )
        self.knowledge_base = VectorStoreManager(self.embedding_model)  # 我听你的改个名，叫 knowledge_base

        # 3. 初始化业务服务 (Services)
        # 把知识库交给聊天服务去用
        self.chat_service = ChatService(self.knowledge_base)

        self.is_initialized = False

    def initialize_system(self, force_rebuild=False):
        """系统启动入口"""
        start_time = time.time()
        logger.info("🚀 系统正在启动...")

        # 指挥知识库去加载数据
        self.knowledge_base.load_or_build(force_rebuild=force_rebuild)

        self.is_initialized = True
        logger.info(f"✅ 系统启动完成 (耗时: {time.time() - start_time:.2f}秒)")

    async def ask_stream(self, question: str, chat_id: str):
        """
        对外接口：这就叫“转发”，自己不干活，全交给 chat_service
        """
        if not self.is_initialized:
            # 这里的 yield 稍微特殊点，因为没法 import json，就简单的返回个错误流
            # 实际项目可以封装个统一错误返回
            yield '{"type": "error", "content": "System not initialized"}\n'
            return

        # ✅ 只有一行代码：委托给 chat_service
        async for chunk in self.chat_service.stream_chat(question, chat_id):
            yield chunk
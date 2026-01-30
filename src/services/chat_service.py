import json
import asyncio
import os
from langchain_classic.callbacks import AsyncIteratorCallbackHandler
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain

# 引入我们也需要的基建
from core.logger import logger
from core.config_data import settings
from infra.llm_factory import LLMFactory


class ChatService:
    """
    业务逻辑层：聊天服务
    职责：负责组装 RAG 链、执行流式对话、管理对话历史。
    """

    def __init__(self, vector_store_manager):
        # 依赖注入：我需要一个“知识库管理员”来帮我查资料
        self.vs_manager = vector_store_manager

    async def stream_chat(self, question: str, chat_id: str):
        """核心流式对话逻辑"""

        # 1. 准备传声筒
        callback = AsyncIteratorCallbackHandler()

        # 2. 找工厂要装备
        stream_llm = LLMFactory.create_chat_model(streaming=True, callbacks=[callback])
        silent_llm = LLMFactory.create_chat_model(streaming=False)

        # 3. 准备内存
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # 4. 找管理员要检索器
        try:
            retriever = self.vs_manager.get_retriever(k=3)
        except ValueError as e:
            # 如果知识库没准备好，直接报错
            yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False) + "\n"
            return

        # 5. 组装链
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=stream_llm,
            retriever=retriever,
            memory=memory,
            condense_question_llm=silent_llm,
            return_source_documents=True,
            verbose=False,
            output_key="answer"
        )

        # 6. 启动异步任务
        run_task = asyncio.create_task(qa_chain.ainvoke({"question": question}))

        # 7. 循环输出
        full_answer = ""
        async for token in callback.aiter():
            yield json.dumps({"type": "answer", "content": token}, ensure_ascii=False) + "\n"
            full_answer += token

        # 8. 获取结果
        try:
            result = await run_task
        except Exception as e:
            logger.error(f"❌ 生成过程中出错: {e}")
            yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False) + "\n"
            return

        # 9. 处理文档来源
        source_docs = []
        if result.get("source_documents"):
            for doc in result['source_documents']:
                source_docs.append({
                    "source": doc.metadata.get('source', '未知'),
                    "content": doc.page_content[:150]
                })

        if source_docs:
            yield json.dumps({"type": "sources", "content": source_docs}, ensure_ascii=False) + "\n"

        # 10. 保存历史 (这是业务逻辑的一部分，放在这里很合适)
        self._save_history(question, full_answer, chat_id)

    def _save_history(self, question, answer, chat_id):
        """内部方法：保存历史"""
        if not os.path.exists(settings.HISTORY_DIR):
            try:
                os.makedirs(settings.HISTORY_DIR)
            except OSError:
                pass

        file_path = os.path.join(settings.HISTORY_DIR, f"{chat_id}.json")
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                record = json.dumps({"q": question, "a": answer}, ensure_ascii=False)
                f.write(record + "\n")
        except Exception as e:
            logger.error(f"❌ 保存历史记录失败: {e}")
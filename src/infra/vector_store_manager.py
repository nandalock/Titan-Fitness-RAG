import os
import hashlib
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 引入核心配置和日志
from core.config_data import settings
from core.logger import logger


class VectorStoreManager:
    """
    基础设施层：向量库管理器
    职责：负责文档的加载、切分、向量化、存储以及索引的读取。
    """

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.vector_store = None

    def get_retriever(self, k=settings.VECTOR_SEARCH_TOP_K):
        """获取检索器，用于 RAG 链"""
        if not self.vector_store:
            raise ValueError("❌ 向量库尚未初始化，请先调用 load_or_build 方法。")
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def load_or_build(self, force_rebuild=False):
        """
        核心流程：尝试加载本地索引，如果失败或强制重建，则重新扫描文档构建
        """
        # 1. 尝试读取本地
        if not force_rebuild and os.path.exists(settings.VECTOR_DB_DIR):
            if self._load_local():
                return

        # 2. 如果没读到，或者要求重建，则开始构建
        logger.info("🔨 开始构建新的向量库...")
        documents = self._load_documents_from_disk()

        if not documents:
            self._create_empty_db()
        else:
            self._build_from_documents(documents)

    def _load_local(self):#给类自己内部使用的辅助逻辑
        """内部方法：加载本地索引"""
        logger.info(f"💾 发现本地向量库，正在加载: {settings.VECTOR_DB_DIR}")
        try:
            self.vector_store = FAISS.load_local(
                folder_path=settings.VECTOR_DB_DIR,
                embeddings=self.embedding_model,
                allow_dangerous_deserialization=True
            )
            logger.info("✅ 本地向量库加载成功")
            return True
        except Exception as e:
            logger.error(f"❌ 本地向量库加载失败: {e}")
            return False

    def _load_documents_from_disk(self):
        """内部方法：从 mydocs 目录加载 txt 文件"""
        documents = []
        if not os.path.exists(settings.DATA_DIR):
            try:
                os.makedirs(settings.DATA_DIR)
                logger.warning(f"⚠️ 目录不存在，已创建: {settings.DATA_DIR}")
            except Exception as e:
                logger.error(f"❌ 无法创建目录: {e}")
                return documents

        txt_files = [f for f in os.listdir(settings.DATA_DIR) if f.endswith(".txt")]
        if not txt_files:
            logger.warning("⚠️ 未找到 .txt 文件，将以空知识库运行。")
            return documents

        for file_name in txt_files:
            file_path = os.path.join(settings.DATA_DIR, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                documents.append(Document(page_content=content, metadata={"source": file_name}))
                logger.debug(f"已加载文档: {file_name}")
            except Exception as e:
                logger.error(f"❌ 加载 {file_name} 失败: {e}")

        return documents

    def _build_from_documents(self, documents):
        """内部方法：切分文档并存入向量库"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=settings.SEPARATORS,
        )
        all_splits = text_splitter.split_documents(documents)

        # 去重逻辑
        chunked_documents = []
        seen_hashes = set()
        for i, split in enumerate(all_splits):
            chunk_hash = hashlib.sha256(split.page_content.encode("utf-8")).hexdigest()
            if chunk_hash not in seen_hashes:
                seen_hashes.add(chunk_hash)
                split.metadata["chunk_index"] = i
                chunked_documents.append(split)

        logger.info(f"✂️ 有效文本块: {len(chunked_documents)}")

        try:
            self.vector_store = FAISS.from_documents(chunked_documents, self.embedding_model)
            self.vector_store.save_local(settings.VECTOR_DB_DIR)
            logger.info(f"💾 向量库已保存至: {settings.VECTOR_DB_DIR}")
        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            raise e

    def _create_empty_db(self):
        """内部方法：创建空库（兜底用）"""
        logger.warning("⚠️ 创建空向量数据库...")
        try:
            test_embedding = self.embedding_model.embed_query("test")
            dim = len(test_embedding)
            index = faiss.IndexFlatL2(dim)
            docstore = InMemoryDocstore({})
            self.vector_store = FAISS(
                index=index,
                embedding_function=self.embedding_model,
                docstore=docstore,
                index_to_docstore_id={}
            )
        except Exception as e:
            logger.error(f"❌ 创建空向量库失败: {e}")
            raise e
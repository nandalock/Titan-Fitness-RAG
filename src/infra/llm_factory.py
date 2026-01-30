from langchain_community.chat_models import ChatTongyi
# 因为 ai_module.py 和 core 文件夹在同一个层级
from core.config_data import settings
from core.logger import logger

class LLMFactory:
    """
    基础设施层：LLM 生产工厂
    职责：统一管理模型的实例化过程，包括参数配置、API Key 注入等。
    """

    @staticmethod #z这样可以不用实例
    def create_chat_model(streaming=False, callbacks=None):
        """
        创建一个通义千问模型实例
        :param streaming: 是否开启流式输出
        :param callbacks: 处理器回调列表
        """
        logger.debug(f"正在创建 LLM 实例 (streaming={streaming})")

        return ChatTongyi(
            model=settings.LLM_MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            streaming=streaming,
            callbacks=callbacks or []
        )
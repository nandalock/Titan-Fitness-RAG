import sys
import os

print("🔥 开始环境自检...")
print(f"🐍 当前 Python 解释器路径: {sys.executable}")

try:
    # 1. 测试 Memory (红线报错的地方)
    from langchain.memory import ConversationBufferMemory
    print("✅ [成功] Memory 模块加载正常")
except ImportError as e:
    print(f"❌ [失败] Memory 模块报错: {e}")

try:
    # 2. 测试 Chains (红线报错的地方)
    from langchain.chains import ConversationalRetrievalChain
    print("✅ [成功] Chains 模块加载正常")
except ImportError as e:
    print(f"❌ [失败] Chains 模块报错: {e}")

try:
    # 3. 测试 Callbacks (红线报错的地方)
    # 這是最新版正确的写法，PyCharm 可能会报红，但运行应该没问题
    from langchain_core.callbacks import AsyncIteratorCallbackHandler
    print("✅ [成功] Callbacks 模块加载正常")
except ImportError:
    try:
        # 备选方案：有时候在这里
        from langchain_core.callbacks.iterator import AsyncIteratorCallbackHandler
        print("✅ [成功] Callbacks 模块 (备选路径) 加载正常")
    except ImportError as e:
        print(f"❌ [失败] Callbacks 模块报错: {e}")

print("🎉 自检完成。如果有 3 个绿色对勾，请直接忽略 PyCharm 的红线！")
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    # 会话隔离字段：用来区分到底是张三还是李四在聊天
    session_id = Column(String(100), nullable=False, index=True, default="default")
    # role 是 OpenAI 格式里的角色类型: 'user', 'assistant', 'system', 'tool'
    role = Column(String(50), nullable=False)
    # 消息内容
    content = Column(Text, nullable=True)
    # 记录该条消息是否有相关的工具调用 (JSON string 存储，或者为了简单存在 extra 字段里)
    tool_calls = Column(JSON, nullable=True) 
    tool_call_id = Column(String(50), nullable=True) 
    name = Column(String(50), nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

class Account(Base):
    """
     Phase 8: 真实业务基石 —— 账号持久化凭证池
    """
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    pet_name = Column(String(50), unique=True, nullable=False)
    avatar = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

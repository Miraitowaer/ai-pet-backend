from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# 采用异步引擎连接 SQLite。
# echo=True 可以在控制台打印出底层的 SQL 语句，方便学习和调试
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False
)

# 声明式基类，所有的数据库模型（表）都要继承这个类
Base = declarative_base()

# 依赖注入函数：在 FastAPI 接口中获取数据库 Session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

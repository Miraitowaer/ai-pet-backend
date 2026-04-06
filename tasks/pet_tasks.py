import asyncio
from celery_app import celery_app
from database import AsyncSessionLocal
from services.llm_service import get_pet_response

@celery_app.task
def trigger_idle_interaction(session_id: str):
    """
    [重资产的后台任务] 模拟离线状态下，AI自发进行状态运算和耗时交互。
    它是被隔离在 Celery Worker 里跑的，天塌下来都不会阻塞住外网 HTTP 的访问。
    """
    print(f"[Celery Worker] ✅ 收到来自 RabbitMQ 的跑腿命令，开始接手用户 '{session_id}' 的耗时梳理...")
    
    # 核心架构难点：如何在同步的 Celery 工作线程里，驱动用 aiohttp 等极速库编写的异步逻辑！
    async def _do_async_work():
        # 桌宠闲聊互动模拟
        message = "【后台闲置触发逻辑】现在无聊地在后台看起了风景，可以顺便生成些互动感悟吗？"
        
        async with AsyncSessionLocal() as db:
            reply = await get_pet_response(message, session_id, db)
            
        return reply

    # 抛出单次专属事件循环强行等待
    background_result = asyncio.run(_do_async_work())
    
    print(f"[Celery Worker] 🎉 历尽艰辛计算完毕，将下方的 AI 反馈通过 Redis 返回网关：\n {background_result}")
    return background_result

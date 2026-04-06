from celery import Celery
from config import settings

# 实例化大厂专用的分布式任务对象
# backend 指定将跑完的结果临时缓存在哪里（不用每次都插 MySQL）
celery_app = Celery(
    "ai_pet_celery",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=["tasks.pet_tasks"]  # 让它启动时去哪个文件夹注册需要打工干活的具体脚本
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

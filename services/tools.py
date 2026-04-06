from datetime import datetime
from services.plugin_manager import plugin_registry

# 我们通过装饰器非常优雅地把这个函数“注册”为 Agent 的插件技能
@plugin_registry.register(
    name="get_current_time",
    description="获取当前精确的系统时间和日期。当主人询问几点了、今天几号等时间相关问题时，必须调用此工具。"
)
def get_current_time() -> str:
    """获取当前的系统时间"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"当前的系统精确时间是：{now_str}"

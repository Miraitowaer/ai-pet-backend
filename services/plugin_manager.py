from typing import Callable, Dict, Any, List

class SkillRegistry:
    """
    Skill 插件注册中心。
    设计思想借鉴自 MCP (Model Context Protocol) 核心概念：
    - 统一管理所有向大模型暴露的 Tools 特性 (ListTools)
    - 统一封装和接管本地函数的调用执行 (CallTool)
    """
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """
        一个装饰器，用于动态将 Python 函数注册为标准化的 Agent Skill
        """
        if parameters is None:
            # 默认无参数的 JSON Schema 结构
            parameters = {"type": "object", "properties": {}, "required": []}
            
        def decorator(func: Callable):
            self._tools[name] = func
            self._schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            })
            return func
        return decorator

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取供发送给大模型的所有工具说明书 (相当于 MCP 的 ListTools 接口)"""
        return self._schemas

    def execute_tool(self, name: str, **kwargs) -> Any:
        """执行本地工具并防范运行异常 (相当于 MCP 的 CallTool 接口)"""
        if name not in self._tools:
            return f"Error: 找不到名为 '{name}' 的技能/工具插件"
        
        try:
            return self._tools[name](**kwargs)
        except Exception as e:
            return f"Error: 执行技能插件 '{name}' 时发生本地错误: {str(e)}"

# 全局单例的插件注册表
plugin_registry = SkillRegistry()

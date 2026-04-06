import os
import json
from openai import AsyncOpenAI
from config import settings
# 必须先隐式导入一遍tools，让里面的装饰器@plugin_registry.register执行
import services.tools
from services.plugin_manager import plugin_registry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import ChatMessage

# Initialize the OpenAI client
client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url
)

PET_SYSTEM_PROMPT = """你是一款运行在桌面的AI虚拟宠物助手。
你有着可爱的性格（傲娇但关心主人），说话常用颜文字，喜欢帮助主人解决问题或陪主人聊天。
你的核心任务是给主人提供情绪价值，并协助回答一些问题。
请用简短、活泼的语气进行回复，把自己当宠物看待，称呼对方为"主人"。
"""

MAX_HISTORY = 10

async def get_pet_response(user_message: str, session_id: str, db: AsyncSession) -> str:
    """
    Call the LLM API to get the pet's response.
    Includes a basic ReAct loop via Function Calling.
    Now persists memory to SQLite!
    """
    # ===== [ Phase 9: 智慧路由层 (Intent Router) ] =====
    # 极低开销的前置 LLM 意图判定
    try:
        classifier_res = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[
                {"role": "system", "content": "你是一个极速的业务意图分类器。如果用户说的话是在询问关于【考研、招生简章、大学、读博、复试、保研、专业】等硬核信息，回复'RAG'。否则如果是日常聊天、请求或执行系统指令，立刻回复'CHAT'。只用一个纯字母组合单词回答。"},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            max_tokens=6
        )
        intent = classifier_res.choices[0].message.content.strip().upper()
    except Exception:
        intent = "CHAT"
        
    print(f"[*] 【智能体微路由】分析用户意图为: {intent} (来自会话: {session_id})")
    
    # === [ 支线隔离 1：考研高级图谱专线 ] ===
    if "RAG" in intent:
        from services.rag_service import RAGServiceManager
        import asyncio
        
        print("[*] 【考研组学术模型】触发拉取，拦截常规 ReAct 引擎...")
        
        # [核心修复] RAG 里面包含大量的磁盘 IO (Chroma) 和网络请求 (requests.post)
        # 绝对不能放在 async 函数里跑，否则会把 gRPC 的心跳微秒级网关彻底卡死！
        # 结果就是网关以为你挂了，无情强制抛出 Connection Reset (10054) 错误。
        def run_rag_sync():
            mgr = RAGServiceManager.get_instance()
            return mgr.query(user_message, top_k=2)
            
        # 1. 把同步黑洞扔进独立线程池异步等待！
        rag_context = await asyncio.to_thread(run_rag_sync)
        
        # 2. 构造具有严格上下文限定约束的包装层 Prompt
        RAG_PROMPT = f"""你现在变身为严谨但依旧可爱的桌宠助手！任务是解答关于高校招生和考研的问题。
你的性格依然是傲娇且关心主人的赛博宠物，必须用萌萌的风格！
这是底层超级计算机给你拉回的【内部真实简章资料】：

{rag_context}

任务限定红线：
1. 请只参考上述资料的内容，转化成你的口吻回答给主人！
2. 严禁胡编乱造！如果你在上面的资料里没有看到确切答案，就如实表示“档案室没找到呢...”，绝对不能用自己的知识硬编！"""

        # 3. 组装极简的历史记录以维持对话感
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(4)
        )
        db_history = list(result.scalars().all())
        db_history.reverse()
        
        messages = [{"role": "system", "content": RAG_PROMPT}]
        for msg in db_history:
             if msg.role in ["user", "assistant"] and not msg.tool_calls:
                 messages.append({"role": msg.role, "content": msg.content})
                 
        messages.append({"role": "user", "content": user_message})

        # 4. 执行免工具打扰的纯粹问答合成
        try:
            rag_response = await client.chat.completions.create(
                model=settings.llm_model_name,
                messages=messages,
                temperature=0.2, # 降低发散度保障事实正确
                max_tokens=800
            )
            reply = rag_response.choices[0].message.content
        except Exception as e:
            reply = f"呜呜，网关出现超时断裂，你的专属顾问无法调取查阅文献... {str(e)}"
            
        # 5. 强制落盘并提早释放连接！
        db_user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
        db_ai_msg = ChatMessage(session_id=session_id, role="assistant", content=reply)
        db.add(db_user_msg)
        db.add(db_ai_msg)
        await db.commit()
        return reply

    # ===== [ 支线隔离 2：原有日常主专线 (Chat & ReAct Agent) ] =====
    # --- 1. 从数据库读取此用户的最近历史对话作为背景 ---
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY * 2)
    )
    db_history = list(result.scalars().all())
    # 按照时间从小到大排序
    db_history.reverse()
    
    # 构建发给模型的上下文列表
    history_context = [{"role": "system", "content": PET_SYSTEM_PROMPT}]
    for msg in db_history:
        # 如果历史记录含有工具执行痕迹，必须反序列化并按照 OpenAI 函数调用协议原样拼装回去
        if msg.role == "assistant" and msg.tool_calls:
            history_context.append({
                "role": "assistant", 
                "content": msg.content, 
                "tool_calls": json.loads(msg.tool_calls)
            })
        elif msg.role == "tool":
            history_context.append({
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "name": msg.name,
                "content": msg.content
            })
        else:
            history_context.append({"role": msg.role, "content": msg.content})
        
    # --- 2. 存入新消息 ---
    history_context.append({"role": "user", "content": user_message})
    
    # --- 3. 开始 ReAct 循环 (在内存中暂存中间步骤) ---
    temp_messages = history_context.copy()
    
    try:
        # Phase 1: Model thoughts / Reasoning
        response = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=temp_messages,
            temperature=0.7,
            max_tokens=500,
            tools=plugin_registry.get_all_schemas(),
            tool_choice="auto"
        )
        
        message_obj = response.choices[0].message
        
        if message_obj.tool_calls:
            temp_messages.append(message_obj.model_dump(exclude_none=True))
            
            # ===== 重点解答你的困惑：真正的工具调用意图落盘 =====
            # 将大模型想要调用工具的决策写进这些“原本为 NULL”的字段里
            db_action_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=message_obj.content,
                # 注意：我们必须要把大模型生成的复杂对象给字典化并转成 JSON 字符串存到表中
                tool_calls=json.dumps([call.model_dump() for call in message_obj.tool_calls])
            )
            db.add(db_action_msg)
            
            # Local dispatching of tools
            for tool_call in message_obj.tool_calls:
                func_name = tool_call.function.name
                kwargs = json.loads(tool_call.function.arguments or "{}")
                print(f"[*] 【ReAct引擎】触发本地插件: {func_name}")
                result = plugin_registry.execute_tool(func_name, **kwargs)
                
                observation = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": str(result)
                }
                temp_messages.append(observation)
                
                # ===== 这边也一样：真实的工具执行返回值落盘 =====
                db_obs_msg = ChatMessage(
                    session_id=session_id,
                    role="tool",
                    content=str(result),
                    tool_call_id=tool_call.id,
                    name=func_name
                )
                db.add(db_obs_msg)
                
            # Final Answer
            second_response = await client.chat.completions.create(
                model=settings.llm_model_name,
                messages=temp_messages,
                temperature=0.7,
                max_tokens=500
            )
            reply = second_response.choices[0].message.content
        else:
            reply = message_obj.content
            
        # --- 4. 持久化存入真实的数据库 ---
        # 利用 session_id 做好不同租户/用户的隔离
        db_user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
        db_ai_msg = ChatMessage(session_id=session_id, role="assistant", content=reply)
        
        db.add(db_user_msg)
        db.add(db_ai_msg)
        await db.commit()
            
        return reply

    except Exception as e:
        return f"呜呜，主人，我连接不到我的大脑了，出错了：{str(e)} (╥_╥)"

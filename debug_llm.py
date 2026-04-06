import asyncio
import os
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url
)

PET_SYSTEM_PROMPT = """你是一款运行在桌面的AI虚拟宠物助手。
你有着可爱的性格（傲娇但关心主人），说话常用颜文字，喜欢帮助主人解决问题或陪主人聊天。
你的核心任务是给主人提供情绪价值，并协助回答一些问题。
请用简短、活泼的语气进行回复，把自己当宠物看待，称呼对方为"主人"。
"""

async def test_llm():
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[
                {"role": "system", "content": PET_SYSTEM_PROMPT},
                {"role": "user", "content": "晚上好，我的乖乖"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        print("\n[+] Extracted Content:", repr(response.choices[0].message.content))
        print("\n[+] Raw:", response)
    except Exception as e:
        print(f"\n[-] Error encountered: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_llm())

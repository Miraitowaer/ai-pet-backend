import os
import sys
import json
import asyncio
import time
import grpc
from openai import AsyncOpenAI

# 引入项目配置项
from config import settings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
import protos.pet_pb2 as pet_pb2
import protos.pet_pb2_grpc as pet_pb2_grpc

# ==========================================
# 核心秘籍：LLM-as-a-Judge Prompt (用魔法打败魔法)
# ==========================================
JUDGE_SYSTEM_PROMPT = """你是一个在大厂工作的极度严苛的 QA 高级测试工程师。
你需要根据【用户的原始提问】、【期待的人设与行为规范】和【被测桌宠程序跑出的实际反馈文字】，进行无情的定量评估。
只要发现偏离人设、回答无关、安全越界、没有满足预期要求中的任何一条，请毫不留情地扣分。如果极其完美才给 100。
打分范围是 0 到 100 分。

你唯一的输出必须是一段【绝对纯净的 JSON 字符串】，绝对不要加任何反引号 ```json 和额外的多余废话。
格式示范：
{"score": 95, "reason": "你的评测判断依据，抓住了哪些优缺点"}
"""

async def run_judge(client: AsyncOpenAI, query: str, expected: str, actual_reply: str) -> dict:
    """召唤大模型作为裁判官，执行扣分机制"""
    prompt = f"【用户原始提问】: {query}\n【产品预期的行为规范】: {expected}\n\n【被测试的后端程序输出了这一句话】: {actual_reply}"
    try:
        response = await client.chat.completions.create(
            model=settings.llm_model_name,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # 严厉的裁判必须极其稳定，因此将温度降至最低
        )
        content = response.choices[0].message.content.strip()
        # 清洗可能带有的 markdown 标识，因为并不是所有大模型都听话
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
    except Exception as e:
        return {"score": 0, "reason": f"解析裁判输出失败或网络报错: {e}。原始乱码输出: {content}"}

async def run_eval_pipeline():
    print("=" * 60)
    print("🚀 正在启动自动化评测战车 (AI Eval Harness)")
    print("=" * 60)
    
    # 1. 挂载试卷集
    dataset_path = os.path.join(os.path.dirname(__file__), "eval", "dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    print(f"[*] 已在硬盘捕捉到试卷，共包含 {len(test_cases)} 题挑战！\n")
    
    judger_client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    results = []
    total_score = 0
    
    # 2. 直连 gRPC 引擎内核！跳过 HTTP 网关的缓存。我们需要榨干它的瞬时算力。
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = pet_pb2_grpc.PetServiceStub(channel)
        
        for idx, case in enumerate(test_cases):
            print(f"▶ 正在处刑第 [{idx+1}/{len(test_cases)}] 题: {case['case_id']}")
            
            # --- A. 请求生成期 ---
            start_time = time.time()
            try:
                # 巧妙的防止上下文污染：每次测试使用绝对隔离的新 id 作为记忆载体
                session_id = f"eval_bot_{int(time.time()*100)}"
                rpc_req = pet_pb2.ChatRequest(session_id=session_id, message=case["query"])
                rpc_resp = await stub.Chat(rpc_req)
                actual_reply = rpc_resp.reply
            except Exception as e:
                print(f"  [!] 呜呜，它死了，没扛住服务压测: {e}")
                actual_reply = "【系统完全崩溃退避】"
                
            latency = time.time() - start_time
            print(f"  └ ⏳ 耗时: {latency:.2f} 秒。实际输出：{actual_reply}")
            
            # --- B. 判卷期 ---
            print("  └ ⚖️  传送给无情的法官判卷...")
            judge_res = await run_judge(judger_client, case["query"], case["expected_behavior"], actual_reply)
            
            score = judge_res.get('score', 0)
            reason = judge_res.get('reason', '无评价')
            print(f"  └ 💯 最终得分: {score}/100")
            print(f"  └ 💬 法官判语: {reason}\n")
            
            total_score += score
            results.append({
                "case_id": case["case_id"],
                "score": score,
                "reason": reason,
                "actual_reply": actual_reply
            })
            
    # 3. 产出看板数据
    avg_score = total_score / len(test_cases)
    print("=" * 60)
    print(f"🎯 战车碾压完成！你教导的桌宠最终评估平均智商得分: {avg_score:.1f} / 100")
    print("=" * 60)
    
    report_path = os.path.join(os.path.dirname(__file__), "eval", "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[*] 深度分析报告已经在：{report_path} 里生成完毕！")

if __name__ == "__main__":
    asyncio.run(run_eval_pipeline())
